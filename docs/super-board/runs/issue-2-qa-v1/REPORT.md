# Issue #2 QA v1

- Issue: https://github.com/maxchangm/super-board/issues/2
- PR: https://github.com/maxchangm/super-board/pull/3
- Host: fresh Pi QA lane, separate from Builder and the future Reviewer.
- Branch: `issue-2-install-include-pi-in-supported-host-lists`.
- Implementation checked: `e074641da8e6b14061bc589b808de5d378e15357`.
- Base: `origin/codex/pi-pilot-20261020` at `bbf279d8cf48d8d934a45edac69f51668526b540`.
- Result: QA passes all four ACs. Independent Review must rerun the commands below.

## Pass P1: preflight evidence

Read the live issue, every issue/PR timeline comment, every changed file and all
review threads and replies through the guarded GitHub reader. Pagination was complete.
The card was in QA, the issue was open and PR #3 was draft against the configured base.
The initial worktree was clean and HEAD matched the PR. No unresolved QA findings or
human requests existed. Three open author-note threads explain the change only.
This is initial read-only verification, not a repair. No repair reservation was supplied.
No canonical repair state, repair-count labels or phase labels were changed.

## Pass P2: classification and test plan

Retain `docs`. The raw diff has five added and five removed lines, all documentation.
No runtime branch, input, authentication, money, schema or deployment behavior changes.
Run one observable check per AC at its relevant seam. Add only board-owned proof.

| AC | Observable check | Expected result |
|---|---|---|
| AC1 | Read usage and execute `bash install.sh --help` | Both list `claude,codex,pi,opencode` |
| AC2 | Read the installation contract | Pi and `.pi/` share the existing host-link conditions |
| AC3 | Compare the whole diff, installer non-comment content and other authoring rules | Only allowed documentation and evidence change |
| AC4 | Run `bash tests/run-safety.sh` | Exit 0 and `PASS: 68 safety suites` |

## Pass P3: independent truth check and results

The installer accepts `pi` at `install.sh:71`, existing folders at line 75,
configured hosts at lines 76-86 and detected hosts at lines 87-88. These match the
updated `.pi/` documentation. Existing Pi link assertions remain at
`tests/test-install.sh:410-417`. Executable installer content is unchanged.
Authoring rules outside the installation contract are unchanged.

`check-ac.py` ran against the original base first. It exited 1 with exactly three
failures for the original host-list and `.pi/` omissions. It then ran against HEAD
and actual installer help, exiting 0 with eight passed checks. `ac-check.log` records
both runs. This proves the documentation assertions can reject the original defect
without temporarily editing implementation files or weakening expected values.

`bash tests/run-safety.sh` exited 0 with `PASS: 68 safety suites`.
`safety.log` records the exact command, revision, duration, output digest and every
suite result. It condenses the 909-line local output, which was read and had no
failed suite. No implementation or existing tests were modified by QA.

## Test-gap ledger

| AC | Unit | Component | Browser e2e | Direct contract/integration proof |
|---|---|---|---|---|
| AC1 | n/a: documentation | n/a: no component | n/a: no UI | `check-ac.py:40-46` |
| AC2 | n/a: documentation | n/a: no component | n/a: no UI | `check-ac.py:48-54` |
| AC3 | n/a: Git scope | n/a: no component | n/a: no UI | `check-ac.py:56-67` |
| AC4 | n/a: suite-level result | n/a: no component | n/a: no UI | `tests/run-safety.sh:10-32`, `safety.log` |

Changed runtime inputs/branches: none. Boundary, money/date, Unicode/CSV, volume,
auth, error-path, idempotency/race, UI-state and accessibility cases are n/a.
Tests assert literal issue requirements and compare actual source against the base,
not mocks or recomputed expected behavior. No High, Medium or Low gaps remain for
this documentation-only scope. Test gaps (not written): none.

## Limits and handoff

No `verify-<app>` map is installed. Ordinary issue checks and the offline suite apply.
Screenshots, browser traces and login are intentionally omitted because there is no UI.
No services, migrations, deployment, release tags or merge were run by this QA lane.
Review owns the next verification and the reviewed-head merge gate.

Local tests: bash tests/run-safety.sh
Additional check: python3 docs/super-board/runs/issue-2-qa-v1/check-ac.py
