from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT_CASES_PATH = REPO_ROOT / "tests" / "unit" / "agent_guidance" / "prompt_cases.yaml"


def load_prompt_cases(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_prompt_cases(payload)
    return payload


def load_results(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    validate_results_payload(payload)
    return payload


def validate_prompt_cases(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("prompt case catalog must be a mapping")

    skills = payload.get("skills")
    cases = payload.get("cases")
    if not isinstance(skills, list) or not all(isinstance(skill, str) and skill for skill in skills):
        raise ValueError("prompt case catalog must define a non-empty skills list")
    if not isinstance(cases, list):
        raise ValueError("prompt case catalog must define cases as a list")

    valid_skills = set(skills)
    seen_ids: set[str] = set()

    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each prompt case must be a mapping")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("each prompt case must define a non-empty id")
        if case_id in seen_ids:
            raise ValueError(f"duplicate prompt case id: {case_id}")
        seen_ids.add(case_id)

        expected = case.get("expected_skills")
        forbidden = case.get("forbidden_skills")
        required_first = case.get("required_first_skill")
        if not isinstance(expected, list) or not expected:
            raise ValueError(f"{case_id} must define a non-empty expected_skills list")
        if not isinstance(forbidden, list):
            raise ValueError(f"{case_id} must define forbidden_skills as a list")
        if len(expected) != len(set(expected)):
            raise ValueError(f"{case_id} has duplicate expected_skills")
        if len(forbidden) != len(set(forbidden)):
            raise ValueError(f"{case_id} has duplicate forbidden_skills")
        if not set(expected).issubset(valid_skills):
            raise ValueError(f"{case_id} references unknown expected skills")
        if not set(forbidden).issubset(valid_skills):
            raise ValueError(f"{case_id} references unknown forbidden skills")
        if set(expected) & set(forbidden):
            raise ValueError(f"{case_id} cannot both expect and forbid the same skill")
        if required_first is not None and required_first not in expected:
            raise ValueError(f"{case_id} required_first_skill must also appear in expected_skills")


def validate_results_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("results payload must be a mapping")

    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise ValueError("results payload must define cases as a list")

    seen_ids: set[str] = set()
    for result in cases:
        if not isinstance(result, dict):
            raise ValueError("each result case must be a mapping")
        case_id = result.get("id")
        observed = result.get("observed_skills")
        notes = result.get("notes", "")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("each result case must define a non-empty id")
        if case_id in seen_ids:
            raise ValueError(f"duplicate result case id: {case_id}")
        seen_ids.add(case_id)
        if not isinstance(observed, list) or not all(isinstance(skill, str) and skill for skill in observed):
            raise ValueError(f"{case_id} observed_skills must be a list of non-empty strings")
        if len(observed) != len(set(observed)):
            raise ValueError(f"{case_id} observed_skills must not contain duplicates")
        if not isinstance(notes, str):
            raise ValueError(f"{case_id} notes must be a string")


def build_markdown_checklist(payload: dict[str, Any]) -> str:
    lines = [
        "# Agent Skill Smoke Checklist",
        "",
        "Use each prompt in an agent-capable runtime and record the selected skills.",
        "",
    ]

    for case in payload["cases"]:
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"Prompt: {case['prompt']}",
                "",
                f"Expected skills: {', '.join(case['expected_skills'])}",
                f"Required first skill: {case.get('required_first_skill', '(none)')}",
                f"Forbidden skills: {', '.join(case['forbidden_skills']) or '(none)'}",
                f"Rationale: {case['rationale']}",
                "",
                "Observed skills:",
                "Pass/Fail:",
                "Notes:",
                "",
            ]
        )

    return "\n".join(lines)


def evaluate_results(payload: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
    case_index = {case["id"]: case for case in payload["cases"]}
    evaluations: list[dict[str, Any]] = []
    result_ids = [item["id"] for item in results["cases"]]

    duplicate_result_ids = sorted({case_id for case_id in result_ids if result_ids.count(case_id) > 1})
    if duplicate_result_ids:
        raise ValueError(f"duplicate result case ids: {duplicate_result_ids}")

    for result in results["cases"]:
        case_id = result["id"]
        if case_id not in case_index:
            raise ValueError(f"unknown result case id: {case_id}")
        case = case_index[case_id]
        observed = result.get("observed_skills", [])
        observed_set = set(observed)
        expected = set(case["expected_skills"])
        forbidden = set(case["forbidden_skills"])
        required_first = case.get("required_first_skill")

        missing = sorted(expected - observed_set)
        unexpected = sorted(forbidden & observed_set)
        first_selected = observed[0] if observed else None
        wrong_first = None
        if required_first is not None and first_selected != required_first:
            wrong_first = {
                "expected": required_first,
                "observed": first_selected,
            }
        passed = not missing and not unexpected and wrong_first is None

        evaluations.append(
            {
                "id": case_id,
                "passed": passed,
                "missing_expected": missing,
                "forbidden_selected": unexpected,
                "required_first_skill": required_first,
                "first_selected_skill": first_selected,
                "wrong_first_selection": wrong_first,
                "observed_skills": observed,
                "notes": result.get("notes", ""),
            }
        )

    missing_cases = sorted(set(case_index) - {item["id"] for item in results["cases"]})
    extra_cases = sorted({item["id"] for item in results["cases"]} - set(case_index))

    return {
        "passed": not missing_cases and not extra_cases and all(item["passed"] for item in evaluations),
        "summary": {
            "total_cases": len(payload["cases"]),
            "evaluated_cases": len(evaluations),
            "passed_cases": sum(1 for item in evaluations if item["passed"]),
            "failed_cases": sum(1 for item in evaluations if not item["passed"]),
            "missing_cases": missing_cases,
            "extra_cases": extra_cases,
        },
        "cases": evaluations,
    }


def build_results_template(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "cases": [
            {
                "id": case["id"],
                "observed_skills": [],
                "notes": "",
            }
            for case in payload["cases"]
        ]
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or evaluate agent skill smoke-test cases."
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=PROMPT_CASES_PATH,
        help="Path to the prompt case catalog YAML.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format for generate/template modes.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Generate a manual smoke-test checklist.")
    generate.add_argument(
        "--output",
        type=Path,
        help="Write output directly to a UTF-8 file instead of stdout.",
    )

    template = subparsers.add_parser("template", help="Generate an empty results template.")
    template.add_argument(
        "--output",
        type=Path,
        help="Write output directly to a UTF-8 file instead of stdout.",
    )

    evaluate = subparsers.add_parser("evaluate", help="Evaluate recorded results.")
    evaluate.add_argument(
        "--results",
        type=Path,
        required=True,
        help="Path to the recorded smoke-test results file (YAML or JSON).",
    )
    evaluate.add_argument(
        "--output",
        type=Path,
        help="Write evaluation output directly to a UTF-8 file instead of stdout.",
    )

    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        payload = load_prompt_cases(args.cases)
        output_text: str

        if args.command == "generate":
            if args.format == "json":
                output_text = json.dumps(payload, ensure_ascii=False, indent=2)
            else:
                output_text = build_markdown_checklist(payload)
        elif args.command == "template":
            template = build_results_template(payload)
            output_text = json.dumps(template, ensure_ascii=False, indent=2)
        else:
            results = load_results(args.results)
            evaluation = evaluate_results(payload, results)
            output_text = json.dumps(evaluation, ensure_ascii=False, indent=2)
            exit_code = 0 if evaluation["passed"] else 1

        if args.output:
            args.output.write_text(output_text + "\n", encoding="utf-8", newline="\n")
        else:
            print(output_text)

        if args.command == "evaluate":
            return exit_code
        return 0
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
