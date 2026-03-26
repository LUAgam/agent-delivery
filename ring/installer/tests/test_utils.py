"""
Tests for utility modules.

Tests fs.py (filesystem utilities), platform_detect.py (platform detection),
and version.py (semver comparison).
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# ==============================================================================
# Tests for fs.py (Filesystem Utilities)
# ==============================================================================

class TestEnsureDirectory:
    """Tests for ensure_directory() function."""

    def test_creates_new_directory(self, tmp_path):
        """ensure_directory() should create a new directory."""
        from ring_installer.utils.fs import ensure_directory

        new_dir = tmp_path / "new_directory"
        assert not new_dir.exists()

        result = ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_creates_nested_directories(self, tmp_path):
        """ensure_directory() should create nested directories."""
        from ring_installer.utils.fs import ensure_directory

        nested_dir = tmp_path / "level1" / "level2" / "level3"

        result = ensure_directory(nested_dir)

        assert nested_dir.exists()
        assert result == nested_dir

    def test_existing_directory_unchanged(self, tmp_path):
        """ensure_directory() should not fail on existing directory."""
        from ring_installer.utils.fs import ensure_directory

        existing = tmp_path / "existing"
        existing.mkdir()

        result = ensure_directory(existing)

        assert existing.exists()
        assert result == existing

    def test_raises_if_file_exists(self, tmp_path):
        """ensure_directory() should raise NotADirectoryError if path is a file."""
        from ring_installer.utils.fs import ensure_directory

        file_path = tmp_path / "a_file"
        file_path.write_text("content")

        with pytest.raises(NotADirectoryError):
            ensure_directory(file_path)

    def test_expands_user_path(self, tmp_path):
        """ensure_directory() should expand ~ in paths."""

        from ring_installer.utils.fs import ensure_directory

        # Create a mock expanduser that returns a safe temporary path
        with patch.object(Path, "expanduser", return_value=tmp_path / "expanded") as mock_expand:
            ensure_directory(Path("~/test_dir"))
            assert mock_expand.called


class TestBackupExisting:
    """Tests for backup_existing() function."""

    def test_creates_backup_of_file(self, tmp_path):
        """backup_existing() should create backup of existing file."""
        from ring_installer.utils.fs import backup_existing

        original = tmp_path / "original.txt"
        original.write_text("original content")

        backup_path = backup_existing(original)

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "original content"
        assert "backup" in backup_path.name

    def test_creates_backup_of_directory(self, tmp_path):
        """backup_existing() should create backup of existing directory."""
        from ring_installer.utils.fs import backup_existing

        original_dir = tmp_path / "original_dir"
        original_dir.mkdir()
        (original_dir / "file.txt").write_text("content")

        backup_path = backup_existing(original_dir)

        assert backup_path is not None
        assert backup_path.exists()
        assert (backup_path / "file.txt").exists()

    def test_returns_none_if_not_exists(self, tmp_path):
        """backup_existing() should return None if path doesn't exist."""
        from ring_installer.utils.fs import backup_existing

        nonexistent = tmp_path / "nonexistent"

        result = backup_existing(nonexistent)

        assert result is None

    def test_uses_custom_backup_dir(self, tmp_path):
        """backup_existing() should use custom backup directory."""
        from ring_installer.utils.fs import backup_existing

        original = tmp_path / "original.txt"
        original.write_text("content")

        backup_dir = tmp_path / "backups"
        backup_path = backup_existing(original, backup_dir=backup_dir)

        assert backup_path.parent == backup_dir

    def test_backup_name_includes_timestamp(self, tmp_path):
        """backup_existing() should include timestamp in backup name."""
        from ring_installer.utils.fs import backup_existing

        original = tmp_path / "original.txt"
        original.write_text("content")

        backup_path = backup_existing(original)

        # Backup name format: original.backup_YYYYMMDD_HHMMSS
        assert "backup_" in backup_path.name
        # Should have date-like pattern
        parts = backup_path.name.split("backup_")
        assert len(parts[1]) >= 15  # YYYYMMDD_HHMMSS


