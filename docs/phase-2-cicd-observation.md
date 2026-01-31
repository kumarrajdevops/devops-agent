# Phase 2: CI/CD Observation (GitHub Actions)

## Scope (locked)
- **CI provider**: GitHub Actions only
- **Output surface**: PR comment (sticky / updated in-place)
- **Config format**: YAML

Out of scope for Phase 2:
- Jenkins, GitLab CI
- Docker / Kubernetes observation
- Any “auto-fix” or mutation behavior
- Any credential storage

## Goal
Produce an explainable, low-noise PR comment that summarizes the current GitHub Actions run for a pull request, with a bias toward:
- **What failed**
- **Where it failed** (job + step)
- **Why it likely failed** (lightweight heuristics, not “AI”)
- **What a human should try next**

## Non-goals
- Perfect root cause analysis
- Parsing every log line
- A dashboard

## Observation model (minimal)

### Entities
- **Run**: a single GitHub Actions workflow run for a PR.
- **Job**: a job within the run.
- **Step**: a step within a job.
- **Finding**: a normalized “thing worth saying” (failure, cancel, flaky suspicion, etc.).
- **Summary**: rendered markdown posted to the PR.

### Data sources (GitHub API)
- List jobs for a workflow run:
  - `actions.listJobsForWorkflowRun`
  - Provides job conclusions and step conclusions.

## PR comment behavior (sticky)

### Requirements
- The agent posts **one** PR comment and **updates** it on subsequent runs.
- The comment is identifiable by a hidden marker:
  - `<!-- devops-agent:sticky -->`
- Default behavior is low-noise:
  - Post/update on failures
  - Optionally post on success via config

### Comment format (markdown)
- Header includes:
  - Project name and “read-only” reminder
  - Workflow + run link
  - Overall conclusion
- Body includes:
  - Failed jobs (links)
  - For each failed job: first failed step (if available)
  - “Next steps” suggestions based on simple rules (e.g., tests, lint, dependencies)

## Configuration (YAML)

### File location
Repo root: `.devops-agent.yml`

### Minimal schema (Phase 2)
```yaml
version: 1

github_actions:
  pr_comment:
    enabled: true
    mode: sticky          # sticky = update in place
    post_on: failure      # failure|always
```

Notes:
- Config is optional; defaults are safe.
- No secrets in this file.

## Safety + trust constraints
- Use GitHub-provided token for API access and commenting.
- Store nothing; emit no credentials.
- Do not modify workflow outcomes; only observe and comment.

## Reference implementation (Phase 2)
- Python entrypoint: `agent/gha_pr_comment.py`

