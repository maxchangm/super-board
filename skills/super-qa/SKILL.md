---
name: super-qa
description: >-
  Super QA canonical workflow for functional bug-bash, evidence capture, and fix-ready issue filing.
  Crawls routes from `docs/super-qa/queue.md` with Playwright, records screenshots/logs/HARs, files
  product-readable issues with clear type/priority/area labels, and continues until traversal is
  complete or only human-gated blockers remain. Crawling is always browser-driven, but the regression
  test it leaves behind is written at whichever layer the defect actually lives — unit or integration
  in Vitest, e2e in Playwright only when the browser is the thing that broke. Use when the user says
  "run super-qa", "QA review", "bug bash", "verify and fix", or invokes `/super-qa`.
---


**For a board worker, before writes or worktree creation:** follow [skill readiness](../super-board/references/skills-readiness.md).
Resolve this lane for the actual host, load the report's files/fallbacks, halt
on missing requirements and recheck each conditional helper before use.

# super-qa

Two modes share this file. **Board worker** (the super-board Tester lane): this file is every super-qa
rule the lane uses. Read the lane rules in run.md with `bash .claude/bin/super-board-role-rules.sh tester`, not
run.md whole; it prints every run.md section the Tester follows. Open another run.md section only when
those rules point at it. **Standalone** (`/super-qa`, the route crawler that builds the spec suite): also read
[references/standalone.md](references/standalone.md), which holds the crawler loop.


## Auth bootstrap — auto-discover, never ask

Before iter 1, resolve a test login. **Never ask the user; discover or create.** Order:

1. **Cached creds** at `.claude/settings.local.json` `.e2e.user` / `.e2e.pass` — use them as-is.
2. **Env-file fallback** — read in order: `.env.production.local`, `.env.local`, `.env`. Pull `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`. If both present, auto-create `e2e-test@<owner-domain>` (owner from `git config user.email` domain, fallback `erictech.ca`) via:
   ```bash
   curl -sS -X POST "$SUPABASE_URL/auth/v1/admin/users" \
     -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
     -H "Content-Type: application/json" \
     -d "{\"email\":\"$E2E_USER\",\"password\":\"$E2E_PASS\",\"email_confirm\":true,\"user_metadata\":{\"role\":\"e2e-test\",\"created_by\":\"super-qa-bootstrap\"}}"
   ```
   Generate a 24-char random password (`openssl rand -base64 24 | tr -d '/+=' | cut -c1-24`). Save to `.claude/settings.local.json` `.e2e` so the next run skips bootstrap. Verify by logging in (`POST /auth/v1/token?grant_type=password` returns access_token).
3. **Unauth-only fallback** — if neither cached creds nor env-file admin key exist, log "no admin key — restricting to public routes" and proceed with `/login`, `/signup`, `/forgot-password` only. Do NOT halt.

The bootstrap is **non-interactive**. If the curl returns an existing-user error (`User already registered`), reset the password via the same admin endpoint and continue. Save creds either way.

## QA loop state board — GitHub Project as the state store

State for the QA↔Build loop lives in a GitHub Project named **`Super Ultimate QA`** (auto-discovered by title at the user/org level). It has six Status columns:

| Column   | Meaning                                              |
|----------|------------------------------------------------------|
| Queue    | Work the next iteration will pick up                 |
| Testing  | Feature currently being explored or verified         |
| Done     | Spec passing, no action needed                       |
| Bug      | Failing spec; Super Build picks these up next        |
| Flaky    | Only passes on retry; quarantine + investigate       |
| Skip     | Out of scope; documented and parked                  |

This board is the durable, machine-readable state for the loop. `docs/super-qa/queue.md` remains the BFS route seed and audit log, but **all actionable findings land on the project board** so the build lane can pick them up without parsing markdown.

### Project resolution

Resolution order (used by `scripts/super-qa-file-bug.sh` and the orchestrator):

1. If `SUPER_QA_PROJECT_TITLE` is set, query `gh project list --owner $SUPER_QA_PROJECT_OWNER --format json` and pick the project whose title matches (case-insensitive).
2. Otherwise default to title `Super Ultimate QA`.
3. Owner defaults to `$(gh repo view --json owner -q .owner.login)` or `SUPER_QA_PROJECT_OWNER` if set.

