"""
Ring Installer - Multi-platform AI agent skill installer.

This package provides tools to install Ring skills, agents, and commands
across multiple AI platforms including Claude Code, Factory AI, Cursor, and Cline.
"""

__version__ = "0.1.0"
__author__ = "Lerian Studio"
__license__ = "Apache-2.0"

from ring_installer.adapters import (
    SUPPORTED_PLATFORMS,
    ClaudeAdapter,
    ClineAdapter,
    CursorAdapter,
    FactoryAdapter,
    PlatformAdapter,
    get_adapter,
)
from ring_installer.core import (
    InstallOptions,
    InstallResult,
    InstallTarget,
    SyncResult,
    UpdateCheckResult,
    check_updates,
    install,
    list_installed,
    load_manifest,
    sync_platforms,
    uninstall,
    uninstall_with_manifest,
    update,
    update_with_diff,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core functions
    "InstallTarget",
    "InstallOptions",
    "InstallResult",
    "UpdateCheckResult",
    "SyncResult",
    "install",
    "update",
    "uninstall",
    "load_manifest",
    "check_updates",
    "update_with_diff",
    "sync_platforms",
    "uninstall_with_manifest",
    "list_installed",
    # Adapters
    "PlatformAdapter",
    "ClaudeAdapter",
    "FactoryAdapter",
    "CursorAdapter",
    "ClineAdapter",
    "get_adapter",
    "SUPPORTED_PLATFORMS",
]
