from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_ROOT = REPO_ROOT / "docs" / "agent" / "skills"
CLAUDE_ROOT = REPO_ROOT / ".claude" / "skills"
GITHUB_INSTRUCTIONS_ROOT = REPO_ROOT / ".github" / "instructions"


def _skill_directories(root: Path) -> list[Path]:
    return sorted(path for path in root.iterdir() if path.is_dir())


def _parse_frontmatter(skill_path: Path) -> dict[str, str]:
    content = skill_path.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    assert len(parts) >= 3, f"{skill_path} must include frontmatter"
    return yaml.safe_load(parts[1])


def test_canonical_and_claude_skill_sets_match() -> None:
    canonical = {path.name for path in _skill_directories(CANONICAL_ROOT)}
    wrappers = {path.name for path in _skill_directories(CLAUDE_ROOT) if path.name.startswith("koiki-")}

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


def test_api_ownership_terms_are_present_in_routing_skills() -> None:
    overview = (CANONICAL_ROOT / "koiki-project-overview" / "SKILL.md").read_text(encoding="utf-8")
    app = (CANONICAL_ROOT / "koiki-app-feature-work" / "SKILL.md").read_text(encoding="utf-8")
    libkoiki = (CANONICAL_ROOT / "koiki-libkoiki-feature-work" / "SKILL.md").read_text(encoding="utf-8")

    assert "`apps/`" in overview
    assert "Todo API" in overview
    assert "framework sample / starter capability" in overview
    assert "downstream customer-specific API" in app
    assert "starter/reference behavior" in app
    assert "starter/sample capability" in libkoiki
    assert "new business-specific APIs" in libkoiki


def test_openai_metadata_tracks_api_ownership_routing_terms() -> None:
    overview = yaml.safe_load(
        (CANONICAL_ROOT / "koiki-project-overview" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )["interface"]
    app = yaml.safe_load(
        (CANONICAL_ROOT / "koiki-app-feature-work" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )["interface"]
    libkoiki = yaml.safe_load(
        (CANONICAL_ROOT / "koiki-libkoiki-feature-work" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )["interface"]

    assert "apps/" in overview["short_description"]
    assert "API ownership" in overview["default_prompt"]
    assert "reference-app" in app["short_description"]
    assert "starter/sample" in libkoiki["short_description"]


def test_claude_wrappers_point_to_canonical_skills() -> None:
    for wrapper_dir in _skill_directories(CLAUDE_ROOT):
        if not wrapper_dir.name.startswith("koiki-"):
            continue
        wrapper_path = wrapper_dir / "SKILL.md"
        assert wrapper_path.exists(), f"{wrapper_dir.name} wrapper is missing SKILL.md"

        content = wrapper_path.read_text(encoding="utf-8")
        assert f"@docs/agent/skills/{wrapper_dir.name}/SKILL.md" in content


def test_claude_wrapper_descriptions_track_api_ownership_routing() -> None:
    overview = _parse_frontmatter(CLAUDE_ROOT / "koiki-project-overview" / "SKILL.md")
    app = _parse_frontmatter(CLAUDE_ROOT / "koiki-app-feature-work" / "SKILL.md")
    libkoiki = _parse_frontmatter(CLAUDE_ROOT / "koiki-libkoiki-feature-work" / "SKILL.md")

    assert "API ownership" in overview["description"]
    assert "apps/" in overview["description"]
    assert "reference-application" in app["description"]
    assert "starter/sample" in libkoiki["description"]


def test_github_and_shared_agent_docs_track_api_ownership_policy() -> None:
    copilot = (REPO_ROOT / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    architecture = (GITHUB_INSTRUCTIONS_ROOT / "architecture.instructions.md").read_text(encoding="utf-8")
    app_instruction = (GITHUB_INSTRUCTIONS_ROOT / "app.instructions.md").read_text(encoding="utf-8")
    libkoiki_instruction = (GITHUB_INSTRUCTIONS_ROOT / "libkoiki.instructions.md").read_text(encoding="utf-8")
    app_doc = (REPO_ROOT / "docs" / "agent" / "app.md").read_text(encoding="utf-8")
    libkoiki_doc = (REPO_ROOT / "docs" / "agent" / "libkoiki.md").read_text(encoding="utf-8")

    for content in [copilot, architecture, app_instruction, app_doc]:
        assert "apps/" in content

    for content in [copilot, architecture, libkoiki_instruction, libkoiki_doc]:
        assert "Todo API" in content
        assert "framework sample / starter capability" in content

    assert "downstream customer-specific API" in app_instruction
    assert "Downstream or customer-specific APIs should start under `apps/`" in app_doc