If no matching project exists, the loop halts with a one-line error and instructs the operator to create one. Do not silently fall back to the repo's primary project — column semantics differ.

### Filing semantics

When the worker finds a red spec, it calls `scripts/super-qa-file-bug.sh`. The script:

- Creates the issue with `source:qa` label and full evidence body.
- Adds the issue to the resolved **Super Ultimate QA** project.
- Sets the Status field to `Bug` (override with `SUPER_QA_TARGET_OPTION_NAME`).

A `Flaky` retry-only finding goes to `Flaky`; out-of-scope routes go to `Skip`. The same issue may also live on a repo-level project for normal triage — Status on the QA project is the loop state; status elsewhere is independent.

## Findings land in clear GitHub Issues, NOT in markdown

Every `[b]` cell triggers the worker to call `scripts/super-qa-file-bug.sh`.
The resulting Project card must be readable from the board without opening it.
Do **not** use legacy `[VFL]`, `verify-fix`, or `severity:P*` wording in new issue titles.

**Title format:**

```text
<emoji> <Type> <route?> — <short action/result>
```

Examples:

```text
🐛 Bug /imports — CSV upload fails after submit
🎨 UX /settings/users — Add user button is a no-op
🧪 Tests /orders — missing coverage for failed payment state
📝 Docs /delivery — SPEC section missing for dispatch flow
```

**Priority labels use plain words:**

- `priority:high` — urgent, release-blocking, data-loss, security/auth, money, or critical feature broken.
- `priority:medium` — important feature degraded, important edge case, a11y/i18n issue, or user confusion that should be fixed soon.
- `priority:low` — polish, cosmetic, copy, documentation, testability, or cleanup.

**Required labels:**

- Type: `bug`, `feature`, `ux`, `tests`, `docs`, or `tech-debt`.
- Source: `source:qa`.
- Priority: `priority:high`, `priority:medium`, or `priority:low`.
- Area: `area:<product-area>` when known (`area:settings`, `area:imports`, `area:admin-shell`, etc.).
- QA category when relevant: `qa:functional`, `qa:visual`, `qa:network`, `qa:console`, `qa:i18n`, `qa:a11y`, `qa:data`, `qa:testability`.
- Suggested skill owner when helpful: `skill:super-build`, `skill:super-qa`, `skill:ui-refine-loop`, or `skill:super-review`. `skill:ui-refine-loop` marks a UI ticket for a human to run `/ui-refine-loop` on; the board never triggers it.

The script adds the issue to the resolved `Super Ultimate QA` project and moves it into the `Bug` column (override with `SUPER_QA_TARGET_OPTION_NAME`) so a human (or `/super-build` with `BUILD_LOOP_SOURCE_COLUMN=Bug`) can pick it up immediately. The repo's standalone feature project is not touched by this flow.

The `iteration-N.md` Section 3 is the per-iter audit (with `gh_issue: <N>` back-references); the GH issue is the durable tracker. The fix-commit message includes `(closes #<N>)` so the issue auto-closes on merge.

**Triage all loop-filed findings:**
```bash
gh issue list -l source:qa --state open
```

This is a carved exception to the project rule "ask before `gh issue create`": the loop is autonomous and unattended, so it is authorized to auto-file — but ONLY with the clear `source:qa` label and the evidence template below.

### Required issue body template

Every auto-filed finding must give a future headless Claude/Super Build session enough context to fix it without re-discovering the bug from scratch:

