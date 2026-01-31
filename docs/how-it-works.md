# How It Works

## End-to-end flow (PR-triggered run)

1. A pull request is opened, updated, or reopened.
2. The CI workflow runs (see `.github/workflows/ci.yml`).
3. The `devops-agent` job runs after `smoke` (and runs even if smoke fails, due to `if: always()`).
4. The agent script (`agent/gha_pr_comment.py`) executes with GitHub Actions environment variables.

### Step-by-step

| Step | Action |
|------|--------|
| 1 | Read `GITHUB_WORKSPACE` for repo root |
| 2 | Load `.devops-agent.yml` (optional); apply defaults |
| 3 | If `pr_comment.enabled` is false → exit 0 |
| 4 | Read `GITHUB_EVENT_PATH` (JSON); extract `pull_request.number` |
| 5 | If no PR in event (e.g. push to main) → exit 0 |
| 6 | Read `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, `GITHUB_RUN_ID` |
| 7 | GET run details: `/repos/{owner}/{repo}/actions/runs/{run_id}` |
| 8 | GET jobs (paginated): `/repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100&page=N` |
| 9 | For each job with `conclusion == "failure"`, find first failed step; classify; build finding |
| 10 | If `post_on == "failure"` and no failures → exit 0 |
| 11 | Build markdown comment |
| 12 | GET `/repos/{owner}/{repo}/issues/{pr_number}/comments` |
| 13 | Search for comment containing `<!-- devops-agent:sticky -->` |
| 14 | If found → PATCH that comment; else → POST new comment |
| 15 | Exit 0 |

## Environment variables

| Variable | Set by | Purpose |
|----------|--------|---------|
| `GITHUB_WORKSPACE` | Actions | Repo checkout path (config file location) |
| `GITHUB_EVENT_PATH` | Actions | Path to event JSON (e.g. pull_request payload) |
| `GITHUB_TOKEN` | Actions | Token for API auth (inherited from workflow) |
| `GITHUB_REPOSITORY` | Actions | `owner/repo` |
| `GITHUB_RUN_ID` | Actions | Current workflow run ID |

## Config resolution

1. Look for `.devops-agent.yml` in repo root.
2. If missing → use built-in defaults.
3. If present → parse minimal YAML (scalars + nested maps only).
4. Override only known keys: `version`, `github_actions.pr_comment.enabled`, `mode`, `post_on`.
5. Unknown keys are ignored.

## GitHub API calls

| Call | When | Pagination |
|------|------|------------|
| GET run | Once per invocation | No |
| GET jobs | Once per invocation | Yes, `per_page=100`, loop until `len(page) < 100` |
| GET comments | Once per invocation | `per_page=100` (PRs rarely have >100 comments) |
| POST comment | When no sticky comment exists | No |
| PATCH comment | When sticky comment exists | No |

## Sticky comment lifecycle

1. **First run**: No comment with marker → POST new comment.
2. **Subsequent runs**: Marker found → PATCH existing comment with new body.
3. **Marker**: `<!-- devops-agent:sticky -->` (hidden in rendered markdown).

The marker ensures exactly one agent comment per PR; updates replace the previous summary.
