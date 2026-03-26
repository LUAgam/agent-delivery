"""
Tests for content transformers.

Tests SkillTransformer, AgentTransformer, CommandTransformer,
transformer pipeline composition, and factory functions.
"""


import pytest

from ring_installer.transformers import (
    AgentTransformer,
    AgentTransformerFactory,
    BaseTransformer,
    CommandTransformer,
    CommandTransformerFactory,
    FrontmatterTransformer,
    PassthroughTransformer,
    SkillTransformer,
    SkillTransformerFactory,
    TerminologyTransformer,
    TransformContext,
    TransformerPipeline,
    TransformResult,
    create_pipeline,
    get_transformer,
    transform_content,
)

# ==============================================================================
# Tests for TransformContext
# ==============================================================================

class TestTransformContext:
    """Tests for TransformContext dataclass."""

    def test_create_context_minimal(self):
        """TransformContext should be creatable with minimal parameters."""
        context = TransformContext(
            platform="claude",
            component_type="skill"
        )

        assert context.platform == "claude"
        assert context.component_type == "skill"
        assert context.source_path == ""
        assert context.metadata == {}
        assert context.options == {}

    def test_create_context_full(self):
        """TransformContext should accept all parameters."""
        context = TransformContext(
            platform="cursor",
            component_type="agent",
            source_path="/path/to/agent.md",
            metadata={"name": "test-agent"},
            options={"verbose": True}
        )

        assert context.platform == "cursor"
        assert context.component_type == "agent"
        assert context.source_path == "/path/to/agent.md"
        assert context.metadata["name"] == "test-agent"
        assert context.options["verbose"] is True


# ==============================================================================
# Tests for TransformResult
# ==============================================================================

class TestTransformResult:
    """Tests for TransformResult dataclass."""

    def test_create_result_success(self):
        """TransformResult should represent successful transformation."""
        result = TransformResult(
            content="transformed content",
            success=True
        )

        assert result.content == "transformed content"
        assert result.success is True
        assert result.errors == []
        assert result.warnings == []

    def test_create_result_failure(self):
        """TransformResult should represent failed transformation."""
        result = TransformResult(
            content="original content",
            success=False,
            errors=["Error 1", "Error 2"]
        )

        assert result.success is False
        assert len(result.errors) == 2
        assert "Error 1" in result.errors

    def test_create_result_with_metadata(self):
        """TransformResult should store transformation metadata."""
        result = TransformResult(
            content="content",
            success=True,
            metadata={"lines_changed": 5}
        )

        assert result.metadata["lines_changed"] == 5


# ==============================================================================
# Tests for PassthroughTransformer
# ==============================================================================

class TestPassthroughTransformer:
    """Tests for PassthroughTransformer."""

    @pytest.fixture
    def transformer(self):
        """Create a PassthroughTransformer."""
        return PassthroughTransformer()

    @pytest.fixture
    def context(self, transform_context):
        """Create a test context."""
        return transform_context(platform="claude", component_type="skill")

    def test_passthrough_returns_unchanged_content(self, transformer, context):
        """PassthroughTransformer should return content unchanged."""
        content = "Original content with **formatting**."
        result = transformer.transform(content, context)

        assert result.content == content
        assert result.success is True

    def test_passthrough_preserves_frontmatter(self, transformer, context, minimal_skill_content):
        """PassthroughTransformer should preserve YAML frontmatter."""
        result = transformer.transform(minimal_skill_content, context)

        assert result.content == minimal_skill_content
        assert result.content.startswith("---")


# ==============================================================================
# Tests for TerminologyTransformer
# ==============================================================================

class TestTerminologyTransformer:
    """Tests for TerminologyTransformer."""

    @pytest.fixture
    def factory_terminology(self):
        """Return Factory AI terminology mapping."""
        return {
            "agent": "droid",
            "skill": "skill",
            "command": "command"
        }

    @pytest.fixture
    def transformer(self, factory_terminology):
        """Create a TerminologyTransformer with Factory terminology."""
        return TerminologyTransformer(factory_terminology)

    @pytest.fixture
    def context(self, transform_context):
        """Create a test context."""
        return transform_context(platform="factory", component_type="skill")

    def test_replaces_lowercase_terms(self, transformer, context):
        """TerminologyTransformer should replace lowercase terms."""
        content = "The agent handles requests."
        result = transformer.transform(content, context)

        assert "droid" in result.content
        assert "agent" not in result.content

    def test_replaces_titlecase_terms(self, transformer, context):
        """TerminologyTransformer should replace title case terms."""
        content = "Agent Configuration"
        result = transformer.transform(content, context)

        assert "Droid" in result.content

    def test_replaces_uppercase_terms(self, transformer, context):
        """TerminologyTransformer should replace uppercase terms."""
        content = "AGENT SETUP"
        result = transformer.transform(content, context)

        assert "DROID" in result.content

    def test_preserves_unchanged_terms(self, transformer, context):
        """TerminologyTransformer should not change terms not in mapping."""
        content = "The skill handles commands."
        result = transformer.transform(content, context)

        # skill and command should remain unchanged
        assert "skill" in result.content
        assert "commands" in result.content


