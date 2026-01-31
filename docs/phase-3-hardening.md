# Phase 3: Hardening & Signal Quality

## Scope (locked)
- **No new CI systems** (GitHub Actions only)
- **No AI**
- **No dashboards**

Goal: make the agent useful, not just working.

## Deliverables

### 1. Status vs conclusion
- Show run **status** (`queued` | `in_progress` | `completed`) and **conclusion** (`success` | `failure` | `cancelled` | `pending`).
- Never display `conclusion: unknown`; use `pending` when the run is still in progress.

### 2. Failure categorization (explainable heuristics)
Categories and example keywords:

| Category      | Keywords / patterns                    | Next-step hint |
|---------------|----------------------------------------|----------------|
| `lint`        | lint, eslint, flake8, ruff, format     | Run linter locally; fix first violation. |
| `tests`       | test, pytest, jest, go test, unittest  | Re-run failing test locally; check snapshots. |
| `build`       | build, compile, tsc, make              | Check first compilation error; verify toolchain. |
| `dependencies`| install, dependency, npm ci, pip       | Check lockfiles and registry access. |
| `infra`       | deploy, terraform, helm, k8s, docker   | Check infrastructure/credentials. |
| `timeout`     | timeout, cancelled, cancelled_by_user  | Increase timeout or retry. |
| `unknown`     | (fallback)                             | Open failed job logs; start from first error. |

### 3. Multiple failures (one section per job)
- Each failed job gets its own clear block.
- Include: job name (link), first failed step, category, next step.
- Avoid nested bullets that are hard to scan.

### 4. PR comment UX
- Clear headers (e.g., `## devops-agent — CI observation (read-only)`).
- Compact run summary (workflow, run link, status, conclusion).
- One block per failed job; cancelled jobs in a separate short section.
- Footer: read-only reminder.
- No redundant or noisy text.

### 5. Safety rails
- **API pagination**: use `per_page`; handle paginated jobs if run has >100 jobs (fetch next page).
- **Defensive defaults**: handle missing `steps`, `conclusion`, `html_url` without crashing.
- **Request timeout**: set a reasonable timeout on GitHub API calls (e.g., 30s).
- **Rate-limit**: avoid hammering the API; one run + jobs + comments flow per invocation.

## Non-goals
- Log parsing
- AI/LLM-based analysis
- New CI integrations (Jenkins, GitLab)
- Dashboards or external UIs
