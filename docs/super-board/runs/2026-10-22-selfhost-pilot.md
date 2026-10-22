# Self-host pilot

Baseline: PASS, 63 safety suites.
Runner setup: 826d25c. Runner source: c03e388.

[10:37:28] super-board run started — config=selfhost-pilot base=pilot/selfhost-20261022 max_workers=1
[10:37:28] dispatch lane=build issue=#16 pid=48397 claim=maxchangm

## Halted result

| Issue | Lanes | Result | Column | Detail |
| --- | --- | --- | --- | --- |
| #16 | build:halted | halted | Ready | Required labels read failed three times. Sandbox denied shared halt-record write. Claim and clean build worktree preserved. No edit, tests, or PR. |

No further wave started. Assignee release and throttle skipped under the halted-run contract.