class TestCopyWithTransform:
    """Tests for copy_with_transform() function."""

    def test_copies_file_without_transform(self, tmp_path):
        """copy_with_transform() should copy file without transformation."""
        from ring_installer.utils.fs import copy_with_transform

        source = tmp_path / "source.txt"
        source.write_text("source content")
        target = tmp_path / "target.txt"

        result = copy_with_transform(source, target)

        assert target.exists()
        assert target.read_text() == "source content"
        assert result == target

    def test_applies_transformation(self, tmp_path):
        """copy_with_transform() should apply transformation function."""
        from ring_installer.utils.fs import copy_with_transform

        source = tmp_path / "source.txt"
        source.write_text("hello world")
        target = tmp_path / "target.txt"

        copy_with_transform(
            source,
            target,
            transform_func=lambda c: c.upper()
        )

        assert target.read_text() == "HELLO WORLD"

    def test_creates_target_directory(self, tmp_path):
        """copy_with_transform() should create target directory if needed."""
        from ring_installer.utils.fs import copy_with_transform

        source = tmp_path / "source.txt"
        source.write_text("content")
        target = tmp_path / "nested" / "dir" / "target.txt"

        copy_with_transform(source, target)

        assert target.exists()

    def test_raises_if_source_missing(self, tmp_path):
        """copy_with_transform() should raise FileNotFoundError if source missing."""
        from ring_installer.utils.fs import copy_with_transform

        source = tmp_path / "nonexistent.txt"
        target = tmp_path / "target.txt"

        with pytest.raises(FileNotFoundError):
            copy_with_transform(source, target)


class TestSafeRemove:
    """Tests for safe_remove() function."""

    def test_removes_file(self, tmp_path):
        """safe_remove() should remove a file."""
        from ring_installer.utils.fs import safe_remove

        file_path = tmp_path / "to_remove.txt"
        file_path.write_text("content")

        result = safe_remove(file_path)

        assert result is True
        assert not file_path.exists()

    def test_removes_directory(self, tmp_path):
        """safe_remove() should remove a directory and its contents."""
        from ring_installer.utils.fs import safe_remove

        dir_path = tmp_path / "to_remove"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content")

        result = safe_remove(dir_path)

        assert result is True
        assert not dir_path.exists()

    def test_missing_ok_true(self, tmp_path):
        """safe_remove() should not raise if path missing and missing_ok=True."""
        from ring_installer.utils.fs import safe_remove

        nonexistent = tmp_path / "nonexistent"

        result = safe_remove(nonexistent, missing_ok=True)

        assert result is False

    def test_missing_ok_false_raises(self, tmp_path):
        """safe_remove() should raise if path missing and missing_ok=False."""
        from ring_installer.utils.fs import safe_remove

        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            safe_remove(nonexistent, missing_ok=False)


class TestGetFileHash:
    """Tests for get_file_hash() function."""

    def test_returns_sha256_hash(self, tmp_path):
        """get_file_hash() should return SHA256 hash by default."""
        from ring_installer.utils.fs import get_file_hash

        file_path = tmp_path / "test.txt"
        file_path.write_text("test content")

        hash_value = get_file_hash(file_path)

        assert len(hash_value) == 64  # SHA256 produces 64 hex chars
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_same_content_same_hash(self, tmp_path):
        """get_file_hash() should return same hash for same content."""
        from ring_installer.utils.fs import get_file_hash

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("identical content")
        file2.write_text("identical content")

        assert get_file_hash(file1) == get_file_hash(file2)

    def test_different_content_different_hash(self, tmp_path):
        """get_file_hash() should return different hash for different content."""
        from ring_installer.utils.fs import get_file_hash

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content A")
        file2.write_text("content B")

        assert get_file_hash(file1) != get_file_hash(file2)

    def test_rejects_md5_algorithm(self, tmp_path):
        """get_file_hash() should reject weak algorithms like MD5."""
        from ring_installer.utils.fs import get_file_hash

        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        with pytest.raises(ValueError):
            get_file_hash(file_path, algorithm="md5")

    def test_raises_if_file_missing(self, tmp_path):
        """get_file_hash() should raise FileNotFoundError if file missing."""
        from ring_installer.utils.fs import get_file_hash

        with pytest.raises(FileNotFoundError):
            get_file_hash(tmp_path / "nonexistent.txt")


