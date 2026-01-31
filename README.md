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
      - uses: kumarrajdevops/devops-agent@v0.1.0
```

[Full usage and config →](.github/actions/devops-agent/README.md)

## Example output

When CI fails, the agent posts a comment like:

```markdown
## devops-agent — CI observation (read-only)

- **Workflow**: CI
- **Run**: [link]
- **Status**: `completed`
- **Conclusion**: `failure`

### Failures

**[smoke](job-link)**
- Failed step: Run tests
- Category: `tests`
- Next: Re-run the failing test locally; check recent changes and any snapshots/fixtures.

_This agent is read-only: it does not deploy, restart, scale, or store credentials._
```

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

Pre-alpha. GitHub Actions only. Docker and Kubernetes out of scope.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
