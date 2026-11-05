# super-qa — BFS Route-Crawler that Builds the Spec Suite

Standalone mode of [super-qa](../SKILL.md). A super-board Tester lane does not read this file.
The SKILL.md sections (auth bootstrap, QA board, filing, test-gap check, security pass, skill
dependencies, safety rails) apply here too.

## Algorithm overview

You are the orchestrator. Your job: drive a BFS crawl of the target app
that **builds `e2e/paths/` into a comprehensive Playwright suite** while
fixing any bugs it stumbles on. Each iteration is a fresh worker — a sub-agent you launch in this
session with the Agent tool — that does ONE iter and exits. There is no
worktree: the worker commits directly to the active branch (default `main`).
This pack ships no headless dispatcher for this loop.

## Autonomous mode — NO AskUserQuestion mid-loop

`/super-qa` is invoked by an operator who walks away (often overnight). The loop must run end-to-end without the
orchestrator pausing on `AskUserQuestion`.

**Decide-and-proceed, don't ask, on these classes of issue:**

- Harness script bugs (parser errors, broken xargs, missing
  `chmod +x`, stale lock files). Fix locally, commit as `🐛 [fix] super-qa: <what>`
  (writing-standard.md § 1), then continue.
- Missing env auto-loads, leftover MCP zombies, log-dir creation.
- Lint / formatting nits introduced by the worker that block its own commit.
- Choosing between equivalent dispatch modes (sequential vs sequential —
  parallel is unsafe, never picked).

**Still halt on these (real forks):**

- Critical-path HUMAN GATE (worker status 4) — production money flow
  red >2 iters. Mandatory halt per skill contract.
- Worker status 2 / 3 with an error that isn't a script bug
  (e.g. Anthropic API down, a production 503, auth credential rejected).
- Working tree dirty with changes the orchestrator didn't make (could be
  user's in-flight work).
- Anything that would delete or rewrite history (`git reset --hard`,
  force-push, branch deletion).

**Status updates instead of questions:** when you make an autonomous fix,
report it in the next status message — what was broken, what you committed
(with SHA), and a one-line revert path, in the session output.

After this loop has run for a while, `e2e/paths/` is the deliverable. CI runs
`npm run test:e2e` on every PR. **No AI involvement in steady-state
regression.** AI is only needed to extend the suite when new pages ship.

```
                AI loop (build phase)            CI (steady state)
               ─────────────────────             ──────────────────
/super-qa      →  e2e/paths/    →    npm run test:e2e on PR
(drains queue.md,        grows toward         catches regressions
 fixes bugs)             comprehensive        without any AI tokens
```

**This skill is INDEPENDENT of `/super-build`.** They share no state.
`super-build` executes new sessions from the GitHub Project board (forward
progress); `super-qa` hardens what already ships by exhaustively
walking the route tree.

## The queue is the curation surface

`docs/super-qa/queue.md` is a markdown checklist the loop reads from
and writes to. Four states per line:

- `[ ]` queued — will be popped next
- `[x]` green spec exists (links to the spec file + iter discovered)
- `[!]` skipped permanently (with reason)
- `[b]` bug found here, children NOT pushed; will be re-tried after fix
- `[?]` flaky — passed on retry, not a bug yet (see flaky policy below)

The queue is **append-only at the back** during normal exploration. The user
can hand-edit it to reorder (turn BFS into DFS for one branch, push something
to the front, etc.). The skill respects whatever the user wrote.

The seed is `client/src/routes.ts` — every static route becomes a `[ ]`
entry under "Level 0".

## What counts as "green" — non-blank guards + forensics

A 200 response with a blank body is a bug, not a green test. Every spec
under `e2e/paths/` enforces:

- **No console errors** (`level === 'error'` only)
- **No uncaught page errors** (`page.on('pageerror', ...)`)
- **No 5xx network responses** during the run
- **No 401/403** on auth-required pages
- **Type-specific non-blank guard** (e.g., list-page: ≥1 row OR
  empty-state element; dashboard: ≥1 widget with non-`—` data) — see
  `docs/super-qa/page-types.md` "Non-blank guard" column

If any of those fire → cell is `[b]` → bug filed.

Per-spec forensics captured by `e2e/lib/report-fixture.ts`:

