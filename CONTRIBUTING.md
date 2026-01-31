# Contributing

## Principles (non-negotiable)
- **Read-only first**: observation, analysis, explanation.
- **No actions**: no changes to infrastructure, CI systems, or runtime environments.
- **Explainable output**: summaries must prioritize clarity over volume.
- **No credential storage**: do not add mechanisms that store secrets/credentials.

## Running tests
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Contribution workflow
- Fork the repo and create a feature branch.
- Open a PR against `main`.
- Keep PRs small and focused.

## Commit message format
Use short, descriptive, imperative commits. Examples:
- `docs: clarify scope and non-goals`
- `chore: add contribution templates`

## PRs that will be rejected
- Adds “auto-fix”, remediation, or any mutation behavior.
- Introduces secret storage or collection of private data without explicit design review.
- Adds dashboards before CLI/GitHub-native outputs.
- Adds broad architecture rewrites without an issue and proposal.

## Code of Conduct
By participating, you agree to abide by `CODE_OF_CONDUCT.md`.