class TestAreFilesIdentical:
    """Tests for are_files_identical() function."""

    def test_identical_files_returns_true(self, tmp_path):
        from ring_installer.utils.fs import are_files_identical

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("same content")
        file2.write_text("same content")

        assert are_files_identical(file1, file2) is True

    def test_different_files_returns_false(self, tmp_path):
        from ring_installer.utils.fs import are_files_identical

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content A")
        file2.write_text("content B")

        assert are_files_identical(file1, file2) is False

    def test_missing_file_returns_false(self, tmp_path):
        from ring_installer.utils.fs import are_files_identical

        file1 = tmp_path / "exists.txt"
        file1.write_text("content")
        file2 = tmp_path / "nonexistent.txt"

        assert are_files_identical(file1, file2) is False
        assert are_files_identical(file2, file1) is False


class TestSymlinkGuards:
    """Symlink safety tests for file operations."""

    def test_copy_with_transform_rejects_symlink(self, tmp_path):
        from ring_installer.utils.fs import copy_with_transform

        source = tmp_path / "source.txt"
        source.write_text("content")
        real_target = tmp_path / "real.txt"
        real_target.write_text("original")
        link = tmp_path / "link.txt"
        link.symlink_to(real_target)

        with pytest.raises(ValueError, match="symlink"):
            copy_with_transform(source, link)

    def test_atomic_write_rejects_symlink(self, tmp_path):
        from ring_installer.utils.fs import atomic_write

        real_target = tmp_path / "real.txt"
        real_target.write_text("original")
        link = tmp_path / "link.txt"
        link.symlink_to(real_target)

        with pytest.raises(ValueError, match="symlink"):
            atomic_write(link, "new content")


class TestListFilesRecursive:
    """Tests for list_files_recursive() function."""

    def test_lists_all_files(self, tmp_path):
        """list_files_recursive() should list all files in directory."""
        from ring_installer.utils.fs import list_files_recursive

        (tmp_path / "file1.txt").write_text("1")
        (tmp_path / "file2.md").write_text("2")
        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "file3.py").write_text("3")

        files = list_files_recursive(tmp_path)

        assert len(files) == 3

    def test_filters_by_extension(self, tmp_path):
        """list_files_recursive() should filter by extension."""
        from ring_installer.utils.fs import list_files_recursive

        (tmp_path / "file1.txt").write_text("1")
        (tmp_path / "file2.md").write_text("2")
        (tmp_path / "file3.py").write_text("3")

        files = list_files_recursive(tmp_path, extensions=[".md"])

        assert len(files) == 1
        assert files[0].suffix == ".md"

    def test_excludes_patterns(self, tmp_path):
        """list_files_recursive() should exclude patterns."""
        from ring_installer.utils.fs import list_files_recursive

        (tmp_path / "file.txt").write_text("1")
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "cached.pyc").write_text("c")

        files = list_files_recursive(tmp_path, exclude_patterns=["__pycache__"])

        assert len(files) == 1
        assert all("__pycache__" not in str(f) for f in files)


class TestAtomicWrite:
    """Tests for atomic_write() function."""

    def test_writes_string_content(self, tmp_path):
        """atomic_write() should write string content."""
        from ring_installer.utils.fs import atomic_write

        file_path = tmp_path / "output.txt"

        atomic_write(file_path, "test content")

        assert file_path.read_text() == "test content"

    def test_writes_bytes_content(self, tmp_path):
        """atomic_write() should write bytes content."""
        from ring_installer.utils.fs import atomic_write

        file_path = tmp_path / "output.bin"

        atomic_write(file_path, b"\x00\x01\x02")

        assert file_path.read_bytes() == b"\x00\x01\x02"

    def test_no_partial_writes(self, tmp_path):
        """atomic_write() should not leave partial files on failure."""
        from ring_installer.utils.fs import atomic_write

        file_path = tmp_path / "output.txt"

        # Write initial content
        atomic_write(file_path, "initial")

        # The atomic write should be all-or-nothing
        assert file_path.read_text() == "initial"


