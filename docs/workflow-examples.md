# Workflow examples

Complete workflow examples for devops-agent. Copy and adapt for your repo.

## Option 1 — Packaged action (recommended)

Minimal setup. Use the published action:

```yaml
name: CI

on:
  pull_request:

permissions:
  contents: read
  actions: read
  pull-requests: write

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Lint check
        run: echo "lint" && exit 1

  tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: echo "test failure" && exit 1

  build:
    runs-on: ubuntu-latest
    steps:
      - name: Build
        run: echo "build error" && exit 1

  devops-agent:
    name: devops-agent (summary)
    runs-on: ubuntu-latest
    needs: [lint, tests, build]
    if: ${{ github.event_name == 'pull_request' && always() }}
    steps:
      - uses: kumarrajdevops/devops-agent@v0.2.5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

No checkout required. The agent runs from the action’s code.

---

## Option 2 — From source

Use when debugging, extending, or contributing. Runs devops-agent from the repo:

```yaml
name: CI

on:
  pull_request:

permissions:
  contents: read
  actions: read
  pull-requests: write

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Lint check
        run: echo "lint" && exit 1

  tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: echo "test failure" && exit 1

  devops-agent:
    runs-on: ubuntu-latest
    needs: [lint, tests]
    if: ${{ github.event_name == 'pull_request' && always() }}
    steps:
      - name: Checkout devops-agent
        uses: actions/checkout@v4
        with:
          repository: kumarrajdevops/devops-agent
          ref: main
          path: devops-agent
          fetch-depth: 1

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Run devops-agent from source
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd devops-agent
          python agent/gha_pr_comment.py
```

Source usage follows `main` and may change. For production, prefer the packaged action (Option 1).

---

## Failure-lab (full demo)

Full workflow that exercises all failure categories: lint, tests, build, deps, infra, timeout.

<details>
<summary>Expand full failure-lab workflow</summary>

```yaml
name: devops-agent failure lab

on:
  pull_request:

permissions:
  contents: read
  actions: read
  pull-requests: write

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Lint check
        run: |
          echo "lint error: formatting issue"
          exit 1

  tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: |
          echo "test failure: assertion failed"
          exit 1

  build:
    runs-on: ubuntu-latest
    steps:
      - name: Build
        run: |
          echo "build error: compilation failed"
          exit 1

  deps:
    runs-on: ubuntu-latest
    steps:
      - name: Install dependencies
        run: |
          echo "dependency error: pip install failed"
          exit 1

  infra:
    runs-on: ubuntu-latest
    steps:
      - name: Infra step
        run: |
          echo "permission denied while accessing docker socket"
          exit 1

  timeout:
    runs-on: ubuntu-latest
    timeout-minutes: 1
    steps:
      - name: Timeout step
        run: |
          echo "sleeping to trigger timeout"
          sleep 120

  devops-agent:
    name: devops-agent (summary)
    runs-on: ubuntu-latest
    needs: [lint, tests, build, deps, infra, timeout]
    if: ${{ github.event_name == 'pull_request' && always() }}
    steps:
      - uses: kumarrajdevops/devops-agent@v0.2.5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
```

</details>
