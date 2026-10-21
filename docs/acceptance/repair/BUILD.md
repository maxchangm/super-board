# Issue #9 initial Build failure

The initial candidate selects the operator's immutable `signal-initial.json`.
The accepted assertion ran unchanged from the issue worktree and exited 1:

```text
AssertionError: operator-held health fault: signal-initial.json: {'status': 'down', 'epoch': 0, 'cause': 'operator-held health fault'}
```

The source loads successfully. Its unhealthy status causes the assertion failure.
Changing endpoint selection does not remove the operator-held health fault.
This is initial work, not a reserved repair or independent diagnosis.

Raw command, traceback and exit code are outside Git at
`/Users/maxchan/Documents/Codex/2026-10-20/op/outputs/super-board-handoff/implementation-evidence/finish-20261021/issue-9-build-lane/`.
Hash input is `build|test_assertion|<string>:1`.
root-cause-hash: 33dd077963ad

Keep the PR draft and the card Ready. Never merge this fixture.
The dispatcher owns canonical repair state and the next attempt.

## First reserved repair

Reservation owner `26655`, attempt 1: changed only the candidate source to the
absolute `signal-repair1.json` path. The unchanged assertion exited 1:

```text
AssertionError: operator-held health fault: signal-repair1.json: {'status': 'degraded', 'epoch': 1, 'cause': 'operator-held health fault'}
```

The alternate signal loads but remains unhealthy. This is the same operator-held
health fault, not a new cause. Raw traceback and exit code: external
`finish-20261021/issue-7-qa/repair1-assertion.log` and `repair1-assertion.exit`.
root-cause-hash: 33dd077963ad

Return failed in Ready on the same draft PR. Canonical state and repair labels
remain dispatcher-owned. Do not run another attempt or merge this fixture.
