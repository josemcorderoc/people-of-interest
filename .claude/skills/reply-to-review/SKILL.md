---
name: reply-to-review
description: Fetch review comments on a PR, address them with code fixes, and reply to each
disable-model-invocation: true
argument-hint: "[pr-number]"
---

## Reply to Review Comments

Address review comments on PR #$ARGUMENTS.

### Current comments

```!
gh api repos/:owner/:repo/pulls/$ARGUMENTS/comments --jq '.[] | "ID: \(.id) | File: \(.path):\(.original_line) | Author: \(.user.login) | Body: \(.body)"'
```

### Process

For each comment:

1. **Evaluate critically** — is it a real bug, unnecessary complexity, out of scope, or a style preference?
2. **If sound**: fix the code with a commit, then reply referencing the commit hash
3. **If unsound**: reply with a clear explanation of why it was dismissed
4. **Reply to every comment** — never leave one without a response

### Reply format

Use `gh api repos/:owner/:repo/pulls/$ARGUMENTS/comments -f body="..." -F in_reply_to=COMMENT_ID` to reply.

Every reply must end with: `— 🤖 Claude`

### Rules

- Never resolve threads — thread resolution is the human reviewer's responsibility
- Never blindly apply suggestions that add complexity without benefit
- Reference commit hashes when fixing code
- Group related fixes into a single commit where practical
