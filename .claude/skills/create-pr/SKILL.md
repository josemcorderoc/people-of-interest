---
name: create-pr
description: Create a pull request for the current branch, linking it to a GitHub issue
disable-model-invocation: true
argument-hint: "[issue-number]"
---

## Create a Pull Request

Create a PR for the current branch linking to issue #$ARGUMENTS.

### Current state

Branch:
```!
git branch --show-current
```

Commits not on main:
```!
git log main..HEAD --oneline
```

### Steps

1. Determine the PR title from the commit(s) — follow Conventional Commits
2. Write the PR body using `.github/PULL_REQUEST_TEMPLATE.md` as the format:
   - `Closes #$ARGUMENTS` as the first line
   - Summary: 1-3 bullet points from the commits
   - Test plan: checklist from the task's acceptance criteria in `.specs/`
3. Push the branch if not already pushed: `git push -u origin $(git branch --show-current)`
4. Create the PR: `gh pr create --title "..." --body "..."`
5. Report the PR URL
