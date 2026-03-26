"""
Factory AI adapter - converts Ring format to Factory's droid-based format.

Factory AI uses similar concepts to Ring but with different terminology:
- agents -> droids
- skills -> skills (same)
- commands -> commands (same)
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ring_installer.adapters.base import PlatformAdapter


class FactoryAdapter(PlatformAdapter):
    """
    Platform adapter for Factory AI.

    Factory AI uses "droids" instead of "agents" and has slight differences
    in how components are structured.

    Key Factory/Droid differences from Claude Code:
    - agents -> droids (terminology)
    - Droid names: lowercase letters, digits, `-`, `_` only (NO colons)
    - Tools: Read, LS, Grep, Glob, Create, Edit, Execute, WebSearch, FetchUrl, TodoWrite
    - Tool categories: read-only, edit, execute, web, mcp
    - Model: "inherit" or full model ID like "claude-opus-4-1-20250805"
    - Commands: Use $ARGUMENTS placeholder (not positional $1, $2)
    - Skills: ~/.factory/skills/<name>/SKILL.md format
    - Droids: ~/.factory/droids/*.md (flat directory, top-level only)
    """

    platform_id = "factory"
    platform_name = "Factory AI"

    # Factory tool name mappings
    _FACTORY_TOOL_NAME_MAP: Dict[str, str] = {
        # Claude Code -> Factory tool names
        "WebFetch": "FetchUrl",
        "FetchURL": "FetchUrl",
        "Bash": "Execute",
        "Write": "Create",  # Factory uses Create for new files
        "MultiEdit": "Edit",  # Factory uses Edit for modifications
        "NotebookEdit": "Edit",
        "BrowseURL": "FetchUrl",
        # MCP tools: Factory uses same mcp__server__tool format as Claude Code
        # No transformation needed for MCP tools
    }

    # Tools that droids cannot use
    # NOTE: Task IS valid - droids CAN spawn other droids via Task tool
    _FACTORY_INVALID_TOOLS: set = {"Dispatch", "SubAgent"}

    # Model shorthand to Factory model ID mapping
    _FACTORY_MODEL_MAP: Dict[str, str] = {
        "opus": "claude-opus-4-5-20251101",
        "sonnet": "claude-sonnet-4-5-20250929",
        "haiku": "claude-haiku-4-5-20251001",
        "inherit": "inherit",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Factory AI adapter.

        Args:
            config: Platform-specific configuration from platforms.json
        """
        super().__init__(config)

    def transform_skill(self, skill_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring skill for Factory AI.

        Updates terminology and adjusts frontmatter for Factory compatibility.

        Args:
            skill_content: The original skill content
            metadata: Optional metadata about the skill

        Returns:
            Transformed skill content for Factory AI
        """
        frontmatter, body = self.extract_frontmatter(skill_content)

        # Update frontmatter terminology
        if frontmatter:
            frontmatter = self._transform_frontmatter(frontmatter)

        # Replace agent references with droid references in body
        body = self._replace_agent_references(body)
        body = self._replace_factory_tool_references(body)

        # Rebuild the content
        if frontmatter:
            return self.create_frontmatter(frontmatter) + "\n" + body
        return body

    def transform_agent(self, agent_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring agent to a Factory AI droid.

        Converts agent format to Factory's droid format, updating terminology
        and structure as needed.

        Args:
            agent_content: The original agent content
            metadata: Optional metadata about the agent

        Returns:
            Transformed droid content for Factory AI
        """
        frontmatter, body = self.extract_frontmatter(agent_content)

        # Transform frontmatter
        if frontmatter:
            frontmatter = self._transform_agent_frontmatter(frontmatter)
            frontmatter = self._qualify_droid_name(frontmatter, metadata)

        # Transform body content
        body = self._transform_agent_body(body)

        # Rebuild the content
        if frontmatter:
            return self.create_frontmatter(frontmatter) + "\n" + body
        return body

    def _qualify_droid_name(
        self,
        frontmatter: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Qualify droid name with plugin namespace.

        Factory installs droids into a single flat directory. To avoid name collisions
        across plugins, droids are namespaced as:

            ring-<plugin>-<name>

        NOTE: Factory droid names can only contain lowercase letters, digits, `-`, `_`.
        Colons are NOT allowed in droid names (they're used for custom: model syntax).

        Example:
            plugin=default, name=code-reviewer -> ring-default-code-reviewer
        """
        result = dict(frontmatter)

        plugin = (metadata or {}).get("plugin")
        if not isinstance(plugin, str) or not plugin:
            return result

        plugin_id = plugin if plugin.startswith("ring-") else f"ring-{plugin}"

        name = result.get("name")
        if not isinstance(name, str) or not name:
            fallback_name = (metadata or {}).get("name")
            if isinstance(fallback_name, str) and fallback_name:
                name = fallback_name
            else:
                return result

        # Already qualified with hyphen (ring-plugin-name format)
        if name.startswith("ring-"):
            return result

        # Convert any colons to hyphens (legacy format cleanup)
        name = name.replace(":", "-")

        result["name"] = f"{plugin_id}-{name}"
        return result

    def transform_command(self, command_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Transform a Ring command for Factory AI.

        Factory command format:
        - Optional YAML frontmatter with `description` and `argument-hint`
        - Body uses `$ARGUMENTS` for all arguments (not positional $1, $2)
        - Filename becomes command name (lowercase, spaces -> `-`)

        Args:
            command_content: The original command content
            metadata: Optional metadata about the command

        Returns:
            Transformed command content for Factory AI
        """
        frontmatter, body = self.extract_frontmatter(command_content)

        # Transform frontmatter for Factory commands
        if frontmatter:
            frontmatter = self._transform_command_frontmatter(frontmatter)

        # Replace agent references in body
        body = self._replace_agent_references(body)
        body = self._replace_factory_tool_references(body)

        # Rebuild the content
        if frontmatter:
            return self.create_frontmatter(frontmatter) + "\n" + body
        return body

    def _transform_command_frontmatter(self, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
        """Transform command frontmatter for Factory.

        Factory command frontmatter fields:
        - description: Shown in slash suggestions
        - argument-hint: Appends inline usage hints (e.g., /command <hint>)
        - allowed-tools: Reserved for future use
        """
        result = dict(frontmatter)

        # Map 'args' or 'arguments' to 'argument-hint'
        if "args" in result and "argument-hint" not in result:
            result["argument-hint"] = result.pop("args")
        elif "arguments" in result and "argument-hint" not in result:
            result["argument-hint"] = result.pop("arguments")

        # Remove fields Factory doesn't use for commands
        for field in ["name", "version", "type", "tags"]:
            result.pop(field, None)

        # Transform any agent terminology in string values
        for key, value in result.items():
            if isinstance(value, str):
                result[key] = self._replace_agent_references(value)

        return result

    def transform_hook(self, hook_content: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Transform a Ring hook for Factory AI.

        Key transformation: Replace Claude Code plugin paths with Factory paths.
        Factory hooks are installed directly to ~/.factory/hooks/, not in a plugin.
        Commands need 'bash' prefix for proper execution.

        Args:
            hook_content: The original hook content (JSON or script)
            metadata: Optional metadata about the hook

        Returns:
            Transformed hook content for Factory AI
        """
        # Replace Claude Code's plugin root variable with Factory's hooks directory
        # Factory hooks are installed to ~/.factory/hooks/, not a plugin directory
        result = hook_content.replace("${CLAUDE_PLUGIN_ROOT}/hooks/", "~/.factory/hooks/")
        result = result.replace("$CLAUDE_PLUGIN_ROOT/hooks/", "~/.factory/hooks/")
        # Also handle any remaining references
        result = result.replace("${CLAUDE_PLUGIN_ROOT}", "~/.factory")
        result = result.replace("$CLAUDE_PLUGIN_ROOT", "~/.factory")
        
        return result

    def get_install_path(self) -> Path:
        """
        Get the installation path for Factory AI.

        Returns:
            Path to ~/.factory directory
        """
        if self._install_path is None:
            env_path = Path(self.config.get("install_path", "~/.factory")).expanduser()
            override = os.environ.get("FACTORY_CONFIG_PATH")
            if override:
                candidate = Path(override).expanduser().resolve()
                home = Path.home().resolve()
                try:
                    candidate.relative_to(home)
                    env_path = candidate
                except ValueError:
                    import logging
                    logging.getLogger(__name__).warning(
                        "FACTORY_CONFIG_PATH=%s ignored: path must be under home", override
                    )
            self._install_path = env_path
        return self._install_path

    def get_component_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Get the component mapping for Factory AI.

        Returns:
            Mapping of Ring components to Factory AI directories
        """
        return {
            "agents": {
                "target_dir": "droids",
                "extension": ".md"
            },
            "commands": {
                "target_dir": "commands",
                "extension": ".md"
            },
            "skills": {
                "target_dir": "skills",
                "extension": ".md"
            },
            "hooks": {
                "target_dir": "hooks",
                "extension": ""  # Multiple extensions supported
            }
        }

    def requires_hooks_in_settings(self) -> bool:
        """
        Check if this platform requires hooks to be merged into settings.

        Factory AI expects hooks to be defined in settings.json, not as
        separate hooks.json files. Hook scripts (.sh, .py) are still
        installed to the hooks directory, but the hooks.json configuration
        must be merged into settings.json.

        Returns:
            True - Factory requires hooks in settings.json
        """
        return True

    def get_settings_path(self) -> Path:
        """
        Get the path to Factory's settings.json file.

        Returns:
            Path to ~/.factory/settings.json
        """
        return self.get_install_path() / "settings.json"

    def merge_hooks_to_settings(
        self,
        hooks_config: Dict[str, Any],
        dry_run: bool = False,
        install_path: Optional[Path] = None
    ) -> bool:
        """
        Merge hooks configuration into Factory's settings.json.

        Factory expects hooks to be defined in settings.json under the "hooks" key,
        not in a separate hooks.json file. This method reads the existing settings,
        merges the hooks configuration, and writes it back.

        Args:
            hooks_config: The hooks configuration to merge (from hooks.json)
            dry_run: If True, don't actually write the file
            install_path: Optional custom install path (uses default if not provided)

        Returns:
            True if successful, False otherwise
        """
        import json
        import logging
        
        logger = logging.getLogger(__name__)
        base_path = install_path or self.get_install_path()
        settings_path = base_path / "settings.json"

        # Read existing settings or create empty dict
        existing_settings: Dict[str, Any] = {}
        if settings_path.exists():
            try:
                content = settings_path.read_text(encoding="utf-8")
                # Handle JSON with comments (Factory allows // comments)
                lines = []
                for line in content.split("\n"):
                    stripped = line.strip()
                    if not stripped.startswith("//"):
                        lines.append(line)
                clean_content = "\n".join(lines)
                existing_settings = json.loads(clean_content)
            except Exception as e:
                logger.warning(f"Failed to read settings.json: {e}")
                # Continue with empty settings

        # Extract hooks from the config
        hooks_to_merge = hooks_config.get("hooks", hooks_config)

        # Merge hooks - combine with existing hooks if any
        existing_hooks = existing_settings.get("hooks", {})

        for event_name, event_hooks in hooks_to_merge.items():
            if event_name not in existing_hooks:
                existing_hooks[event_name] = []

            # Add new hooks, avoiding duplicates based on (command + matcher) combination
            existing_hook_keys = {
                (h.get("hooks", [{}])[0].get("command", ""), h.get("matcher", ""))
                for h in existing_hooks[event_name]
                if h.get("hooks")
            }

            for hook_entry in event_hooks:
                # Transform hook commands to use Factory paths
                transformed_entry = self._transform_hook_entry(hook_entry, base_path)
                hook_commands = transformed_entry.get("hooks", [])
                if hook_commands:
                    cmd = hook_commands[0].get("command", "")
                    matcher = transformed_entry.get("matcher", "")
                    key = (cmd, matcher)
                    if cmd and key not in existing_hook_keys:
                        existing_hooks[event_name].append(transformed_entry)
                        existing_hook_keys.add(key)

        existing_settings["hooks"] = existing_hooks
        existing_settings["enableHooks"] = True

        if dry_run:
            logger.info(f"[DRY RUN] Would merge hooks into {settings_path}")
            return True

        try:
            # Write settings back
            settings_path.write_text(
                json.dumps(existing_settings, indent=2),
                encoding="utf-8"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to write settings.json: {e}")
            return False

    def _transform_hook_entry(
        self,
        hook_entry: Dict[str, Any],
        install_path: Path
    ) -> Dict[str, Any]:
        """
        Transform a hook entry's commands for Factory compatibility.

        Converts Claude Code plugin paths to Factory absolute paths:
        - ${CLAUDE_PLUGIN_ROOT}/hooks/script.sh -> ~/.factory/hooks/script.sh
        - $CLAUDE_PLUGIN_ROOT/hooks/script.sh -> ~/.factory/hooks/script.sh

        Args:
            hook_entry: A hook entry dict with 'hooks' array and optional 'matcher'
            install_path: The Factory installation path

        Returns:
            Transformed hook entry with updated command paths
        """
        result = dict(hook_entry)
        hooks_path = install_path / "hooks"

        if "hooks" in result:
            transformed_hooks = []
            for hook_cmd in result["hooks"]:
                if not isinstance(hook_cmd, dict):
                    transformed_hooks.append(hook_cmd)
                    continue

                transformed_cmd = dict(hook_cmd)
                if "command" in transformed_cmd:
                    cmd = transformed_cmd["command"]
                    # Transform Claude plugin paths to Factory absolute paths
                    # Use absolute path with ~ expansion for portability
                    cmd = cmd.replace(
                        "${CLAUDE_PLUGIN_ROOT}/hooks/",
                        f"{hooks_path}/"
                    )
                    cmd = cmd.replace(
                        "$CLAUDE_PLUGIN_ROOT/hooks/",
                        f"{hooks_path}/"
                    )
                    # Handle any remaining plugin root references
                    cmd = cmd.replace("${CLAUDE_PLUGIN_ROOT}", str(install_path))
                    cmd = cmd.replace("$CLAUDE_PLUGIN_ROOT", str(install_path))
                    transformed_cmd["command"] = cmd
                transformed_hooks.append(transformed_cmd)
            result["hooks"] = transformed_hooks

        return result

    def should_skip_hook_file(self, filename: str) -> bool:
        """
        Check if a hook file should be skipped during normal installation.

        For Factory, hooks.json should not be installed as a file - its content
        should be merged into settings.json instead. However, hook scripts
        (.sh, .py) should still be installed.

        Args:
            filename: The hook filename

        Returns:
            True if this file should be skipped (will be handled specially)
        """
        return filename == "hooks.json"

    def get_terminology(self) -> Dict[str, str]:
        """
        Get Factory AI terminology.

        Returns:
            Mapping of Ring terms to Factory AI terms
        """
        return {
            "agent": "droid",
            "skill": "skill",
            "command": "command",
            "hook": "trigger"
        }

    def is_native_format(self) -> bool:
        """
        Check if this platform uses Ring's native format.

        Returns:
            False - Factory AI requires transformation
        """
        return False

    def _transform_frontmatter(self, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform frontmatter for Factory AI compatibility.

        NOTE: subagent_type is intentionally preserved because Factory's Task tool
        uses it to invoke droids. The Task tool looks for `subagent_type` parameter.

        Args:
            frontmatter: Original frontmatter dictionary

        Returns:
            Transformed frontmatter dictionary
        """
        result = dict(frontmatter)

        # Rename agent-related field names (metadata fields, not Task tool params)
        if "agent" in result:
            result["droid"] = result.pop("agent")

        if "agents" in result:
            result["droids"] = result.pop("agents")

        # NOTE: Do NOT rename subagent_type - Factory's Task tool uses this field name
        # to identify which droid to invoke. Renaming it would break Task invocations.

        # Transform any string values containing "agent" terminology
        for key, value in result.items():
            if isinstance(value, str):
                result[key] = self._replace_agent_references(value)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_agent_references(v) if isinstance(v, str) else v
                    for v in value
                ]

        return result

    def _transform_agent_frontmatter(self, frontmatter: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform agent-specific frontmatter to droid frontmatter.

        Factory droid frontmatter fields:
        - name: Required. Lowercase letters, digits, `-`, `_` only
        - description: Optional, ≤500 chars
        - model: "inherit" or full model ID like "claude-opus-4-1-20250805"
        - tools: Omit for all, category string, or array of tool IDs
        - reasoningEffort: Optional (off, none, low, medium, high)

        NOTE: Do NOT rename subagent_type - Factory's Task tool uses it to invoke droids.

        Args:
            frontmatter: Original agent frontmatter

        Returns:
            Transformed droid frontmatter
        """
        result = dict(frontmatter)

        # Transform model shorthand to Factory model ID
        if "model" in result:
            model = result["model"]
            if model in self._FACTORY_MODEL_MAP:
                result["model"] = self._FACTORY_MODEL_MAP[model]
            elif not model.startswith("claude") and model != "inherit":
                # Unknown model, default to inherit
                result["model"] = "inherit"

        # Transform tools list for Factory compatibility
        if "tools" in result:
            result["tools"] = self._transform_tools_for_factory(result["tools"])

        # Remove fields that Factory doesn't use
        for field in ["type", "version", "last_updated", "changelog", "output_schema"]:
            result.pop(field, None)

        # Ensure description is within Factory's 500 char limit
        if "description" in result and isinstance(result["description"], str):
            if len(result["description"]) > 500:
                result["description"] = result["description"][:497] + "..."

        return result

    def _transform_agent_body(self, body: str) -> str:
        """
        Transform agent body content to droid format.

        Args:
            body: Original agent body content

        Returns:
            Transformed droid body content
        """
        # Replace terminology
        body = self._replace_agent_references(body)
        body = self._replace_factory_tool_references(body)

        # Replace section headers
        replacements = [
            ("# Agent ", "# Droid "),
            ("## Agent ", "## Droid "),
            ("### Agent ", "### Droid "),
        ]

        for old, new in replacements:
            body = body.replace(old, new)

        return body

    def _transform_tools_for_factory(self, tools: Any) -> Any:
        """Normalize tool names in frontmatter for Factory.

        Factory validates the `tools:` list strictly; invalid entries cause the
        droid to be rejected during load.

        Factory tool categories (can be used as shorthand):
        - read-only: Read, LS, Grep, Glob
        - edit: Create, Edit, ApplyPatch
        - execute: Execute
        - web: WebSearch, FetchUrl

        NOTE: TodoWrite is automatically included for all droids.
        """
        if not isinstance(tools, list):
            # Could be a category string like "read-only"
            return tools

        normalized: List[Any] = []
        for tool in tools:
            if not isinstance(tool, str):
                normalized.append(tool)
                continue

            # Skip tools that droids cannot use
            if tool in self._FACTORY_INVALID_TOOLS:
                continue

            # Map tool names to Factory equivalents
            mapped = self._FACTORY_TOOL_NAME_MAP.get(tool, tool)
            if mapped not in normalized:  # Avoid duplicates
                normalized.append(mapped)

        return normalized if normalized else None  # Return None to enable all tools

    def _replace_factory_tool_references(self, text: str) -> str:
        """Replace tool references in content so installed droids' instructions match Factory."""
        result = text
        for old, new in self._FACTORY_TOOL_NAME_MAP.items():
            result = result.replace(old, new)
        return result

    def _replace_agent_references(self, text: str) -> str:
        """
        Replace agent references with droid references.

        This function performs selective replacement to avoid replacing
        "agent" in unrelated contexts like "user agent", URLs, or code blocks.

        Args:
            text: Text containing agent references

        Returns:
            Text with droid references
        """
        # Protect code blocks, inline code, and URLs from replacement
        protected_regions: List[Tuple[int, int]] = []

        patterns = [
            r"```[\s\S]*?```",  # fenced code blocks
            r"`[^`]+`",  # inline code
            r"https?://[^\s)]+|www\.[^\s)]+",  # URLs
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, text):
                protected_regions.append((match.start(), match.end()))

        if protected_regions:
            protected_regions.sort()
            merged: List[List[int]] = []
            for start, end in protected_regions:
                if not merged or start > merged[-1][1]:
                    merged.append([start, end])
                else:
                    merged[-1][1] = max(merged[-1][1], end)

            placeholders: List[str] = []
            parts: List[str] = []
            last = 0
            for i, (start, end) in enumerate(merged):
                parts.append(text[last:start])
                placeholders.append(text[start:end])
                parts.append(f"\x00RING_PROTECTED_{i}\x00")
                last = end
            parts.append(text[last:])
            masked = "".join(parts)
        else:
            placeholders = []
            masked = text

        # Ring-specific context patterns
        # NOTE: Factory droid names use hyphens, not colons (colons reserved for custom: prefix)
        ring_contexts = [
            # Task tool subagent_type references: ring-plugin:name -> ring-plugin-name
            (r'subagent_type["\s]*[:=]["\s]*["\']?ring-([^:]+):([^"\'>\s]+)', r'subagent_type="\1-\2'),
            (r'"ring-([^:]+):([^"]+)"', r'"ring-\1-\2"'),
            (r"'ring-([^:]+):([^']+)'", r"'ring-\1-\2'"),
            # Tool references with -agent suffix
            (r'"ring:([^"]*)-agent"', r'"ring-\1-droid"'),
            (r"'ring:([^']*)-agent'", r"'ring-\1-droid'"),
            # Don't rename subagent_type field name - Factory Task tool uses it
            # Only transform subagent -> subdroid in prose
            (r'\bsubagent\b(?!_type)', 'subdroid'),
            (r'\bSubagent\b(?!_type)', 'Subdroid'),
        ]

        result = masked
        for pattern, replacement in ring_contexts:
            result = re.sub(pattern, replacement, result)

        # General agent terminology (with exclusions)
        general_replacements = [
            # Skip "user agent" and similar patterns
            (r'\b(?<!user\s)(?<!User\s)(?<!USER\s)agent\b(?!\s+string)(?!\s+header)', 'droid'),
            (r'\b(?<!user\s)(?<!User\s)(?<!USER\s)Agent\b(?!\s+string)(?!\s+header)', 'Droid'),
            (r'\bAGENT\b(?!\s+STRING)(?!\s+HEADER)', 'DROID'),
            (r'\b(?<!user\s)(?<!User\s)(?<!USER\s)agents\b(?!\s+strings)(?!\s+headers)', 'droids'),
            (r'\b(?<!user\s)(?<!User\s)(?<!USER\s)Agents\b(?!\s+strings)(?!\s+headers)', 'Droids'),
            (r'\bAGENTS\b(?!\s+STRINGS)(?!\s+HEADERS)', 'DROIDS'),
        ]

        for pattern, replacement in general_replacements:
            result = re.sub(pattern, replacement, result)

        # Restore protected regions
        for i, original in enumerate(placeholders):
            result = result.replace(f"\x00RING_PROTECTED_{i}\x00", original)

        return result

    def get_target_filename(self, source_filename: str, component_type: str) -> str:
        """
        Get the target filename for a component in Factory AI.

        Args:
            source_filename: Original filename
            component_type: Type of component

        Returns:
            Target filename, with agent->droid renaming if applicable
        """
        filename = super().get_target_filename(source_filename, component_type)

        # Remove -agent suffix (Factory uses the name field, not filename suffix)
        if component_type == "agent":
            filename = re.sub(r'-agent\.md$', '.md', filename)
            filename = re.sub(r'_agent\.md$', '.md', filename)

        return filename

    def requires_flat_components(self, component_type: str) -> bool:
        """
        Check if Factory requires flat directory structure for a component type.

        Factory/Droid only scans top-level .md files in:
        - ~/.factory/droids/ (agents)
        - ~/.factory/commands/ (commands)
        
        Skills use ~/.factory/skills/<name>/SKILL.md structure.

        Args:
            component_type: Type of component (agents, commands, skills, hooks)

        Returns:
            True for agents and commands since Factory requires flat structure
        """
        # Factory scans droids and commands as flat lists at top-level.
        # Commands: "Commands must live at the top level of the commands directory.
        #           Nested folders are ignored today."
        # Skills: expects skills/<name>/SKILL.md structure.
        return component_type in {"agents", "commands", "skills"}

    def get_flat_filename(self, source_filename: str, component_type: str, plugin_name: str) -> str:
        """
        Get a flattened filename with plugin prefix for Factory.

        Factory requires droids to be in top-level ~/.factory/droids/ directory.
        When installing multiple plugins, we prefix filenames to avoid collisions.

        Args:
            source_filename: Original filename
            component_type: Type of component (agent, command, skill)
            plugin_name: Name of the plugin this component belongs to

        Returns:
            Filename with plugin prefix
            (e.g., "code-reviewer.md" from "default" plugin -> "ring-default-code-reviewer.md")
        """
        from pathlib import Path

        source_path = Path(source_filename)
        stem = source_path.stem

        # For agents/droids, remove -agent suffix and add prefix (no -droid suffix needed)
        # Factory expects filename to match the name field exactly
        if component_type == "agent":
            stem = re.sub(r'-agent$', '', stem)
            stem = re.sub(r'_agent$', '', stem)
            return f"ring-{plugin_name}-{stem}.md"

        # For other component types, just add prefix
        return f"ring-{plugin_name}-{stem}{source_path.suffix}"
