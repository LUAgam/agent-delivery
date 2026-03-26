# Changelog

All notable changes to deep-project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.2.1] - 2026-02-28

### Fixed
- **Plugin root discovery** — SessionStart hook now injects `DEEP_PLUGIN_ROOT` into Claude's context via `additionalContext`, eliminating slow `find` commands for script discovery. Falls back to filename-based search that works with both hyphen and underscore directory naming (fixes marketplace install path mismatch). ([#3](https://github.com/piercelamb/deep-project/issues/3))

## [0.2.0] - 2026-01-30

### Changed
- **Unified session ID** - Changed `DEEP_PROJECT_SESSION_ID` to shared `DEEP_SESSION_ID`
- **Normalized env var** - Changed `CLAUDE_SESSION_ID` to `DEEP_SESSION_ID` in env file writes and all scripts
- SessionStart hook now checks if `DEEP_SESSION_ID` already matches before outputting
- Prevents duplicate output when multiple deep-* plugins run together

## [0.1.0] - 2025-01-01

### Added
- Initial release
- Project decomposition workflow for breaking down high-level requirements
- Planning unit generation for /deep-plan
- SessionStart hook for session ID capture
