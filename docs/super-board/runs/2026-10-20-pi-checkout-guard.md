# Pi checkout guard pilot — 2026-10-20

Issue: https://github.com/maxchangm/super-board/issues/4
PR: https://github.com/maxchangm/super-board/pull/5
Board: https://github.com/users/maxchangm/projects/4
Repository Projects: https://github.com/maxchangm/super-board/projects

## Scope and ownership

Codex selected and reproduced one defect, created the issue, moved it to Ready, prepared two design candidates, and dispatched the native Pi wave. Pi Build implemented the regression and fix. Fresh Pi QA and Review sessions verified them. Native Pi 1.3.0 used openai/gpt-6.1-sol. Git author identity alone is not attribution evidence.

| Event | HKT | Evidence |
|---|---|---|
| First Pi Build starts | 19:45:36 | session 01a15921-99ea-7617-862c-08ae70c613f6 |
| Failing regression committed | 19:54:18 | a2f109ffb57e9ca3904517d83dbec1930495a33e |
| Fix committed | 20:06:10 | 74b8d70037bfbd2121050548bdcd28058e8c8ad7 |
| Pi Build handoff restart | 20:17:12 | session 01a1593e-8599-7284-ab20-4888d4a4ad19 |
| Pi QA starts | 20:37:07 | session 01a15950-c248-72c5-92a8-e8822872c906 |
| Pi Review starts | 20:58:49 | session 01a15964-a1b6-75d4-a8f4-4d1287bd9571 |
| Gate merge | 21:22:43 | squash a1a289a0088985a800a8770a1654dd2bb23e434c |

## Wave results

| Wave | Issue | Result | Column | Detail |
|---|---|---|---|---|
| 1 | #4 | halted in Build | Building | Required PR diff read omitted metadata. Implementation and 69-suite proof were pushed. Claims and clean worktree were preserved. |
| 2 | #4 | Build, QA and Review advanced | Done | Explicit read recovery and handoff restart. Unchanged head-pinned gate passed and landing was verified. No repair was consumed. |

## Verified results

- Before: the direct Pi lane and full Pi wave accepted a different configured checkout in the isolated parent probe. Recording stubs reached QA/Done. No real model edits in a wrong checkout were tested.
- After: the exact parent probe refuses both commands with both roots in the diagnostic and zero Pi/GitHub calls.
- QA and Review independently reproduced 81 historical failing subtests. The corrected four-method CLI regression passes for source and installed Pi/Codex waves and lanes, distinct linked worktrees, valid aliases/subdirectories/relative paths and omitted paths, and setup repair.
- All 69 safety suites passed in Build, resumed Build, QA, Review and the merge gate. The merged tree equals the gate-tested tree: 55bfb25d923d43e47e5b8d4ced2fb02900c9994c.
- The 220 pack, test and reference blobs on reusable source branch codex/pi-lanes-reviewed-plan match the verified merge. The accepted commits are pushed and the pilot installation is refreshed.
- Issue Closed, board Done, assignee released, planner empty, no active lane/card locks or board worktrees. The owned wave marker is removed. Throttle did not change max_workers. Calibration is disabled.

## Limits and setup correction

A dedicated board isolated the trial. Leaving it unlinked from the repository was a setup omission. The board is now linked and both directions were verified through GitHub's API. Privacy is unchanged.

This proves a functional guard and a completed Pi workflow with one orchestrator recovery. It does not prove unattended reliability or a general Pstack/Claude/Pi quality or speed advantage. Review's 98/100 truth score is a model assessment, not a comparative measurement. No production branch merge, deployment or release tag occurred.
