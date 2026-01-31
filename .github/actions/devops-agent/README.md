# devops-agent

Read-only CI observer — summarizes workflow failures and posts a sticky PR comment.

## Usage

Add this job to your workflow (runs after your main jobs):

```yaml
  devops-agent:
    name: devops-agent (PR comment)
    runs-on: ubuntu-latest
    needs: [your-main-job]  # or your job list
    if: ${{ github.event_name == 'pull_request' && always() }}
    permissions:
      contents: read
      actions: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: kumarrajdevops/devops-agent@v0.1.0
```

## Permissions required

- `contents: read` — read repo (config)
- `actions: read` — read workflow run and jobs
- `pull-requests: write` — post/update PR comment

## What it does NOT do

- No deploys, restarts, scaling, or mutations
- No credential storage
- No auto-fix

## Optional config

Add `.devops-agent.yml` at repo root to override defaults:

```yaml
github_actions:
  pr_comment:
    enabled: true
    post_on: failure   # failure | always
```
