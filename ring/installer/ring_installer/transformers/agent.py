"""
Agent content transformer.

Transforms Ring agent markdown files to platform-specific formats.
"""

import re
from typing import Any, Dict, List, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class AgentTransformer(BaseTransformer):
    """
    Transformer for Ring agent files.

    Handles transformation of agent definitions including:
    - Claude: passthrough (native format)
    - Factory: agent -> droid, update references
    - Cursor: convert to agent format (frontmatter + body)
    - Cline: convert to prompt template
    """

    def __init__(
        self,
        platform: str,
        terminology: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the agent transformer.

        Args:
            platform: Target platform identifier
            terminology: Platform-specific terminology mapping
        """
        super().__init__()
        self.platform = platform
        self.terminology = terminology or {}

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform agent content for the target platform.

        Args:
            content: Original agent content
            context: Transformation context

        Returns:
            TransformResult with transformed content
        """
        errors = self.validate(content, context)
        if errors:
            return TransformResult(content=content, success=False, errors=errors)

        frontmatter, body = self.extract_frontmatter(content)

        # Transform based on platform
        if self.platform == "claude":
            return self._transform_claude(frontmatter, body, context)
        elif self.platform == "factory":
            return self._transform_factory(frontmatter, body, context)
        elif self.platform == "cursor":
            return self._transform_cursor(frontmatter, body, context)
        elif self.platform == "cline":
            return self._transform_cline(frontmatter, body, context)
        else:
            return TransformResult(content=content, success=True)

    def _transform_claude(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """Transform agent for Claude Code (passthrough)."""
        if frontmatter:
            content = self.create_frontmatter(frontmatter) + "\n" + body
        else:
            content = body

        return TransformResult(content=content, success=True)

    def _transform_factory(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """
        Transform agent to Factory AI droid format.

        Converts terminology and structure for Factory compatibility.
        """
        # Transform frontmatter
        transformed_fm = self._transform_factory_frontmatter(frontmatter)

        # Transform body
        transformed_body = self._transform_factory_body(body)

        if transformed_fm:
            content = self.create_frontmatter(transformed_fm) + "\n" + transformed_body
        else:
            content = transformed_body

        return TransformResult(content=content, success=True)

    def _transform_cursor(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """
        Transform agent to Cursor agent format.

        Cursor agents use YAML frontmatter (name, description) plus body.
        """
        name = frontmatter.get("name", context.metadata.get("name", "untitled-agent"))
        description = frontmatter.get("description", "")
        clean_desc = self.clean_yaml_string(description).replace("\n", " ").strip()[:1024]
        normalized_name = self._normalize_cursor_name(name) or "untitled-agent"

        parts: List[str] = []
        parts.append(self.create_frontmatter({"name": normalized_name, "description": clean_desc}).rstrip())
        parts.append("")
        parts.append(self.transform_body_for_cursor(body))

        return TransformResult(content="\n".join(parts), success=True)

    def _transform_cline(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """
        Transform agent to Cline prompt format.

        Converts agent definition to prompt template with
        role definition and capabilities.
        """
        parts: List[str] = []

        # Extract metadata
        name = frontmatter.get("name", context.metadata.get("name", "Untitled Agent"))
        description = frontmatter.get("description", "")
        model = frontmatter.get("model", "")

        # HTML comments for metadata
        parts.append(f"<!-- Prompt: {name} -->")
        parts.append("<!-- Type: agent -->")
        if model:
            parts.append(f"<!-- Recommended Model: {model} -->")
        if context.source_path:
            parts.append(f"<!-- Source: {context.source_path} -->")
        parts.append("")

        # Title with role indicator
        parts.append(f"# {self.to_title_case(name)} Agent")
        parts.append("")

        # Role description
        if description:
            clean_desc = self.clean_yaml_string(description)
            parts.append("## Role")
            parts.append("")
            parts.append(clean_desc)
            parts.append("")

        # Model recommendation
        if model:
            parts.append(f"**Recommended Model:** `{model}`")
            parts.append("")

        # Output requirements
        output_schema = frontmatter.get("output_schema", {})
        if output_schema:
            parts.append("## Expected Output Format")
            parts.append("")
            output_format = output_schema.get("format", "markdown")
            parts.append(f"Format: {output_format}")
            parts.append("")
            required_sections = output_schema.get("required_sections", [])
            if required_sections:
                parts.append("Required sections:")
                for section in required_sections:
                    section_name = section.get("name", "")
                    if section_name:
                        parts.append(f"- {section_name}")
                parts.append("")

        # Behavior and capabilities
        parts.append("## Behavior")
        parts.append("")
        parts.append(self.transform_body_for_cline(body))

        return TransformResult(content="\n".join(parts), success=True)

    def _transform_factory_frontmatter(
        self,
        frontmatter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform agent frontmatter to droid frontmatter."""
        result = dict(frontmatter)

        # Rename agent-related fields
        if "agent" in result:
            result["droid"] = result.pop("agent")

        if "agents" in result:
            result["droids"] = result.pop("agents")

        if "subagent_type" in result:
            result["subdroid_type"] = result.pop("subagent_type")

        # Add Factory-specific type
        if "type" not in result:
            result["type"] = "droid"

        # Transform string values
        for key, value in list(result.items()):
            if isinstance(value, str):
                result[key] = self._replace_agent_references(value)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_agent_references(v) if isinstance(v, str) else v
                    for v in value
                ]

        return result

    def _transform_factory_body(self, body: str) -> str:
        """Transform agent body to droid format."""
        result = self._replace_agent_references(body)

        # Replace section headers
        replacements = [
            ("# Agent ", "# Droid "),
            ("## Agent ", "## Droid "),
            ("### Agent ", "### Droid "),
        ]

        for old, new in replacements:
            result = result.replace(old, new)

        return result

    def _replace_agent_references(self, text: str) -> str:
        """Replace agent references with droid references."""
        replacements = [
            (r'\bagent\b', 'droid'),
            (r'\bAgent\b', 'Droid'),
            (r'\bAGENT\b', 'DROID'),
            (r'\bagents\b', 'droids'),
            (r'\bAgents\b', 'Droids'),
            (r'\bAGENTS\b', 'DROIDS'),
            (r'\bsubagent\b', 'subdroid'),
            (r'\bSubagent\b', 'Subdroid'),
            (r'\bsubagent_type\b', 'subdroid_type'),
            (r'"ring:([^"]*)-agent"', r'"ring:\1-droid"'),
            (r"'ring:([^']*)-agent'", r"'ring:\1-droid'"),
        ]

        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)

        return result



class AgentTransformerFactory:
    """Factory for creating platform-specific agent transformers."""

    PLATFORM_TERMINOLOGY = {
        "claude": {"agent": "agent"},
        "factory": {"agent": "droid"},
        "cursor": {"agent": "agent"},
        "cline": {"agent": "prompt"},
    }

    @classmethod
    def create(cls, platform: str) -> AgentTransformer:
        """
        Create an agent transformer for the specified platform.

        Args:
            platform: Target platform identifier

        Returns:
            Configured AgentTransformer
        """
        terminology = cls.PLATFORM_TERMINOLOGY.get(platform, {})
        return AgentTransformer(platform=platform, terminology=terminology)
