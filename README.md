# devops-agent

Read-only CI observer for GitHub Actions. Summarizes workflow failures and posts a sticky PR comment — no deploys, no restarts, no credential storage.

## Why this exists

CI failure logs are noisy and fragmented. Teams waste time hunting through job outputs to find what failed and why. devops-agent observes your runs, classifies failures (lint, tests, build, deps, infra, timeout), and posts a single explainable summary to the PR. It never changes anything; it only observes and explains.

## What it does

- Observes GitHub Actions runs on pull requests
- Summarizes failures with job links, failed step, and category
- Suggests next steps based on failure type
- Updates one sticky comment per PR (no spam)

## What it does NOT do

- No deploys, restarts, scaling, or infrastructure changes
- No auto-fix or remediation
- No credential storage

## Quick start

Add this job to your workflow (after your main jobs):

```yaml
  devops-agent:
    runs-on: ubuntu-latest
    needs: [your-job]
    if: ${{ github.event_name == 'pull_request' && always() }}
    permissions:
      contents: read
      actions: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: kumarrajdevops/devops-agent@v0.2.2
```

## Example output

When CI fails, the agent posts a comment like:

```markdown
## ❌ devops-agent — Failures detected (Run #123)

- **Workflow**: CI
- **Run**: [link]

### Failures

**[smoke](job-link)**
- Failed step: Run tests
- Category: `tests`
- Next: Re-run the failing test locally; check recent changes and any snapshots/fixtures.

_This agent is read-only: it does not deploy, restart, scale, or store credentials._
```

When a later run succeeds, the same comment is updated to:

```markdown
## ✅ devops-agent — All checks passed (Run #124)

- **Workflow**: CI
- **Recovery run**: [link]

Previous CI failures have been resolved.

_This agent is read-only: it does not deploy, restart, scale, or store credentials._
```

## Comment behavior (auditable, single sticky)

devops-agent maintains **one sticky comment per PR**. The comment is never deleted.

| State | Header | When |
|-------|--------|------|
| Failure | `❌ devops-agent — Failures detected (Run #N)` | Run has failed jobs |
| Recovery | `✅ devops-agent — All checks passed (Run #N)` | Run succeeds after a previous failure |
| Stable | (no update) | Run succeeds and comment already shows recovery |

- **Single comment** — The agent finds its comment by marker and updates it in place. No duplicate comments.
- **Recovery transition** — When CI goes from failed to passing, the comment is updated once to show recovery. Subsequent successful runs do not trigger further updates.
- **Audit trail** — Run numbers in headers let auditors trace failure and recovery. History is preserved.

## Config (optional)

Add `.devops-agent.yml` at repo root:

```yaml
github_actions:
  pr_comment:
    enabled: true
    post_on: failure   # failure | always
```

## Docs

- [How it works](docs/how-it-works.md)
- [Architecture & extension points](docs/architecture.md)
- [Vision & principles](docs/vision.md)

## Status

Pre-1.0. GitHub Actions only. Docker and Kubernetes out of scope.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
