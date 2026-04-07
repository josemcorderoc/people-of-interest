---
name: edit-issue
description: Edit a GitHub issue (title, body, labels, state)
disable-model-invocation: true
argument-hint: "[issue-number]"
---

## Edit a GitHub Issue

Edit issue #$ARGUMENTS.

### Available actions

- **Edit body:** `gh issue edit $ARGUMENTS --body "..."`
- **Add labels:** `gh issue edit $ARGUMENTS --add-label "label1,label2"`
- **Remove labels:** `gh issue edit $ARGUMENTS --remove-label "label1"`
- **Edit title:** `gh issue edit $ARGUMENTS --title "..."`
- **Close:** `gh issue close $ARGUMENTS`
- **Add comment:** `gh issue comment $ARGUMENTS --body "..."`

### Current state

```!
gh issue view $ARGUMENTS
```

Ask the user what changes to make, or follow the calling agent's instructions.
