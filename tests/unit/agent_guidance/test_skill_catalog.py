from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_ROOT = REPO_ROOT / "docs" / "agent" / "skills"
CLAUDE_ROOT = REPO_ROOT / ".claude" / "skills"


def _skill_directories(root: Path) -> list[Path]:
    return sorted(path for path in root.iterdir() if path.is_dir())


def _parse_frontmatter(skill_path: Path) -> dict[str, str]:
    content = skill_path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    assert len(parts) >= 3, f"{skill_path} must include frontmatter"
    return yaml.safe_load(parts[1])


def test_canonical_and_claude_skill_sets_match() -> None:
    canonical = {path.name for path in _skill_directories(CANONICAL_ROOT)}
    wrappers = {path.name for path in _skill_directories(CLAUDE_ROOT)}

    assert canonical, "canonical skill directories must exist"
    assert canonical == wrappers


def test_canonical_skills_have_expected_contract_files() -> None:
    for skill_dir in _skill_directories(CANONICAL_ROOT):
        skill_name = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        openai_yaml = skill_dir / "agents" / "openai.yaml"

        assert skill_md.exists(), f"{skill_name} is missing SKILL.md"
        assert openai_yaml.exists(), f"{skill_name} is missing agents/openai.yaml"

        frontmatter = _parse_frontmatter(skill_md)
        assert frontmatter["name"] == skill_name
        assert frontmatter.get("description"), f"{skill_name} description must be present"

        metadata = yaml.safe_load(openai_yaml.read_text(encoding="utf-8"))
        interface = metadata["interface"]
        assert interface["display_name"]
        assert interface["short_description"]
        assert interface["default_prompt"]
        assert f"${skill_name}" in interface["default_prompt"]


def test_claude_wrappers_point_to_canonical_skills() -> None:
    for wrapper_dir in _skill_directories(CLAUDE_ROOT):
        wrapper_path = wrapper_dir / "SKILL.md"
        assert wrapper_path.exists(), f"{wrapper_dir.name} wrapper is missing SKILL.md"

        content = wrapper_path.read_text(encoding="utf-8")
        assert f"@docs/agent/skills/{wrapper_dir.name}/SKILL.md" in content