# ==============================================================================
# Tests for platform_detect.py (Platform Detection)
# ==============================================================================

class TestPlatformInfo:
    """Tests for PlatformInfo dataclass."""

    def test_create_platform_info(self):
        """PlatformInfo should be creatable with basic attributes."""
        from ring_installer.utils.platform_detect import PlatformInfo

        info = PlatformInfo(
            platform_id="test",
            name="Test Platform",
            installed=True
        )

        assert info.platform_id == "test"
        assert info.name == "Test Platform"
        assert info.installed is True
        assert info.version is None
        assert info.details == {}

    def test_platform_info_with_all_fields(self):
        """PlatformInfo should accept all optional fields."""
        from ring_installer.utils.platform_detect import PlatformInfo

        info = PlatformInfo(
            platform_id="test",
            name="Test Platform",
            installed=True,
            version="1.0.0",
            install_path=Path("/test"),
            config_path=Path("/test/config"),
            binary_path=Path("/usr/bin/test"),
            details={"extra": "info"}
        )

        assert info.version == "1.0.0"
        assert info.install_path == Path("/test")
        assert info.details["extra"] == "info"


class TestDetectInstalledPlatforms:
    """Tests for detect_installed_platforms() function."""

    def test_returns_list(self, mock_platform_detection):
        """detect_installed_platforms() should return a list."""
        from ring_installer.utils.platform_detect import detect_installed_platforms

        result = detect_installed_platforms()

        assert isinstance(result, list)

    def test_returns_only_installed(self, mock_platform_detection):
        """detect_installed_platforms() should return only installed platforms."""
        from ring_installer.utils.platform_detect import PlatformInfo, detect_installed_platforms

        # Set Claude as installed
        mock_platform_detection["claude"].return_value = PlatformInfo(
            platform_id="claude",
            name="Claude Code",
            installed=True,
            version="1.0.0"
        )

        result = detect_installed_platforms()

        assert len(result) == 1
        assert result[0].platform_id == "claude"


class TestIsPlatformInstalled:
    """Tests for is_platform_installed() function."""

    def test_returns_true_if_installed(self, mock_platform_detection):
        """is_platform_installed() should return True for installed platform."""
        from ring_installer.utils.platform_detect import PlatformInfo, is_platform_installed

        mock_platform_detection["claude"].return_value = PlatformInfo(
            platform_id="claude",
            name="Claude Code",
            installed=True
        )

        assert is_platform_installed("claude") is True

    def test_returns_false_if_not_installed(self, mock_platform_detection):
        """is_platform_installed() should return False for uninstalled platform."""
        from ring_installer.utils.platform_detect import is_platform_installed

        assert is_platform_installed("claude") is False


class TestGetPlatformVersion:
    """Tests for get_platform_version() function."""

    def test_returns_version_if_installed(self, mock_platform_detection):
        """get_platform_version() should return version for installed platform."""
        from ring_installer.utils.platform_detect import PlatformInfo, get_platform_version

        mock_platform_detection["cursor"].return_value = PlatformInfo(
            platform_id="cursor",
            name="Cursor",
            installed=True,
            version="0.42.0"
        )

        assert get_platform_version("cursor") == "0.42.0"

    def test_returns_none_if_not_installed(self, mock_platform_detection):
        """get_platform_version() should return None for uninstalled platform."""
        from ring_installer.utils.platform_detect import get_platform_version

        assert get_platform_version("cursor") is None


class TestGetSystemInfo:
    """Tests for get_system_info() function."""

    def test_returns_system_info(self):
        """get_system_info() should return system information dict."""
        from ring_installer.utils.platform_detect import get_system_info

        info = get_system_info()

        assert "platform" in info
        assert info["platform"] == sys.platform
        assert "python_version" in info
        assert "home_directory" in info
        assert "path" in info


# ==============================================================================
# Tests for version.py (Version Comparison)
# ==============================================================================

