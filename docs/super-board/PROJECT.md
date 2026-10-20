# Super Board Pi pilot

This repository authors the reusable Super Board skills, scripts and safety hooks.
The pilot uses a single real documentation issue to exercise Build, independent QA,
Review, the reviewed-head merge gate and confirmed Done on a dedicated base branch.

GitHub board: https://github.com/users/maxchangm/projects/4
Repository: https://github.com/maxchangm/super-board
Base branch: `codex/pi-pilot-20261020`
Runtime: Pi, provider `openai`, model `gpt-6.1-sol`
Verification: `bash tests/run-safety.sh`

This pilot changes no product service, database or production deployment.
A successful documentation issue demonstrates workflow feasibility. It does not
measure Pstack's effect on bug-finding or design quality.
