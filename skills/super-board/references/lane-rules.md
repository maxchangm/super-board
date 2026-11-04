# Lane rules — close proof, thread-only stops, rounds, found problems

The rules every lane shares. The lane skills and `run.md` point here; nothing in this file names a
project. A project's own paths and markers come from its board config (`close_proof`, `intake_column`
in `config-schema.json`). A runner or wrapper changes a lane by changing these files, never by adding
prompt text that overrides them.

## 1. Close proof

A `bug` or `feature` card closes only with **AFTER screenshots at the merged code** (plus **BEFORE**
when one exists) in the closing comment, and with **every acceptance-criteria box ticked from a PASS
row** of the final QA or Review "Acceptance criteria" table. Without both, it does not close.

- The judge is `super-board-close-proof.py` (rules in its docstring, tests in `tests/test_close_proof.py`).
  Reviewer's merge protocol step 4 runs `close`: it comments, ticks the boxes, closes the issue and
  moves the card to Done when the proof holds. When it does not, it comments the missing proof, ends the
  comment with `<!-- super-board:close-held merge=<oid8> -->`, leaves the issue open and moves the card
  to **QA** (exit 3). The merge itself already happened; Reviewer stops there.
- A refactor, a card that is neither bug nor feature, a QA comment that states `No visual surface:
  <reason>`, and an approved-change card whose merged PR changed no UI file close with
  `**No visual surface:** <reason>.` in place of images. UI files are `close_proof.ui_globs`.
- QA puts its screenshots in a comment that names the reviewed head (`git rev-parse --short=8`), with
  its acceptance table. That comment is what the judge reads. Never edit a screenshot.
- **Close-held card.** A card in QA whose PR is merged and whose issue carries the held marker for that
  merge gets one evidence-only QA pass (super-qa → "Close-held evidence pass"). It changes no code.

## 2. A thread-only review stop is not a try

Super Review's Gate 1 (an unresolved `[builder]` or `[qa]` thread) returns the card without judging any
code. It therefore does **not** add or raise `loop:rebuild-N`, writes no Reviewer report, and posts one
PR comment that ends with `<!-- super-review:gate1:<issue>:<ids> -->` (`<ids>`: the database ids of the
first comments of the open threads, comma-separated). Build already resolves every `[builder]` thread
before handoff, so a thread that is still open after Build is the Builder's miss, not a new finding.
When any open thread id already appears in an earlier gate1 marker on the PR, the second stop counts:
raise `loop:rebuild-N` as for any bounce.

## 3. Rounds in QA and Review

The 3-try limit (`rebuild_cap`) stays. To keep it from being spent on one problem at a time:

1. **Round 1** (no earlier `[qa] [report]` on the PR for QA, no `prior_report` for Review): report
   **every problem you can prove**, each with class, severity, `file:line` and evidence. Do not stop at
   the first. An unproven suspicion is not a finding.
2. **Later rounds**: verify only (a) each finding of the previous round against the code, and (b) new
   breakage in the lines changed since the previous round's head (`git diff <prev-head>..HEAD`). A new
   observation about lines nobody changed since round 1 is a round-1 miss: do not send the card back for it.
3. **Scope.** The issue's Acceptance Criteria and the plan's scope statement (the plan comment's
   "In scope / Out of scope" section, when the plan has one) say what the card is for. A proven
   problem outside that scope is **not a send-back**. File it (section 4) and carry on.

## 4. Found problems

- **Build:** a bug found while working that sits in a file this card already changes is fixed in the
  same PR, with a `Found and fixed:` bullet in the PR body's `solution` block. Any other bug found
  becomes an issue (below). Do not widen the diff for it.
- **QA and Review:** a proven problem outside the card's scope becomes an issue (below), mentioned in
  the report as `filed #N`. It never bounces the card.
- **Filing:** `bash .claude/bin/super-review-file-refactor.sh --config <cfg> --found-by build|qa|review --from-issue <N> --title ... --body-file ... --fingerprint ...`.
  It creates the issue with `bug` and `found-by:<lane>` labels, a `Found while working #N` link,
  places it in the board's intake column (`intake_column`, default `Backlog`; never Ready), and comments
  the new number on #N. A repeat of the same fingerprint adds a sighting instead of a second issue.