```markdown
## Summary
<one sentence: what is wrong and where>

## Repro steps
1. <exact login/route/action>
2. <next action>
3. <observed failure>

## Expected behavior
<what should happen, citing SPEC.md, DESIGN.md, or product intent when possible>

## Actual behavior
<what happened instead>

## Evidence
- Screenshot: <embedded image or repo/raw path>
- Console: <0 errors or paste relevant lines / path to console.log>
- Network: <failed requests or path to network.json/HAR>
- Page errors: <0 errors or path to pageerrors.log>
- Spec: `<e2e/paths/...spec.ts>`

## Suggested fix path
- Suggested owner: `super-build` | `super-qa` | `super-review` | `ui-refine-loop` (UI ticket — a human can run `/ui-refine-loop`; the board never triggers it)
- Suggested skills: `mattpocock-skills:diagnosing-bugs`, `mattpocock-skills:tdd`, `verification-before-completion`
- Notes for implementer: <first suspected file/function, if known>

## Acceptance criteria
- [ ] <user-visible behavior fixed>
- [ ] <Playwright/regression coverage added or updated>
- [ ] <Super QA rerun passes this route>
```

If a screenshot/network/console artifact does not exist, explicitly write `not captured` and explain why. Do not leave evidence ambiguous.

### Filing guardrails

`super-qa-file-bug.sh` validates issue bodies before filing. It must reject weak tickets that are missing required sections or still contain placeholders like `TBD`, `<...>`, or `TODO:`. Do not bypass this with `SUPER_QA_ALLOW_WEAK_BODY=1` during normal autonomous runs. `--check-body` runs only these checks and exits (0, or the refusal code) without calling `gh`; super-collect's dry run uses it.

Every filed issue must include:

- `## Board summary` near the top for quick project-card context.
- A hidden `super-qa-meta` block with route, spec, iteration, area, category, priority, type, and `fingerprint`.
- A deterministic fingerprint. Use a meaningful key when known, such as `settings-users|add-user|no-op`; otherwise the script derives one from kind/route/category/title.

Dedupe policy: before creating a new issue, the script searches open `source:qa` issues for the fingerprint. If a match exists, it comments with the new evidence and returns the existing issue number instead of creating a duplicate Ready card.

## Test-gap check (after build)

Issue-scoped mode only (super-board Tester, or any run handed a finished diff). The
Builder's tests answer "does it do what I built?"; this answers "what breaks silently?".
Scope is the diff: `git diff --name-only $(git merge-base HEAD origin/<base>)...HEAD`.
On auth, money, data-loss or security changes, hand steps 1-3 to a read-only sub-agent
given only the ACs, the range and the changed-file list, so it is not anchored on the
Builder's reasoning.

1. **Ledger.** Every AC → the asserting `file:line` at unit, component and e2e, or `none`,
   or `n/a: <reason>`. Fill the unit column for all ACs first, then component, then e2e.
   A test that runs the code but asserts nothing about the AC is `none`.
2. **Edge cases.** For each changed input or branch, mark each class pinned (`file:line`),
   gap (exact witness value, never "consider edge cases") or n/a: boundaries (limit−1 /
   limit / limit+1; 0 vs null vs empty), money and dates (rounding, timezone shift, month
   end), input (unicode, very long, CSV injection), volume (0 / 1 / many, paging), auth
   (logged out, another user's id, wrong tier), error paths (every catch and rejected
   promise), idempotency and races (double-submit, replay), UI states (loading, empty,
   error, disabled), accessibility (role + accessible name, focus).
3. **Test the tests.** Flag a test that asserts on its own mock, recomputes the expected
   value with the code under test, or cannot fail. For high-risk logic, name the surviving
   mutant (`>` → `>=`, a dropped branch) no test would catch.
4. **Rank.** High: an AC with no test at any rung; any gap in auth/ownership, money,
   security or data loss. Medium: a partly covered branch, a surviving mutant, a missing
   loading/empty/error state. Low: cosmetic, copy, logging.
5. **Act.** Write every High gap now, red first, through `mattpocock-skills:tdd` (or
   `tdd-v2` where the repo has it), at the rung the localisation ladder picks. A new test
   that passes on its first run has not been seen to fail: break the guarded line, see
   red, restore it, see green; the mutation never reaches a commit. A High gap that needs
   app code changed to pass or to become testable is a **Fail**: bounce to Builder
   (QA → Ready) with the list (witness, expected, rung, target file). Medium and Low go
   in the handoff under `Test gaps (not written)` and never block.

## Security pass (every PR)

