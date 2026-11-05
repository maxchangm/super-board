#!/usr/bin/env python3
"""Offline tests for merge_policy.red_auto_merge: the policy half and the GitHub half. No network, no writes."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


policy = load("policy", "super-board-merge-policy.py")
helper = load("helper", "super-board-red-auto-merge.py")
HEAD = "a" * 40
EXCLUDE = ["src/lib/auth/**", "src/proxy.ts", "**/permissions/**"]
RULE = {"roots": [543], "exclude_globs": EXCLUDE, "label": "D40"}
BLAST = [{"category": "blast", "why": "label blast:red"}]
CFG = {"base_branch": "dev", "approval": {"trusted_request_bots": ["robot[bot]"]}, "merge_policy": {"red_auto_merge": RULE}}


def verdict(text="Merge", at="2026-11-05T10:00:00Z", login="robot[bot]", actor="Bot"):
    return {"body": f"**Review:** ok\n\n**Reviewer's recommendation:** {text}.\n**Why:** x", "created_at": at,
            "user": {"login": login, "type": actor}}


class Fake:
    """parents: issue -> parent; comments: source number -> comment list."""

    def __init__(self, parents, comments, issues=(42,), base="dev", head=HEAD):
        self.parents, self.by_source, self.issues, self.base_name, self.head = parents, comments, set(issues), base, head

    def base(self, pr):
        return self.base_name

    def pr(self, pr):
        return self.head, self.issues

    def comments(self, number):
        return self.by_source.get(number, [])

    def parent(self, number):
        return self.parents.get(number)


def run(gh, expect=HEAD, head_time="2026-11-05T09:00:00Z", cfg=CFG):
    return helper.qualify(cfg, 7, HEAD, expect, head_time, gh)


class PolicyHalf(unittest.TestCase):
    def eligible(self, human=BLAST, needs=(), paths=("src/lib/x.ts",), diff="", rule=RULE):
        return policy.red_auto_merge(rule, human, list(needs), list(paths), diff)["eligible"]

    def test_only_blast_and_size_holds_are_eligible(self):
        self.assertTrue(self.eligible())
        self.assertTrue(self.eligible(human=BLAST + [{"category": "size", "why": "big"}]))
        self.assertTrue(self.eligible(human=[{"category": "size", "why": "big"}]))
        self.assertFalse(self.eligible(human=[{"category": "size", "why": "big"}, {"category": "money", "why": "label"}]))
        self.assertFalse(self.eligible(human=BLAST + [{"category": "auth", "why": "label"}]))
        self.assertFalse(self.eligible(human=[]))
        self.assertFalse(self.eligible(needs=["run it"]))

    def test_not_configured_is_not_eligible(self):
        self.assertFalse(self.eligible(rule=None))
        self.assertFalse(self.eligible(rule={"roots": [], "exclude_globs": EXCLUDE}))

    def test_an_excluded_path_holds_even_when_renamed_away(self):
        self.assertFalse(self.eligible(paths=["src/lib/auth/session.ts"]))
        self.assertFalse(self.eligible(paths=["src/proxy.ts"]))
        moved = "diff --git a/src/lib/auth/a.ts b/src/lib/other/a.ts\nsimilarity index 100%\nrename from src/lib/auth/a.ts\nrename to src/lib/other/a.ts\n"
        self.assertFalse(self.eligible(paths=["src/lib/other/a.ts"], diff=moved))
        self.assertTrue(self.eligible(paths=["src/lib/other/a.ts"], diff=""))


class GitHubHalf(unittest.TestCase):
    PARENTS = {42: 563, 563: 543}

    def test_a_descendant_with_a_fresh_merge_recommendation_qualifies(self):
        out = run(Fake(self.PARENTS, {42: [verdict()]}))
        self.assertTrue(out["qualifies"], out)
        self.assertEqual(out["label"], "D40")

    def test_the_root_itself_and_a_deep_descendant_qualify(self):
        self.assertTrue(run(Fake({}, {543: [verdict()]}, issues=(543,)))["qualifies"])
        self.assertTrue(run(Fake({42: 7, 7: 8, 8: 563, 563: 543}, {42: [verdict()]}))["qualifies"])

    def test_an_issue_outside_the_roots_does_not(self):
        self.assertFalse(run(Fake({42: 100}, {42: [verdict()]}))["qualifies"])
        self.assertFalse(run(Fake({}, {42: [verdict()]}))["qualifies"])

    def test_one_linked_issue_outside_the_roots_holds_the_pr(self):
        gh = Fake({42: 563, 563: 543}, {42: [verdict()]}, issues=(42, 99))
        self.assertFalse(run(gh)["qualifies"])

    def test_a_parent_cycle_ends(self):
        self.assertFalse(run(Fake({42: 43, 43: 42}, {42: [verdict()]}))["qualifies"])

    def test_review_must_recommend_merge(self):
        self.assertFalse(run(Fake(self.PARENTS, {42: [verdict("Do not merge")]}))["qualifies"])
        self.assertFalse(run(Fake(self.PARENTS, {}))["qualifies"])
        newer_no = [verdict("Merge", "2026-11-05T10:00:00Z"), verdict("Do not merge", "2026-11-05T11:00:00Z")]
        self.assertFalse(run(Fake(self.PARENTS, {42: newer_no}))["qualifies"])
        newer_yes = [verdict("Do not merge", "2026-11-05T10:00:00Z"), verdict("Merge", "2026-11-05T11:00:00Z")]
        self.assertTrue(run(Fake(self.PARENTS, {42: newer_yes}))["qualifies"])

    def test_a_tie_with_a_no_holds(self):
        tie = [verdict("Merge"), verdict("Do not merge")]
        self.assertFalse(run(Fake(self.PARENTS, {42: tie}))["qualifies"])

    def test_a_recommendation_older_than_the_head_commit_does_not_count(self):
        gh = Fake(self.PARENTS, {42: [verdict(at="2026-11-05T08:00:00Z")]})
        self.assertFalse(run(gh)["qualifies"])

    def test_only_a_listed_bot_counts(self):
        self.assertFalse(run(Fake(self.PARENTS, {42: [verdict(login="someone", actor="User")]}))["qualifies"])
        self.assertFalse(run(Fake(self.PARENTS, {42: [verdict(login="other[bot]")]}))["qualifies"])

    def test_a_conditional_recommendation_is_not_merge(self):
        comment = verdict()
        comment["body"] = "**Reviewer's recommendation:** Merge after the migration runs.\n"
        self.assertFalse(run(Fake(self.PARENTS, {42: [comment]}))["qualifies"])

    def test_the_comment_on_the_pr_counts(self):
        self.assertTrue(run(Fake(self.PARENTS, {7: [verdict()]}))["qualifies"])

    def test_the_review_must_have_passed_this_exact_head(self):
        gh = Fake(self.PARENTS, {42: [verdict()]})
        self.assertFalse(run(gh, expect="")["qualifies"])
        self.assertFalse(run(gh, expect="b" * 40)["qualifies"])
        self.assertTrue(run(gh, expect=HEAD[:12])["qualifies"])
        self.assertFalse(run(Fake(self.PARENTS, {42: [verdict()]}, head="c" * 40))["qualifies"])

    def test_the_base_branch_must_match(self):
        self.assertFalse(run(Fake(self.PARENTS, {42: [verdict()]}, base="main"))["qualifies"])

    def test_no_roots_never_qualifies(self):
        cfg = {"base_branch": "dev", "merge_policy": {}}
        self.assertFalse(run(Fake(self.PARENTS, {42: [verdict()]}), cfg=cfg)["qualifies"])

    def test_an_unreadable_head_time_raises_so_main_fails_closed(self):
        with self.assertRaises(ValueError):
            run(Fake(self.PARENTS, {42: [verdict()]}), head_time="")


if __name__ == "__main__":
    unittest.main()
