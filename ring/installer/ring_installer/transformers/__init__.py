"""
Content transformers for Ring multi-platform installer.

This module provides transformers for converting Ring components
(skills, agents, commands, hooks) to platform-specific formats.

Supported Platforms:
- Claude Code: Native Ring format (passthrough)
- Factory AI: Agents -> Droids transformation
- Cursor: Skills -> Skills, Agents -> Agents, Commands -> Commands
- Cline: All components -> Prompts
"""

from pathlib import Path
from typing import Dict, Optional, Type

from ring_installer.transformers.agent import (
    AgentTransformer,
    AgentTransformerFactory,
)
from ring_installer.transformers.base import (
    BaseTransformer,
    FrontmatterTransformer,
    PassthroughTransformer,
    TerminologyTransformer,
    TransformContext,
    TransformerPipeline,
    TransformResult,
    normalize_cursor_name,
)
from ring_installer.transformers.cline_prompts import (
    ClinePromptsGenerator,
    ClinePromptsTransformer,
    generate_cline_prompt,
    generate_prompts_index,
    write_cline_prompts,
)
from ring_installer.transformers.command import (
    CommandTransformer,
    CommandTransformerFactory,
)
from ring_installer.transformers.cursor_rules import (
    CursorRulesGenerator,
    CursorRulesTransformer,
    generate_cursorrules_from_skills,
    write_cursorrules,
)
from ring_installer.transformers.hooks import (
    HookTransformer,
    HookTransformerFactory,
    generate_hooks_json,
    parse_hooks_json,
)
from ring_installer.transformers.skill import (
    SkillTransformer,
    SkillTransformerFactory,
)

# Component type to transformer factory mapping
TRANSFORMER_FACTORIES: Dict[str, Dict[str, Type]] = {
    "skill": {
        "claude": SkillTransformer,
        "factory": SkillTransformer,
        "cursor": SkillTransformer,
        "cline": SkillTransformer,
    },
    "agent": {
        "claude": AgentTransformer,
        "factory": AgentTransformer,
        "cursor": AgentTransformer,
        "cline": AgentTransformer,
    },
    "command": {
        "claude": CommandTransformer,
        "factory": CommandTransformer,
        "cursor": CommandTransformer,
        "cline": CommandTransformer,
    },
    "hook": {
        "claude": HookTransformer,
        "factory": HookTransformer,
        "cursor": HookTransformer,
        "cline": HookTransformer,
    },
}


def get_transformer(
    platform: str,
    component_type: str
) -> BaseTransformer:
    """
    Get a transformer for the specified platform and component type.

    Args:
        platform: Target platform (claude, factory, cursor, cline)
        component_type: Component type (skill, agent, command, hook)

    Returns:
        Configured transformer instance

    Raises:
        ValueError: If platform or component type is not supported
    """
    platform = platform.lower()
    component_type = component_type.lower().rstrip("s")  # skills -> skill

    if component_type not in TRANSFORMER_FACTORIES:
        raise ValueError(
            f"Unsupported component type: '{component_type}'. "
            f"Supported: {', '.join(TRANSFORMER_FACTORIES.keys())}"
        )

    platform_transformers = TRANSFORMER_FACTORIES[component_type]

    if platform not in platform_transformers:
        raise ValueError(
            f"Unsupported platform: '{platform}'. "
            f"Supported: {', '.join(platform_transformers.keys())}"
        )

    # Use the appropriate factory
    if component_type == "skill":
        return SkillTransformerFactory.create(platform)
    elif component_type == "agent":
        return AgentTransformerFactory.create(platform)
    elif component_type == "command":
        return CommandTransformerFactory.create(platform)
    elif component_type == "hook":
        return HookTransformerFactory.create(platform)

    # Fallback
    transformer_class = platform_transformers[platform]
    return transformer_class(platform=platform)


def transform_content(
    content: str,
    platform: str,
    component_type: str,
    metadata: Optional[Dict] = None,
    source_path: str = ""
) -> TransformResult:
    """
    Transform content for a specific platform.

    This is a convenience function that creates the appropriate
    transformer and context, then performs the transformation.

    Args:
        content: Source content to transform
        platform: Target platform
        component_type: Type of component
        metadata: Optional metadata dict
        source_path: Optional source file path

    Returns:
        TransformResult with transformed content
    """
    transformer = get_transformer(platform, component_type)

    context = TransformContext(
        platform=platform,
        component_type=component_type,
        source_path=source_path,
        metadata=metadata or {}
    )

    return transformer.transform(content, context)


def create_pipeline(
    platform: str,
    component_types: Optional[list] = None
) -> TransformerPipeline:
    """
    Create a transformation pipeline for a platform.

    Args:
        platform: Target platform
        component_types: Optional list of component types to include

    Returns:
        Configured TransformerPipeline
    """
    pipeline = TransformerPipeline()

    types_to_include = component_types or ["skill", "agent", "command"]

    for component_type in types_to_include:
        try:
            transformer = get_transformer(platform, component_type)
            pipeline.add(transformer)
        except ValueError:
            pass  # Skip unsupported combinations

    return pipeline