| Artifact | Path |
|----------|------|
| Screenshot per `report.step()` | `docs/super-qa/report/<slug>/tc-N/<locale>/*.jpg` |
| Console errors | `docs/super-qa/report/<slug>/tc-N/<locale>/console.log` |
| Page errors | `docs/super-qa/report/<slug>/tc-N/<locale>/pageerrors.log` |
| Network HAR | `docs/super-qa/report/<slug>/tc-N/<locale>/network.har` |
| Network summary | `docs/super-qa/report/<slug>/tc-N/<locale>/network.json` |
| Sentry probe | `docs/super-qa/report/<slug>/tc-N/sentry-events.json` |

The fixture (`e2e/lib/report-fixture.ts`) **already captures** console
errors, page errors, failed requests, network summary, and Sentry events,
plus HAR via `recordHar`. Disk writes are gated behind
`SUPER_QA_FORENSICS=1`; set it in every worker's environment. Fixture
exposes everything via `report.forensics.*` (e.g.
`report.forensics.consoleErrors`).

## Algorithm

### 1. Determine iteration count
- If user provides arg (e.g. `/super-qa 5`), use that count.
- If `--resume`, start at `max(existing iteration-*.md) + 1`.
- Default: **10 iterations, sequential**. (Concurrency is unsafe — workers
  share `queue.md`. To run parallel work, branch and run a second
  orchestrator.)

Report once: `🐛 Super QA starting — N iterations`.

### 2. For each iteration N (sequential)

**2a. Pre-flight**
- `next_n = max(existing iteration-*.md numbers in docs/super-qa/iter/) + 1`. If none exist, start at 1.
- Confirm working tree is clean (`git status` has no staged/unstaged tracked
  changes — untracked files are OK). If dirty → halt and notify.
- Verify `docs/super-qa/queue.md` exists. If not, refuse to dispatch
  and report — the queue is hand-seeded once via this skill's setup
  (or already by the commit that introduced the skill).

**2b. Launch the iteration worker**

Launch one sub-agent (Agent tool) in the repo root, no worktree, with
prompt = `references/iteration-preamble.md` + a per-iteration footer (iter
num, base SHA, mandatory final-commit format) and `SUPER_QA_FORENSICS=1`.
When it returns, classify the iteration:
- `0` iter complete — a `🧪 [test] super-qa: iter N` commit is on the current branch.
- `2` worker failed — it errored and left no done or WIP marker.
- `3` no done-commit — it finished but no `🧪 [test] super-qa: iter N` commit exists.
- `4` HUMAN GATE — its output contains `HUMAN GATE TRIPPED:`.
- `5` WIP-CHECKPOINT — it hit its budget mid-fix and left a `🚧 [wip] super-qa:` commit;
  the next iter picks it up.

Report: `🔍 Iter N launched`.

**2c. Wait, then advance**

On status 0:
- Read the close-out commit subject to extract `(X bugs, Y items)`.
- Report: `✅ Iter N done — X bugs, Y items processed`.
- Loop to next iteration.

On status 2 / 3 / 4 / 5:
- Report the worker's last output (its final 50 lines).
- Halt the loop (unless `--continue-on-error` was passed).
- Exit 4 (HUMAN GATE) is mandatory halt regardless — see "critical paths"
  below.
- Exit 5 (WIP) is **not** halt; the next iter's regression phase finds the
  red spec and finishes the fix. Continue.

### 3. Termination check (after every iter)

Stop when **any** of:

- Queue has no `[ ]` items left — natural completion.
- User-supplied iteration count `N` is reached (the `N` in `/super-qa N`).
- A halt gate fires (HUMAN GATE, dirty tree, worker status 2/3/4).
- User interrupts.

**Notification trigger (NOT a stop):** after 3 consecutive iters with zero
bugs found, report a summary like *"diminishing returns: 3 iters, 0
bugs, N items still in queue — continuing"*. The loop continues until the
queue actually drains (or `N` is reached). The user can interrupt manually
if they accept the diminishing returns.

Rationale: zero bugs in recent iters does not prove the unexplored remainder
of the queue is clean. The only way to know is to keep going. The previous
"3 zero-bug iters" auto-halt was budget pragmatism dressed up as completeness.

Coverage % is reported every iter as a progress indicator, never a gate.

### 4. Final report

