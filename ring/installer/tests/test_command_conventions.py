"""
Tests for command naming conventions.

Validates that all command frontmatter `name` fields follow the unified
ring: namespace convention and do not contain the leading-slash bug.
"""

from pathlib import Path

import pytest
import yaml

# Repository root is two levels up from this test file (installer/tests/ -> repo root).
REPO_ROOT = Path(__file__).resolve().parents[2]

# Active plugin directories to scan.
ACTIVE_PLUGINS = ["default", "dev-team", "pm-team", "pmo-team", "finops-team", "tw-team"]

# Directories to exclude from scanning.
EXCLUDED_PATHS = {".archive", "installer"}


def _collect_command_files() -> list[tuple[str, Path]]:
    """Collect all command markdown files from active plugin directories.

    Returns a list of (test_id, path) tuples suitable for pytest parametrize.
    Skips archived directories and test fixture files.
    """
    command_files: list[tuple[str, Path]] = []

    for plugin_dir in ACTIVE_PLUGINS:
        commands_dir = REPO_ROOT / plugin_dir / "commands"
        if not commands_dir.is_dir():
            continue

        for md_file in sorted(commands_dir.glob("*.md")):
            # Skip anything under an excluded path (belt-and-suspenders check).
            if any(part in EXCLUDED_PATHS for part in md_file.parts):
                continue

            test_id = f"{plugin_dir}/{md_file.name}"
            command_files.append((test_id, md_file))

    return command_files


def _parse_frontmatter(path: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file.

    Returns the parsed dict, or None if no valid frontmatter is found.
    """
    content = path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        return None

    end = content.find("---", 3)
    if end == -1:
        return None

    yaml_text = content[3:end].strip()
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None


# Collect once at module level so pytest can parametrize.
_COMMAND_FILES = _collect_command_files()


@pytest.mark.parametrize(
    "test_id, command_path",
    _COMMAND_FILES,
    ids=[t[0] for t in _COMMAND_FILES],
)
class TestCommandNameConventions:
    """Validate naming conventions for command frontmatter."""

    def test_has_name_field(self, test_id: str, command_path: Path):
        """Command frontmatter must contain a 'name' field."""
        frontmatter = _parse_frontmatter(command_path)

        assert frontmatter is not None, (
            f"{test_id}: No valid YAML frontmatter found"
        )
        assert "name" in frontmatter, (
            f"{test_id}: Frontmatter is missing the 'name' field"
        )

    def test_name_does_not_start_with_slash(self, test_id: str, command_path: Path):
        """Command name must NOT start with '/' (the leading-slash bug)."""
        frontmatter = _parse_frontmatter(command_path)
        if frontmatter is None or "name" not in frontmatter:
            pytest.skip("No valid name field to check")

        name = frontmatter["name"]

        assert not str(name).startswith("/"), (
            f"{test_id}: name '{name}' starts with '/' — "
            "remove the leading slash"
        )

    def test_name_starts_with_ring_prefix(self, test_id: str, command_path: Path):
        """Command name must start with 'ring:' (unified namespace)."""
        frontmatter = _parse_frontmatter(command_path)
        if frontmatter is None or "name" not in frontmatter:
            pytest.skip("No valid name field to check")

        name = frontmatter["name"]

        assert str(name).startswith("ring:"), (
            f"{test_id}: name '{name}' does not start with 'ring:' — "
            "all commands must use the unified ring: namespace"
        )
