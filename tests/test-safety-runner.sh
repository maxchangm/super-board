#!/usr/bin/env bash
# Exercise aggregation with tiny fixtures; never recursively run the actual suite.
set -euo pipefail
PACK=$(cd "$(dirname "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$WORK/tests"
cp "$PACK/tests/run-safety.sh" "$WORK/tests/"
fail() { echo "FAIL: $1" >&2; exit 1; }
if bash "$WORK/tests/run-safety.sh" >/dev/null 2>&1; then fail 'empty suite passed'; fi
printf 'exit 3\n' > "$WORK/tests/test-a-failure.sh"
printf 'echo reached\n' > "$WORK/tests/test-z-success.sh"
printf 'print("python reached")\n' > "$WORK/tests/test_python.py"
rc=0
out=$(bash "$WORK/tests/run-safety.sh" 2>&1) || rc=$?
[ "$rc" -eq 1 ] || fail "failed suite did not fail gate: $rc"
[[ "$out" == *reached* && "$out" == *'python reached'* ]] || fail 'failure hid later suites'
rm "$WORK/tests/test-a-failure.sh"
bash "$WORK/tests/run-safety.sh" >/dev/null || fail 'passing suites failed'
cat > "$WORK/tests/test-isolation.sh" <<'SH'
[ -z "${SUPER_BOARD_SKILLS_CATALOG+x}" ] || { echo 'inherited live skill catalog' >&2; exit 1; }
[ -z "${SB_REPO_PATH+x}" ] || { echo 'inherited repository path' >&2; exit 1; }
[ "${SB_GITHUB_READ_STRICT:-}" = 1 ] || { echo 'strict read mode changed' >&2; exit 1; }
SH
out=$(SUPER_BOARD_SKILLS_CATALOG="$WORK/live-catalog.json" SB_REPO_PATH="$PACK" SB_GITHUB_READ_STRICT=1 \
  bash "$WORK/tests/run-safety.sh" 2>&1) || fail "$out"
echo 'PASS: test-safety-runner.sh (empty, failure, continuation, success, isolation)'
