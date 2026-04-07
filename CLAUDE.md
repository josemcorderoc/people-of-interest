# People of Interest

## Workflow

This project follows **Spec Driven Development (SDD)**. See agents in `.claude/agents/` for phase-specific instructions.

### Phases

1. **Requirements** — `requirements-agent` → **critique-agent** loop → user approves
2. **Design** — `design-agent` → **critique-agent** loop → user approves
3. **Tasks** — `task-creator-agent` → **critique-agent** loop → user approves
4. **Implementation** — `implementation-agent` → delivers PRs → human reviews
5. **QA** — `qa-agent` → validates against specs
6. **Bug Fix** — `bug-fix-agent` → when issues are found

### Rules

- **Never skip phases.** Each phase produces a spec that the next phase consumes.
- **Review at phase gates.** Present output to the human for approval before moving on.
- **Keep specs anchored.** When implementation reveals spec gaps, update the spec first.
- **Specs live in `.specs/`** organized by feature.
- **Traceability.** Each task lists traced IDs (FR, DD, NFR, EC) in its Traces field.

## Conventions

- **Clean Architecture** — Separate entities, use cases, interfaces, infrastructure.
- **Test Driven Development** — Tests first. Red → Green → Refactor.
- **Conventional Commits** — `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:`
- **Feature branches + PRs** — No direct commits to `main`. All work via PRs with human review.
- **Latest versions** — Use the latest stable version of all dependencies.
- **Shared S3 Data** — Pageview dumps read from `s3://poi-pageview-dumps/pageviews/`. Never download from Wikimedia directly.
- **Wikimedia compliance** — Polite `User-Agent` headers for any Wikimedia API calls. Image URLs via `Special:FilePath`.
