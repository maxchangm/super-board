#!/usr/bin/env python3
"""Read-only, head-bound human approval shared by the planner and merge gate.

A trusted request pins the code and human steps BEFORE a human replies `done`.
Labels only describe UI state. They never authorize a merge. No GitHub writes.
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from datetime import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

_reader_spec = importlib.util.spec_from_file_location("github_read", Path(__file__).with_name("super-board-github-read.py"))
github_read = importlib.util.module_from_spec(_reader_spec)
_reader_spec.loader.exec_module(github_read)

PREFIX = "approval-request: "
SHA = re.compile(r"[0-9a-f]{40}\Z")
SCOPE = re.compile(r"[0-9a-f]{64}\Z")
PATCH = re.compile(r"[0-9a-f]{64}\Z")
BLOCK = re.compile(r"Reason tag:[^\n]*🙋|^approval-request:", re.M)
DONE = re.compile(r"\s*done[.!]?\s*\Z", re.I)
# GitHub's closing keywords: KEYWORD[:] #N or KEYWORD[:] owner/repo#N.
CLOSES = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?):?\s+([\w.-]+/[\w.-]+)?#(\d+)\b", re.I)


def body_links(body, repo):
    """Same-repo issues a PR body closes; other-repo references are ignored."""
    return {int(n) for other, n in CLOSES.findall(body) if not other or other.lower() == repo}


def scope_for(plan):
    # Exclude UI-only `done`; a label change must not change what was approved.
    relevant = {key: plan.get(key, []) for key in ("human", "migrations", "run", "needs_you")}
    return hashlib.sha256(json.dumps(relevant, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def request_for(repo, pr, head, scope, patch=None):
    # patch: sha256 of the PR's own changes, byte for byte (its diff against the merge base with the base branch,
    # minus hunk line numbers and index lines; the merge gate builds it).
    request = {"repo": repo.lower(), "pr": int(pr), "head": head, "scope": scope}
    if patch:
        request["patch"] = patch
    return request


def covers(request, expected):
    """Does an approved request still describe the code and steps being checked?

    Same head: yes. A newer head: only when both carry the same diff hash, so merging the base into the
    PR keeps the approval while any change to the PR's own diff (even a force-push) voids it.
    """
    rest = {k: v for k, v in expected.items() if k not in ("head", "patch")}
    if any(request.get(k) != v for k, v in rest.items()):
        return False
    return request.get("head") == expected.get("head") or bool(
        request.get("patch") and request.get("patch") == expected.get("patch"))


def marker(request):
    return PREFIX + json.dumps(request, sort_keys=True, separators=(",", ":"))


def parse_request(comment):
    lines = [line for line in (comment.get("body") or "").splitlines() if line.startswith(PREFIX)]
    if len(lines) != 1:
        return None
    try:
        value = json.loads(lines[0][len(PREFIX):])
        if (not isinstance(value, dict) or not isinstance(value.get("repo"), str)
                or not re.fullmatch(r"[^/\s]+/[^/\s]+", value["repo"])
                or type(value.get("pr")) is not int or value["pr"] < 1
                or not SHA.fullmatch(value.get("head", ""))
                or not SCOPE.fullmatch(value.get("scope", ""))
                or ("patch" in value and not PATCH.fullmatch(str(value["patch"])))):
            return None
        return value
    except (ValueError, TypeError):
        return None


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("missing comment timestamp")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("comment timestamp lacks timezone")
    return result


def trusted_bots(config):
    """Logins the board config lists in approval.trusted_request_bots: bots whose request comment counts. Default none."""
    bots = ((config or {}).get("approval") or {}).get("trusted_request_bots") or []
    return frozenset(b for b in bots if isinstance(b, str))


def can_request(user, permission, bots):
    # A request pins the code and steps before a human replies `done`. A listed bot may post it; no other bot may.
    if user.get("type") == "Bot" and user.get("login") in bots:
        return True
    return permission(user["login"]) in ("write", "maintain", "admin")


def trusted_blocks(comments, permission, bots=frozenset()):
    result = []
    for block in comments:
        if not BLOCK.search(block.get("body") or ""):
            continue
        user = block.get("user") or {}
        if not user.get("login") or user.get("type") not in ("User", "Bot"):
            raise ValueError("requester identity could not be verified")
        if can_request(user, permission, bots):
            result.append(block)
    return result


def validate(comments, expected, permission, bots=frozenset()):
    """Pure verdict; permission(login) is a current repository permission lookup."""
    def hold(why):
        return {"approved": False, "why": why}

    if not SHA.fullmatch(expected.get("head", "")):
        return hold("current PR head is unavailable")
    try:
        blocks = trusted_blocks(comments, permission, bots)
        if not blocks:
            return hold("no request from a trusted repository collaborator")
        # Any later human block supersedes the old request, including one with
        # missing/malformed metadata. Equal-second requests are ambiguous: hold.
        latest_time = max(timestamp(c.get("created_at")) for c in blocks)
        latest = [c for c in blocks if timestamp(c.get("created_at")) == latest_time]
        if len(latest) != 1:
            return hold("ambiguous newest human request")
        request_comment = latest[0]
        request = parse_request(request_comment)
        if request is None or not covers(request, expected):
            return hold("the latest request does not cover the current code and human steps")
        if timestamp(request_comment.get("updated_at")) != latest_time:
            return hold("approval request was edited; post a fresh request")
        requester = request_comment.get("user") or {}
        if not requester.get("login") or not can_request(requester, permission, bots):
            return hold("requester authority could not be verified")
        if not isinstance(request_comment.get("source"), int) or not request_comment.get("id"):
            return hold("request identity is missing")
        for comment in comments:
            if (not comment.get("id") or not DONE.fullmatch(comment.get("body") or "")
                    or comment.get("source") != request_comment.get("source")):
                continue
            created = timestamp(comment.get("created_at"))
            if created <= latest_time or timestamp(comment.get("updated_at")) != created:
                continue
            author = comment.get("user") or {}
            if (author.get("type") == "User" and author.get("login")
                    and permission(author["login"]) in ("write", "maintain", "admin")):
                return {"approved": True, "why": "trusted human confirmed the current request",
                        "carriedFrom": request["head"] if request["head"] != expected["head"] else None,
                        "request": request, "requestId": request_comment.get("id"),
                        "approvalId": comment.get("id"), "approver": author["login"]}
        return hold("waiting for a trusted human to comment done on the current request")
    except (ValueError, TypeError, KeyError):
        return hold("approval evidence is incomplete or unreadable")


class GitHub:
    def __init__(self, repo):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("missing or invalid repository")
        self.repo = repo.lower()
        self.permissions = {}

    @staticmethod
    def read(*args):
        kind = ("approval" if "graphql" in args else "comments" if "--paginate" in args
                else "permission" if args[-1].endswith("/permission") else "json")
        return github_read.read(list(args), kind)[1]

    def permission(self, login):
        if not re.fullmatch(r"[A-Za-z0-9_-]+(?:\[bot\])?", login):
            return None
        if login not in self.permissions:
            value = self.read("api", f"repos/{self.repo}/collaborators/{login}/permission")
            self.permissions[login] = value.get("permission")
        return self.permissions[login]

    def comments(self, number):
        pages = self.read("api", "--paginate", "--slurp",
                          f"repos/{self.repo}/issues/{number}/comments?per_page=100")
        if not isinstance(pages, list) or not pages or any(not isinstance(p, list) for p in pages):
            raise ValueError("unreadable comments")
        if any(not isinstance(c, dict) for page in pages for c in page):
            raise ValueError("unreadable comment")
        return [dict(comment, source=number) for page in pages for comment in page]

    def pr(self, number):
        # Paginate linked issues too: an omitted newer request must never make
        # an older approval authoritative. Remote-repository links are ignored.
        # GitHub fills closingIssuesReferences only for PRs into the default
        # branch, so a PR into another base takes its body's closing keywords,
        # read in this same head-pinned snapshot.
        query = '''query($owner:String!,$repo:String!,$pr:Int!,$endCursor:String){
          repository(owner:$owner,name:$repo){defaultBranchRef{name}
            pullRequest(number:$pr){headRefOid state baseRefName body
            closingIssuesReferences(first:100,after:$endCursor){
              pageInfo{hasNextPage endCursor} nodes{number repository{nameWithOwner}}
            }}}}'''
        owner, name = self.repo.split("/")
        pages = self.read("api", "graphql", "--paginate", "--slurp", "-f", f"query={query}",
                          "-F", f"owner={owner}", "-F", f"repo={name}", "-F", f"pr={number}")
        snapshots, issues = set(), set()
        if not isinstance(pages, list) or not pages:
            raise ValueError("unreadable PR")
        for page in pages:
            if page.get("errors"):
                raise ValueError("incomplete PR response")
            repository = page["data"]["repository"]
            pr = repository["pullRequest"]
            if pr["state"] != "OPEN":
                raise ValueError("PR is not open")
            snapshots.add((pr["headRefOid"], pr["baseRefName"], pr["body"],
                           (repository["defaultBranchRef"] or {}).get("name")))
            links = pr["closingIssuesReferences"]
            for issue in links["nodes"]:
                if issue["repository"]["nameWithOwner"].lower() == self.repo:
                    issues.add(issue["number"])
        if links["pageInfo"]["hasNextPage"] or len(snapshots) != 1:
            raise ValueError("PR changed or issue links are incomplete")
        head, base, body, default = snapshots.pop()
        if not all(isinstance(v, str) for v in (head, base, body, default)) or not SHA.fullmatch(head):
            raise ValueError("unreadable PR head, base or body")
        if base != default:
            issues |= body_links(body, self.repo)
        return head, issues

    def check(self, number, head=None, scope=None, issue=None, bots=frozenset(), patch=None):
        current_head, issues = self.pr(number)
        if issue is not None and issue not in issues:
            return {"approved": False, "why": "request issue is not linked to this PR"}
        if head is not None and current_head != head:
            return {"approved": False, "headChanged": True, "why": "PR head changed after review"}
        comments = []
        for source in sorted(issues | {number}):
            comments.extend(self.comments(source))
        expected = {"repo": self.repo, "pr": number, "head": current_head}
        if scope is not None:
            expected["scope"] = scope
        if patch:
            expected["patch"] = patch
        return validate(comments, expected, self.permission, bots)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int)
    ap.add_argument("--head")
    ap.add_argument("--patch", help="sha256 of the PR's exact own diff; lets an approval survive a base merge")
    ap.add_argument("--plan", help="JSON plan from merge-policy")
    ap.add_argument("--request", action="store_true", help="print a pinned request; no network or writes")
    ap.add_argument("--deps", action="store_true", help="enrich the dependency graph on stdin")
    ap.add_argument("--config", help="board config JSON; approval.trusted_request_bots lists bots whose request counts")
    args = ap.parse_args()
    bots = trusted_bots(json.load(open(args.config))) if args.config else frozenset()
    # The wave planner reads the config once (it may be a pipe), so it hands the list down in the environment.
    bots |= trusted_bots({"approval": {"trusted_request_bots": json.loads(os.environ.get("SB_TRUSTED_REQUEST_BOTS") or "[]")}})
    if args.request:
        if not args.pr or not args.head or not SHA.fullmatch(args.head) or not args.plan:
            ap.error("request requires --pr, full --head and --plan")
        print(marker(request_for(args.repo, args.pr, args.head, scope_for(json.loads(args.plan)), args.patch)))
        return
    if args.deps:
        graph = json.load(sys.stdin)
        github = GitHub(args.repo) if args.repo else None
        for entry in graph.values():
            entry["needsYouDone"] = False
            entry["approvalRefresh"] = False
            if not entry.get("needsYou") or github is None:
                continue
            try:
                comments = github.comments(entry["number"])
                blocks = trusted_blocks(comments, github.permission, bots)
                latest = max(blocks, key=lambda c: timestamp(c.get("created_at"))) if blocks else {}
                request = parse_request(latest)
                if request is None or request["repo"] != github.repo:
                    continue
                result = github.check(request["pr"], head=request["head"], issue=entry["number"], bots=bots)
                entry["needsYouDone"] = result["approved"]
                entry["approvalRefresh"] = result.get("headChanged", False)
                entry["approvalWhy"] = result["why"]
            except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
                entry["approvalWhy"] = "approval evidence could not be verified"
        print(json.dumps(graph))
        return
    if not args.pr or not args.head or not args.plan:
        ap.error("check requires --pr, --head and --plan")
    try:
        result = GitHub(args.repo).check(args.pr, args.head, scope_for(json.loads(args.plan)), bots=bots, patch=args.patch)
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError):
        result = {"approved": False, "why": "approval evidence could not be verified"}
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except github_read.ReadHalted as error:
        print(f"GitHub read halt: {error}", file=sys.stderr)
        sys.exit(github_read.HALTED)
