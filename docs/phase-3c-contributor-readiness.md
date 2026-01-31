# Phase 3C: Architecture & Contributor Readiness

## Scope (locked)
- No new features
- No new CI integrations
- Documentation and contributor tooling only

## Deliverables

### 1. Architecture diagram (textual)
- High-level flow: trigger → config → API → render → comment
- Data flow between components
- No fancy diagrams; ASCII/text only

### 2. "How it works" deep doc
- End-to-end flow for a PR-triggered run
- Environment variables and their roles
- Config resolution and defaults
- GitHub API calls and pagination
- Sticky comment lifecycle (create vs update)

### 3. Clear extension points
- Where to add a new failure category
- Where to add a new CI provider (future)
- Where to add a new output surface (future)
- Config schema extension pattern

### 4. Contributor labels
- `bug`, `enhancement`, `documentation`, `good first issue`, `help wanted`

### 5. Issue templates
- Bug report
- Feature request