QA's one security check. Run it on every PR, not only on security labels; with no PR yet
(a `qa` card with no diff), say `pr-security-review: no diff` on the `Did:` line.

1. Load `pr-security-review` and follow it on the PR's diff against its base branch
   (`gh pr view <PR> --json baseRefName`). It runs in this lane, not in a sub-agent: it
   launches its own finding and false-positive sub-tasks.
2. Each finding it keeps is a QA failure, filed the normal way: one `❌ Not done` line
   (`security: <category> — <one line> · <file:line>`), one `[builder]` PR thread on that
   line, then the **Fail** exit (QA → Ready, `loop:rebuild-N`). A finding outside the
   card's scope is filed with `super-qa-file-bug.sh` (`source:qa`, priority high) and still
   fails the card while the PR adds the hole.
3. A finding you can show is wrong goes on the `✅ Done` line with the proof.
4. No findings → `pr-security-review: 0 findings` on the `Did:` line.
5. Skill missing → Block the card (`🔐`, needs install). Never pass a PR unchecked.

This replaces Claude Code's built-in `/security-review`, which super-qa no longer calls.
For a deep audit of the whole repo, mention `security-audit` (standalone, if installed);
never run it from the lane.


## Skill dependencies

The worker (per `references/iteration-preamble.md`) must load and follow:

- `mattpocock-skills:ask-matt` (router — when the right flow is unclear)
- `mattpocock-skills:tdd` (the discipline layer — seams, red-green, assertion
  anti-patterns; does not change with the kind of test)
- `mattpocock-skills:diagnosing-bugs`
- `verification-before-completion` (no Matt Pocock equivalent — kept as-is)
- `pr-security-review` — the security pass on every PR (bundled with the pack)
- `testing-strategy` — coverage judgment per component type, and what to skip.
  Consult it for *what is worth testing*; it does not pick the layer. The
  localisation ladder in `references/iteration-preamble.md` picks the layer.
- `vitest` — mechanics for unit and integration tests in a TS/JS repo. 19
  references (`core-expect`, `features-mocking`, `features-coverage`,
  `core-hooks`, `advanced-vi`).
- `playwright-best-practices` — when writing or refactoring a spec. Reference
  its `core/locators.md` (data-testid first, `getByRole` fallback),
  `core/fixtures-hooks.md` (custom fixtures for auth, pre-test seeding, teardown),
  `core/test-data.md` (test data factories), and `core/page-object-model.md` (POM for
  reusable interactions). Keep specs reusable as the suite grows.

## Test target & safety rails

The default target is the app target configured by `BASE_URL`. Treat production URLs as production and prefer preview/staging for mutating flows.

Safety rails (enforced by the iteration preamble):
- Test user: configure via app env, for example `QA_BOT_EMAIL` / `QA_BOT_PASSWORD`.
- All written test data is prefixed `[TEST] ` so it's greppable.
- Sentry tag `source=super-qa` on errors.
- DB resets DISABLED (`RESET_DB=false`) — would wipe prod.
- Email sending mocked via `RESEND_API_KEY=mock_<anything>`. **Required:** run against a staging deploy (`NODE_ENV=staging`, `EMAIL_DRY_RUN=1`) — not prod. If no staging URL is configured, halt with `STATUS: halt (no-staging-env)`.
- Override the target via `BASE_URL=…` in the worker's environment.

## super-board integration

When invoked by super-board (env `SUPER_BOARD_RUN=1` or invocation contains "super-board run"):

- **GitHub budget** — every "move card" is `.claude/bin/super-board-card.sh --config <cfg> move <N> <Status>` (1 GraphQL point; `gh project item-list` / `field-list` cost ~100–200). Comments, labels and PR reads go over REST; [rate-limit-etiquette.md](../super-board/references/rate-limit-etiquette.md) → "Price list" has the calls.

### State protocol (same as super-build)
- Read from issue + PR comments + PR review threads.
- Respect handed-down worktree + branch.
- After pushing tests, evidence or fixes to a PR, refresh [PR author notes](../super-board/references/pr-author-notes.md) before the handoff. Keep file summaries current and explain critical changed sections on the PR.

