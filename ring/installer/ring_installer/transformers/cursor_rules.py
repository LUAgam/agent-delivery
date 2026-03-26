"""
Cursor rules generator.

Generates .cursorrules files from Ring skills and components.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class CursorRulesGenerator(BaseTransformer):
    """
    Generator for Cursor .cursorrules files.

    Creates consolidated rules files from multiple Ring skills,
    formatted according to Cursor's conventions.
    """

    def __init__(self):
        """Initialize the generator."""
        super().__init__()
        self.rules: List[Dict[str, Any]] = []

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """Not used for generator - use add_skill and generate instead."""
        raise NotImplementedError("Use add_skill() and generate() methods")

    def add_skill(
        self,
        content: str,
        name: str,
        source_path: Optional[str] = None
    ) -> None:
        """
        Add a skill to be included in the rules file.

        Args:
            content: Skill content (markdown with frontmatter)
            name: Skill name
            source_path: Original file path
        """
        frontmatter, body = self.extract_frontmatter(content)

        rule = {
            "name": frontmatter.get("name", name),
            "description": frontmatter.get("description", ""),
            "trigger": frontmatter.get("trigger", ""),
            "skip_when": frontmatter.get("skip_when", ""),
            "content": body,
            "source": source_path,
        }

        self.rules.append(rule)

    def generate(self, include_metadata: bool = True) -> str:
        """
        Generate the consolidated .cursorrules file.

        Args:
            include_metadata: Whether to include source metadata comments

        Returns:
            Complete .cursorrules file content
        """
        parts: List[str] = []

        # Header
        parts.append("# Cursor Rules")
        parts.append("")
        parts.append("These rules are generated from Ring skills.")
        parts.append("Edit with caution - changes may be overwritten on update.")
        parts.append("")
        parts.append("---")
        parts.append("")

        # Generate each rule
        for rule in self.rules:
            parts.append(self._format_rule(rule, include_metadata))
            parts.append("")
            parts.append("---")
            parts.append("")

        return "\n".join(parts)

    def _format_rule(self, rule: Dict[str, Any], include_metadata: bool) -> str:
        """Format a single rule entry."""
        parts: List[str] = []

        name = rule["name"]
        description = rule.get("description", "")
        trigger = rule.get("trigger", "")
        skip_when = rule.get("skip_when", "")
        content = rule.get("content", "")

        # Rule header
        parts.append(f"## {self.to_title_case(name)}")
        parts.append("")

        # Source comment
        if include_metadata and rule.get("source"):
            parts.append(f"<!-- Source: {rule['source']} -->")
            parts.append("")

        # Description
        if description:
            clean_desc = self.clean_yaml_string(description)
            parts.append(clean_desc)
            parts.append("")

        # Trigger conditions
        if trigger:
            parts.append("### When to Apply")
            parts.append("")
            self.add_list_items(parts, trigger)
            parts.append("")

        # Skip conditions
        if skip_when:
            parts.append("### Skip When")
            parts.append("")
            self.add_list_items(parts, skip_when)
            parts.append("")

        # Main content
        if content:
            parts.append("### Instructions")
            parts.append("")
            parts.append(self._transform_content(content))

        return "\n".join(parts)

    def _transform_content(self, content: str) -> str:
        """Transform content for Cursor compatibility."""
        # Use base class method with additional ring: prefix removal
        result = self.transform_body_for_cursor(content)
        result = result.replace("ring:", "")  # Remove ring: prefix
        return result


class CursorRulesTransformer(BaseTransformer):
    """
    Transformer that generates .cursorrules content from individual skills.

    This transformer is designed to work with the pipeline pattern,
    accumulating rules from multiple skills.
    """

    def __init__(self):
        """Initialize the transformer."""
        super().__init__()
        self.generator = CursorRulesGenerator()

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform a skill to a .cursorrules entry.

        This accumulates rules; call generate() to get final output.

        Args:
            content: Skill content
            context: Transformation context

        Returns:
            TransformResult with the transformed rule entry
        """
        name = context.metadata.get("name", "unknown")
        source = context.source_path

        # Add to generator
        self.generator.add_skill(content, name, source)

        # Return individual transformed rule
        frontmatter, body = self.extract_frontmatter(content)
        rule_content = self._format_single_rule(frontmatter, body, name)

        return TransformResult(
            content=rule_content,
            success=True,
            metadata={"rule_name": name}
        )

    def generate_combined(self, include_metadata: bool = True) -> str:
        """
        Generate the combined .cursorrules file.

        Args:
            include_metadata: Whether to include source comments

        Returns:
            Complete .cursorrules content
        """
        return self.generator.generate(include_metadata)

    def _format_single_rule(
        self,
        frontmatter: Dict[str, Any],
        body: str,
        name: str
    ) -> str:
        """Format a single rule entry."""
        parts: List[str] = []

        # Header
        rule_name = frontmatter.get("name", name)
        parts.append(f"## {self.to_title_case(rule_name)}")
        parts.append("")

        # Description
        description = frontmatter.get("description", "")
        if description:
            clean_desc = self.clean_yaml_string(description)
            parts.append(clean_desc)
            parts.append("")

        # Trigger
        trigger = frontmatter.get("trigger", "")
        if trigger:
            parts.append("### When to Apply")
            parts.append("")
            self._add_list_items(parts, trigger)
            parts.append("")

        # Skip
        skip_when = frontmatter.get("skip_when", "")
        if skip_when:
            parts.append("### Skip When")
            parts.append("")
            self._add_list_items(parts, skip_when)
            parts.append("")

        # Content
        parts.append("### Instructions")
        parts.append("")
        parts.append(self._transform_body(body))

        return "\n".join(parts)

    def _transform_body(self, body: str) -> str:
        """Transform body for Cursor."""
        result = body

        replacements = [
            ("subagent", "sub-workflow"),
            ("Subagent", "Sub-workflow"),
            ("Task tool", "workflow"),
            ("Skill tool", "rule"),
        ]

        for old, new in replacements:
            result = result.replace(old, new)

        result = re.sub(
            r'`ring:([^`]+)`',
            lambda m: f"**{self.to_title_case(m.group(1))}**",
            result
        )

        return result



def generate_cursorrules_from_skills(
    skills: List[Dict[str, str]],
    include_metadata: bool = True
) -> str:
    """
    Generate a .cursorrules file from a list of skills.

    Args:
        skills: List of dicts with 'content', 'name', and optionally 'source'
        include_metadata: Whether to include source comments

    Returns:
        Complete .cursorrules file content
    """
    generator = CursorRulesGenerator()

    for skill in skills:
        generator.add_skill(
            content=skill.get("content", ""),
            name=skill.get("name", "unknown"),
            source_path=skill.get("source")
        )

    return generator.generate(include_metadata)


def write_cursorrules(
    output_path: Path,
    skills: List[Dict[str, str]],
    include_metadata: bool = True
) -> Path:
    """
    Write a .cursorrules file from skills.

    Args:
        output_path: Path to write the file
        skills: List of skill dicts
        include_metadata: Whether to include source comments

    Returns:
        Path to the written file
    """
    content = generate_cursorrules_from_skills(skills, include_metadata)

    output_path = Path(output_path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path
