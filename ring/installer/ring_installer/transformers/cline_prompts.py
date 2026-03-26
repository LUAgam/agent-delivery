"""
Cline prompts generator.

Generates companion prompts for Cline from Ring skills and agents.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class ClinePromptsGenerator(BaseTransformer):
    """
    Generator for Cline prompt files.

    Creates prompt templates from Ring skills, agents, and commands
    formatted for use with Cline's prompt system.
    """

    def __init__(self):
        """Initialize the generator."""
        super().__init__()
        self.prompts: List[Dict[str, Any]] = []

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """Not used for generator - use add_component and generate_prompt instead."""
        raise NotImplementedError("Use add_component() and generate_prompt() methods")

    def add_component(
        self,
        content: str,
        component_type: str,
        name: str,
        source_path: Optional[str] = None
    ) -> None:
        """
        Add a component to be converted to a prompt.

        Args:
            content: Component content (markdown with frontmatter)
            component_type: Type of component (skill, agent, command)
            name: Component name
            source_path: Original file path
        """
        frontmatter, body = self.extract_frontmatter(content)

        prompt = {
            "name": frontmatter.get("name", name),
            "type": component_type,
            "description": frontmatter.get("description", ""),
            "model": frontmatter.get("model", ""),
            "frontmatter": frontmatter,
            "content": body,
            "source": source_path,
        }

        self.prompts.append(prompt)

    def generate_prompt(self, prompt: Dict[str, Any]) -> str:
        """
        Generate a single prompt file content.

        Args:
            prompt: Prompt data dictionary

        Returns:
            Formatted prompt content
        """
        component_type = prompt.get("type", "skill")

        if component_type == "agent":
            return self._generate_agent_prompt(prompt)
        elif component_type == "command":
            return self._generate_command_prompt(prompt)
        else:
            return self._generate_skill_prompt(prompt)

    def generate_index(self) -> str:
        """
        Generate an index file listing all prompts.

        Returns:
            Markdown index content
        """
        lines = [
            "# Ring Prompts for Cline",
            "",
            "This directory contains Ring skills, agents, and commands",
            "converted to Cline prompts.",
            "",
        ]

        # Group by type
        by_type: Dict[str, List[Dict[str, Any]]] = {
            "agent": [],
            "command": [],
            "skill": []
        }

        for prompt in self.prompts:
            prompt_type = prompt.get("type", "skill")
            if prompt_type in by_type:
                by_type[prompt_type].append(prompt)

        # Add sections
        for prompt_type, prompts in by_type.items():
            if prompts:
                lines.append(f"## {prompt_type.title()}s")
                lines.append("")
                for prompt in prompts:
                    name = prompt.get("name", "")
                    desc = prompt.get("description", "")
                    clean_desc = self.clean_yaml_string(desc)[:80]
                    lines.append(f"- **{self.to_title_case(name)}** - {clean_desc}")
                lines.append("")

        return "\n".join(lines)

    def _generate_skill_prompt(self, prompt: Dict[str, Any]) -> str:
        """Generate a skill-based prompt."""
        parts: List[str] = []

        name = prompt.get("name", "Untitled")
        description = prompt.get("description", "")
        frontmatter = prompt.get("frontmatter", {})
        content = prompt.get("content", "")

        # Metadata comments
        parts.append(f"<!-- Prompt: {name} -->")
        parts.append("<!-- Type: skill -->")
        if prompt.get("source"):
            parts.append(f"<!-- Source: {prompt['source']} -->")
        parts.append("")

        # Title
        parts.append(f"# {self.to_title_case(name)}")
        parts.append("")

        # Description
        if description:
            clean_desc = self.clean_yaml_string(description)
            parts.append(f"> {clean_desc}")
            parts.append("")

        # Trigger conditions
        trigger = frontmatter.get("trigger", "")
        if trigger:
            parts.append("## Use This Prompt When")
            parts.append("")
            self.add_list_items(parts, trigger)
            parts.append("")

        # Skip conditions
        skip_when = frontmatter.get("skip_when", "")
        if skip_when:
            parts.append("## Do Not Use When")
            parts.append("")
            self.add_list_items(parts, skip_when)
            parts.append("")

        # Related
        related = frontmatter.get("related", {})
        if related:
            similar = related.get("similar", [])
            complementary = related.get("complementary", [])
            if similar or complementary:
                parts.append("## Related Prompts")
                parts.append("")
                if similar:
                    parts.append("**Similar:** " + ", ".join(similar))
                if complementary:
                    parts.append("**Works well with:** " + ", ".join(complementary))
                parts.append("")

        # Instructions
        parts.append("## Instructions")
        parts.append("")
        parts.append(self._transform_content(content))

        return "\n".join(parts)

    def _generate_agent_prompt(self, prompt: Dict[str, Any]) -> str:
        """Generate an agent-based prompt."""
        parts: List[str] = []

        name = prompt.get("name", "Untitled Agent")
        description = prompt.get("description", "")
        model = prompt.get("model", "")
        frontmatter = prompt.get("frontmatter", {})
        content = prompt.get("content", "")

        # Metadata comments
        parts.append(f"<!-- Prompt: {name} -->")
        parts.append("<!-- Type: agent -->")
        if model:
            parts.append(f"<!-- Recommended Model: {model} -->")
        if prompt.get("source"):
            parts.append(f"<!-- Source: {prompt['source']} -->")
        parts.append("")

        # Title
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

        # Behavior
        parts.append("## Behavior")
        parts.append("")
        parts.append(self._transform_content(content))

        return "\n".join(parts)

    def _generate_command_prompt(self, prompt: Dict[str, Any]) -> str:
        """Generate a command-based prompt."""
        parts: List[str] = []

        name = prompt.get("name", "Untitled Command")
        description = prompt.get("description", "")
        frontmatter = prompt.get("frontmatter", {})
        content = prompt.get("content", "")

        # Metadata comments
        parts.append(f"<!-- Prompt: {name} -->")
        parts.append("<!-- Type: command -->")
        if prompt.get("source"):
            parts.append(f"<!-- Source: {prompt['source']} -->")
        parts.append("")

        # Title
        parts.append(f"# {self.to_title_case(name)}")
        parts.append("")

        # Description
        if description:
            clean_desc = self.clean_yaml_string(description)
            parts.append(f"> {clean_desc}")
            parts.append("")

        # Parameters
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
                param_line += " (required)" if required else " (optional)"
                if arg_desc:
                    param_line += f": {arg_desc}"
                if default:
                    param_line += f" [default: {default}]"
                parts.append(param_line)
            parts.append("")

        # Steps
        parts.append("## Steps")
        parts.append("")
        parts.append(self._transform_content(content))

        return "\n".join(parts)

    def _transform_content(self, content: str) -> str:
        """Transform content for Cline compatibility."""
        # Use base class method
        return self.transform_body_for_cline(content)


class ClinePromptsTransformer(BaseTransformer):
    """
    Transformer that generates Cline prompts from Ring components.

    Works with the pipeline pattern, generating individual prompt files.
    """

    def __init__(self):
        """Initialize the transformer."""
        super().__init__()
        self.generator = ClinePromptsGenerator()

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform a component to a Cline prompt.

        Args:
            content: Component content
            context: Transformation context

        Returns:
            TransformResult with the prompt content
        """
        name = context.metadata.get("name", "unknown")
        component_type = context.component_type
        source = context.source_path

        # Add to generator for index
        self.generator.add_component(content, component_type, name, source)

        # Generate the prompt
        prompt_data = {
            "name": name,
            "type": component_type,
            "source": source,
        }

        # Extract frontmatter
        frontmatter, body = self.extract_frontmatter(content)
        prompt_data["description"] = frontmatter.get("description", "")
        prompt_data["model"] = frontmatter.get("model", "")
        prompt_data["frontmatter"] = frontmatter
        prompt_data["content"] = body

        prompt_content = self.generator.generate_prompt(prompt_data)

        return TransformResult(
            content=prompt_content,
            success=True,
            metadata={"prompt_name": name, "prompt_type": component_type}
        )

    def generate_index(self) -> str:
        """
        Generate the prompts index file.

        Returns:
            Index file content
        """
        return self.generator.generate_index()


