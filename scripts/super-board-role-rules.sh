#!/usr/bin/env bash
# Print the run.md sections one board worker role must read, in file order.
#
#   bash .claude/bin/super-board-role-rules.sh <builder|tester|reviewer> [run.md]
#
# Super Board owns the map below: each line is an exact run.md heading. A section is the
# heading plus its text up to the next heading of any level, so a child section is listed
# on its own. Headings inside ``` fences are text, not headings. Sections the map leaves
# out serve the orchestrator or another role. Exit 64 on a bad role, 66 when run.md is
# missing, 3 when a mapped heading is no longer in run.md (each one named on stderr).
set -euo pipefail

role=${1:-}
run_md=${2:-"$(dirname "$0")/../skills/super-board/references/run.md"}

shared_top='## Required GitHub reads can pause a run
## Lanes and label routing
## Branch + PR model — one branch, one PR per issue
## PR description template
## PR review-comment threads — prefix + resolution protocol'
shared_end='## Commenting cadence (issue + PR, every lane)
## Worker contract (every lane on claim)
### Anti-zombie addendum (added 2026-05-22 after #381 worker storm)
## Halt gates
### Root-cause hash (used by the rebuild-cap gate)
## Worker rate-limit etiquette (read before any burst of gh calls)
## Worker self-check (mandatory on exit, every lane)
### Known issue — multi-attempt card moves (added 2026-05-22)
### Known issue — lane-zombie workers (added 2026-05-24, auto-remediated)'

case "$role" in
  builder) own='### Builder pre-flight (before ANY card goes Ready → Building)
### Builder (first pass)
### Builder (rebuild)
### The rebase pass' ;;
  tester) own='### Tester (first pass — repo-backed)
#### Screenshot embed format (mandatory on every QA exit — added 2026-05-22)
### Tester (rebuild — when Reviewer bounced for `[qa]` thread fixes)' ;;
  reviewer) own='### Reviewer
### Merge protocol (Reviewer only — added 2026-08-06, issue #9)
### The rebase pass
### The wave-start sweep' ;;
  *) echo "usage: super-board-role-rules.sh <builder|tester|reviewer> [run.md]" >&2; exit 64 ;;
esac
[ -f "$run_md" ] || { echo "super-board-role-rules: no run.md at $run_md" >&2; exit 66; }

printf '<!-- %s rules from %s; open another run.md section only when these point at it -->\n\n' "$role" "$run_md"
printf '%s\n%s\n%s\n' "$shared_top" "$own" "$shared_end" | awk '
  FNR == NR { want[$0] = 1; next }
  /^[ \t]*```/ { fence = !fence }
  !fence && /^#+ / { on = ($0 in want); if (on) seen[$0] = 1 }
  on { print }
  END {
    for (h in want) if (!(h in seen)) { print "super-board-role-rules: run.md has no heading: " h > "/dev/stderr"; bad = 1 }
    exit bad ? 3 : 0
  }' - "$run_md"