After termination (or on halt):
- Aggregate: total iters, items moved from `[ ]` → `[x]` / `[b]` / `[!]`,
  total bugs found, total fixed, queue size now.
- Report a summary linking to all `docs/super-qa/iter/iteration-*.md`
  and the current `docs/super-qa/report/QA-REPORT.md`.

## One iteration, in plain English

The worker (per iter N) runs three phases:

**Phase 1 — Regression.** `npx playwright test e2e/paths/` against
everything. Any red spec? Apply the retry policy (re-run once in isolation).
Real reds get filed as bugs in `iteration-N.md`, fixed via TDD, re-run until
green. This is the "verify what we already have" step.

**Phase 2 — Explore.** Until the budget is hit (default: 5 cells popped
OR 30 min wall-clock):
1. Pop the top `[ ]` item from `queue.md`.
2. Classify via the URL-pattern heuristic in `docs/super-qa/page-types.md`.
3. Write a spec at `e2e/paths/<slug>.spec.ts` using the test recipe for that type.
4. Run it.
   - **Green** → mark `[x]`. Walk the rendered page; push newly-discovered
     children (links / buttons / dialogs / tabs — see preamble for the
     verbatim "what counts as a child" rule) to the back of the queue. Cap
     children pushed per page at **10**.
   - **Red** → file the bug to `iteration-N.md`. **Mark `[b]`. Do NOT push
     children.** Try to fix via TDD if budget allows; otherwise leave for
     next iter. After fix, re-mark `[ ]` so a future iter expands the
     subtree.

**Phase 3 — Report.** Write `docs/super-qa/iter/iteration-N.md` (bugs
found, items processed, queue size before/after, coverage snapshot). Run
`npm run qa:report:render`. Commit:
`🧪 [test] super-qa: iter N (X bugs, Y items, Z PRs opened)` (writing-standard.md § 1).

## The bug-handling rule (non-blocking)

> When a spec goes red, the worker logs the bug, marks the item `[b]`, **stops
> expanding into that subtree**, and continues with the rest of the iter's
> batch. Other siblings in the queue still get tested.

A bug on `/customers/:id` shouldn't block exploration of `/orders` or
`/dashboard`. Maximum coverage per iter; one bug never halts the loop.

Fix can happen:
- **Same iter** — if budget allows, the worker runs TDD on the bug after
  the explore phase.
- **Next iter** — if budget exhausted, the bug sits in `iteration-N.md` and
  Phase 1 of iter N+1 finds the red spec and finishes the fix.
- **Manually by human** — fix it whenever; the loop picks it up on the next
  regression pass.

After fix, the `[b]` item gets re-marked `[ ]` and a future iter processes
it (and pushes its children).

## Page-type taxonomy

Classification gives the worker a test recipe per kind of place. See
`docs/super-qa/page-types.md` for the canonical list:

```
list-page       form-page       settings-page
detail-page     dashboard-page  modal/drawer
public-page     import-flow     wizard
                                settings-tab
```

Classification order: URL-pattern heuristic first (cheap default) → AI
override if the heuristic looks wrong → hand-curated override in
`page-types.md` if the user wants to lock something in.

## Critical paths (HUMAN GATE)

`docs/super-qa/critical-paths.md` is a hand-curated list of
money-flow specs that MUST always be green (login, create order, take
payment, run cutoff snapshot, send driver email). The user maintains it;
the skill never auto-edits it.

If any critical-path spec has been red for **>2 consecutive iters**, the
the iteration ends with status **4 (HUMAN GATE)**. The loop halts. A human investigates.
This protects production-critical flows from being silently broken by
in-flight queue items.

## Multi-step user journeys — `docs/super-qa/flows.md`

`critical-paths.md` is the *money-flow guard* (login, checkout, payment) —
small, hand-curated, mandatory human gate if red >2 iters. It is **not** a
coverage layer.

`docs/super-qa/flows.md` is a separate, broader hand-curated list of
*multi-step user journeys* the BFS crawler doesn't reliably exercise on its
own. Examples:

- create user → set role → user logs in → sees their assigned region
- import CSV → review preview → confirm import → verify rows in `/orders`
- create order → assign driver → driver email mock fires → order moves to dispatched

