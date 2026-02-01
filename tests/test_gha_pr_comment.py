"""Phase 4A: Minimal unit tests for devops-agent pure functions."""

import tempfile
from pathlib import Path

import pytest

# Import internal functions for testing (pure, no side effects)
from agent.gha_pr_comment import (
    _build_failure_comment,
    _build_recovery_comment,
    _classify_failure,
    _format_run_state,
    _get_config,
    _read_optional_config_yaml,
)


class TestClassifyFailure:
    """Failure categorization is explainable and deterministic."""

    def test_lint(self):
        cat, _ = _classify_failure("Run eslint", "smoke")
        assert cat == "lint"

    def test_tests(self):
        cat, _ = _classify_failure("pytest", "test")
        assert cat == "tests"

    def test_build(self):
        cat, _ = _classify_failure("Compile", "build")
        assert cat == "build"

    def test_dependencies(self):
        cat, _ = _classify_failure("npm ci", "ci")
        assert cat == "dependencies"

    def test_infra(self):
        cat, _ = _classify_failure("helm upgrade", "deploy")
        assert cat == "infra"

    def test_timeout(self):
        cat, _ = _classify_failure("step timeout", "job")
        assert cat == "timeout"

    def test_unknown(self):
        cat, _ = _classify_failure("random", "other")
        assert cat == "unknown"

    def test_infra_step_name(self):
        cat, _ = _classify_failure("Infra step", "infra")
        assert cat == "infra"


class TestConfigParsing:
    """Config loading and merging with defaults."""

    def test_no_config_returns_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = _get_config(Path(tmp))
            assert cfg["github_actions"]["pr_comment"]["enabled"] is True
            assert cfg["github_actions"]["pr_comment"]["post_on"] == "failure"

    def test_missing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = _read_optional_config_yaml(Path(tmp))
            assert out is None

    def test_config_enabled_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".devops-agent.yml"
            config_path.write_text("github_actions:\n  pr_comment:\n    enabled: false\n")
            cfg = _get_config(Path(tmp))
            assert cfg["github_actions"]["pr_comment"]["enabled"] is False

    def test_config_post_on_always(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".devops-agent.yml"
            config_path.write_text("github_actions:\n  pr_comment:\n    post_on: always\n")
            cfg = _get_config(Path(tmp))
            assert cfg["github_actions"]["pr_comment"]["post_on"] == "always"


class TestBuildComment:
    """PR comment rendering."""

    def test_failure_comment_has_failures_section(self):
        run = {"name": "CI", "html_url": "https://example.com/run", "run_number": 123}
        findings = [
            {
                "jobName": "smoke",
                "jobUrl": "https://example.com/job",
                "stepName": "Run tests",
                "category": "tests",
                "next": "Re-run locally.",
            }
        ]
        body = _build_failure_comment(run, "123", findings, [])
        assert "<!-- devops-agent:sticky -->" in body
        assert "state=failure" in body
        assert "devops-agent — Failures detected (Run #123)" in body
        assert "### Failures" in body
        assert "smoke" in body
        assert "Run tests" in body
        assert "tests" in body
        assert "read-only" in body

    def test_recovery_comment(self):
        run = {"name": "CI", "html_url": "https://example.com/run", "run_number": 124}
        body = _build_recovery_comment(run, "124")
        assert "<!-- devops-agent:sticky -->" in body
        assert "state=recovered" in body
        assert "devops-agent — All checks passed (Run #124)" in body
        assert "Previous CI failures have been resolved" in body

    def test_run_state_in_progress(self):
        run = {"status": "in_progress"}
        assert _format_run_state(run) == "In progress (final result pending)"

    def test_run_state_completed_failed(self):
        run = {"status": "completed", "conclusion": "failure"}
        assert _format_run_state(run) == "Completed — Failed"

    def test_run_state_completed_success(self):
        run = {"status": "completed", "conclusion": "success"}
        assert _format_run_state(run) == "Completed — Successful"