# ==============================================================================
# Tests for FrontmatterTransformer
# ==============================================================================

class TestFrontmatterTransformer:
    """Tests for FrontmatterTransformer."""

    @pytest.fixture
    def context(self, transform_context):
        """Create a test context."""
        return transform_context(platform="factory", component_type="agent")

    def test_rename_fields(self, context):
        """FrontmatterTransformer should rename fields."""
        transformer = FrontmatterTransformer(
            field_mapping={"agent": "droid", "subagent_type": "subdroid_type"}
        )

        content = """---
name: test
agent: helper
subagent_type: worker
---

Body content
"""
        result = transformer.transform(content, context)

        assert "droid:" in result.content
        assert "subdroid_type:" in result.content
        assert "agent:" not in result.content
        assert "subagent_type:" not in result.content

    def test_remove_fields(self, context):
        """FrontmatterTransformer should remove specified fields."""
        transformer = FrontmatterTransformer(
            remove_fields=["internal_field", "debug"]
        )

        content = """---
name: test
internal_field: value
debug: true
---

Body content
"""
        result = transformer.transform(content, context)

        assert "name:" in result.content
        assert "internal_field" not in result.content
        assert "debug" not in result.content

    def test_add_fields(self, context):
        """FrontmatterTransformer should add new fields."""
        transformer = FrontmatterTransformer(
            add_fields={"type": "droid", "platform": "factory"}
        )

        content = """---
name: test
---

Body content
"""
        result = transformer.transform(content, context)

        assert "type:" in result.content
        assert "platform:" in result.content

    def test_no_frontmatter_passthrough(self, context, content_without_frontmatter):
        """FrontmatterTransformer should pass through content without frontmatter."""
        transformer = FrontmatterTransformer(
            field_mapping={"agent": "droid"}
        )

        result = transformer.transform(content_without_frontmatter, context)

        assert result.content == content_without_frontmatter


# ==============================================================================
# Tests for TransformerPipeline
# ==============================================================================

class TestTransformerPipeline:
    """Tests for TransformerPipeline composition."""

    @pytest.fixture
    def context(self, transform_context):
        """Create a test context."""
        return transform_context(platform="factory", component_type="agent")

    def test_empty_pipeline(self, context):
        """Empty pipeline should return content unchanged."""
        pipeline = TransformerPipeline()

        result = pipeline.transform("test content", context)

        assert result.content == "test content"
        assert result.success is True

    def test_single_transformer_pipeline(self, context):
        """Pipeline with single transformer should work."""
        pipeline = TransformerPipeline([PassthroughTransformer()])

        result = pipeline.transform("test content", context)

        assert result.content == "test content"
        assert result.success is True

    def test_chained_transformers(self, context):
        """Pipeline should chain transformers in order."""
        terminology = {"agent": "droid"}
        frontmatter_mods = {"add_fields": {"platform": "factory"}}

        pipeline = TransformerPipeline()
        pipeline.add(TerminologyTransformer(terminology))
        pipeline.add(FrontmatterTransformer(**frontmatter_mods))

        content = """---
name: test-agent
---

The agent handles requests.
"""
        result = pipeline.transform(content, context)

        assert "droid" in result.content
        assert "platform:" in result.content

    def test_pipeline_add_returns_self(self, context):
        """Pipeline.add() should return self for chaining."""
        pipeline = TransformerPipeline()

        result = pipeline.add(PassthroughTransformer())

        assert result is pipeline

    def test_pipeline_stops_on_failure(self, context):
        """Pipeline should stop when a transformer fails."""

        class FailingTransformer(BaseTransformer):
            def transform(self, content, context):
                return TransformResult(
                    content=content,
                    success=False,
                    errors=["Intentional failure"]
                )

        pipeline = TransformerPipeline([
            FailingTransformer(),
            PassthroughTransformer()  # Should not be called
        ])

        result = pipeline.transform("test", context)

        assert result.success is False
        assert "Intentional failure" in result.errors

    def test_pipeline_aggregates_warnings(self, context):
        """Pipeline should aggregate warnings from all transformers."""

        class WarningTransformer(BaseTransformer):
            def __init__(self, warning):
                super().__init__()
                self.warning = warning

            def transform(self, content, context):
                return TransformResult(
                    content=content,
                    success=True,
                    warnings=[self.warning]
                )

        pipeline = TransformerPipeline([
            WarningTransformer("Warning 1"),
            WarningTransformer("Warning 2")
        ])

        result = pipeline.transform("test", context)

        assert result.success is True
        assert len(result.warnings) == 2

    def test_pipeline_len(self):
        """Pipeline should report correct length."""
        pipeline = TransformerPipeline()
        assert len(pipeline) == 0

        pipeline.add(PassthroughTransformer())
        assert len(pipeline) == 1