### Card types
- **Built card (`feature`, `bug`, no label):** worktree at `.claude/worktrees/issue-<N>-qa/` checked out at Builder's branch tip.
- **`qa` card (skipped Building):** move it Ready → QA yourself, create `issue-<N>-<slug>` from the base branch, test what is already there (run.md → "qa cards").
- **A live URL with no repo** is not a board card: `/super-qa <url>` runs standalone.

### Rounds, scope and found problems
[lane-rules.md §§ 3–4](../super-board/references/lane-rules.md). Round 1 (no earlier `[qa] [report]` on the PR): report **every problem you can prove**, each with `file:line` and evidence, not the first one.
A later round verifies only the previous round's findings and new breakage in lines changed since the previous round's head
(`git diff <prev-head>..HEAD`); an old problem you missed is not a reason to send the card back now. Scope is the issue's
Acceptance Criteria plus the plan's scope statement (its "In scope / Out of scope" section, when the plan has one). A proven problem
outside it is filed with `bash .claude/bin/super-review-file-refactor.sh --config <cfg> --found-by qa --from-issue <N> ...`, listed in the
report as `filed #<new>`, and does not fail the card. The 3-try limit (`rebuild_cap`) stays.

### Close-held evidence pass
A card in QA whose PR is **merged** and whose issue carries `<!-- super-board:close-held merge=<oid8> -->` for that merge was held by the
close proof ([lane-rules.md § 1](../super-board/references/lane-rules.md)). This pass writes no code, opens no PR and does not rebuild:
1. Skip the worktree. Test the merged behaviour at `target.url`, once per acceptance criterion with a visual surface, desktop 1920×1080,
   with the criterion's result in view. Do not crop, blur or edit a screenshot.
2. Publish each PNG so it outlives the branch: follow `close_proof.evidence_route` from the config when set, else commit the PNGs to
   a `runs/issue-<N>-evidence-<oid8>` branch and link `raw/<SHA>/...` URLs.
3. Post ONE comment on the issue that names the merge commit (first 8 hex digits), embeds the images, carries an `### Acceptance criteria`
   table with a PASS or FAIL row per box, and ends with `<!-- super-board:close-evidence merge=<oid8> -->`. A fix with no visible
   surface says `No visual surface: <reason>` instead of images.
4. Run `python3 .claude/bin/super-board-close-proof.py close --config <cfg> --issue <N> --pr <P> --merge <sha> --head <reviewed head>`.
   Exit 0 closes the card. Exit 3 again means the proof is still missing: do not loop, stop with the card in QA and say what is missing.
   One evidence pass per merge: when the close-evidence marker for that merge is already on the issue, do not run another.

### Lifecycle (Tester, first pass)
The full steps are run.md → Tester (first pass — repo-backed), in the `super-board-role-rules.sh tester` output. Summary:
1. Pull latest of base; checkout `issue-<N>-<slug>` into worktree (a `qa` card: create it from the base).
2. Read issue + PR + Builder's handoff.
3. Build issue-scoped test plan: ONE observable test per AC.
3a. Existing project verifier → follow [project-verifier.md](references/project-verifier.md)
for affected selection, host readiness, real assertions and fresh proof.
3b. Run the **Test-gap check** (above) against the Builder's diff; its High gaps join the plan.
3c. Run the **Security pass** (above) on the PR's diff. Any kept finding → Fail (step 7).
4. Run tests. Capture evidence to `docs/super-board/runs/issue-<N>-qa-v<N>/`. **For any UI-affecting issue, capture at least one screenshot per AC** (Playwright `page.screenshot` or `browse --screenshot`). Save with descriptive names: `ac1-<short-desc>.png`, not `screenshot1.png`.
5. **Commit the evidence directory** to the issue branch alongside test files (`git add docs/super-board/runs/issue-<N>-qa-v<N>/ && git commit && git push`). This is non-optional — without it, the inline image markdown in the issue comment won't render on GitHub.
6. **Pass** → tick the PR's `ac` block with proof lines, write `visual` for UI, append a `history` row, rewrite `status` (`super-board-pr-body.sh`) → `[qa] [report] ✅` PR comment with results + evidence path → **issue comment with screenshot evidence** (see "Issue-comment evidence format" below) → move QA → Review. Clean up worktree.
7. **Fail** → leave failing ACs unchecked with the reason, append a `history` row, rewrite `status` → `[qa] [report] ❌` PR comment with per-AC expected/actual + repro file:line + evidence path + "what fixed should look like" → issue comment with the failure screenshots → increment rebuild counter → move QA → Ready (label `loop:rebuild-N`). Clean up worktree.

