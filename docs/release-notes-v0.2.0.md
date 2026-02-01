# Release notes — v0.2.0

## Add hybrid recovery model for auditable CI status transitions

v0.2.0 adds an auditable, single-sticky-comment workflow that resolves confusion when CI recovers after failures.

### Highlights

**Hybrid recovery model**
- When a run succeeds after failures, the sticky comment is updated once to show recovery
- Comment is never deleted — full audit trail preserved
- No repeated updates on every successful run (low noise)

**Run-numbered headers**
- `❌ devops-agent — Failures detected (Run #25)`
- `✅ devops-agent — All checks passed (Run #26)`
- Auditors can trace failure and recovery to specific runs

**Single sticky comment**
- Agent finds its comment by permanent marker and updates in place
- Pagination for PRs with many comments
- Fixes duplicate-comment bug from v0.1.x

**Signal quality**
- Timeout classification for cancelled jobs that ran near their limit
- Broader infra categorization (infra, permission, socket, network)
- Human-friendly run state wording (no raw `pending` or `unknown`)

### Upgrade

Update your workflow:

```yaml
- uses: kumarrajdevops/devops-agent@v0.2.0
```

No config changes required. Existing `.devops-agent.yml` works as-is.
