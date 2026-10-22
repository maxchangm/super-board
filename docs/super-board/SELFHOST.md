# Super Board self-host pilot

Runner source: 01ed7335e1e6aa2b064ce5d728c710ff67a2f0e0 (startup repair PR #18).
Board: https://github.com/users/maxchangm/projects/4.
Target repository: maxchangm/super-board.
Target base: pilot/selfhost-20261022, initially c03e388.
Backend: Codex, one worker. Build, QA and Review run as separate lane sessions.
Checks: bash tests/run-safety.sh, as used by .github/workflows/cross-platform.yml.

Install the pinned source with `bash install.sh --hosts codex --protect-main <runner-checkout>`.
Required helper files must resolve from the actual Codex host inventory. This machine uses an explicit catalog captured from Codex app-server skills/list because its native skill config contains a name-based activation record the pinned resolver does not parse. The catalog is local and uncommitted.
The testing-strategy helper comes from anthropics/knowledge-work-plugins. The verification-before-completion helper comes from the installed superpowers plugin.

The runner setup commit is separate from the product base. This keeps runtime configuration out of product CI, whose status smoke test expects no active config. Keep the installed source fixed during the run.
This pilot proves workflow execution only. It does not establish a Pstack quality improvement.

On 2026-10-22 the owner requested reuse of existing project #4. Pilot issue #16 moved there from the extra project #5. The initial Build halted before edits because a GitHub read failed and its sandbox could not write the shared halt marker. Preserve the worktree and claim until the run is repaired or explicitly cancelled. No automatic restart is authorized by board cleanup.
Project #5 was deleted after its sole issue and Ready status were verified on project #4. Its pre-deletion snapshot is retained in local pilot evidence. The stopped wave lock was removed after process exit verification.

## A1 acceptance attempt

The owner authorized A1 after PR #1 merged. Issue #16 was completed during supervised PR review and is not autonomous acceptance evidence. Fresh issue #17 is the only admitted A1 task. Preserve the old issue-16 worktree and logs as historical evidence.

The startup repair rejects unsupported native gh formatting before network/marker access, grants shared runtime writes to lane/grading sandboxes, and isolates test fixture defaults from the merge gate strict environment. Native sandbox probes verified shared writes and unrelated main-checkout source denial. Both agent and strict-mode GitHub-read suites pass all 23 tests. Independent source review is clear. The full strict-environment suite must pass before launch.

The runner installation is copied from pinned source 01ed733; installed launcher/read-helper bytes were compared with that source. Local skill inventory was refreshed through native Codex skills/list and all required helpers resolve. Source and setup commits remain separate. The pilot base will advance by fast-forward to the tested repair source before any worker starts.

A1 passes only after real Build, QA and Review lane sessions deliver the accepted issue-17 correction, the normal merge gate merges it into pilot/selfhost-20261022, and project #4 marks it Done. Record startup repairs separately from any rescues after the new launch. No claim of reliability or superiority over upstream follows from one documentation task.