### Optional project feature verifier

For an existing `.agents/skills/verify-<app>/` map, verifier creation during Onboard,
or source/selector upkeep, read [project-verifier.md](references/project-verifier.md).
Run relevant mapped features alongside issue AC checks; state missing/stale coverage
in the existing handoff. A map inspection or starter template proves no test pass.

### Optional runtime performance and memory checks

For runtime evidence requested by the issue, or a configured
`runtime_verification.config`, read [runtime-verification.md](references/runtime-verification.md).
Use the shared runner with a project-owned scenario and existing Playwright. Compare
pinned original/changed apps with matching data/environment, warmups and at least
five alternating samples each. Attach timing ranges, heap evidence, correctness
failures and verdict to the normal QA handoff under `Runtime checks:`. A noisy or
inconclusive result cannot prove a performance AC; do not replace correctness
checks or add profiling to unrelated issues.

### Pass-handoff PR comment MUST include the test command
Every Pass-handoff PR comment includes a `Local tests:` line with the EXACT command Reviewer will re-run as the self-verification gate:
```
Local tests:  npm test --run streaming
```
This is non-optional. Reviewer re-runs this command; red → bounce back to QA.

### Issue-comment evidence format (REQUIRED — both pass and fail)

The Tester's issue comment is the user's primary visibility into "is this actually fixed." A bare directory path is not sufficient — the user wants to *see* the proof on the issue page.

**The canonical template lives in `.claude/skills/super-board/references/run.md` → "Screenshot embed format" (right after Tester first pass, in the `super-board-role-rules.sh tester` output).** Do not duplicate it here; both lanes (super-board Tester + standalone super-qa) follow that exact format. Summary of rules workers must obey:

- Capture screenshots at the standard viewports for UI ACs: **desktop 1920×1080, tablet 1024×768, mobile 375×667**.
- Commit the screenshots to the issue branch and push *before* writing the comment — inline image URLs won't render unless the file is on GitHub.
- Use the `https://github.com/<OWNER>/<REPO>/raw/<SHA>/...` URL form, `<SHA>` = the commit that added the screenshots, so images keep rendering after the branch is deleted on merge. Resolve `<OWNER>/<REPO>` from `git remote get-url origin`.
- Embed the same screenshots in BOTH the PR timeline comment AND the issue comment — the issue page is the user's primary view.
- Name the evidence folder once (`runs/issue-<N>-qa-v<V>/`) — no file lists.
- For non-visual ACs (API tests, migration SQL), skip the screenshot table but keep the evidence-path line. State the omission explicitly so the user knows it was intentional.
- If screenshot capture fails (no display, headless crash), document the reason and link alternative evidence (log file, HTTP trace) rather than silently dropping the requirement.
- Failure comments use the same format with broken-state screenshots (e.g., `before-fix-desktop.png`).

### Lifecycle (Tester, rebuild — when Reviewer bounced for [qa] thread fixes)
1. Read PR review threads; filter `[qa]` prefix.
2. For each unresolved `[qa]` thread: apply fix to test files → resolve thread via `gh api graphql resolveReviewThread`.
3. Re-run full test suite for the ticket.
4. Save evidence to `runs/issue-<N>-qa-v<N+1>/`.
5. Commit + push. Verify ALL `[qa]` threads resolved.
6. Update the PR's `ac`, `history`, `status` blocks; post `[qa] [report]` PR + issue comments (writing-standard.md § 4). Move QA → Review.

### Failure → `root-cause-hash:` line required
Hash lane = `qa`. Same input definition as super-build.

### Block/Skip exits use the §4 mandatory template
Same rule as super-build.