Each entry in `flows.md` is one line per flow with a slug. The worker
generates or updates `e2e/flows/<slug>.spec.ts` for each entry. Specs in
`e2e/flows/` run alongside `e2e/paths/` in Phase 1 regression — same fixture,
same forensics, same `[b]` rules apply. They are **not** pushed via BFS
expansion; they exist as hand-curated chains.

Flows take precedence over individual route specs when both exist for the
same endpoint — a green `e2e/paths/orders.spec.ts` doesn't override a red
`e2e/flows/create-order-end-to-end.spec.ts`.

The user maintains `flows.md`; the skill never auto-edits it. To add a new
flow, the user hand-edits the file; the next iter's Phase 1 picks up the
new slug and generates the spec from a flow recipe.

### `flows.md` template (the worker creates this on first encounter if missing)

```markdown
# super-qa multi-step user journeys

One line per flow. Format: `- slug — short description (route1 → route2 → ...)`

The worker generates / updates `e2e/flows/<slug>.spec.ts` per entry.
These run in Phase 1 regression alongside `e2e/paths/`.

## Flows

- onboard-user — create user, set role, user logs in, sees their region
  (/admin/users/new → /login → /dashboard)
- import-csv-end-to-end — import CSV, review preview, confirm, verify rows
  (/imports → /imports/preview → /orders)
```

## Coexistence with `/super-build`

`super-qa-file-bug.sh` files bugs into the **Super Ultimate QA** project's `Bug` column. This is a separate board from `/super-build`'s standalone feature queue (`BUILD_LOOP_PROJECT`), so the two skills can run concurrently without column races:

- **Standalone `/super-build`** keeps reading `Ready` from its configured feature project. Untouched by `/super-qa`.
- **`Bug` cards reach a builder** when someone moves them to `Ready`, or when `/super-build` runs with `BUILD_LOOP_SOURCE_COLUMN=Bug` against this board. Builds go to `QA` as PRs; nothing moves to `Done` without the Reviewer's merge gate.

If you intentionally want a single board for both lanes, set `BUILD_LOOP_PROJECT=$SUPER_QA_PROJECT_NUMBER` and `BUILD_LOOP_SOURCE_COLUMN=Bug`. Don't do this by accident — the column semantics differ.

## Files involved

```
.claude/skills/super-qa/
├─ SKILL.md                            ← orchestrator instructions (this file)
└─ references/
   └─ iteration-preamble.md            ← worker contract (verbatim prompt)

scripts/super-qa-file-bug.sh           ← files a red spec onto the QA board (installed to .claude/bin/)

docs/super-qa/
├─ README.md                           ← operator's guide
├─ HANDOFF.md                          ← context handoff
├─ queue.md                            ← THE queue (loop reads/writes)
├─ page-types.md                       ← taxonomy + per-page overrides
├─ critical-paths.md                   ← hand-curated money-flow guard
└─ iter/
   ├─ iteration-1.md                   ← per-iter bug log + report
   └─ ...

e2e/paths/                             ← THE deliverable (one spec per place)

docs/super-qa/report/
└─ QA-REPORT.md                        ← regenerated every iter (existing)
```

## Recovery / re-entry

- Default: starts a new batch numbered after the last `iteration-*.md`
  (e.g. if iters 1-5 exist, the next batch starts at 6).
- `--resume`: only run iters whose number is greater than `max(existing)`.
- A leftover `🚧 [wip] super-qa:` commit on the current branch (from a status-5 iteration)
  is OK — the next iter's regression phase finds the red spec and finishes
  the fix.

## Stop conditions

- Queue empty (no `[ ]` items left) — natural completion.
- Iteration count reached (the user-supplied `N`).
- Worker status 2 / 3 / 4 — halt and report.
- User interrupts.

**Note:** "3 consecutive zero-bug iters" is **no longer** a stop condition.
It triggers a "diminishing returns" report but the loop
continues exploring the rest of the queue. See "Termination check" above
for rationale.

## Invocation patterns

- `/super-qa` → 10 iters, sequential, default budget
- `/super-qa 5` → 5 iters
- `/super-qa --resume` → continue from `max(existing) + 1`
- `/super-qa --continue-on-error` → don't halt on a single iter failure

## Companion skill

`/super-build` executes pending issues from the GitHub Project board.
Independent of this skill — they share no state. Run `/super-build` to make
forward progress; run `/super-qa` to grow the spec suite + harden
shipped code.
