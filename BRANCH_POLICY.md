# Branch and release policy (WP4)

> **Status (2026-07-23):** This document describes the current
> branch topology of the repository and the WP4 follow-up required
> to make it sane for outside contributors.

---

## Current state (pre-WP4-fix)

The repository's `origin/HEAD` points to
`day-03-v0.3.2/cooler-structural-fix`. This is a **historical
engineering branch** that contains the full Day 1-14 commit history
through the v1.0.0 release (`8282d29`) and the Day 14 plant-rename
(`2b24a3c`). The `main` branch exists but is **not the default**;
it is a one-commit-branch that points at the WP0 ground truth.

The remediation work (WP0-WP6) is on a chain of short-lived branches:
`remediation/wp0-ground-truth` -> `remediation/wp1-methodology` -> ...

---

## What is wrong with that

1. **Default branch should be `main`.** Outside contributors
   clone the default branch. A historical engineering branch as
   the default is misleading.

2. **`main` is empty.** The current `main` is one commit (WP0).
   It should be the integration branch for the post-remediation
   state.

3. **Remediation branches are sequential.** The WP0-WP6 work was
   structured as a chain of branches so each one is reviewable in
   isolation. That is good for review; it is bad for integration
   because `main` doesn't reflect the integrated state.

---

## WP4 follow-up (after WP0-WP6 PRs are merged)

After the WP0-WP6 PRs are merged, the recommended branch state is:

1. **Default branch: `main`.** This requires changing the default
   branch on GitHub (Settings -> Branches -> Default branch). The
   historical engineering branch
   (`day-03-v0.3.2/cooler-structural-fix`) is preserved for
   archaeology but is not the default.

2. **`main` reflects the integrated post-remediation state.** All
   WP0-WP6 commits are merged into `main`. The single source of
   truth for "what is in the repo right now" is `main`.

3. **Future work branches off `main`.** New features branch from
   `main`, not from the historical engineering branch.

4. **The `remediation/*` branches are archived.** They are
   preserved in the reflog and visible in the GitHub branch list,
   but no new work goes on them.

---

## Git commands for the WP4 follow-up (for the user)

The WP4 follow-up requires GitHub repo admin access. Suggested
sequence:

```bash
# 1. After all WP PRs are merged into day-03-v0.3.2/cooler-structural-fix
git fetch origin

# 2. Create the new main from the integrated state
git checkout -b main origin/day-03-v0.3.2/cooler-structural-fix
git push -u origin main

# 3. (On github.com) Settings -> Branches -> Default branch -> main

# 4. (Optional) Protect the old historical branch
#    Settings -> Branches -> Add rule -> Branch name pattern: day-03-v0.3.2/*
#    -> Require pull request reviews before merging
```

These commands are documented here for the user, not executed by
the assistant. The user is the repo admin and decides when to
switch the default branch.
