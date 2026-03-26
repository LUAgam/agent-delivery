"""
Utility modules for Ring installer.
"""

from ring_installer.utils.fs import (
    are_files_identical,
    backup_existing,
    copy_with_transform,
    ensure_directory,
    get_file_hash,
    safe_remove,
)
from ring_installer.utils.platform_detect import (
    detect_installed_platforms,
    get_platform_version,
    is_platform_installed,
)
from ring_installer.utils.version import (
    InstallManifest,
    Version,
    check_for_updates,
    compare_versions,
    get_installed_version,
    get_ring_version,
    is_update_available,
    save_install_manifest,
)

__all__ = [
    # Filesystem utilities
    "copy_with_transform",
    "backup_existing",
    "ensure_directory",
    "safe_remove",
    "get_file_hash",
    "are_files_identical",
    # Platform detection
    "detect_installed_platforms",
    "get_platform_version",
    "is_platform_installed",
    # Version management
    "Version",
    "InstallManifest",
    "compare_versions",
    "is_update_available",
    "get_ring_version",
    "get_installed_version",
    "check_for_updates",
    "save_install_manifest",
]