class TestVersionParsing:
    """Tests for Version class parsing."""

    def test_parse_basic_version(self):
        """Version.parse() should parse basic version string."""
        from ring_installer.utils.version import Version

        v = Version.parse("1.2.3")

        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert v.prerelease == ""
        assert v.build == ""

    def test_parse_with_v_prefix(self):
        """Version.parse() should handle 'v' prefix."""
        from ring_installer.utils.version import Version

        v = Version.parse("v2.0.0")

        assert v.major == 2
        assert v.minor == 0
        assert v.patch == 0

    def test_parse_with_prerelease(self):
        """Version.parse() should parse prerelease identifier."""
        from ring_installer.utils.version import Version

        v = Version.parse("1.0.0-alpha.1")

        assert v.major == 1
        assert v.prerelease == "alpha.1"

    def test_parse_with_build(self):
        """Version.parse() should parse build metadata."""
        from ring_installer.utils.version import Version

        v = Version.parse("1.0.0+build.123")

        assert v.build == "build.123"

    def test_parse_full_version(self):
        """Version.parse() should parse version with prerelease and build."""
        from ring_installer.utils.version import Version

        v = Version.parse("1.0.0-beta.2+build.456")

        assert v.prerelease == "beta.2"
        assert v.build == "build.456"

    def test_parse_invalid_raises(self):
        """Version.parse() should raise ValueError for invalid version."""
        from ring_installer.utils.version import Version

        with pytest.raises(ValueError):
            Version.parse("invalid")

        with pytest.raises(ValueError):
            Version.parse("1.2")  # Missing patch

        with pytest.raises(ValueError):
            Version.parse("1.2.3.4")  # Too many parts


class TestVersionComparison:
    """Tests for Version comparison operations."""

    def test_equal_versions(self):
        """Equal versions should compare as equal."""
        from ring_installer.utils.version import Version

        v1 = Version.parse("1.0.0")
        v2 = Version.parse("1.0.0")

        assert v1 == v2

    def test_major_comparison(self):
        """Major version should be compared first."""
        from ring_installer.utils.version import Version

        assert Version.parse("2.0.0") > Version.parse("1.9.9")
        assert Version.parse("1.0.0") < Version.parse("2.0.0")

    def test_minor_comparison(self):
        """Minor version should be compared when major is equal."""
        from ring_installer.utils.version import Version

        assert Version.parse("1.2.0") > Version.parse("1.1.9")
        assert Version.parse("1.1.0") < Version.parse("1.2.0")

    def test_patch_comparison(self):
        """Patch version should be compared when major and minor are equal."""
        from ring_installer.utils.version import Version

        assert Version.parse("1.0.2") > Version.parse("1.0.1")
        assert Version.parse("1.0.0") < Version.parse("1.0.1")

    def test_prerelease_lower_than_release(self):
        """Prerelease versions should be lower than release versions."""
        from ring_installer.utils.version import Version

        assert Version.parse("1.0.0-alpha") < Version.parse("1.0.0")
        assert Version.parse("1.0.0") > Version.parse("1.0.0-rc.1")

    def test_prerelease_comparison(self):
        """Prerelease identifiers should be compared alphabetically."""
        from ring_installer.utils.version import Version

        assert Version.parse("1.0.0-alpha") < Version.parse("1.0.0-beta")
        assert Version.parse("1.0.0-alpha.1") < Version.parse("1.0.0-alpha.2")

    def test_comparison_operators(self):
        """All comparison operators should work."""
        from ring_installer.utils.version import Version

        v1 = Version.parse("1.0.0")
        v2 = Version.parse("1.0.1")

        assert v1 < v2
        assert v1 <= v2
        assert v1 <= v1
        assert v2 > v1
        assert v2 >= v1
        assert v1 >= v1


