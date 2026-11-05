#!/usr/bin/env python3
"""super-board-red-auto-merge.py — the GitHub half of merge_policy.red_auto_merge. Read-only, no writes.

    super-board-red-auto-merge.py --config <cfg.json> --repo <owner/name> --pr <N> --head <full sha>
                                  --expect-head <reviewed sha> --head-time <ISO-8601 committer date of --head>

The merge policy (super-board-merge-policy.py) already said the PR is held ONLY by the blast radius and touches no
excluded path. This answers the rest, and the gate skips the human only when `qualifies` is true:

- the Review passed this exact head (--expect-head is the head the Reviewer wrote down; the PR head is still it),
- the PR targets the config's base_branch,
- every issue the PR closes is merge_policy.red_auto_merge.roots, or a sub-issue of one at any depth
  (GraphQL `parent`, walked upward),
- the newest "**Reviewer's recommendation:** Merge." comment on the PR or those issues, posted by a bot listed in
  approval.trusted_request_bots, says Merge and is not older than the head commit.

Anything unreadable or missing answers `qualifies: false`: today's behaviour, the human decides.
Stdout: {"qualifies": bool, "why": str, "label": str, "issues": [N]}.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


def _load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


approval = _load("super-board-approval")
github_read = approval.github_read

# `**Reviewer's recommendation:** Merge.` or `... Do not merge.` alone on its line (the Review lane's block).
VERDICT = re.compile(r"\*\*Reviewer's recommendation:\*\*[ \t]*(Do not merge|Merge)\.?[ \t]*(?:\n|\Z)", re.I)
MAX_DEPTH = 25


class Live:
    def __init__(self, repo):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("missing or invalid repository")
        self.repo = repo
        self.github = approval.GitHub(repo)

    def base(self, pr):
        value = github_read.read(["pr", "view", str(pr), "--repo", self.repo, "--json", "baseRefName,headRefOid"], "json")[1]
        return value["baseRefName"]

    def pr(self, pr):
        return self.github.pr(pr)

    def comments(self, number):
        return self.github.comments(number)

    def parent(self, number):
        owner, name = self.repo.split("/")
        query = f'query{{repository(owner:"{owner}",name:"{name}"){{issue(number:{int(number)}){{parent{{number}}}}}}}}'
        issue = github_read.read(["api", "graphql", "-f", f"query={query}"], "json")[1]["data"]["repository"]["issue"]
        if issue is None:
            raise ValueError(f"issue #{number} not found")
        return (issue.get("parent") or {}).get("number")


def root_of(gh, number, roots):
    """The configured root that `number` is, or sits under at any depth; None when it is under none."""
    seen = set()
    while number is not None and number not in seen and len(seen) < MAX_DEPTH:
        if number in roots:
            return number
        seen.add(number)
        number = gh.parent(number)
    return None


def qualify(cfg, pr, head, expect, head_time, gh):
    rule = (cfg.get("merge_policy") or {}).get("red_auto_merge") or {}
    label = rule.get("label") or "red_auto_merge"
    roots = {int(r) for r in rule.get("roots") or []}

    def answer(ok, why, issues=()):
        return {"qualifies": ok, "why": why, "label": label, "issues": sorted(issues)}

    if not roots:
        return answer(False, "red_auto_merge has no roots")
    if len(expect or "") < 7 or not head.startswith(expect):
        return answer(False, "the Review did not pass this exact head")
    if gh.base(pr) != cfg.get("base_branch"):
        return answer(False, f"the PR does not target {cfg.get('base_branch')}")
    live_head, issues = gh.pr(pr)
    if live_head != head:
        return answer(False, "the PR head moved")
    if not issues:
        return answer(False, "the PR closes no issue")
    for number in sorted(issues):
        if root_of(gh, number, roots) is None:
            return answer(False, f"issue #{number} is not under {', '.join('#%d' % r for r in sorted(roots))}", issues)
    bots = approval.trusted_bots(cfg)
    verdicts = []
    for source in sorted(issues | {pr}):
        for comment in gh.comments(source):
            found = VERDICT.search(comment.get("body") or "")
            user = comment.get("user") or {}
            if found and user.get("type") == "Bot" and user.get("login") in bots:
                verdicts.append((approval.timestamp(comment.get("created_at")), found.group(1).lower() == "merge"))
    if not verdicts:
        return answer(False, "no Review recommendation from a trusted bot", issues)
    newest = max(t for t, _ in verdicts)
    if not all(merge for t, merge in verdicts if t == newest):
        return answer(False, "the newest Review recommendation is not Merge", issues)
    if newest < approval.timestamp(head_time):
        return answer(False, "the newest Review recommendation is older than the head commit", issues)
    under = ", ".join("#%d" % i for i in sorted(issues))
    return answer(True, f"{under} sits under the rewrite map, only the blast radius and/or the size limit held it, no auth-gate file changed, and the newest Review recommendation on this head is Merge", issues)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--expect-head", default="")
    ap.add_argument("--head-time", required=True)
    a = ap.parse_args()
    try:
        result = qualify(json.load(open(a.config)), a.pr, a.head, a.expect_head, a.head_time, Live(a.repo))
    except (ValueError, KeyError, TypeError, OSError) as error:
        result = {"qualifies": False, "why": f"evidence could not be verified ({type(error).__name__})", "label": "", "issues": []}
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except github_read.ReadHalted as error:
        print(f"GitHub read halt: {error}", file=sys.stderr)
        sys.exit(github_read.HALTED)