# Platform-specific generator functions
def generate_cursor_output(
    skills: list,
    agents: list = None,
    commands: list = None,
    include_metadata: bool = True
) -> Dict[str, str]:
    """
    Generate all Cursor output files.

    Args:
        skills: List of skill content dicts
        agents: Optional list of agent content dicts
        commands: Optional list of command content dicts
        include_metadata: Include source metadata

    Returns:
        Dict mapping output filenames to content
    """
    agents = agents or []
    commands = commands or []
    output = {}

    for idx, skill in enumerate(skills, start=1):
        transformer = get_transformer("cursor", "skill")
        context = TransformContext(
            platform="cursor",
            component_type="skill",
            source_path=skill.get("source", ""),
            metadata={"name": skill.get("name", "unknown")}
        )
        result = transformer.transform(skill.get("content", ""), context)
        if result.success:
            raw_name = skill.get("name") or Path(skill.get("source", "")).stem or f"untitled-skill-{idx}"
            safe_name = normalize_cursor_name(raw_name) or f"untitled-skill-{idx}"
            filename = f"skills/{safe_name}.md"
            output[filename] = result.content

    for idx, agent in enumerate(agents, start=1):
        transformer = get_transformer("cursor", "agent")
        context = TransformContext(
            platform="cursor",
            component_type="agent",
            source_path=agent.get("source", ""),
            metadata={"name": agent.get("name", "unknown")}
        )
        result = transformer.transform(agent.get("content", ""), context)
        if result.success:
            raw_name = agent.get("name") or Path(agent.get("source", "")).stem or f"untitled-agent-{idx}"
            safe_name = normalize_cursor_name(raw_name) or f"untitled-agent-{idx}"
            filename = f"agents/{safe_name}.md"
            output[filename] = result.content

    for idx, command in enumerate(commands, start=1):
        transformer = get_transformer("cursor", "command")
        context = TransformContext(
            platform="cursor",
            component_type="command",
            source_path=command.get("source", ""),
            metadata={"name": command.get("name", "unknown")}
        )
        result = transformer.transform(command.get("content", ""), context)
        if result.success:
            cmd_name = command.get("name")
            if cmd_name:
                cmd_name = cmd_name.replace("/", "")
            raw_name = cmd_name or Path(command.get("source", "")).stem or f"untitled-command-{idx}"
            safe_name = normalize_cursor_name(raw_name) or f"untitled-command-{idx}"
            filename = f"commands/{safe_name}.md"
            output[filename] = result.content

    return output


def generate_cline_output(
    skills: list = None,
    agents: list = None,
    commands: list = None
) -> Dict[str, str]:
    """
    Generate all Cline output files.

    Args:
        skills: Optional list of skill content dicts
        agents: Optional list of agent content dicts
        commands: Optional list of command content dicts

    Returns:
        Dict mapping output filenames to content
    """
    skills = skills or []
    agents = agents or []
    commands = commands or []
    output = {}

    generator = ClinePromptsGenerator()

    # Process skills
    for skill in skills:
        generator.add_component(
            skill.get("content", ""),
            "skill",
            skill.get("name", "unknown"),
            skill.get("source")
        )

    # Process agents
    for agent in agents:
        generator.add_component(
            agent.get("content", ""),
            "agent",
            agent.get("name", "unknown"),
            agent.get("source")
        )

    # Process commands
    for command in commands:
        generator.add_component(
            command.get("content", ""),
            "command",
            command.get("name", "unknown"),
            command.get("source")
        )

    # Generate all prompt files
    for prompt_data in generator.prompts:
        prompt_content = generator.generate_prompt(prompt_data)
        prompt_type = prompt_data.get("type", "skill")
        name = prompt_data.get("name", "unknown")
        filename = f"prompts/{prompt_type}s/{name}.md"
        output[filename] = prompt_content

    # Generate index
    output["prompts/index.md"] = generator.generate_index()

    return output


__all__ = [
    # Base classes
    "BaseTransformer",
    "TransformContext",
    "TransformResult",
    "TransformerPipeline",
    "PassthroughTransformer",
    "TerminologyTransformer",
    "FrontmatterTransformer",
    # Component transformers
    "SkillTransformer",
    "SkillTransformerFactory",
    "AgentTransformer",
    "AgentTransformerFactory",
    "CommandTransformer",
    "CommandTransformerFactory",
    "HookTransformer",
    "HookTransformerFactory",
    # Cursor-specific
    "CursorRulesGenerator",
    "CursorRulesTransformer",
    "generate_cursorrules_from_skills",
    "write_cursorrules",
    # Cline-specific
    "ClinePromptsGenerator",
    "ClinePromptsTransformer",
    "generate_cline_prompt",
    "generate_prompts_index",
    "write_cline_prompts",
    # Factory functions
    "get_transformer",
    "transform_content",
    "create_pipeline",
    "generate_cursor_output",
    "generate_cline_output",
    # Hook utilities
    "generate_hooks_json",
    "parse_hooks_json",
]