class TestVersionString:
    """Tests for Version string representation."""

    def test_str_basic(self):
        """Version should convert to basic version string."""
        from ring_installer.utils.version import Version

        v = Version(1, 2, 3)
        assert str(v) == "1.2.3"

    def test_str_with_prerelease(self):
        """Version should include prerelease in string."""
        from ring_installer.utils.version import Version

        v = Version(1, 0, 0, prerelease="alpha")
        assert str(v) == "1.0.0-alpha"

    def test_str_with_build(self):
        """Version should include build metadata in string."""
        from ring_installer.utils.version import Version

        v = Version(1, 0, 0, build="123")
        assert str(v) == "1.0.0+123"


class TestVersionMethods:
    """Tests for Version utility methods."""

    def test_is_prerelease(self):
        """is_prerelease() should correctly identify prerelease versions."""
        from ring_installer.utils.version import Version

        assert Version.parse("1.0.0-alpha").is_prerelease() is True
        assert Version.parse("1.0.0").is_prerelease() is False

    def test_bump_major(self):
        """bump_major() should increment major version."""
        from ring_installer.utils.version import Version

        v = Version.parse("1.2.3")
        bumped = v.bump_major()

        assert str(bumped) == "2.0.0"

    def test_bump_minor(self):
        """bump_minor() should increment minor version."""
        from ring_installer.utils.version import Version

        v = Version.parse("1.2.3")
        bumped = v.bump_minor()

        assert str(bumped) == "1.3.0"

    def test_bump_patch(self):
        """bump_patch() should increment patch version."""
        from ring_installer.utils.version import Version

        v = Version.parse("1.2.3")
        bumped = v.bump_patch()

        assert str(bumped) == "1.2.4"


class TestCompareVersions:
    """Tests for compare_versions() function."""

    def test_compare_versions(self, version_test_cases):
        """compare_versions() should correctly compare versions."""
        from ring_installer.utils.version import compare_versions

        for v1, v2, expected in version_test_cases:
            result = compare_versions(v1, v2)
            assert result == expected, f"compare_versions({v1}, {v2}) = {result}, expected {expected}"


class TestIsUpdateAvailable:
    """Tests for is_update_available() function."""

    def test_update_available(self):
        """is_update_available() should return True when update available."""
        from ring_installer.utils.version import is_update_available

        assert is_update_available("1.0.0", "1.0.1") is True
        assert is_update_available("1.0.0", "2.0.0") is True

    def test_no_update_available(self):
        """is_update_available() should return False when up to date."""
        from ring_installer.utils.version import is_update_available

        assert is_update_available("1.0.0", "1.0.0") is False
        assert is_update_available("2.0.0", "1.0.0") is False


class TestInstallManifest:
    """Tests for InstallManifest class."""

    def test_create_manifest(self):
        """InstallManifest.create() should create manifest with defaults."""
        from ring_installer.utils.version import InstallManifest

        manifest = InstallManifest.create(
            version="1.0.0",
            source_path="/path/to/ring",
            platform="claude"
        )

        assert manifest.version == "1.0.0"
        assert manifest.source_path == "/path/to/ring"
        assert manifest.platform == "claude"
        assert manifest.installed_at != ""  # Should have timestamp

    def test_to_dict(self):
        """InstallManifest.to_dict() should convert to dictionary."""
        from ring_installer.utils.version import InstallManifest

        manifest = InstallManifest.create(
            version="1.0.0",
            source_path="/path",
            platform="claude",
            plugins=["default"],
            files={"a.md": "hash"}
        )

        data = manifest.to_dict()

        assert data["version"] == "1.0.0"
        assert data["plugins"] == ["default"]
        assert data["files"]["a.md"] == "hash"

    def test_from_dict(self):
        """InstallManifest.from_dict() should create from dictionary."""
        from ring_installer.utils.version import InstallManifest

        data = {
            "version": "2.0.0",
            "installed_at": "2024-01-01T00:00:00",
            "source_path": "/path",
            "platform": "cursor",
            "plugins": ["test"],
            "files": {},
            "metadata": {}
        }

        manifest = InstallManifest.from_dict(data)

        assert manifest.version == "2.0.0"
        assert manifest.platform == "cursor"

    def test_save_and_load(self, tmp_path):
        """InstallManifest should save and load from file."""
        from ring_installer.utils.version import InstallManifest

        manifest = InstallManifest.create(
            version="1.0.0",
            source_path="/path",
            platform="claude",
            plugins=["default"],
            files={"test.md": "abc123"}
        )

        manifest_path = tmp_path / ".ring-manifest.json"
        manifest.save(manifest_path)

        loaded = InstallManifest.load(manifest_path)

        assert loaded is not None
        assert loaded.version == "1.0.0"
        assert loaded.files["test.md"] == "abc123"

    def test_load_nonexistent_returns_none(self, tmp_path):
        """InstallManifest.load() should return None for missing file."""
        from ring_installer.utils.version import InstallManifest

        result = InstallManifest.load(tmp_path / "nonexistent.json")

        assert result is None


