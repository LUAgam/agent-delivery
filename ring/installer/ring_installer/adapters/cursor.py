"""
Cursor adapter - converts Ring format to Cursor native format.

Cursor uses:
- skills -> skills/ (SKILL.md with frontmatter)
- agents -> agents/ (frontmatter + body)
- commands -> commands/ (plain markdown, no frontmatter)
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ring_installer.adapters.base import PlatformAdapter
from ring_installer.transformers.base import BaseTransformer, normalize_cursor_name


class CursorAdapter(PlatformAdapter):
    """
    Platform adapter for Cursor.

    Cursor uses skills, agents, and commands in their native directories
    and formats. Skills and agents use YAML frontmatter; commands are plain markdown.
    """

    platform_id = "cursor"
    platform_name = "Cursor"

    @staticmethod
    def _as_text(value: Any, default: str = "") -> str:
        """Coerce frontmatter value to str; avoid crashes on non-string YAML types."""
        if value is None:
            return default
        text = value if isinstance(value, str) else str(value)
        text = text.strip()
        return text or default

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Cursor adapter.

        Args:
            config: Platform-specific configuration from platforms.json
        """
        super().__init__(config)

    def transform_skill(self, skill_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring skill to Cursor skill format.

        Converts the Ring skill format to Cursor's skill format with YAML
        frontmatter (name, description) for agent discovery.

        Args:
            skill_content: The original skill content
            metadata: Optional metadata about the skill

        Returns:
            Transformed skill content for Cursor
        """
        frontmatter, body = self.extract_frontmatter(skill_content)

        name = self._as_text(
            frontmatter.get("name", metadata.get("name") if metadata else None),
            "untitled-skill",
        )
        description = self._as_text(frontmatter.get("description", ""))
        clean_desc = self._clean_yaml_string(description)
        clean_desc_single = clean_desc.replace("\n", " ").strip()[:1024]
        normalized_name = normalize_cursor_name(name) or "untitled-skill"

        parts: List[str] = []
        parts.append(self.create_frontmatter({"name": normalized_name, "description": clean_desc_single}).rstrip())
        parts.append("")

        parts.append(f"# {self._to_title_case(name)}")
        parts.append("")

        if clean_desc:
            parts.append(clean_desc)
            parts.append("")

        trigger = frontmatter.get("trigger", "")
        if trigger:
            parts.append("## When to Apply")
            parts.append("")
            clean_trigger = self._clean_yaml_string(trigger)
            for line in clean_trigger.split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    parts.append(line)
                elif line:
                    parts.append(f"- {line}")
            parts.append("")

        skip_when = frontmatter.get("skip_when", "")
        if skip_when:
            parts.append("## Skip When")
            parts.append("")
            clean_skip = self._clean_yaml_string(skip_when)
            for line in clean_skip.split("\n"):
                line = line.strip()
                if line.startswith("-"):
                    parts.append(line)
                elif line:
                    parts.append(f"- {line}")
            parts.append("")

        parts.append("## Instructions")
        parts.append("")
        parts.append(self._transform_body_for_cursor(body))

        return "\n".join(parts)

    def transform_agent(self, agent_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring agent to Cursor agent format.

        Converts agent format to Cursor's agent format with YAML frontmatter
        (name, description) for subagent discovery.

        Args:
            agent_content: The original agent content
            metadata: Optional metadata about the agent

        Returns:
            Transformed agent content for Cursor
        """
        frontmatter, body = self.extract_frontmatter(agent_content)

        name = self._as_text(
            frontmatter.get("name", metadata.get("name") if metadata else None),
            "untitled-agent",
        )
        description = self._as_text(frontmatter.get("description", ""))
        clean_desc = self._clean_yaml_string(description).replace("\n", " ").strip()[:1024]
        normalized_name = normalize_cursor_name(name) or "untitled-agent"

        parts: List[str] = []
        parts.append(self.create_frontmatter({"name": normalized_name, "description": clean_desc}).rstrip())
        parts.append("")
        parts.append(self._transform_body_for_cursor(body))

        return "\n".join(parts)

    def transform_command(self, command_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring command to Cursor command format.

        Cursor commands are plain markdown files (no frontmatter), triggered
        with / in chat. Filename determines command name.

        Args:
            command_content: The original command content
            metadata: Optional metadata about the command

        Returns:
            Transformed command content for Cursor (plain markdown)
        """
        frontmatter, body = self.extract_frontmatter(command_content)

        name = self._as_text(
            frontmatter.get("name", metadata.get("name") if metadata else None),
            "Untitled Command",
        )
        description = self._as_text(frontmatter.get("description", ""))
        clean_desc = self._clean_yaml_string(description)

        parts: List[str] = []
        parts.append(f"# {self._to_title_case(name)}")
        parts.append("")

        if clean_desc:
            parts.append(clean_desc)
            parts.append("")

        cmd_name = normalize_cursor_name(name.replace("/", "")) or "untitled-command"
        parts.append("## Usage")
        parts.append("")
        parts.append(f"/{cmd_name}")
        parts.append("")

        raw_args = frontmatter.get("args", [])
        if isinstance(raw_args, dict):
            args: List[Any] = [raw_args]
        elif isinstance(raw_args, list):
            args = raw_args
        else:
            args = []

        if args:
            parts.append("## Parameters")
            parts.append("")
            for arg in args:
                if not isinstance(arg, dict):
                    continue
                arg_name = self._as_text(arg.get("name", ""), "")
                arg_desc = self._as_text(arg.get("description", ""), "")
                required = "required" if arg.get("required", False) else "optional"
                param_line = f"- **{arg_name}** ({required})"
                if arg_desc:
                    param_line += f": {arg_desc}"
                parts.append(param_line)
            parts.append("")

        parts.append("## Steps")
        parts.append("")
        parts.append(self._transform_body_for_cursor(body))

        return "\n".join(parts)

    def get_install_path(self) -> Path:
        """
        Get the installation path for Cursor.

        Returns:
            Path to ~/.cursor directory
        """
        if self._install_path is None:
            base_path = self.config.get("install_path", "~/.cursor")
            self._install_path = Path(base_path).expanduser()
        return self._install_path

    def get_component_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Get the component mapping for Cursor.

        Returns:
            Mapping of Ring components to Cursor directories
        """
        return {
            "agents": {
                "target_dir": "agents",
                "extension": ".md"
            },
            "commands": {
                "target_dir": "commands",
                "extension": ".md"
            },
            "skills": {
                "target_dir": "skills",
                "extension": ".md"
            }
        }

    def get_terminology(self) -> Dict[str, str]:
        """
        Get Cursor terminology.

        Returns:
            Mapping of Ring terms to Cursor terms
        """
        return {
            "agent": "agent",
            "skill": "skill",
            "command": "command",
            "hook": "automation"
        }

    def is_native_format(self) -> bool:
        """
        Check if this platform uses Ring's native format.

        Returns:
            False - Cursor requires transformation
        """
        return False

    def _to_title_case(self, text: str) -> str:
        """
        Convert text to title case, handling kebab-case and snake_case.

        Args:
            text: Input text

        Returns:
            Title-cased text
        """
        # Replace separators with spaces
        text = text.replace("-", " ").replace("_", " ")
        # Title case
        return text.title()

    def _clean_yaml_string(self, text: str) -> str:
        """
        Clean up YAML multi-line string markers.

        Args:
            text: YAML string value

        Returns:
            Cleaned string
        """
        # Remove | and > markers
        text = re.sub(r'^[|>]\s*', '', text)
        # Clean up extra whitespace
        return text.strip()

    def _transform_body_for_cursor(self, body: str) -> str:
        """
        Transform body content for Cursor compatibility.

        Args:
            body: Original body content

        Returns:
            Transformed body content
        """
        result = body
        for old, new in BaseTransformer.CURSOR_REPLACEMENTS:
            result = result.replace(old, new)

        # Remove Ring-specific tool references that don't apply
        result = re.sub(r'`ring:[^`]+`', lambda m: self._transform_ring_reference(m.group(0)), result)

        # Normalize /ring: command references for all component types
        result = result.replace("/ring:", "/")

        return result

    def _transform_ring_reference(self, ref: str) -> str:
        """
        Transform a Ring tool reference to Cursor format.

        Args:
            ref: Ring reference like `ring:skill-name`

        Returns:
            Cursor-friendly reference
        """
        # Extract the name from the reference
        match = re.match(r'`ring:([^`]+)`', ref)
        if match:
            name = match.group(1)
            # Convert to readable format
            readable = self._to_title_case(name)
            return f"**{readable}**"
        return ref

    def generate_cursorrules_entry(self, rule_content: str, rule_name: str) -> str:
        """
        Generate an entry for the main .cursorrules file.

        Cursor allows rules to be defined in a single .cursorrules file
        or in separate files. This generates an entry for the combined format.

        Args:
            rule_content: The rule content
            rule_name: Name of the rule

        Returns:
            Formatted entry for .cursorrules
        """
        return f"""
---
## {self._to_title_case(rule_name)}

{rule_content}
"""

    def get_cursorrules_path(self, project_path: Optional[Path] = None) -> Path:
        """
        Get the path to the .cursorrules file.

        Args:
            project_path: Optional project directory path

        Returns:
            Path to .cursorrules file
        """
        if project_path:
            return project_path / ".cursorrules"
        return self.get_install_path() / ".cursorrules"
