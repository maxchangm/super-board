#!/usr/bin/env python3
"""Close proof: the verdict rules and the `close` path, offline (gh and the card script are stubs)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/super-board-close-proof.py"
spec = importlib.util.spec_from_file_location("close_proof", SCRIPT)
cp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cp)

BOT = "app[bot]"
HEAD = "a1b2c3d4" * 5
MERGE = "f0e1d2c3" * 5


def c(body, by=BOT, at="2026-11-04T01:00:00Z"):
    return {"body": body, "by": by, "at": at}


def table(*rows):
    return c("### Acceptance criteria\n| Check | Result |\n|---|---|\n" + "\n".join(rows))


class JudgeTests(unittest.TestCase):
    def test_images_once_per_url_at_most_six(self):
        self.assertEqual(cp.images_of('![a](https://x/1.png) <img width="9" src="https://x/2.png"> ![dup](https://x/1.png)'),
                         ["![a](https://x/1.png)", "![](https://x/2.png)"])
        self.assertEqual(len(cp.images_of(" ".join(f"![](https://x/{i}.png)" for i in range(9)))), 6)

    def test_boxes_are_only_those_under_the_acceptance_heading(self):
        body = "## Notes\n- [ ] not a criterion\n## Acceptance Criteria\n- [ ] One\n- [x] Two\n\n## Later\n- [ ] Three"
        self.assertEqual([(b["text"], b["checked"], b["line"]) for b in cp.acceptance_boxes(body)], [("One", False, 3), ("Two", True, 4)])

    def test_rows_keep_pass_and_fail(self):
        rows = cp.acceptance_rows("x\n### Acceptance criteria\n| Check | Result |\n|---|---|\n| A | PASS: it works. More text. |\n"
                                  "| B | **FAIL**: broken |\n\n### Other\n| C | PASS: no |")
        self.assertEqual(rows, [{"criterion": "A", "pass": True, "proof": "it works."},
                                {"criterion": "B", "pass": False, "proof": "**FAIL**: broken"}])

    def test_after_is_the_newest_bot_comment_naming_the_head(self):
        v = cp.judge({"labels": ["bug"], "head": HEAD, "merge": MERGE, "comments": [
            c(f"QA at {HEAD}\n![old](https://x/old.png)", at="2026-11-03T00:00:00Z"),
            c(f"QA at {HEAD}\n![new](https://x/new.png)", at="2026-11-04T00:00:00Z"),
            c("QA at ffffffff\n![other](https://x/other.png)", at="2026-11-04T02:00:00Z"),
            c(f"a person says {HEAD}\n![human](https://x/human.png)", by="max", at="2026-11-04T03:00:00Z")]})
        after = v["comment"].split("**After**")[1]
        self.assertTrue(v["ok"])
        self.assertIn("![new](https://x/new.png)", after)
        for gone in ("old", "other", "human"):
            self.assertNotIn(gone, after)

    def test_after_may_name_the_merge_commit(self):
        v = cp.judge({"labels": ["bug"], "head": HEAD, "merge": MERGE, "comments": [
            c(f"QA at {HEAD}\nno image", at="2026-11-03T00:00:00Z"),
            c(f"Evidence at merge commit {MERGE[:8]}\n![evidence](https://x/e.png)", at="2026-11-04T00:00:00Z"),
            c("Evidence at 99999999\n![other](https://x/o.png)", at="2026-11-04T02:00:00Z")]})
        self.assertTrue(v["ok"])
        self.assertIn("e.png", v["comment"])
        self.assertNotIn("o.png", v["comment"])

    def test_our_own_markers_are_never_read_back_as_after(self):
        for marker in (cp.PROOF_MARKER, f"<!-- super-board:close-evidence merge={MERGE[:8]} -->", cp.HELD(MERGE)):
            v = cp.judge({"labels": ["bug"], "head": HEAD, "merge": MERGE, "comments": [c(f"{HEAD}\n![x](https://x/x.png)\n{marker}")]})
            self.assertFalse(v["ok"], marker)

    def test_bug_without_after_is_held_with_the_marker(self):
        v = cp.judge({"labels": ["bug"], "head": HEAD, "merge": MERGE, "comments": []})
        self.assertFalse(v["ok"])
        self.assertIn("no AFTER screenshot", v["note"])
        self.assertIn(f"<!-- super-board:close-held merge={MERGE[:8]} -->", v["note"])

    def test_refactor_neither_kind_and_stated_reason_close_without_images(self):
        self.assertIn("refactor with no UI change", cp.judge({"labels": ["refactor", "bug"]})["comment"])
        self.assertIn("neither a bug nor a feature", cp.judge({"labels": ["chore"]})["comment"])
        v = cp.judge({"labels": ["bug"], "head": HEAD, "comments": [c(f"QA at {HEAD}\nNo visual surface: nothing renders.")]})
        self.assertIn("**No visual surface:** nothing renders.", v["comment"])

    def test_before_comes_from_the_marker_comment_else_the_reporter(self):
        cfg = {"close_proof": {"before_markers": ["<!-- repro -->"]}}
        base = {"labels": ["bug"], "head": HEAD, "body": "![mine](https://x/reporter.png)",
                "comments": [c("<!-- repro -->\n![r](https://x/repro.png)", at="2026-11-01T00:00:00Z"), c(f"QA {HEAD}\n![a](https://x/a.png)")]}
        self.assertIn("repro.png", cp.judge(base, cfg)["comment"].split("**After**")[0])
        self.assertIn("reporter.png", cp.judge(base)["comment"].split("**After**")[0])
        # a marked comment that names the head is still not an AFTER
        both = dict(base, comments=[c(f"<!-- repro -->\n{HEAD}\n![r](https://x/repro.png)")])
        self.assertFalse(cp.judge(both, cfg)["ok"])

    def test_skip_markers_keep_a_project_comment_out_of_after(self):
        cfg = {"close_proof": {"skip_markers": ["<!-- fuzz -->"]}}
        inputs = {"labels": ["bug"], "head": HEAD, "comments": [c(f"{HEAD}\n![f](https://x/f.png)\n<!-- fuzz -->")]}
        self.assertFalse(cp.judge(inputs, cfg)["ok"])
        self.assertTrue(cp.judge(inputs)["ok"])

    def test_boxes_by_position_then_by_words_and_fail_proves_nothing(self):
        body = "## Acceptance Criteria\n- [ ] Rendered bytes equal today's output for the fixtures\n- [ ] An unknown variable throws"
        pos = cp.judge({"labels": ["refactor"], "body": body, "comments": [table("| Same bytes | PASS: digests match. |", "| Throws | PASS: test at line 7. |")]})
        self.assertTrue(pos["ok"])
        self.assertIn("- [x] An unknown variable throws", pos["body"])
        words = cp.judge({"labels": ["refactor"], "body": body, "comments": [table("| Unknown variable throws | PASS: ok. |")]})
        self.assertFalse(words["ok"])
        self.assertIn("- Rendered bytes equal", words["note"])
        self.assertFalse(cp.judge({"labels": ["refactor"], "body": body, "comments": [table("| a | PASS: x. |", "| b | FAIL: y. |")]})["ok"])
        self.assertIsNone(cp.judge({"labels": ["refactor"], "body": "## Acceptance Criteria\n- [x] Done already"})["body"])

    def test_approved_change_needs_after_only_when_a_ui_file_changed(self):
        cfg = {"close_proof": {"ui_globs": ["src/app/**", "!src/app/api/**", "src/components/**", "**/*.css"]}}
        base = {"labels": ["approved-change"], "head": HEAD, "comments": [c(f"QA at {HEAD}\nNo visual surface: nothing renders.")]}
        for f in ("src/app/page.tsx", "src/components/a/B.tsx", "src/styles/site.css"):
            self.assertFalse(cp.judge({**base, "files": ["docs/a.md", f]}, cfg)["ok"], f)
        for files in ([], ["src/lib/a.ts", "src/app/api/x/route.ts", "tests/a.test.ts"]):
            self.assertIn("approved change with no UI file", cp.judge({**base, "files": files}, cfg)["comment"])
        self.assertTrue(cp.judge({**base, "files": ["src/app/page.tsx"], "comments": [c(f"QA at {HEAD}\n![x](https://x/x.png)")]}, cfg)["ok"])

    def test_without_ui_globs_every_file_is_ui(self):
        base = {"labels": ["approved-change"], "head": HEAD, "files": ["src/lib/a.ts"], "comments": []}
        self.assertFalse(cp.judge(base)["ok"])

    def test_glob_rules(self):
        g = ["src/app/**", "!src/app/api/**", "**/*.css"]
        self.assertTrue(cp.is_ui_file("src/app/a/page.tsx", g) and cp.is_ui_file("x/y/z.css", g) and cp.is_ui_file("a.css", g))
        self.assertFalse(cp.is_ui_file("src/app/api/x/route.ts", g) or cp.is_ui_file("src/lib/a.ts", g))


STUB_GH = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >> "$GH_LOG"
case "$*" in
  *"--input -"*) cat > "$GH_LOG.stdin" ;;
  *"issue comment"*) cat >> "$GH_LOG.comment" ;;
  *"issues/5/comments"*) cat "$FIX/issue-comments.json" ;;
  *"issues/7/comments"*) echo '[[]]' ;;
  *"pulls/7/files"*) echo '[[{"filename":"src/app/page.tsx"}]]' ;;
  *"issues/5"*) cat "$FIX/issue.json" ;;
esac
exit 0
"""


class CloseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        scripts = self.tmp / "scripts"
        scripts.mkdir()
        for name in ("super-board-close-proof.py", "super-board-github-read.py"):
            shutil.copy(ROOT / "scripts" / name, scripts / name)
        card = scripts / "super-board-card.sh"
        card.write_text('#!/usr/bin/env bash\necho "card $*" >> "$GH_LOG"\n')
        gh = self.tmp / "gh"
        gh.write_text(STUB_GH)
        for p in (card, gh):
            p.chmod(p.stat().st_mode | stat.S_IEXEC)
        (self.tmp / "cfg.json").write_text(json.dumps({"repo": {"remote": "https://github.com/o/r.git"}}))
        self.env = {**os.environ, "PATH": f"{self.tmp}:{os.environ['PATH']}", "GH_LOG": str(self.tmp / "gh.log"),
                    "FIX": str(self.tmp), "SB_GITHUB_HALT_FILE": str(self.tmp / "halt.json"), "SB_GITHUB_RETRY_DELAY": "0"}

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def close(self, issue, comments):
        (self.tmp / "issue.json").write_text(json.dumps(issue))
        (self.tmp / "issue-comments.json").write_text(json.dumps([comments]))
        r = subprocess.run([sys.executable, str(self.tmp / "scripts/super-board-close-proof.py"), "close", "--config", str(self.tmp / "cfg.json"),
                            "--issue", "5", "--pr", "7", "--merge", MERGE, "--head", HEAD], capture_output=True, text=True, env=self.env)
        log = (self.tmp / "gh.log").read_text() if (self.tmp / "gh.log").exists() else ""
        return r, log

    def gh_comment(self, body):
        return {"body": body, "created_at": "2026-11-04T01:00:00Z", "user": {"login": BOT}}

    def test_proven_card_is_commented_ticked_closed_and_moved_to_done(self):
        issue = {"labels": [{"name": "bug"}], "body": "## Acceptance Criteria\n- [ ] It works"}
        r, log = self.close(issue, [self.gh_comment(f"QA at {HEAD}\n![x](https://x/x.png)\n### Acceptance criteria\n| It works | PASS: yes. |")])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("issue close 5 -R o/r", log)
        self.assertIn("card --config", log)
        self.assertIn("move 5 Done", log)
        self.assertIn("- [x] It works", (self.tmp / "gh.log.stdin").read_text())
        self.assertIn(cp.PROOF_MARKER, (self.tmp / "gh.log.comment").read_text())

    def test_card_without_after_is_not_closed_and_goes_to_qa(self):
        r, log = self.close({"labels": [{"name": "bug"}], "body": ""}, [])
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertNotIn("issue close", log)
        self.assertNotIn("Done", log)
        self.assertIn("move 5 QA", log)
        self.assertIn("super-board:close-held", (self.tmp / "gh.log.comment").read_text())

    def test_judge_input_may_carry_the_config(self):
        inputs = {"labels": ["approved-change"], "head": HEAD, "files": ["src/lib/a.ts"], "comments": [],
                  "config": {"close_proof": {"ui_globs": ["src/app/**"]}}}
        r = subprocess.run([sys.executable, str(SCRIPT), "judge", "--input", "-"], input=json.dumps(inputs), capture_output=True, text=True)
        self.assertIn("approved change with no UI file", json.loads(r.stdout)["comment"])

    def test_judge_input_mode_prints_json(self):
        r = subprocess.run([sys.executable, str(SCRIPT), "judge", "--input", "-"], input=json.dumps({"labels": ["bug"], "head": HEAD, "comments": []}),
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(json.loads(r.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
