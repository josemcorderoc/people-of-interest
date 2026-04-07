---
name: open-issue
description: Open a GitHub issue for a bug or problem found during QA or development
disable-model-invocation: true
argument-hint: "[title]"
---

## Open a GitHub Issue

Create a new issue for a bug, defect, or improvement found during QA review or development.

### Steps

1. **Gather context** from the calling agent or conversation:
   - What was found (bug, missing feature, quality issue)
   - Where it was found (file paths, test output, PR number)
   - Severity: `critical`, `major`, `minor`
   - Related spec traces (FR, DD, NFR, EC IDs) if applicable

2. **Create labels** (if they don't exist):
   - Severity: `severity:critical`, `severity:major`, `severity:minor`
   - Source: `found-in:qa`, `found-in:review`, `found-in:testing`
   - Type: `bug`, `enhancement`, `test-gap`

3. **Create the issue** using `gh issue create`:

   ```bash
   gh issue create \
     --title "$ARGUMENTS" \
     --label "bug,severity:<level>,found-in:<source>" \
     --body "$(cat <<'EOF'
   ## Description
   <What is wrong or missing>

   ## Found During
   <QA review / PR review / testing> of <task/PR reference>

   ## Steps to Reproduce
   <How to trigger the issue, or which test demonstrates it>

   ## Expected Behavior
   <What should happen according to specs>

   ## Actual Behavior
   <What happens instead>

   ## Spec References
   <Traced requirement/design/edge case IDs, if applicable>

   ## Suggested Fix
   <Optional: guidance on how to address it>
   EOF
   )"
   ```

4. **Link to related PR or task** if applicable:
   - `gh issue comment <number> --body "Related to #<PR-or-issue>"`

5. **Report** the created issue number and URL.
