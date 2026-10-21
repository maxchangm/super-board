# Super Board focused repair instructions

Read CLAUDE.md. Never invoke task-observer or its protocol. Never add a co-author trailer.
The owner authorized finishing this reviewed integration through Project #4 linked
to maxchangm/super-board, named Super Board. Claude acceptance is deferred at the
owner's explicit request. All active product work uses Pi.

Current phase: fix issue #12, absent repair-phase display labels. Use
`.claude/super-board/configs/super-board.json`. The only permitted merge destination
for this focused fix is `codex/pi-pilot-20261020`. Do not deploy or create a release tag.
Pi lane workers own implementation, QA and Review. Use pstack:poteto-mode at
`/Users/maxchan/.codex/plugins/cache/pstack/pstack/1.1.0/skills/poteto-mode/SKILL.md`.
Read issue #12 and all comments. Commit a failing faithful regression before the
small shared fix. Preserve the canonical record, ownership, counts, failure halts
and head-bound merge policy. Do not add a runner or an evaluation framework.

The real acceptance run halted and all owned worker processes exited. Issue #9
has one persisted idle canonical record with repairs=0 and pending_lane=build.
The failed command partially applied loop:rebuild-0. No mutation was replayed.
Preserve all halted issue #7/#8/#9 worktrees, claims, branches and draft PRs.
Do not resume fixtures or reset their state as part of #12. After this fix is
independently accepted, the coordinator will explicitly resume acceptance #7.

PR #1 is the existing integration delivery. Its overlapping helper paths are an
intentional stacked correction from this observed defect, not a duplicate fix.
Proceed with the appropriate preflight conflict note. PR #1 currently closes no
separate implementation issue. Do not modify or merge PR #1 from this #12 lane.

Issue worktrees do not copy ignored installed resources. Invoke installed helpers
and skills by absolute path under the configured project root when absent in your
worktree. Never commit copied pack files or helpers. Keep raw evidence in
`/Users/maxchan/Documents/Codex/2026-10-20/op/outputs/super-board-handoff/implementation-evidence/finish-20261021/`.

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
