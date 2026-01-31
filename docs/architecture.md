# Architecture

## High-level flow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  GitHub Actions │     │  devops-agent    │     │  GitHub API     │
│  (CI workflow)  │     │  (agent/)        │     │                 │
└────────┬────────┘     └────────┬─────────┘     └────────┬────────┘
         │                       │                        │
         │  PR event             │                        │
         │  GITHUB_* env vars    │                        │
         ├──────────────────────►│                        │
         │                       │  GET /actions/runs     │
         │                       │  GET /actions/runs/…/jobs
         │                       ├───────────────────────►│
         │                       │◄───────────────────────┤
         │                       │  GET /issues/…/comments
         │                       ├───────────────────────►│
         │                       │◄───────────────────────┤
         │                       │  POST or PATCH comment │
         │                       ├───────────────────────►│
         │                       │                        │
         │  sticky PR comment    │                        │
         │◄──────────────────────┤                        │
         │                       │                        │
```

## Data flow

1. **Trigger**: PR opened/synchronized/reopened → CI workflow runs
2. **Config**: `.devops-agent.yml` read from repo root (optional; defaults apply)
3. **Observation**: GitHub API fetches run + jobs (paginated)
4. **Analysis**: Failed jobs → first failed step → category + next-step hint
5. **Render**: Markdown comment built from findings
6. **Publish**: Find existing sticky comment by marker; update or create

## Components

| Component | Location | Responsibility |
|-----------|----------|----------------|
| Config loader | `_read_optional_config_yaml`, `_get_config` | Parse `.devops-agent.yml`; merge with defaults |
| Event reader | `_read_json` (GITHUB_EVENT_PATH) | Extract PR number from event |
| Classifier | `_classify_failure` | Map job/step names → category + next-step |
| Comment builder | `_build_comment` | Render markdown from run, jobs, findings |
| API client | `GitHubClient` | HTTP calls to api.github.com with token |
| Main flow | `main()` | Orchestrate config → fetch → analyze → publish |

## Extension points

### Add a new failure category
**Where**: `_classify_failure()` in `agent/gha_pr_comment.py`

Add a condition before the `unknown` fallback:

```python
if any(x in hay for x in ["your", "keywords"]):
    return ("your_category", "Your next-step hint.")
```

### Add a new CI provider (future)
**Where**: New module under `agent/` (e.g. `agent/jenkins_pr_comment.py`)

- Implement the same contract: read config, fetch run/jobs, build findings, publish
- Entrypoint called from a provider-specific workflow or CLI
- Share: config schema, comment format, marker

### Add a new output surface (future)
**Where**: New function alongside `_build_comment`, new publish path in `main()`

- CLI: print markdown to stdout instead of POST
- Issue comment: same body, different API endpoint (`POST /repos/.../issues/{issue_number}/comments`)

### Extend config schema
**Where**: `_get_config()`, `_read_optional_config_yaml()`

- Add keys to the minimal YAML parser
- Add defaults in `_get_config`
- Merge user overrides shallowly