# ==============================================================================
# Tests for SkillTransformer
# ==============================================================================

class TestSkillTransformer:
    """Tests for SkillTransformer platform-specific transformations."""

    def test_claude_passthrough(self, sample_skill_content, transform_context):
        """Claude transformer should pass through skill content."""
        transformer = SkillTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="skill")

        result = transformer.transform(sample_skill_content, context)

        assert result.success is True
        # Claude preserves frontmatter
        assert result.content.startswith("---")

    def test_factory_terminology(self, sample_skill_content, transform_context):
        """Factory transformer should replace agent terminology."""
        transformer = SkillTransformerFactory.create("factory")
        context = transform_context(platform="factory", component_type="skill")

        result = transformer.transform(sample_skill_content, context)

        assert result.success is True
        # Factory preserves frontmatter but changes terminology
        assert result.content.startswith("---")

    def test_cursor_skill_format(self, sample_skill_content, transform_context):
        """Cursor transformer should convert to skill format with frontmatter."""
        transformer = SkillTransformerFactory.create("cursor")
        context = transform_context(platform="cursor", component_type="skill")

        result = transformer.transform(sample_skill_content, context)

        assert result.success is True
        assert result.content.startswith("---")
        assert "name:" in result.content
        assert "description:" in result.content
        assert "# " in result.content
        assert "When to Apply" in result.content or "Instructions" in result.content

    def test_cline_prompt_format(self, sample_skill_content, transform_context):
        """Cline transformer should convert to prompt format."""
        transformer = SkillTransformerFactory.create("cline")
        context = transform_context(platform="cline", component_type="skill")

        result = transformer.transform(sample_skill_content, context)

        assert result.success is True
        # Cline removes frontmatter
        assert not result.content.startswith("---")
        # Should have prompt metadata
        assert "<!-- Prompt:" in result.content
        assert "<!-- Type: skill -->" in result.content

    def test_empty_content_fails(self, transform_context):
        """Transformer should fail on empty content."""
        transformer = SkillTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="skill")

        result = transformer.transform("", context)

        assert result.success is False
        assert len(result.errors) > 0

    def test_whitespace_content_fails(self, transform_context):
        """Transformer should fail on whitespace-only content."""
        transformer = SkillTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="skill")

        result = transformer.transform("   \n\t  ", context)

        assert result.success is False


# ==============================================================================
# Tests for AgentTransformer
# ==============================================================================

class TestAgentTransformer:
    """Tests for AgentTransformer platform-specific transformations."""

    def test_claude_passthrough(self, sample_agent_content, transform_context):
        """Claude transformer should pass through agent content."""
        transformer = AgentTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="agent")

        result = transformer.transform(sample_agent_content, context)

        assert result.success is True
        assert result.content.startswith("---")

    def test_factory_droid_conversion(self, sample_agent_content, transform_context):
        """Factory transformer should convert agent to droid."""
        transformer = AgentTransformerFactory.create("factory")
        context = transform_context(platform="factory", component_type="agent")

        result = transformer.transform(sample_agent_content, context)

        assert result.success is True
        # Should contain droid terminology
        assert "droid" in result.content.lower() or "Droid" in result.content

    def test_cursor_agent_format(self, sample_agent_content, transform_context):
        """Cursor transformer should convert agent to Cursor agent format with frontmatter."""
        transformer = AgentTransformerFactory.create("cursor")
        context = transform_context(platform="cursor", component_type="agent")

        result = transformer.transform(sample_agent_content, context)

        assert result.success is True
        assert result.content.startswith("---")
        assert "name:" in result.content
        assert "description:" in result.content

    def test_cline_prompt_format(self, sample_agent_content, transform_context):
        """Cline transformer should convert agent to prompt."""
        transformer = AgentTransformerFactory.create("cline")
        context = transform_context(platform="cline", component_type="agent")

        result = transformer.transform(sample_agent_content, context)

        assert result.success is True
        assert "<!-- Prompt:" in result.content
        assert "<!-- Type: agent -->" in result.content
        assert "Role" in result.content or "Behavior" in result.content