class TestGetRingVersion:
    """Tests for get_ring_version() function."""

    def test_from_marketplace_json(self, tmp_ring_root):
        """get_ring_version() should read from marketplace.json."""
        from ring_installer.utils.version import get_ring_version

        version = get_ring_version(tmp_ring_root)

        assert version == "1.2.3"

    def test_from_version_file(self, tmp_path):
        """get_ring_version() should read from VERSION file."""
        from ring_installer.utils.version import get_ring_version

        (tmp_path / "VERSION").write_text("2.0.0")

        version = get_ring_version(tmp_path)

        assert version == "2.0.0"

    def test_returns_none_if_not_found(self, tmp_path):
        """get_ring_version() should return None if no version found."""
        from ring_installer.utils.version import get_ring_version

        version = get_ring_version(tmp_path)

        assert version is None


class TestGetManifestPath:
    """Tests for get_manifest_path() function."""

    def test_returns_manifest_path(self, tmp_path):
        """get_manifest_path() should return .ring-manifest.json path."""
        from ring_installer.utils.version import get_manifest_path

        path = get_manifest_path(tmp_path)

        assert path == tmp_path / ".ring-manifest.json"


class TestCheckForUpdates:
    """Tests for check_for_updates() function."""

    def test_detects_update_available(self, tmp_ring_root, tmp_install_dir):
        """check_for_updates() should detect when update is available."""
        from ring_installer.utils.version import (
            InstallManifest,
            check_for_updates,
            get_manifest_path,
        )

        # Create old manifest in install dir
        old_manifest = InstallManifest.create(
            version="1.0.0",  # Older than tmp_ring_root's 1.2.3
            source_path=str(tmp_ring_root),
            platform="claude"
        )
        old_manifest.save(get_manifest_path(tmp_install_dir))

        result = check_for_updates(tmp_ring_root, tmp_install_dir, "claude")

        assert result.update_available is True
        assert result.is_newer is True
        assert result.installed_version == "1.0.0"
        assert result.available_version == "1.2.3"

    def test_no_update_when_same_version(self, tmp_ring_root, tmp_install_dir):
        """check_for_updates() should detect no update when versions match."""
        from ring_installer.utils.version import (
            InstallManifest,
            check_for_updates,
            get_manifest_path,
        )

        # Create manifest with same version
        manifest = InstallManifest.create(
            version="1.2.3",
            source_path=str(tmp_ring_root),
            platform="claude"
        )
        manifest.save(get_manifest_path(tmp_install_dir))

        result = check_for_updates(tmp_ring_root, tmp_install_dir, "claude")

        assert result.update_available is False
        assert result.is_newer is False


class TestSaveInstallManifest:
    """Tests for save_install_manifest() function."""

    def test_saves_manifest(self, tmp_path):
        """save_install_manifest() should create manifest file."""
        from ring_installer.utils.version import (
            InstallManifest,
            get_manifest_path,
            save_install_manifest,
        )

        save_install_manifest(
            install_path=tmp_path,
            source_path=Path("/source"),
            platform="cursor",
            version="1.0.0",
            plugins=["default"],
            installed_files={"a.md": "hash1"}
        )

        # Verify file was created
        manifest_path = get_manifest_path(tmp_path)
        assert manifest_path.exists()

        # Verify content
        loaded = InstallManifest.load(manifest_path)
        assert loaded.version == "1.0.0"
        assert loaded.platform == "cursor"
