"""
Hook content transformer.

Generates and transforms hook configurations for different platforms.
"""

import json
from typing import Any, Dict, List, Optional

from ring_installer.transformers.base import (
    BaseTransformer,
    TransformContext,
    TransformResult,
)


class HookTransformer(BaseTransformer):
    """
    Transformer for Ring hook files.

    Handles transformation of hook configurations:
    - Claude: passthrough (native hooks.json format)
    - Factory: convert to .factory/hooks format
    - Cursor: best-effort conversion or skip
    - Cline: best-effort conversion or skip
    """

    def __init__(self, platform: str):
        """
        Initialize the hook transformer.

        Args:
            platform: Target platform identifier
        """
        super().__init__()
        self.platform = platform

    def transform(self, content: str, context: TransformContext) -> TransformResult:
        """
        Transform hook content for the target platform.

        Args:
            content: Original hook content
            context: Transformation context

        Returns:
            TransformResult with transformed content
        """
        # Determine file type from source path
        source_path = context.source_path or ""
        is_json = source_path.endswith(".json")
        is_script = source_path.endswith(".sh") or source_path.endswith(".py")

        if self.platform == "claude":
            return self._transform_claude(content, context, is_json)
        elif self.platform == "factory":
            return self._transform_factory(content, context, is_json, is_script)
        elif self.platform == "cursor":
            return self._transform_cursor(content, context, is_json, is_script)
        elif self.platform == "cline":
            return self._transform_cline(content, context, is_json, is_script)
        else:
            return TransformResult(content=content, success=True)

    def _transform_claude(
        self,
        content: str,
        context: TransformContext,
        is_json: bool
    ) -> TransformResult:
        """Transform hook for Claude Code (passthrough)."""
        return TransformResult(content=content, success=True)

    def _transform_factory(
        self,
        content: str,
        context: TransformContext,
        is_json: bool,
        is_script: bool
    ) -> TransformResult:
        """
        Transform hook for Factory AI.

        Factory uses a similar hooks concept but with different format.
        """
        if is_json:
            return self._transform_factory_hooks_json(content, context)
        elif is_script:
            return self._transform_factory_script(content, context)

        return TransformResult(content=content, success=True)

    def _transform_factory_hooks_json(
        self,
        content: str,
        context: TransformContext
    ) -> TransformResult:
        """Transform hooks.json to Factory format."""
        try:
            hooks_config = json.loads(content)
        except json.JSONDecodeError as e:
            return TransformResult(
                content=content,
                success=False,
                errors=[f"Invalid JSON: {e}"]
            )

        # Transform hook configuration
        transformed = self._convert_claude_hooks_to_factory(hooks_config)

        # Serialize back to JSON
        output = json.dumps(transformed, indent=2)
        return TransformResult(content=output, success=True)

    def _convert_claude_hooks_to_factory(
        self,
        hooks_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Claude hooks config to Factory format."""
        result: Dict[str, Any] = {
            "version": "1.0",
            "triggers": []
        }

        hooks = hooks_config.get("hooks", [])
        for hook in hooks:
            event = hook.get("event", "")
            command = hook.get("command", "")

            # Map event names
            event_mapping = {
                "SessionStart": "session_start",
                "SessionEnd": "session_end",
                "PreToolUse": "pre_tool",
                "PostToolUse": "post_tool",
                "Stop": "stop",
                "UserPromptSubmit": "prompt_submit",
            }

            factory_event = event_mapping.get(event, event.lower())

            trigger = {
                "event": factory_event,
                "action": command,
            }

            # Copy conditions if present
            if "match_files" in hook:
                trigger["match_files"] = hook["match_files"]
            if "match_tools" in hook:
                trigger["match_tools"] = hook["match_tools"]

            result["triggers"].append(trigger)

        return result

    def _transform_factory_script(
        self,
        content: str,
        context: TransformContext
    ) -> TransformResult:
        """Transform hook script for Factory."""
        # Replace terminology in scripts
        result = content

        replacements = [
            ("agent", "droid"),
            ("AGENT", "DROID"),
            ("Agent", "Droid"),
        ]

        for old, new in replacements:
            result = result.replace(old, new)

        return TransformResult(content=result, success=True)

    def _transform_cursor(
        self,
        content: str,
        context: TransformContext,
        is_json: bool,
        is_script: bool
    ) -> TransformResult:
        """
        Transform hook for Cursor.

        Cursor has limited hook support - generate automation skills
        or skip with warning.
        """
        warnings: List[str] = []

        if is_json:
            # Try to convert to Cursor automation format
            try:
                hooks_config = json.loads(content)
                transformed = self._convert_to_cursor_automation(hooks_config)
                if transformed:
                    output = json.dumps(transformed, indent=2)
                    return TransformResult(
                        content=output,
                        success=True,
                        warnings=["Converted to Cursor automation format (limited support)"]
                    )
            except json.JSONDecodeError:
                pass

            warnings.append("Cursor has limited hook support - some features may not work")
            return TransformResult(content=content, success=True, warnings=warnings)

        elif is_script:
            # Scripts can't be directly used in Cursor
            warnings.append(
                f"Hook script '{context.source_path}' cannot be converted for Cursor - "
                "manual integration may be required"
            )
            return TransformResult(content=content, success=True, warnings=warnings)

        return TransformResult(content=content, success=True)

    def _convert_to_cursor_automation(
        self,
        hooks_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Convert hooks to Cursor automation format if possible."""
        # Cursor's automation is limited - return simplified format
        automations: List[Dict[str, Any]] = []

        hooks = hooks_config.get("hooks", [])
        for hook in hooks:
            event = hook.get("event", "")

            # Only SessionStart maps reasonably to Cursor
            if event == "SessionStart":
                automation = {
                    "trigger": "project_open",
                    "action": "run_rule",
                    "rule": hook.get("command", "").replace("bash ", "")
                }
                automations.append(automation)

        if automations:
            return {"automations": automations}
        return None

    def _transform_cline(
        self,
        content: str,
        context: TransformContext,
        is_json: bool,
        is_script: bool
    ) -> TransformResult:
        """
        Transform hook for Cline.

        Cline has very limited hook support via VS Code settings.
        Generate best-effort conversion with warnings.
        """
        warnings: List[str] = []

        if is_json:
            warnings.append(
                "Cline hooks are managed via VS Code extension settings - "
                "manual configuration may be required"
            )

            try:
                hooks_config = json.loads(content)
                # Generate documentation comments about what hooks do
                docs = self._generate_cline_hook_docs(hooks_config)
                return TransformResult(
                    content=docs,
                    success=True,
                    warnings=warnings,
                    metadata={"original_config": hooks_config}
                )
            except json.JSONDecodeError:
                pass

        elif is_script:
            warnings.append(
                f"Hook script '{context.source_path}' cannot be used directly in Cline - "
                "consider converting to a prompt"
            )

        return TransformResult(content=content, success=True, warnings=warnings)

    def _generate_cline_hook_docs(self, hooks_config: Dict[str, Any]) -> str:
        """Generate documentation about hooks for Cline users."""
        lines = [
            "# Hook Configuration Reference",
            "",
            "The following hooks are configured in Ring. Cline does not support",
            "automatic hooks, but you can manually trigger these behaviors.",
            "",
        ]

        hooks = hooks_config.get("hooks", [])
        for hook in hooks:
            event = hook.get("event", "Unknown")
            command = hook.get("command", "")

            lines.append(f"## {event}")
            lines.append("")
            lines.append(f"**Original command:** `{command}`")
            lines.append("")

            # Add guidance based on event type
            if event == "SessionStart":
                lines.append("**Cline equivalent:** Run this manually at session start")
            elif event == "PreToolUse":
                lines.append("**Cline equivalent:** Review before tool execution")
            elif event == "PostToolUse":
                lines.append("**Cline equivalent:** Run after tool completion")

            lines.append("")

        return "\n".join(lines)


class HookTransformerFactory:
    """Factory for creating platform-specific hook transformers."""

    @classmethod
    def create(cls, platform: str) -> HookTransformer:
        """
        Create a hook transformer for the specified platform.

        Args:
            platform: Target platform identifier

        Returns:
            Configured HookTransformer
        """
        return HookTransformer(platform=platform)


def generate_hooks_json(
    hooks: List[Dict[str, Any]],
    platform: str = "claude"
) -> str:
    """
    Generate a hooks.json configuration file.

    Args:
        hooks: List of hook configurations
        platform: Target platform

    Returns:
        JSON string of hooks configuration
    """
    config = {
        "hooks": hooks
    }

    return json.dumps(config, indent=2)


def parse_hooks_json(content: str) -> List[Dict[str, Any]]:
    """
    Parse a hooks.json configuration file.

    Args:
        content: JSON content

    Returns:
        List of hook configurations
    """
    try:
        config = json.loads(content)
        return config.get("hooks", [])
    except json.JSONDecodeError:
        return []
