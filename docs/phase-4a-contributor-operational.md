# Phase 4A: Contributor Readiness (Operational)

## Scope (tight)
- Minimal unit tests
- CI enforcement (tests must pass)
- Issue templates (already present from Phase 3C)

## Test targets (what, not how)

### 1. Failure categorization (`_classify_failure`)
| Input (job_name, step_name) | Expected category |
|-----------------------------|-------------------|
| ("smoke", "Run eslint") | lint |
| ("test", "pytest") | tests |
| ("build", "Compile") | build |
| ("ci", "npm ci") | dependencies |
| ("deploy", "helm upgrade") | infra |
| ("job", "step timeout") | timeout |
| ("other", "random") | unknown |

### 2. Config parsing
- No config file → defaults returned
- Config with `enabled: false` → overrides default
- Config with `post_on: always` → overrides default

### 3. PR comment rendering (`_build_comment`)
- No failures → success message, no Failures section
- One failed job → Failures section with job link, step, category, next
- Contains sticky marker
- Contains read-only disclaimer

## File structure
```
tests/
  test_gha_pr_comment.py   # all unit tests
```

## Acceptance criteria
- All tests pass locally
- CI runs tests on every PR and push
- CI fails if any test fails
- No API mocking (pure functions only)

## Non-goals
- Integration tests
- E2E tests
- High coverage targets
- Testing GitHubClient (network)
