---
description: Review the current uncommitted changes against this project's conventions
---

Review what changed, as a tech lead would before merging. If the repo has no git history yet,
review the files touched in this session instead.

Load the rules that apply to the touched paths (`.claude/rules/**`) and check against them, not
against generic best practice.

## Order

1. **Correctness first.** Trace the change. What input makes it wrong?
2. **Architecture.** `backend/tests/test_architecture.py` and the Konsist tests encode the real
   rules, if a change needs one of those relaxed, that is the finding.
3. **Tests.** New behaviour without a test is incomplete. A test that would pass with the feature
   deleted is not a test.
4. **The documented story.** This project's value is that its README says where it loses. If a
   change makes a README number stale, a limitation obsolete, or an ADR wrong, that is a blocking
   finding, not a nitpick.
5. **Comments.** Default is none. Flag any comment that narrates what the code does. Keep only
   the ones that explain a *why* that is not visible: a constraint, an upstream quirk, a
   deliberate trade.

## Output

Findings ordered most severe first, each with `file:line`, what breaks, and the concrete input
that breaks it. Then a one-line verdict: ship / fix first / needs a decision from the user.

Say plainly when you find nothing. An empty review is a valid result and better than invented
findings.
