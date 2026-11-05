#!/usr/bin/env bash
# super-board-role-rules.sh prints each worker role's run.md sections and refuses a map that run.md outgrew.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
S="$ROOT/scripts/super-board-role-rules.sh"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
fails=0; fail() { echo "FAIL: $*" >&2; fails=$((fails + 1)); }

# 1 — every mapped heading is in run.md; each role gets its own lifecycle and the shared worker rules.
for pair in 'builder|### Builder (first pass)' 'tester|### Tester (first pass — repo-backed)' 'reviewer|### Merge protocol (Reviewer only'; do
  role=${pair%%|*}; want=${pair#*|}
  bash "$S" "$role" >"$T/out" 2>"$T/err" || fail "$role exited $? ($(cat "$T/err"))"
  [ -s "$T/out" ] || fail "$role printed nothing"
  grep -qF "$want" "$T/out" || fail "$role output lacks $want"
  grep -qF '## Worker self-check (mandatory on exit, every lane)' "$T/out" || fail "$role output lacks the worker self-check"
  grep -qF '## Orchestrator delegation contract' "$T/out" && fail "$role output carries orchestrator-only text"
done
bash "$S" tester >"$T/out"
grep -qF '#### Screenshot embed format' "$T/out" || fail "tester output lacks the screenshot embed format"
grep -qF '### Reviewer' "$T/out" && fail "tester output carries the Reviewer lifecycle"
bash "$S" reviewer >"$T/out"
grep -qF '### Reviewer' "$T/out" || fail "reviewer output lacks the Reviewer lifecycle"

# 2 — a mapped heading that run.md lost fails, naming it.
sed 's/^### Reviewer$/### Reviewer renamed/' "$ROOT/skills/super-board/references/run.md" >"$T/run.md"
bash "$S" reviewer "$T/run.md" >/dev/null 2>"$T/err"; rc=$?
[ "$rc" -eq 3 ] || fail "missing heading exited $rc, want 3"
grep -qxF 'super-board-role-rules: run.md has no heading: ### Reviewer' "$T/err" || fail "missing heading not named: $(cat "$T/err")"

# 3 — a bad role is a usage error.
bash "$S" orchestrator >/dev/null 2>&1; rc=$?
[ "$rc" -eq 64 ] || fail "bad role exited $rc, want 64"

# 4 — the installed copy finds the installed run.md.
mkdir "$T/app"; bash "$ROOT/install.sh" --no-hooks "$T/app" >/dev/null 2>&1 || fail "install.sh failed"
(cd "$T/app" && bash .claude/bin/super-board-role-rules.sh tester) >"$T/out" 2>&1
grep -qF '### Tester (first pass' "$T/out" || fail "installed script cannot read the installed run.md"

[ "$fails" -eq 0 ] && echo "PASS: role rules" || exit 1
