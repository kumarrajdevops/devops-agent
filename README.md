# devops-agent

## What problem does this solve?
DevOps teams don’t have a single, explainable view of CI/CD health. Failures are scattered across logs and runs, and the signal-to-noise ratio is poor.

This project starts by making CI/CD failures easier to understand and act on (by humans), without introducing risk.

## What this agent does
- Observes CI/CD runs (starting with GitHub Actions).
- Summarizes failures into clear, opinionated explanations.
- Detects repeat patterns across runs (e.g., flaky tests, dependency failures).
- Produces human-readable output via CLI and GitHub-native artifacts (issues/PR comments later).

## What this agent does NOT do
- No deploys.
- No restarts.
- No scaling.
- No mutations in Docker / Kubernetes / cloud resources.
- No “auto-fix”.
- No credentials stored by the agent.

## How it works (high level)
- Collect read-only CI/CD run metadata and logs from supported providers.
- See [docs/how-it-works.md](docs/how-it-works.md) for details; [docs/architecture.md](docs/architecture.md) for extension points.
- Normalize events into a common observation model.
- Generate summaries that explain what failed and likely why.
- Output summaries in a simple CLI-first format.

## Current status
🚧 Status: Pre-Alpha (observation only)

Scope gate: **CI/CD observation only**. Docker and Kubernetes are explicitly out of scope for now.

## Roadmap (very short)
- Phase 1: Establish open-source foundation (docs, contribution hygiene, skeleton).
- Phase 2: Define CI/CD observation model and initial GitHub Actions observer.
- Phase 3A: Hardening and signal quality (failure categorization, PR comment UX, safety rails).
- Phase 3C: Architecture and contributor readiness (docs, extension points, issue templates).

## Contributing
See `CONTRIBUTING.md`.
