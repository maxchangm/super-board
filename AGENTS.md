# Super Board focused readiness fix

Read CLAUDE.md. Never invoke task-observer or its protocol. Never add a co-author.
The owner authorized finishing the integration using repository-linked Project4.
Claude live acceptance is deferred. Use Pi. Parent is orchestration only.
Current phase: only issue14, keep readiness Card data outside shell commands.
Use .claude/super-board/configs/super-board.json, base codex/pi-pilot-20261020.
Issue7 and its retained fixtures8/9 are held and must not be changed by this fix.
No patch to guard-secrets, guard policy, canonical repair state or budgets.

Full operator evidence and task trail:
/Users/maxchan/Documents/Codex/2026-10-20/op/outputs/super-board-handoff/implementation-evidence/finish-20261021/
Native rejection source was identified in session01a15cac-5793-7365-a705-0127e7f67754.
Ordinary Card prose matched the existing secret guard because the launcher told
the worker to inline it into Bash. Keep the guard. Use the existing file-input
contract with the complete hydrated Card and preserve halt evidence.
Stage a faithful failing regression before the minimal fix. Fresh QA/Review follow.

Every required diff read first fetches --kind metadata with
files,labels,body,additions,deletions,changedFiles,headRefOid. Then --kind diff
MUST pass --meta pointing to that fresh file. Never omit --meta.
Use installed helpers by absolute root path in worktrees lacking ignored pack.
Do not inline captured Card/transcript text into Bash during reproduction.
Ordinary reports have no blocked-by footer. It is only for an actual blocker,
and a bare dash is a human gate. The body uses - None. under Blocked by.
Preserve issue7QA and its nested fixture repos at their current absolute paths.
No force checkout/push and no changes to main.
Use pstack poteto-mode at
/Users/maxchan/.codex/plugins/cache/pstack/pstack/1.1.0/skills/poteto-mode/SKILL.md.

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
