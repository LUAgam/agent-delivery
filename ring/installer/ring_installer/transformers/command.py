"""
Command content transformer.

Transforms Ring slash command files to platform-specific formats.
"""

import re
from typing import Any, Dict, List, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class CommandTransformer(BaseTransformer):
    """
    Transformer for Ring command files.

    Handles transformation of slash command definitions:
    - Claude: passthrough (native format)
    - Factory: minimal terminology changes
    - Cursor: convert to command format (plain markdown)
    - Cline: convert to action prompt (commands don't exist)
    """

    def __init__(
        self,
        platform: str,
        terminology: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the command transformer.

        Args:
            platform: Target platform identifier
            terminology: Platform-specific terminology mapping
        """
        super().__init__()
        self.platform = platform
        self.terminology = terminology or {}

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform command content for the target platform.

        Args:
            content: Original command content
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
        """Transform command for Claude Code (passthrough)."""
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
        Transform command for Factory AI.

        Factory supports commands but with droid terminology.
        """
        transformed_fm = self._transform_factory_frontmatter(frontmatter)
        transformed_body = self._replace_agent_references(body)

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
        Transform command to Cursor command format.

        Cursor commands are plain markdown (no frontmatter), triggered with / in chat.
        """
        parts: List[str] = []

        name = frontmatter.get("name", context.metadata.get("name", "Untitled Command"))
        description = frontmatter.get("description", "")
        clean_desc = self.clean_yaml_string(description)

        parts.append(f"# {self.to_title_case(name)}")
        parts.append("")

        if clean_desc:
            parts.append(clean_desc)
            parts.append("")

        cmd_name = self._normalize_cursor_name(name) or "untitled-command"
        parts.append("## Usage")
        parts.append("")
        parts.append(f"/{cmd_name}")
        parts.append("")

        args = frontmatter.get("args", [])
        if args:
            parts.append("## Parameters")
            parts.append("")
            for arg in args:
                arg_name = arg.get("name", "")
                arg_desc = arg.get("description", "")
                required = "required" if arg.get("required", False) else "optional"
                default = arg.get("default", "")

                param_line = f"- **{arg_name}** ({required})"
                if arg_desc:
                    param_line += f": {arg_desc}"
                if default:
                    param_line += f" [default: {default}]"
                parts.append(param_line)
            parts.append("")

        parts.append("## Steps")
        parts.append("")
        transformed_body = self.transform_body_for_cursor(body)
        transformed_body = transformed_body.replace("/ring:", "/")
        parts.append(transformed_body)

        return TransformResult(content="\n".join(parts), success=True)

    def _transform_cline(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        context: TransformContext
    ) -> TransformResult:
        """
        Transform command to Cline action prompt format.

        Cline doesn't have slash commands, so we convert to prompts.
        """
        parts: List[str] = []

        # Extract metadata
        name = frontmatter.get("name", context.metadata.get("name", "Untitled Command"))
        description = frontmatter.get("description", "")

        # HTML comments for metadata
        parts.append(f"<!-- Prompt: {name} -->")
        parts.append("<!-- Type: command -->")
        if context.source_path:
            parts.append(f"<!-- Source: {context.source_path} -->")
        parts.append("")

        # Title
        parts.append(f"# {self.to_title_case(name)}")
        parts.append("")

        # Description
        if description:
            clean_desc = self.clean_yaml_string(description)
            parts.append(f"> {clean_desc}")
            parts.append("")

        # Arguments/parameters
        args = frontmatter.get("args", [])
        if args:
            parts.append("## Parameters")
            parts.append("")
            for arg in args:
                arg_name = arg.get("name", "")
                arg_desc = arg.get("description", "")
                required = arg.get("required", False)
                default = arg.get("default", "")

                param_line = f"- **{arg_name}**"
                if required:
                    param_line += " (required)"
                else:
                    param_line += " (optional)"
                if arg_desc:
                    param_line += f": {arg_desc}"
                if default:
                    param_line += f" [default: {default}]"
                parts.append(param_line)
            parts.append("")

        # Instructions
        parts.append("## Steps")
        parts.append("")
        # Command transformer needs to replace /ring: with @ for Cline
        transformed_body = self.transform_body_for_cline(body)
        transformed_body = transformed_body.replace("/ring:", "@")
        parts.append(transformed_body)

        return TransformResult(content="\n".join(parts), success=True)

    def _transform_factory_frontmatter(
        self,
        frontmatter: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform command frontmatter for Factory."""
        result = dict(frontmatter)

        # Transform string values containing agent references
        for key, value in list(result.items()):
            if isinstance(value, str):
                result[key] = self._replace_agent_references(value)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_agent_references(v) if isinstance(v, str) else v
                    for v in value
                ]

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
            (r'"ring:([^"]*)-agent"', r'"ring:\1-droid"'),
        ]

        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result)

        return result



class CommandTransformerFactory:
    """Factory for creating platform-specific command transformers."""

    PLATFORM_TERMINOLOGY = {
        "claude": {"command": "command"},
        "factory": {"command": "command"},
        "cursor": {"command": "command"},
        "cline": {"command": "prompt"},
    }

    @classmethod
    def create(cls, platform: str) -> CommandTransformer:
        """
        Create a command transformer for the specified platform.

        Args:
            platform: Target platform identifier

        Returns:
            Configured CommandTransformer
        """
        terminology = cls.PLATFORM_TERMINOLOGY.get(platform, {})
        return CommandTransformer(platform=platform, terminology=terminology)