def generate_cline_prompt(
    content: str,
    component_type: str,
    name: str,
    source_path: Optional[str] = None
) -> str:
    """
    Generate a single Cline prompt from a Ring component.

    Args:
        content: Component content
        component_type: Type (skill, agent, command)
        name: Component name
        source_path: Optional source path

    Returns:
        Formatted prompt content
    """
    generator = ClinePromptsGenerator()
    generator.add_component(content, component_type, name, source_path)

    if generator.prompts:
        return generator.generate_prompt(generator.prompts[0])
    return ""


def generate_prompts_index(
    prompts: List[Dict[str, str]]
) -> str:
    """
    Generate an index file for multiple prompts.

    Args:
        prompts: List of prompt info dicts with name, type, description

    Returns:
        Index file content
    """
    generator = ClinePromptsGenerator()

    for prompt in prompts:
        generator.add_component(
            content=prompt.get("content", ""),
            component_type=prompt.get("type", "skill"),
            name=prompt.get("name", "unknown"),
            source_path=prompt.get("source")
        )

    return generator.generate_index()


def write_cline_prompts(
    output_dir: Path,
    components: List[Dict[str, str]],
    generate_index_file: bool = True
) -> List[Path]:
    """
    Write Cline prompt files from Ring components.

    Args:
        output_dir: Directory to write prompts
        components: List of component dicts with content, type, name
        generate_index_file: Whether to create an index.md

    Returns:
        List of paths to written files
    """
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    written_files: List[Path] = []
    generator = ClinePromptsGenerator()

    for component in components:
        content = component.get("content", "")
        component_type = component.get("type", "skill")
        name = component.get("name", "unknown")
        source = component.get("source")

        generator.add_component(content, component_type, name, source)

        # Generate and write the prompt
        prompt_data = generator.prompts[-1]
        prompt_content = generator.generate_prompt(prompt_data)

        # Write to appropriate subdirectory
        subdir = output_dir / f"{component_type}s"
        subdir.mkdir(exist_ok=True)

        filename = f"{name.replace(' ', '-').lower()}.md"
        file_path = subdir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(prompt_content)

        written_files.append(file_path)

    # Generate index
    if generate_index_file:
        index_content = generator.generate_index()
        index_path = output_dir / "index.md"

        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

        written_files.append(index_path)

    return written_files