# ==============================================================================
# Tests for CommandTransformer
# ==============================================================================

class TestCommandTransformer:
    """Tests for CommandTransformer platform-specific transformations."""

    def test_claude_passthrough(self, sample_command_content, transform_context):
        """Claude transformer should pass through command content."""
        transformer = CommandTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="command")

        result = transformer.transform(sample_command_content, context)

        assert result.success is True
        assert result.content.startswith("---")

    def test_factory_preserves_command_with_droid_refs(self, sample_command_content, transform_context):
        """Factory transformer should preserve command format with droid terminology."""
        transformer = CommandTransformerFactory.create("factory")
        context = transform_context(platform="factory", component_type="command")

        result = transformer.transform(sample_command_content, context)

        assert result.success is True

    def test_cursor_command_format(self, sample_command_content, transform_context):
        """Cursor transformer should convert command to plain markdown (no frontmatter)."""
        transformer = CommandTransformerFactory.create("cursor")
        context = transform_context(platform="cursor", component_type="command")

        result = transformer.transform(sample_command_content, context)

        assert result.success is True
        assert not result.content.startswith("---")
        assert "Parameters" in result.content
        assert "Steps" in result.content

    def test_cline_prompt_format(self, sample_command_content, transform_context):
        """Cline transformer should convert command to action prompt."""
        transformer = CommandTransformerFactory.create("cline")
        context = transform_context(platform="cline", component_type="command")

        result = transformer.transform(sample_command_content, context)

        assert result.success is True
        assert "<!-- Prompt:" in result.content
        assert "<!-- Type: command -->" in result.content
        assert "Parameters" in result.content
        assert "Steps" in result.content


# ==============================================================================
# Tests for get_transformer() Factory
# ==============================================================================

class TestGetTransformer:
    """Tests for get_transformer() factory function."""

    @pytest.mark.parametrize("platform", ["claude", "factory", "cursor", "cline"])
    def test_get_skill_transformer(self, platform):
        """get_transformer() should return skill transformer for each platform."""
        transformer = get_transformer(platform, "skill")
        assert isinstance(transformer, SkillTransformer)

    @pytest.mark.parametrize("platform", ["claude", "factory", "cursor", "cline"])
    def test_get_agent_transformer(self, platform):
        """get_transformer() should return agent transformer for each platform."""
        transformer = get_transformer(platform, "agent")
        assert isinstance(transformer, AgentTransformer)

    @pytest.mark.parametrize("platform", ["claude", "factory", "cursor", "cline"])
    def test_get_command_transformer(self, platform):
        """get_transformer() should return command transformer for each platform."""
        transformer = get_transformer(platform, "command")
        assert isinstance(transformer, CommandTransformer)

    def test_get_transformer_handles_plural_component_type(self):
        """get_transformer() should handle plural component types."""
        # 'skills' should work same as 'skill'
        transformer = get_transformer("claude", "skills")
        assert isinstance(transformer, SkillTransformer)

        transformer = get_transformer("claude", "agents")
        assert isinstance(transformer, AgentTransformer)

    def test_get_transformer_unsupported_platform_raises(self):
        """get_transformer() should raise ValueError for unsupported platform."""
        with pytest.raises(ValueError) as exc_info:
            get_transformer("unknown", "skill")

        assert "Unsupported platform" in str(exc_info.value)

    def test_get_transformer_unsupported_component_raises(self):
        """get_transformer() should raise ValueError for unsupported component."""
        with pytest.raises(ValueError) as exc_info:
            get_transformer("claude", "unknown")

        assert "Unsupported component type" in str(exc_info.value)


# ==============================================================================
# Tests for transform_content() Convenience Function
# ==============================================================================

class TestTransformContent:
    """Tests for transform_content() convenience function."""

    def test_transform_skill(self, sample_skill_content):
        """transform_content() should transform skill content."""
        result = transform_content(
            content=sample_skill_content,
            platform="cursor",
            component_type="skill"
        )

        assert result.success is True
        assert "# " in result.content  # Has title

    def test_transform_with_metadata(self, minimal_skill_content):
        """transform_content() should pass metadata to transformer."""
        result = transform_content(
            content=minimal_skill_content,
            platform="cline",
            component_type="skill",
            metadata={"name": "custom-name"},
            source_path="/path/to/skill.md"
        )

        assert result.success is True
        assert "<!-- Source:" in result.content


