# Changelog

## [0.2.2] — 2025-01-31

### Fixed

- **Action path** — Run script from action repo using `github.action_path`; fixes "can't open file" when action runs in a different repo.

## [0.2.1] — 2025-01-31

### Fixed

- **Action packaging** — Add `action.yml` at repo root so `uses: kumarrajdevops/devops-agent@v0.2.1` works. Required for packaged action mode.

## [0.2.0] — 2025-01-31

### Added

- **Hybrid recovery model** — When a run succeeds after failures, the sticky comment is updated once to show recovery (`✅ devops-agent — All checks passed (Run #N)`). The comment is never deleted. Preserves auditability.
- **Run number in headers** — Headers include run number (e.g. `Run #25`) for traceability.
- **Timeout classification** — Cancelled jobs that ran near their timeout are classified as `timeout` with actionable next steps.
- **Infra categorization** — Broader keyword matching for infra failures (infra, permission, socket, network).
- **Single sticky comment** — Comment lookup uses a permanent marker; one comment per PR, updated in place. Pagination for PRs with many comments.
- **Human-friendly run state** — Replaces raw status/conclusion with clear wording (e.g. `In progress (final result pending)`, `Completed — Failed`).

### Changed

- Header wording: `devops-agent — Failures detected` and `devops-agent — All checks passed` (CI-agnostic, future-proof).
- Failure comment format: one block per failed job for better scanability.

### Fixed

- Sticky comment reuse — Agent now correctly finds and updates the same comment instead of creating duplicates.
