# Ring for OpenCode

OpenCode platform integration for the Ring skills library. This directory contains the runtime plugin and installer that brings Ring's skills, agents, and commands to [OpenCode](https://github.com/ohmyopencode/opencode).

## Architecture

```
platforms/opencode/
├── installer.sh          # Installer script (reads from Ring monorepo)
├── plugin/               # TypeScript runtime plugin (RingUnifiedPlugin)
│   ├── config/           # Configuration handler and schema
│   ├── hooks/            # Session-start, context-injection hooks
│   ├── lifecycle/        # Event routing
│   ├── loaders/          # Agent, skill, command loaders
│   ├── tools/            # Custom Ring tools
│   └── utils/            # State management
├── prompts/              # Prompt templates (session-start, context-injection)
├── standards/            # Coding standards (from dev-team/docs/standards/)
├── templates/            # Project templates
├── src/                  # CLI (doctor, config-manager)
├── ring.jsonc            # Default Ring configuration
└── ring-config.schema.json  # JSON schema for ring.jsonc
```

## How It Works

The installer reads skills, agents, and commands directly from the Ring monorepo's canonical directories (`default/`, `dev-team/`, `pm-team/`, etc.) and applies transformations for OpenCode compatibility:

1. **Agent transform**: `type` → `mode`, strip unsupported frontmatter (version, output_schema), normalize tool names
2. **Skill transform**: Keep `name` and `description` in frontmatter, normalize tool references in body
3. **Command transform**: Strip `argument-hint` (unsupported), normalize tool references
4. **Hooks**: Not installed (OpenCode uses plugin-based hooks incompatible with Ring's file-based hooks)

After transformation, files are installed to `~/.config/opencode/`:
- `agent/*.md` — Agents (35 from 6 Ring plugins)
- `skill/*/SKILL.md` — Skills (86 from 6 Ring plugins)
- `command/*.md` — Commands (33 from 6 Ring plugins)
- `skill/shared-patterns/*.md` — Shared patterns (merged from all plugins)

## Installation

```bash
# From the Ring monorepo root:
./platforms/opencode/installer.sh

# Or with custom config dir:
OPENCODE_CONFIG_DIR=~/.config/opencode ./platforms/opencode/installer.sh
```

## Configuration

User config lives at `~/.config/opencode/ring/config.jsonc`. Use it to disable specific agents, skills, commands, or hooks:

```jsonc
{
  "disabled_agents": ["finops-analyzer"],
  "disabled_skills": ["regulatory-templates"],
  "disabled_commands": []
}
```

## Key Differences from Claude Code

| Feature | Claude Code | OpenCode |
|---------|------------|----------|
| Directory names | Plural (`agents/`, `skills/`) | Singular (`agent/`, `skill/`) |
| Tool names | Capitalized (`Bash`, `Read`) | Lowercase (`bash`, `read`) |
| Hooks | File-based (JSON + scripts) | Plugin-based (TypeScript) |
| Agent type field | `type: reviewer` | `mode: subagent` |
| Argument hints | `argument-hint: "[files]"` | Not supported |

## Previously: ring-for-opencode

This was previously a separate repository (`LerianStudio/ring-for-opencode`). It was consolidated into the Ring monorepo to eliminate content drift and sync overhead. The runtime plugin and installer are maintained here; skills, agents, and commands come from the Ring monorepo's canonical sources.