# ==============================================================================
# Tests for create_pipeline() Function
# ==============================================================================

class TestCreatePipeline:
    """Tests for create_pipeline() function."""

    def test_create_pipeline_default(self):
        """create_pipeline() should create pipeline with default component types."""
        pipeline = create_pipeline("cursor")

        # Default includes skill, agent, command
        assert len(pipeline) >= 1

    def test_create_pipeline_specific_components(self):
        """create_pipeline() should accept specific component types."""
        pipeline = create_pipeline("cursor", component_types=["skill"])

        assert len(pipeline) == 1


# ==============================================================================
# Parametrized Tests Across All Platforms
# ==============================================================================

@pytest.mark.parametrize("platform", ["claude", "factory", "cursor", "cline"])
class TestAllPlatformTransformers:
    """Tests that apply to all platform transformers."""

    def test_skill_transform_returns_result(self, platform, sample_skill_content, transform_context):
        """All skill transformers should return TransformResult."""
        transformer = SkillTransformerFactory.create(platform)
        context = transform_context(platform=platform, component_type="skill")

        result = transformer.transform(sample_skill_content, context)

        assert isinstance(result, TransformResult)
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    def test_agent_transform_returns_result(self, platform, sample_agent_content, transform_context):
        """All agent transformers should return TransformResult."""
        transformer = AgentTransformerFactory.create(platform)
        context = transform_context(platform=platform, component_type="agent")

        result = transformer.transform(sample_agent_content, context)

        assert isinstance(result, TransformResult)
        assert isinstance(result.content, str)

    def test_command_transform_returns_result(self, platform, sample_command_content, transform_context):
        """All command transformers should return TransformResult."""
        transformer = CommandTransformerFactory.create(platform)
        context = transform_context(platform=platform, component_type="command")

        result = transformer.transform(sample_command_content, context)

        assert isinstance(result, TransformResult)
        assert isinstance(result.content, str)

    def test_preserves_essential_content(self, platform, sample_skill_content, transform_context):
        """Transformers should preserve essential content from body."""
        transformer = SkillTransformerFactory.create(platform)
        context = transform_context(platform=platform, component_type="skill")

        result = transformer.transform(sample_skill_content, context)

        # Core documentation should be preserved (in some form)
        # The word "sample" should appear somewhere
        assert "sample" in result.content.lower() or "Sample" in result.content


# ==============================================================================
# Edge Case Tests
# ==============================================================================

class TestTransformerEdgeCases:
    """Tests for edge cases and error handling."""

    def test_content_without_frontmatter(self, content_without_frontmatter, transform_context):
        """Transformers should handle content without frontmatter."""
        transformer = SkillTransformerFactory.create("cursor")
        context = transform_context(platform="cursor", component_type="skill")

        result = transformer.transform(content_without_frontmatter, context)

        assert result.success is True
        assert len(result.content) > 0

    def test_malformed_frontmatter(self, content_with_invalid_frontmatter, transform_context):
        """Transformers should handle malformed frontmatter gracefully."""
        transformer = SkillTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="skill")

        # Should not raise an exception
        result = transformer.transform(content_with_invalid_frontmatter, context)

        # Result depends on implementation; it may pass or fail but shouldn't crash
        assert isinstance(result, TransformResult)

    def test_unicode_content(self, transform_context):
        """Transformers should handle unicode content."""
        content = """---
name: unicode-test
description: Test with unicode characters
---

# Unicode Test

This content has unicode: , ,
Japanese:
Emoji:
"""
        transformer = SkillTransformerFactory.create("cursor")
        context = transform_context(platform="cursor", component_type="skill")

        result = transformer.transform(content, context)

        assert result.success is True
        # Unicode should be preserved
        assert "" in result.content or "Unicode" in result.content

    def test_very_long_content(self, transform_context):
        """Transformers should handle very long content."""
        long_body = "This is a long line. " * 1000

        content = f"""---
name: long-content
---

{long_body}
"""
        transformer = SkillTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="skill")

        result = transformer.transform(content, context)

        assert result.success is True
        assert len(result.content) > 10000

    def test_special_yaml_characters(self, transform_context):
        """Transformers should handle special YAML characters."""
        content = """---
name: special-chars
description: "Quotes: 'single' and \"double\""
trigger: |
  - When using: colons
  - Or # hashes
---

Content with special chars: {} [] : #
"""
        transformer = SkillTransformerFactory.create("claude")
        context = transform_context(platform="claude", component_type="skill")

        result = transformer.transform(content, context)

        assert result.success is True
