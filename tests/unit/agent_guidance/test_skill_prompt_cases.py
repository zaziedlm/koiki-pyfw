from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_CASES_PATH = Path(__file__).with_name("prompt_cases.yaml")
CANONICAL_ROOT = REPO_ROOT / "docs" / "agent" / "skills"


def _load_prompt_cases() -> dict:
    return yaml.safe_load(PROMPT_CASES_PATH.read_text(encoding="utf-8"))


def test_prompt_case_catalog_matches_skill_directories() -> None:
    payload = _load_prompt_cases()
    declared_skills = set(payload["skills"])
    canonical_skills = {path.name for path in CANONICAL_ROOT.iterdir() if path.is_dir()}

    assert declared_skills == canonical_skills


def test_prompt_cases_are_well_formed() -> None:
    payload = _load_prompt_cases()
    valid_skills = set(payload["skills"])
    case_ids = [case["id"] for case in payload["cases"]]

    assert len(case_ids) == len(set(case_ids)), "prompt case ids must be unique"

    for case in payload["cases"]:
        assert case["id"]
        assert case["prompt"]
        assert case["rationale"]
        assert case["expected_skills"], f'{case["id"]} must expect at least one skill'

        expected = case["expected_skills"]
        forbidden = case["forbidden_skills"]
        required_first = case.get("required_first_skill")

        assert len(expected) == len(set(expected)), f'{case["id"]} has duplicate expected skills'
        assert len(forbidden) == len(set(forbidden)), f'{case["id"]} has duplicate forbidden skills'
        assert set(expected).issubset(valid_skills), f'{case["id"]} references unknown expected skills'
        assert set(forbidden).issubset(valid_skills), f'{case["id"]} references unknown forbidden skills'
        assert set(expected).isdisjoint(forbidden), f'{case["id"]} cannot expect and forbid the same skill'
        if required_first is not None:
            assert required_first in valid_skills, f'{case["id"]} references unknown required_first_skill'
            assert required_first in expected, f'{case["id"]} required_first_skill must also be expected'


def test_every_skill_has_positive_coverage_in_prompt_cases() -> None:
    payload = _load_prompt_cases()
    coverage = Counter()

    for case in payload["cases"]:
        for skill in case["expected_skills"]:
            coverage[skill] += 1

    missing = [skill for skill in payload["skills"] if coverage[skill] == 0]
    assert not missing, f"prompt catalog is missing positive coverage for: {missing}"


def test_prompt_catalog_includes_negative_examples_for_specific_skills() -> None:
    payload = _load_prompt_cases()
    negative_coverage = Counter()

    for case in payload["cases"]:
        for skill in case["forbidden_skills"]:
            negative_coverage[skill] += 1

    for skill in [
        "koiki-project-overview",
        "koiki-refapp-feature-work",
        "koiki-libkoiki-feature-work",
        "koiki-auth-security",
    ]:
        assert negative_coverage[skill] > 0, f"{skill} should have at least one negative example"
