# Super Board self-host pilot

Runner source: c03e388d1b49492ff9b35f0c60295e9bdb77d9d6.
Board: https://github.com/users/maxchangm/projects/5.
Target repository: maxchangm/super-board.
Target base: pilot/selfhost-20261022, initially c03e388.
Backend: Codex, one worker. Build, QA and Review run as separate lane sessions.
Checks: bash tests/run-safety.sh, as used by .github/workflows/cross-platform.yml.

Install the pinned source with `bash install.sh --hosts codex --protect-main <runner-checkout>`.
Required helper files must resolve from the actual Codex host inventory. This machine uses an explicit catalog captured from Codex app-server skills/list because its native skill config contains a name-based activation record the pinned resolver does not parse. The catalog is local and uncommitted.
The testing-strategy helper comes from anthropics/knowledge-work-plugins. The verification-before-completion helper comes from the installed superpowers plugin.

The runner setup commit is separate from the product base. This keeps runtime configuration out of product CI, whose status smoke test expects no active config. Keep the installed source fixed during the run.
This pilot proves workflow execution only. It does not establish a Pstack quality improvement.
