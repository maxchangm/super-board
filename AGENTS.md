# Super Board live acceptance restart

Read CLAUDE.md. Never invoke task-observer or its protocol. Never add a co-author trailer.
The owner authorized finishing the integration through repository-linked Project #4,
Super Board. Claude live acceptance is explicitly deferred. Use Pi, not Claude.
All product work remains in Pi lanes. Current phase: finish issue #7 acceptance.
Use `.claude/super-board/configs/super-board.json`; report merge target is
`codex/pi-pilot-20261020`. No production deployment or release tag.

Fix #12 is independently accepted as merge51aac56 (PR13). The accepted helper was
refreshed in the pilot and both preserved fixture roots; hashes match. Code carried
into source PR1 as2d2c9e5. Do not edit product scripts, skills or policies in this run.
Read the detailed `acceptance-resume-plan.md` and CURRENT.md in
`/Users/maxchan/Documents/Codex/2026-10-20/op/outputs/super-board-handoff/implementation-evidence/finish-20261021/`.

Reuse issue #8 / PR10 in QA, and issue #9 / PR11 from its FIRST RESERVED REPAIR.
Initial #9 failure already ran and one canonical record retains repairs=0,
phase=idle, pending_lane=build. Do not replay that initial failure, reset counters,
create replacement fixture issues/PRs or write canonical state from a lane.
Only the existing wave coordinator owns reservations and diagnosis transitions.

The existing owned issue7QA worktree and partial report are handed off after
read-only reconciliation. It can fast-forward to this current accepted base with
--ff-only, preserving its known untracked report/receipts. Its nested fixture roots
MUST stay at the same absolute paths. Reuse the existing fixture configs in the
external evidence folder. Start each child wave in its exact configured repo.path.
Never remove the parent issue7QA directory on cleanup: it contains retained nested
Git repositories/configs. Keep its branch; a fresh Reviewer can use a clean detached
worktree from the actual remote issue branch head. No force checkout or force push.

Prove the real restricted gate, two real reserved failed repairs, restart/diagnosis,
stale-head rejection and no Done before merge. Close/archive controlled fixtures
only after proof is retained. No fixture may merge. Keep report concise and raw logs
in the external evidence root. No standalone QA project or new runner/framework.

Every required diff read MUST first fetch complete --kind metadata with
files,labels,body,additions,deletions,changedFiles,headRefOid, then pass --meta to
--kind diff. Never omit it. Ordinary reports have no blocked-by footer. That footer
is reserved for actual blockers and `-` means a human gate, not no dependencies.
Use installed helpers by absolute path under the configured project root if an issue
worktree lacks ignored pack resources. Never commit copied pack/helper files.
Use pstack:poteto-mode at
`/Users/maxchan/.codex/plugins/cache/pstack/pstack/1.1.0/skills/poteto-mode/SKILL.md`.

<!-- super-board:begin v3.1.2 (managed; edits inside are overwritten on upgrade) -->
## Super Board

Board: Backlog · Ready · Building · QA · Review · Blocked · Done. Labels route: `qa` skips Building · `bug`, `feature`, none → built first.

| When | Use | NEVER |
|---|---|---|
| Set up / repair the board | `/super-board onboard` | DON'T hand-edit config mid-run |
| Check tickets before a run | `/super-board lint` | NEVER run with AC-less tickets |
| Drain the board | `/super-board run` | NEVER build, test or merge from the orchestrator |
| Board state / halt | `/super-board status` · `/super-board stop` | |
| Build one ticket | `/super-build` | NEVER build outside the card's worktree |
| QA a branch, or a live URL alone | `/super-qa` · `/super-qa <url>` | NEVER mark QA pass without evidence |
| Review a PR, merge | `/super-review` | NEVER `gh pr merge` direct — merge gate only |
| File bugs from Sentry, PostHog, PRs | `/super-collect` | DON'T file without a verifier pass |
| UI polish | `/ui-refine-loop` (human runs it) | board NEVER runs it |
| Diagram / explainer page | `/visual` | |
| Commit, pull, push this branch | `/git-sync` | NEVER force push or rebase shared history |

| Rule | Value |
|---|---|
| Config | `.claude/super-board/configs/<slug>.json` |
| Isolation | 1 card · 1 worktree · 1 branch |
| Merge | auto for normal changes · money, auth, destructive schema (DROP/TRUNCATE/RENAME) → human · PR > 400 changed lines → human |
| Migrations | additive → robot migrates allowed DBs only · live DB ALWAYS → 🙋 needs you |
| Blocked card | block-template comment · last line `blocked-by:` · 🙋 = needs you |
| Secrets | NEVER read `.env`; key names via `.claude/bin/super-board-env-check.sh` |

## Writing (super-board)

| Thing | Format → `.claude/skills/super-board/references/writing-standard.md` |
|---|---|
| Commit, PR title | `<emoji> [type] scope: subject` + short bullets · ✨ feat 🐛 fix 🔧 chore ♻️ refactor 🧪 test 📝 docs |
| PR body | blocks: status · Problem · Solution · AC + proof · history · Before\|After · Risk — `super-board-pr-body.sh` |
| Ticket | Problem · Context · Fix · AC · Risk · Blocked by → `docs/agents/issue-tracker.md` |
| Comment | `[role] [label] status` · Did · ✅ Done · ❌ Not done · Next · ≤ 8 lines |
| PR author notes | file + critical inline review comments: Purpose · What changed · Why it matters → `pr-author-notes.md` |

- NEVER chain steps with arrows. One step per line, lettered under Where.
- NEVER link screenshots. Embed a raw URL pinned to a sha.
- DON'T repeat file lists in status comments. DON'T write "Not verified" or "Next" in a PR body.
<!-- super-board:end -->
