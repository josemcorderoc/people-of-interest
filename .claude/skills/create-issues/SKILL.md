---
name: create-issues
description: Create GitHub issues from the task breakdown with traceability labels
disable-model-invocation: true
argument-hint: "[feature-name]"
---

## Create GitHub Issues from Tasks

Read the task breakdown and specs to create GitHub issues with traceability labels.

### Steps

1. **Read the specs:**
   - `.specs/$ARGUMENTS/tasks.md` — tasks with Traces field
   - `.specs/$ARGUMENTS/requirements.md` — FR/NFR/EC IDs
   - `.specs/$ARGUMENTS/design.md` — DD IDs

2. **Create labels** (if they don't exist):
   - Phase: `phase:1-bootstrap`, `phase:2-domain`, etc.
   - Requirements: `req:FR-001`, etc.
   - Design decisions: `dd:DD-001`, etc.
   - NFRs: `nfr:NFR-001`, etc.
   - Edge cases: `ec:EC-1`, etc.

3. **For each task**, create a GitHub issue:
   - Title: `T-XX: <title>`
   - Labels: phase + all `req:`, `dd:`, `nfr:`, `ec:` from the task's Traces field
   - Body: dependencies + description + acceptance criteria as checkboxes

4. **Add to project** if one exists

5. **Report** created issues
