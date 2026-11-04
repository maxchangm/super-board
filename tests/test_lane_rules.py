#!/usr/bin/env python3
"""The shared lane rules (references/lane-rules.md) are wired into every lane that must follow them.

Lane behaviour is prose an agent reads, so these tests pin the sentences a lane acts on: a rule removed
from a lane file, or a lane file that stops pointing at the rule, fails here.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
read = lambda p: (ROOT / p).read_text()
RUN = read("skills/super-board/references/run.md")
REVIEW = read("skills/super-review/SKILL.md")
QA = read("skills/super-qa/SKILL.md")
BUILD = read("skills/super-build/SKILL.md")
RULES = read("skills/super-board/references/lane-rules.md")
SCHEMA = read("skills/super-board/references/config-schema.json")
FLAT = lambda s: re.sub(r"\s+", " ", s)
CLOSE = "super-board-close-proof.py close"


class GateOne(unittest.TestCase):
    """A thread-only review stop is not a try."""

    def test_both_review_files_forbid_bumping_the_rebuild_label_and_post_the_marker(self):
        for name, text in (("run.md", RUN), ("super-review", REVIEW)):
            t = FLAT(text)
            self.assertIn("A thread-only stop is not a try", t, name)
            self.assertIn("do not add or raise `loop:rebuild-N`", t, name)
            self.assertIn("<!-- super-review:gate1:<issue>:<ids> -->", t, name)
            self.assertIn("that stop counts, raise `loop:rebuild-N`", t, name)

    def test_the_rule_text_says_the_same(self):
        t = FLAT(RULES)
        for phrase in ("does **not** add or raise `loop:rebuild-N`", "writes no Reviewer report",
                       "already appears in an earlier gate1 marker"):
            self.assertIn(phrase, t)


class Rounds(unittest.TestCase):
    """D27: every provable problem in round 1; later rounds verify; out-of-scope is filed, not sent back."""

    def test_rule_text(self):
        t = FLAT(RULES)
        for phrase in ("report **every problem you can prove**", "only (a) each finding of the previous round",
                       "new breakage in the lines changed since the previous round's head", "is **not a send-back**",
                       "The 3-try limit (`rebuild_cap`) stays"):
            self.assertIn(phrase, t)

    def test_qa_review_and_run_md_carry_it(self):
        self.assertIn("report **every problem you can prove**", FLAT(QA))
        self.assertIn("new breakage in lines changed since the previous round's head", FLAT(QA))
        self.assertIn("--found-by qa", QA)
        self.assertIn("round 1 lists every problem you can prove", FLAT(REVIEW))
        self.assertIn("--found-by review", REVIEW)
        self.assertIn("round 1 lists every problem you can prove", FLAT(RUN))
        self.assertIn("never bounces the card", FLAT(REVIEW))


class FoundProblems(unittest.TestCase):
    """D26: fixed in the same PR when the file is already changed; otherwise an intake issue."""

    def test_build_rule(self):
        for name, t in (("super-build", FLAT(BUILD)), ("run.md", FLAT(RUN)), ("lane-rules", FLAT(RULES))):
            self.assertIn("already changes", t, name)
            self.assertIn("`Found and fixed:`", t, name)
        self.assertIn("--found-by build", BUILD)
        self.assertIn("never Ready", RULES)


class CloseProof(unittest.TestCase):
    def test_merge_protocols_close_through_the_judge_not_by_hand(self):
        for name, text in (("run.md", RUN), ("super-review", REVIEW)):
            t = FLAT(text)
            self.assertIn(CLOSE, t, name)
            self.assertIn("Never close or move to Done by hand", t, name)
            self.assertIn("**QA**", t, name)

    def test_qa_runs_one_evidence_pass_per_merge_then_closes_through_the_judge(self):
        t = FLAT(QA)
        self.assertIn("### Close-held evidence pass", t)
        self.assertIn("<!-- super-board:close-held merge=<oid8> -->", t)
        self.assertIn("<!-- super-board:close-evidence merge=<oid8> -->", t)
        self.assertIn("close_proof.evidence_route", t)
        self.assertIn(CLOSE, t)
        self.assertIn("One evidence pass per merge", t)

    def test_the_judge_script_is_installed_with_the_other_bin_scripts(self):
        self.assertTrue((ROOT / "scripts/super-board-close-proof.py").is_file())
        self.assertIn("super-board-close-proof.py", read("install.sh") + read("CLAUDE.md"))


class ConfigKeys(unittest.TestCase):
    def test_schema_documents_the_project_keys_and_stays_project_agnostic(self):
        parsed = json.loads(re.sub(r"(?m)^\s*//.*$", "", SCHEMA))
        for key in ("ui_globs", "before_markers", "skip_markers", "evidence_route"):
            self.assertIn(key, parsed["close_proof"])
        self.assertIn("intake_column", parsed)
        for name, text in (("lane-rules", RULES), ("close-proof", read("scripts/super-board-close-proof.py"))):
            self.assertNotRegex(text.lower(), r"schoolmind|factory|src/app", name)


if __name__ == "__main__":
    unittest.main()
