#!/usr/bin/env python3
"""Close proof: a bug or feature card closes only with AFTER screenshots and every acceptance box proven.

  super-board-close-proof.py judge --input FILE|- [--config CFG]   offline verdict as JSON, no GitHub
      (the input may carry the board config as "config" instead of --config)
  super-board-close-proof.py judge --config CFG --issue N --pr P --merge SHA [--head SHA]   reads GitHub, prints the verdict
  super-board-close-proof.py close --config CFG --issue N --pr P --merge SHA [--head SHA]   judge, then close or hold

Verdict: {"ok": true, "comment": ..., "body": <issue body with boxes ticked | null>}
      or {"ok": false, "note": ...}   (the note ends with the held marker for the merge)

Rules (the one place they live; super-review's merge protocol calls `close`):
- AFTER images: the newest bot comment that names the reviewed PR head or the merge commit (first 8 hex
  digits) and holds image markdown. Our own markers are never read back as proof.
- BEFORE images: the newest comment carrying a config `close_proof.before_markers` marker, else the
  reporter's own images (issue body, non-bot comments).
- Acceptance boxes: the `- [ ]` lines under the issue's "Acceptance Criteria" heading. A box is proven by a
  PASS row of the final "Acceptance criteria" table (same head rule): by position when the table has one row
  per box, else by the row sharing the most words.
- bug and feature cards need AFTER and every box proven, else {ok:false}: the card stays out of Done and goes
  back to QA for evidence. A refactor, a card that is neither bug nor feature, a stated `No visual surface:
  <reason>` in the QA comment, or an approved-change card whose PR changed no UI file closes with the reason.
- UI files come from config `close_proof.ui_globs` (`!` prefix excludes). Unset: every file counts as UI.
Exit: judge 0 (verdict printed) · close 0 closed, 3 held in QA · 64 usage · 79 required read unavailable.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HELD = lambda merge: f"<!-- super-board:close-held merge={str(merge)[:8]} -->"
PROOF_MARKER = "<!-- super-board:close-proof -->"
OWN = [PROOF_MARKER, "<!-- super-board:close-held", "<!-- super-board:close-evidence"]
IMG = re.compile(r'!\[[^\]]*\]\((https?:[^)\s]+)\)|<img\b[^>]*?\ssrc="(https?:[^"]+)"')
MAX_IMAGES = 6


def images_of(text):
    seen, out = set(), []
    for m in IMG.finditer(text or ""):
        url = m.group(1) or m.group(2)
        if url in seen:
            continue
        seen.add(url)
        out.append(m.group(0) if m.group(1) else f"![]({url})")
    return out[:MAX_IMAGES]


def acceptance_boxes(body):
    boxes, inside = [], False
    for i, line in enumerate((body or "").split("\n")):
        if re.match(r"^#{1,6}\s", line):
            inside = re.match(r"^#{1,6}\s*acceptance criteria\b", line, re.I) is not None
        m = inside and re.match(r"^(\s*[-*]\s+)\[( |x|X)\]\s+(.*\S)\s*$", line)
        if m:
            boxes.append({"line": i, "text": m.group(3), "checked": m.group(2) != " "})
    return boxes


def acceptance_rows(text):
    lines = (text or "").split("\n")
    start = next((i for i, l in enumerate(lines) if re.match(r"^[#*\s]*acceptance criteria\b", l, re.I)), -1)
    if start < 0:
        return []
    rows = []
    for line in lines[start + 1:]:
        if re.match(r"^#{1,6}\s", line) and rows:
            break
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in re.sub(r"^\||\|$", "", line.strip()).split("|")]
        if len(cells) < 2 or all(re.match(r"^:?-+:?$", c) for c in cells):
            continue
        result = next((c for c in cells[1:] if re.match(r"^\W*(PASS|FAIL|BLOCKED|NOT RUN)\b", c, re.I)), None)
        if not result:
            continue
        proof = re.sub(r"^\W*PASS\b[:\s—–-]*", "", result, flags=re.I)
        rows.append({"criterion": cells[0], "pass": re.match(r"^\W*PASS\b", result, re.I) is not None,
                     "proof": re.split(r"(?<=\.)\s", proof)[0].strip()})
    return rows


def _words(s):
    return set(re.findall(r"[a-z0-9]{3,}", str(s).lower()))


def _overlap(a, b):
    x, y = _words(a), _words(b)
    return len(x & y) / min(len(x), len(y)) if x and y else 0


def _prove(boxes, rows):
    proven, unproven = [], []
    by_position = len(rows) == len(boxes)
    for i, b in enumerate(boxes):
        if b["checked"]:
            continue
        if by_position:
            row = rows[i]
        else:
            best = max(rows, key=lambda r: _overlap(b["text"], r["criterion"]), default=None)
            row = best if best and _overlap(b["text"], best["criterion"]) >= 0.5 else None
        if row and row["pass"]:
            proven.append({"box": b, "proof": row["proof"]})
        else:
            unproven.append(b["text"])
    return proven, unproven


def _glob(pattern):
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def is_ui_file(path, globs):
    """Last matching glob wins; a `!` prefix excludes. No globs configured: every file is UI."""
    if not globs:
        return True
    hit = False
    for g in globs:
        neg = g.startswith("!")
        if _glob(g[1:] if neg else g).match(str(path)):
            hit = not neg
    return hit


def judge(inputs, cfg=None):
    cfg = (cfg or {}).get("close_proof") or {}
    labels, body = inputs.get("labels") or [], inputs.get("body") or ""
    head, merge = inputs.get("head"), inputs.get("merge") or ""
    files = inputs.get("files") or []
    comments = sorted(inputs.get("comments") or [], key=lambda c: str(c.get("at") or ""))
    is_bot = lambda c: str(c.get("by") or "").endswith("[bot]")
    bot = [c for c in comments if is_bot(c)]
    ids = [str(h)[:8].lower() for h in (head, merge) if h]
    at = [c for c in bot if any(i in c["body"].lower() for i in ids)] if ids else bot
    skip = OWN + list(cfg.get("skip_markers") or []) + list(cfg.get("before_markers") or [])
    own = lambda c: any(m in c["body"] for m in skip)
    latest = lambda lst: next((r for r in (images_of(c["body"]) for c in reversed(lst)) if r), [])
    after = latest([c for c in at if not own(c)])
    marks = list(cfg.get("before_markers") or [])
    from_marked = latest([c for c in bot if any(m in c["body"] for m in marks)])
    reporter = images_of("\n".join([body] + [c["body"] for c in comments if not is_bot(c)]))
    before = from_marked or reporter
    stated = next((m.group(1).strip() for c in reversed([c for c in at if not own(c)])
                   if (m := re.search(r"^\W*No visual surface:\s*(.+)$", c["body"], re.I | re.M))), None)
    approved = "approved-change" in labels
    bug_or_feature = "bug" in labels or "feature" in labels
    ui = cfg.get("ui_globs")
    if inputs.get("no_visual"):
        reason = inputs["no_visual"]
    elif approved:
        reason = None if any(is_ui_file(f, ui) for f in files) else "approved change with no UI file"
    elif "refactor" in labels:
        reason = "refactor with no UI change"
    elif not bug_or_feature:
        reason = "the card is neither a bug nor a feature"
    else:
        reason = stated
    kind = "approved-change" if approved else "feature" if "feature" in labels else "bug"

    boxes = acceptance_boxes(body)
    table = next((r for r in (acceptance_rows(c["body"]) for c in reversed(at)) if r), [])
    proven, unproven = _prove(boxes, table)

    holds = []
    if not after and not reason:
        holds.append(f"**Status:** Not closed: this {kind} card has no AFTER screenshot"
                     + (f" for the reviewed PR head `{str(head)[:8]}`" if head else "")
                     + ". Closing needs the Before and After screenshots in the closing comment.\n"
                     "**Next:** QA captures an AFTER screenshot of the merged behaviour and posts it as image markdown in a "
                     "comment that names the PR head or the merge commit. A fix with no visible surface says "
                     "`No visual surface: <reason>` in that comment instead.")
    if unproven:
        n = len(unproven)
        holds.append(f"**Status:** Not closed: {n} acceptance criteri{'on has' if n == 1 else 'a have'} no PASS row in the "
                     "final QA or Review table:\n" + "\n".join(f"- {t}" for t in unproven) +
                     "\n**Next:** QA proves each one in an `### Acceptance criteria` table with a PASS row per criterion.")
    if holds:
        return {"ok": False, "note": "\n\n".join(holds) + f"\n\n{HELD(merge)}\n"}

    if after:
        before_part = f"\n\n**Before**\n" + "\n".join(before) if before else ""
        head_part = f" (reviewed PR head `{str(head)[:8]}`)" if head else ""
        visual = f"**Visual proof:**{before_part}\n\n**After**{head_part}\n" + "\n".join(after)
    else:
        why = re.sub(r"[.\s]+$", "", str(reason))
        visual = f"**No visual surface:** {why}."
    ticks = ("\n\n**Acceptance criteria ticked:**\n" +
             "\n".join(f"- {p['box']['text']}: {p['proof'] or 'PASS'}" for p in proven)) if proven else ""
    new_body = None
    if proven:
        lines = body.split("\n")
        for p in proven:
            lines[p["box"]["line"]] = lines[p["box"]["line"]].replace("[ ]", "[x]", 1)
        new_body = "\n".join(lines)
    return {"ok": True, "comment": f"{visual}{ticks}\n\n{PROOF_MARKER}\n", "body": new_body}


def slug_of(cfg):
    remote = (cfg.get("repo") or {}).get("remote") or ""
    return re.sub(r"\.git$", "", re.sub(r"^(git@github\.com:|https://github\.com/)", "", remote))


def gh_read(*args):
    r = subprocess.run([sys.executable, str(HERE / "super-board-github-read.py"), "--kind", "json", "--", *args],
                       capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr)
        sys.exit(79 if r.returncode == 79 else 70)
    return json.loads(r.stdout)


def read_inputs(slug, issue, pr, head, merge, labels_from_issue=True):
    info = gh_read("api", f"repos/{slug}/issues/{issue}")
    pages = lambda n: [c for page in gh_read("api", "--paginate", "--slurp", f"repos/{slug}/issues/{n}/comments") for c in page]
    comment = lambda c: {"body": c.get("body") or "", "at": c.get("created_at"), "by": (c.get("user") or {}).get("login")}
    comments = [comment(c) for c in pages(issue)] + ([comment(c) for c in pages(pr)] if pr else [])
    files = []
    if pr:
        files = [f["filename"] for page in gh_read("api", "--paginate", "--slurp", f"repos/{slug}/pulls/{pr}/files?per_page=100")
                 for f in page]
    return {"labels": [l["name"] for l in info.get("labels", [])], "body": info.get("body") or "", "comments": comments,
            "files": files, "head": head, "merge": merge}


def gh(*args, stdin=None):
    r = subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr)
        sys.exit(70)
    return r.stdout


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=("judge", "close"))
    p.add_argument("--config")
    p.add_argument("--input")
    p.add_argument("--issue", type=int)
    p.add_argument("--pr", type=int)
    p.add_argument("--merge", default="")
    p.add_argument("--head")
    a = p.parse_args()
    cfg = json.loads(Path(a.config).read_text()) if a.config else {}
    if a.input:
        if a.mode == "close":
            p.error("close reads GitHub; --input is for judge")
        inputs = json.loads(sys.stdin.read() if a.input == "-" else Path(a.input).read_text())
        verdict = judge(inputs, cfg or inputs.get("config"))
        print(json.dumps(verdict))
        return 0
    if not (a.config and a.issue):
        p.error("--config and --issue are required without --input")
    slug = slug_of(cfg)
    verdict = judge(read_inputs(slug, a.issue, a.pr, a.head, a.merge), cfg)
    if a.mode == "judge":
        print(json.dumps(verdict))
        return 0
    card = str(HERE / "super-board-card.sh")
    move = lambda col: subprocess.run(["bash", card, "--config", a.config, "move", str(a.issue), col], check=True)
    if not verdict["ok"]:
        gh("issue", "comment", str(a.issue), "-R", slug, "--body-file", "-", stdin=verdict["note"])
        move("QA")
        print(f"not closed: #{a.issue} moved to QA for evidence")
        return 3
    if verdict["body"] is not None:
        gh("api", "-X", "PATCH", f"repos/{slug}/issues/{a.issue}", "--input", "-", stdin=json.dumps({"body": verdict["body"]}))
    gh("issue", "comment", str(a.issue), "-R", slug, "--body-file", "-", stdin=verdict["comment"])
    gh("issue", "close", str(a.issue), "-R", slug)
    move("Done")
    print(f"closed: #{a.issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
