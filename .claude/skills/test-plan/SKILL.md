---
name: test-plan
description: Execute the test plan of a pull request and update the checkboxes
disable-model-invocation: true
argument-hint: "[pr-number]"
---

## Execute PR Test Plan

Run all test plan items for PR #$ARGUMENTS and update the checkboxes.

### Steps

1. **Read the PR body** to get the test plan:
   ```
   gh api repos/:owner/:repo/pulls/$ARGUMENTS --jq '.body'
   ```

2. **For each unchecked test plan item** (`- [ ]`):
   - Parse what needs to be verified
   - Execute the verification (run tests, start services, curl endpoints, etc.)
   - Record PASS or FAIL

3. **Update the PR body** — check off passing items:
   ```
   gh api repos/:owner/:repo/pulls/$ARGUMENTS -X PATCH -f body="..."
   ```

4. **Report results** — list each item with PASS/FAIL. If any fail, describe the failure.

### Rules

- Start Docker services if needed (`docker compose up -d`)
- Run tests in the correct directory (`cd backend`, `cd frontend`)
- Use `uv run` for Python, `npm` for frontend
- Stop services after testing (`docker compose down`)
- If a test requires a browser (visual check), note it as "requires manual verification"
- **Merge gate:** A PR must not be merged while any test plan item remains unchecked. If all items pass, report "ready to merge". If any item fails or is not yet runnable, report "not ready to merge" with the blockers listed.
