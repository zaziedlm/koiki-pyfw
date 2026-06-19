from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "scripts" / "agent_skill_smoke.py"


def test_generate_markdown_checklist() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "generate"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "# Agent Skill Smoke Checklist" in result.stdout
    assert "ambiguous-layer-routing" in result.stdout
    assert "Required first skill:" in result.stdout
    assert "Observed skills:" in result.stdout


def test_template_outputs_all_case_ids() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "template"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    case_ids = [case["id"] for case in payload["cases"]]

    assert "ambiguous-layer-routing" in case_ids
    assert "frontend-only-change" in case_ids


def test_generate_can_write_utf8_file(tmp_path: Path) -> None:
    output_path = tmp_path / "agent-skill-checklist.md"

    subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "generate", "--output", str(output_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    content = output_path.read_text(encoding="utf-8")
    assert "ユーザー管理の変更が必要" in content
    assert "koiki-project-overview" in content


def test_evaluate_passes_for_valid_results(tmp_path: Path) -> None:
    results_path = tmp_path / "results.json"
    results_path.write_text(
        json.dumps(
            {
                "cases": [
                    {"id": "ambiguous-layer-routing", "observed_skills": ["koiki-project-overview"]},
                    {"id": "app-business-feature", "observed_skills": ["koiki-refapp-feature-work"]},
                    {"id": "reusable-framework-capability", "observed_skills": ["koiki-libkoiki-feature-work"]},
                    {"id": "todo-business-api-not-framework-precedent", "observed_skills": ["koiki-refapp-feature-work"]},
                    {"id": "todo-framework-sample-maintenance", "observed_skills": ["koiki-libkoiki-feature-work"]},
                    {"id": "downstream-app-specific-api", "observed_skills": ["koiki-business-app-feature-work"]},
                    {"id": "business-app-vs-refapp-disambiguation", "observed_skills": ["koiki-business-app-feature-work"]},
                    {"id": "ambiguous-new-api-ownership", "observed_skills": ["koiki-project-overview"]},
                    {"id": "auth-security-change", "observed_skills": ["koiki-auth-security"]},
                    {"id": "app-sso-change", "observed_skills": ["koiki-auth-security", "koiki-refapp-feature-work"]},
                    {"id": "framework-auth-change", "observed_skills": ["koiki-auth-security", "koiki-libkoiki-feature-work"]},
                    {"id": "test-scope-question", "observed_skills": ["koiki-testing"]},
                    {"id": "ci-test-coverage-scope", "observed_skills": ["koiki-testing", "koiki-project-overview"]},
                    {"id": "frontend-only-change", "observed_skills": ["koiki-project-overview"]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "evaluate", "--results", str(results_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["passed"] is True
    assert payload["summary"]["failed_cases"] == 0
    assert payload["cases"][0]["first_selected_skill"] == "koiki-project-overview"
    assert payload["cases"][0]["wrong_first_selection"] is None


def test_evaluate_fails_for_missing_expected_or_forbidden_skill(tmp_path: Path) -> None:
    results_path = tmp_path / "results.json"
    results_path.write_text(
        json.dumps(
            {
                "cases": [
                    {"id": "ambiguous-layer-routing", "observed_skills": ["koiki-refapp-feature-work"]},
                    {"id": "app-business-feature", "observed_skills": ["koiki-project-overview", "koiki-refapp-feature-work"]},
                    {"id": "reusable-framework-capability", "observed_skills": ["koiki-libkoiki-feature-work"]},
                    {"id": "todo-business-api-not-framework-precedent", "observed_skills": ["koiki-refapp-feature-work"]},
                    {"id": "todo-framework-sample-maintenance", "observed_skills": ["koiki-libkoiki-feature-work"]},
                    {"id": "downstream-app-specific-api", "observed_skills": ["koiki-business-app-feature-work"]},
                    {"id": "business-app-vs-refapp-disambiguation", "observed_skills": ["koiki-business-app-feature-work"]},
                    {"id": "ambiguous-new-api-ownership", "observed_skills": ["koiki-project-overview"]},
                    {"id": "auth-security-change", "observed_skills": ["koiki-auth-security"]},
                    {"id": "app-sso-change", "observed_skills": ["koiki-auth-security", "koiki-refapp-feature-work"]},
                    {"id": "framework-auth-change", "observed_skills": ["koiki-auth-security", "koiki-libkoiki-feature-work"]},
                    {"id": "test-scope-question", "observed_skills": ["koiki-testing"]},
                    {"id": "ci-test-coverage-scope", "observed_skills": ["koiki-testing", "koiki-project-overview"]},
                    {"id": "frontend-only-change", "observed_skills": ["koiki-project-overview"]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "evaluate", "--results", str(results_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["passed"] is False
    failed_ids = {case["id"] for case in payload["cases"] if not case["passed"]}
    assert "ambiguous-layer-routing" in failed_ids
    assert "app-business-feature" in failed_ids
    ambiguous_case = next(case for case in payload["cases"] if case["id"] == "ambiguous-layer-routing")
    assert ambiguous_case["wrong_first_selection"]["expected"] == "koiki-project-overview"
    assert ambiguous_case["wrong_first_selection"]["observed"] == "koiki-refapp-feature-work"


def test_evaluate_rejects_duplicate_or_unknown_result_ids(tmp_path: Path) -> None:
    results_path = tmp_path / "results.json"
    results_path.write_text(
        json.dumps(
            {
                "cases": [
                    {"id": "ambiguous-layer-routing", "observed_skills": ["koiki-project-overview"]},
                    {"id": "ambiguous-layer-routing", "observed_skills": ["koiki-project-overview"]},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "evaluate", "--results", str(results_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "duplicate result case id" in result.stderr
