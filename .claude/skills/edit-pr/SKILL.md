---
name: edit-pr
description: Edit a GitHub pull request (title, body, labels, reviewers)
disable-model-invocation: true
argument-hint: "[pr-number]"
---

## Edit a Pull Request

Edit PR #$ARGUMENTS.

### Available actions

- **Edit body:** `gh pr edit $ARGUMENTS --body "..."`
- **Add labels:** `gh pr edit $ARGUMENTS --add-label "label1,label2"`
- **Edit title:** `gh pr edit $ARGUMENTS --title "..."`
- **Add reviewer:** `gh pr edit $ARGUMENTS --add-reviewer "user"`
- **Add comment:** `gh pr comment $ARGUMENTS --body "..."`

### Current state

```!
gh pr view $ARGUMENTS
```

Ask the user what changes to make, or follow the calling agent's instructions.
