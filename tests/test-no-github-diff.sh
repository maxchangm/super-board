#!/usr/bin/env bash
# GitHub answers HTTP 406 to `gh pr diff` and the diff/patch media types once a PR changes more
# than 300 files (2026-11-04: PR #560, 316 files, halted a QA lane on all three attempts).
# A lane reads the diff from the local checkout (`git diff origin/<base>...<head>`, see
# local_diff in scripts/super-board-github-read.py). This fails if any lane text or script
# asks GitHub for a diff again. RELEASE-NOTES.md is history and this file names the patterns.
set -uo pipefail
cd "$(dirname "$0")/.."
HITS=$(git grep -InE 'pr[ -]diff|vnd\.github(\.[a-z0-9]+)?\.(diff|patch)|(Accept|-H)[^|]*\.(diff|patch)\b' \
  -- . ':!RELEASE-NOTES.md' ':!tests/test-no-github-diff.sh' ':!diagrams')
if [ -n "$HITS" ]; then
  printf '%s\n' "$HITS" >&2
  echo "FAIL: read the PR diff with local git, never gh pr diff or the GitHub diff media type" >&2
  exit 1
fi
echo "PASS: test-no-github-diff.sh (no lane text or script asks GitHub for a PR diff)"
