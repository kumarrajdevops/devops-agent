"""
devops-agent (Phase 2)
Read-only CI/CD observer for GitHub Actions that posts a sticky PR comment.

Trust constraints:
- No credential storage (uses GITHUB_TOKEN only)
- No mutations except PR comment
- No external network calls besides GitHub API
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_optional_config_yaml(repo_root: Path) -> Optional[Dict[str, Any]]:
    """
    Minimal YAML reader for Phase 2 schema only.
    Supported keys:
      version: 1
      github_actions:
        pr_comment:
          enabled: true|false
          mode: sticky
          post_on: failure|always

    Notes:
    - This intentionally does NOT implement full YAML.
    - Scalars only, nested maps only.
    """
    config_path = repo_root / ".devops-agent.yml"
    if not config_path.exists():
        return None

    raw = config_path.read_text(encoding="utf-8")
    lines = []
    for line in raw.splitlines():
        line = line.replace("\t", "  ")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(line)

    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]

    for line in lines:
        indent = len(re.match(r"^ *", line).group(0))  # type: ignore[union-attr]
        trimmed = line.strip()
        m = re.match(r"^([A-Za-z0-9_]+):(?:\s+(.*))?$", trimmed)
        if not m:
            continue

        key = m.group(1)
        value = m.group(2)

        while len(stack) > 1 and indent <= stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]

        if value is None:
            cur[key] = {}
            stack.append((indent, cur[key]))
            continue

        v = value.strip()
        if v == "true":
            cur[key] = True
        elif v == "false":
            cur[key] = False
        elif re.match(r"^\d+$", v):
            cur[key] = int(v)
        else:
            cur[key] = v

    return root


def _get_config(repo_root: Path) -> Dict[str, Any]:
    defaults: Dict[str, Any] = {
        "version": 1,
        "github_actions": {
            "pr_comment": {
                "enabled": True,
                "mode": "sticky",
                "post_on": "failure",  # failure|always
            }
        },
    }

    cfg = _read_optional_config_yaml(repo_root)
    if not cfg:
        return defaults

    out = json.loads(json.dumps(defaults))
    if isinstance(cfg.get("version"), int):
        out["version"] = cfg["version"]

    gha = cfg.get("github_actions") or {}
    if isinstance(gha, dict):
        pc = gha.get("pr_comment") or {}
        if isinstance(pc, dict):
            if isinstance(pc.get("enabled"), bool):
                out["github_actions"]["pr_comment"]["enabled"] = pc["enabled"]
            if isinstance(pc.get("mode"), str):
                out["github_actions"]["pr_comment"]["mode"] = pc["mode"]
            if isinstance(pc.get("post_on"), str):
                out["github_actions"]["pr_comment"]["post_on"] = pc["post_on"]

    return out


def _classify_failure(step_name: str = "", job_name: str = "") -> Tuple[str, str]:
    hay = f"{job_name}\n{step_name}".lower()
    if any(x in hay for x in ["lint", "eslint", "flake8", "ruff", "format"]):
        return ("lint", "Run the linter locally and fix the first reported violation.")
    if any(x in hay for x in ["test", "pytest", "jest", "go test", "unittest"]):
        return ("tests", "Re-run the failing test locally; check recent changes and any snapshots/fixtures.")
    if any(x in hay for x in ["build", "compile", "tsc", "make"]):
        return ("build", "Check the first compilation error; verify toolchain versions and missing dependencies.")
    if any(x in hay for x in ["install", "dependency", "npm ci", "pip install"]):
        return ("dependencies", "Check dependency resolution/network errors; verify lockfiles and registry access.")
    if any(x in hay for x in ["deploy", "terraform", "helm", "k8s", "kubernetes", "docker"]):
        return ("infra", "Check infrastructure config and credentials; verify deploy target.")
    if any(x in hay for x in ["timeout", "cancelled", "cancelled_by_user"]):
        return ("timeout", "Increase job/step timeout or retry; check for flaky steps.")
    return ("unknown", "Open the failed job logs and start from the first error line.")


def _build_comment(run: Dict[str, Any], jobs: List[Dict[str, Any]], findings: List[Dict[str, Any]]) -> str:
    marker = "<!-- devops-agent:sticky -->"
    run_url = run.get("html_url") or ""
    workflow_name = run.get("name") or run.get("workflow_name") or "workflow"
    status = run.get("status") or "unknown"
    # GitHub often returns conclusion=null while the run is still in progress.
    conclusion = run.get("conclusion")

    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
    cancelled_jobs = [j for j in jobs if j.get("conclusion") == "cancelled"]

    lines: List[str] = []
    lines.append(marker)
    lines.append("## devops-agent — CI observation (read-only)")
    lines.append("")
    lines.append(f"- **Workflow**: {workflow_name}")
    if run_url:
        lines.append(f"- **Run**: {run_url}")
    lines.append(f"- **Status**: `{status}`")
    if conclusion:
        lines.append(f"- **Conclusion**: `{conclusion}`")
    elif status in ("queued", "in_progress"):
        lines.append("- **Conclusion**: `pending`")
    elif status == "completed":
        lines.append("- **Conclusion**: `—`")
    lines.append("")

    if not failed_jobs and not cancelled_jobs:
        lines.append("✅ No failed or cancelled jobs detected for this run.")
        return "\n".join(lines)

    if failed_jobs:
        lines.append("### Failures")
        for f in findings:
            jname = f.get("jobName") or ""
            jurl = f.get("jobUrl")
            step = f.get("stepName")
            cat = f.get("category")
            nxt = f.get("next")
            lines.append("")
            if jurl:
                lines.append(f"**[{jname}]({jurl})**")
            else:
                lines.append(f"**{jname}**")
            if step:
                lines.append(f"- Failed step: {step}")
            if cat:
                lines.append(f"- Category: `{cat}`")
            if nxt:
                lines.append(f"- Next: {nxt}")
        lines.append("")

    if cancelled_jobs:
        lines.append("### Cancelled")
        for j in cancelled_jobs:
            name = j.get("name", "")
            url = j.get("html_url")
            if url:
                lines.append(f"- [{name}]({url})")
            else:
                lines.append(f"- {name}")
        lines.append("")

    lines.append("_This agent is read-only: it does not deploy, restart, scale, or store credentials._")
    return "\n".join(lines)


@dataclass
class GitHubClient:
    token: str

    def request(self, method: str, url_path: str, body: Optional[Dict[str, Any]] = None) -> Any:
        data = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "devops-agent",
        }
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(
            url=f"https://api.github.com{url_path}",
            data=data,
            method=method,
            headers=headers,
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                pass
            raise RuntimeError(f"{method} {url_path} failed: {e.code} {e.reason}\n{err_body}") from e


def main() -> int:
    repo_root = Path(os.environ.get("GITHUB_WORKSPACE", os.getcwd()))
    config = _get_config(repo_root)

    if not config["github_actions"]["pr_comment"]["enabled"]:
        print("PR comment disabled by config.")
        return 0

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("Missing GITHUB_EVENT_PATH")
    event = _read_json(event_path)

    pr = event.get("pull_request") or {}
    pr_number = pr.get("number")
    if not pr_number:
        print("No pull_request found in event payload; skipping.")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN")
    gh = GitHubClient(token=token)

    repo_full = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" not in repo_full:
        raise RuntimeError("Missing GITHUB_REPOSITORY")
    owner, repo = repo_full.split("/", 1)

    run_id = os.environ.get("GITHUB_RUN_ID")
    if not run_id:
        raise RuntimeError("Missing GITHUB_RUN_ID")

    run = gh.request("GET", f"/repos/{owner}/{repo}/actions/runs/{run_id}")
    jobs: List[Dict[str, Any]] = []
    page = 1
    while True:
        jobs_resp = gh.request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs?per_page=100&page={page}",
        )
        page_jobs = jobs_resp.get("jobs", []) if isinstance(jobs_resp, dict) else []
        jobs.extend(page_jobs)
        if len(page_jobs) < 100:
            break
        page += 1

    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
    findings: List[Dict[str, Any]] = []
    for j in failed_jobs:
        steps = j.get("steps") or []
        failed_step = next((s for s in steps if s.get("conclusion") == "failure"), None)
        category, nxt = _classify_failure(
            step_name=(failed_step.get("name") if failed_step else "") or "",
            job_name=j.get("name", "") or "",
        )
        findings.append(
            {
                "jobName": j.get("name", "") or "",
                "jobUrl": j.get("html_url"),
                "stepName": (failed_step.get("name") if failed_step else None),
                "category": category,
                "next": nxt,
            }
        )

    post_on = config["github_actions"]["pr_comment"]["post_on"]
    should_post = post_on == "always" or (
        post_on == "failure" and (bool(failed_jobs) or run.get("conclusion") == "failure")
    )
    if not should_post:
        print("Configured to post on failure only, and no failures detected; skipping.")
        return 0

    body = _build_comment(run=run, jobs=jobs, findings=findings)

    marker = "<!-- devops-agent:sticky -->"
    comments = gh.request("GET", f"/repos/{owner}/{repo}/issues/{pr_number}/comments?per_page=100")
    existing = None
    if isinstance(comments, list):
        for c in comments:
            if isinstance(c, dict) and isinstance(c.get("body"), str) and marker in c["body"]:
                existing = c
                break

    if existing and existing.get("id"):
        gh.request("PATCH", f"/repos/{owner}/{repo}/issues/comments/{existing['id']}", {"body": body})
        print(f"Updated sticky PR comment: {existing['id']}")
    else:
        gh.request("POST", f"/repos/{owner}/{repo}/issues/{pr_number}/comments", {"body": body})
        print("Created sticky PR comment.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)

