# Super Board acceptance instructions

Read CLAUDE.md. Never invoke task-observer. Never add a co-author trailer.
The owner authorized finishing the reviewed integration and its acceptance through
Project #4 linked to maxchangm/super-board. The board is now named Super Board.
Use `.claude/super-board/configs/super-board.json` for this acceptance wave.
The permitted merge destination for acceptance reports is `codex/pi-pilot-20261020`.
Do not deploy or create a release tag. Never merge fault-injection fixtures.

Pi lane workers own implementation, QA and Review. Read the assigned issue and all
comments. Issue #7 owns remaining live Pi boundary acceptance. Claude acceptance is
tracked as blocked in #6 because Claude Code is signed out. Preserve that distinction.
Run issue-scoped QA under run.md, not standalone super-qa route crawling or another board.
Use pstack:poteto-mode at
`/Users/maxchan/.codex/plugins/cache/pstack/pstack/1.1.0/skills/poteto-mode/SKILL.md`.
Do not change product scripts, skills or policy mid-run. File a focused defect if needed.
Keep reports small. Keep raw logs outside tracked files in
`/Users/maxchan/Documents/Codex/2026-10-20/op/outputs/super-board-handoff/implementation-evidence/finish-20261021/`.

Issue worktrees share Git history but do not copy ignored installed resources.
Invoke helpers and skills by absolute path under the configured `repo.path` when
an issue worktree has no installed pack. Never commit copied pack files or helpers.
Disposable child fixture checkouts need their own correctly pinned config.repo.path
and lifecycle ownership. Use this same repo-linked Project #4 and isolated branches.
Never run two dispatchers against the same fixture. Preserve dirty or halted work.

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
