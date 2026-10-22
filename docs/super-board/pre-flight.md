# Self-host pilot preflight

Scope: issue #16 only, documentation correction on pilot/selfhost-20261022.

[✓] GitHub repository and project #5 are readable and writable; issue #16 was created and moved to Ready.
[✓] Project #5 has Backlog, Ready, Building, QA, Review, Blocked, Done and no other admitted cards.
[✓] Issue #16 has explicit Problem, Context, Fix, checklist Acceptance Criteria, Risk and exact `- None.` dependencies.
[✓] Existing duplicate/overlap preflight returned proceed, clean, no duplicate and no overlap.
[✓] Codex CLI 0.163.0 is installed and authenticated with ChatGPT.
[✓] Live Codex skills/list inventory resolves all required Build, QA and Review helpers.
[✓] Configured verification command is the repository-owned `bash tests/run-safety.sh`.
[✓] Codex launcher scripts pass bash syntax checks; host detection returns codex.
[✓] No database, application server, external service secret or browser is required for this documentation ticket.
[✓] No existing Super Board dispatcher or lane process was found before launch.
[✓] Dedicated pilot base and separate runner setup branches were pushed. Main is not a merge target.

The runner stays detached at its setup commit with installed source from c03e388. Worker branches start from the dedicated pilot base, not the runner setup commit. The live host catalog and installed helper copies stay local.
