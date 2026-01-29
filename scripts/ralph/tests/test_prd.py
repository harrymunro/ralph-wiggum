#!/usr/bin/env python3
"""Tests for PRD loading and saving functionality.

Tests JSON and YAML format support for PRD files.
"""

import json
import os
import sys
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from v_ralph import (
    get_prd_format,
    load_prd,
    save_prd,
    check_prd_valid_json,
    YAML_AVAILABLE,
)
from shared.errors import PRDNotFoundError


class TestGetPrdFormat:
    """Tests for get_prd_format() function."""

    def test_json_extension(self):
        """Test that .json files are detected as JSON format."""
        assert get_prd_format("prd.json") == "json"
        assert get_prd_format("/path/to/prd.json") == "json"
        assert get_prd_format("./project/prd.json") == "json"

    def test_yaml_extension(self):
        """Test that .yaml files are detected as YAML format."""
        assert get_prd_format("prd.yaml") == "yaml"
        assert get_prd_format("/path/to/prd.yaml") == "yaml"
        assert get_prd_format("./project/prd.yaml") == "yaml"

    def test_yml_extension(self):
        """Test that .yml files are detected as YAML format."""
        assert get_prd_format("prd.yml") == "yaml"
        assert get_prd_format("/path/to/prd.yml") == "yaml"
        assert get_prd_format("./project/prd.yml") == "yaml"

    def test_case_insensitive_extensions(self):
        """Test that extensions are case-insensitive."""
        assert get_prd_format("prd.JSON") == "json"
        assert get_prd_format("prd.YAML") == "yaml"
        assert get_prd_format("prd.YML") == "yaml"
        assert get_prd_format("prd.Yml") == "yaml"

    def test_no_extension_defaults_to_json(self):
        """Test that files without extension default to JSON."""
        assert get_prd_format("prd") == "json"
        assert get_prd_format("/path/to/prd") == "json"

    def test_unknown_extension_defaults_to_json(self):
        """Test that unknown extensions default to JSON."""
        assert get_prd_format("prd.txt") == "json"
        assert get_prd_format("prd.xml") == "json"


class TestLoadPrdJson:
    """Tests for load_prd() with JSON files."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON PRD file."""
        prd_data = {
            "project": "Test Project",
            "userStories": [
                {"id": "US-001", "title": "Test Story", "passes": False}
            ]
        }
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps(prd_data))

        loaded = load_prd(str(prd_file))
        assert loaded == prd_data

    def test_load_json_file_not_found(self, tmp_path):
        """Test that loading a non-existent file raises PRDNotFoundError."""
        with pytest.raises(PRDNotFoundError):
            load_prd(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json(self, tmp_path):
        """Test that loading invalid JSON raises ValueError."""
        prd_file = tmp_path / "prd.json"
        prd_file.write_text("{ invalid json }")

        with pytest.raises(ValueError) as exc_info:
            load_prd(str(prd_file))
        assert "Invalid JSON" in str(exc_info.value)


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
class TestLoadPrdYaml:
    """Tests for load_prd() with YAML files."""

    def test_load_valid_yaml(self, tmp_path):
        """Test loading a valid YAML PRD file."""
        yaml_content = """
project: Test Project
userStories:
  - id: US-001
    title: Test Story
    passes: false
"""
        prd_file = tmp_path / "prd.yaml"
        prd_file.write_text(yaml_content)

        loaded = load_prd(str(prd_file))
        assert loaded["project"] == "Test Project"
        assert len(loaded["userStories"]) == 1
        assert loaded["userStories"][0]["id"] == "US-001"

    def test_load_valid_yml(self, tmp_path):
        """Test loading a valid .yml PRD file."""
        yaml_content = """
project: Test Project
branchName: feature/test
"""
        prd_file = tmp_path / "prd.yml"
        prd_file.write_text(yaml_content)

        loaded = load_prd(str(prd_file))
        assert loaded["project"] == "Test Project"
        assert loaded["branchName"] == "feature/test"

    def test_load_yaml_file_not_found(self, tmp_path):
        """Test that loading a non-existent YAML file raises PRDNotFoundError."""
        with pytest.raises(PRDNotFoundError):
            load_prd(str(tmp_path / "nonexistent.yaml"))

    def test_load_invalid_yaml(self, tmp_path):
        """Test that loading invalid YAML raises ValueError."""
        prd_file = tmp_path / "prd.yaml"
        # Invalid YAML - bad indentation
        prd_file.write_text("project: Test\n  bad:\nindent")

        with pytest.raises(ValueError) as exc_info:
            load_prd(str(prd_file))
        assert "Invalid YAML" in str(exc_info.value)


class TestSavePrdJson:
    """Tests for save_prd() with JSON files."""

    def test_save_valid_json(self, tmp_path):
        """Test saving a PRD to JSON format."""
        prd_data = {
            "project": "Test Project",
            "userStories": [
                {"id": "US-001", "title": "Test Story", "passes": False}
            ]
        }
        prd_file = tmp_path / "prd.json"

        result = save_prd(str(prd_file), prd_data)
        assert result is True

        # Verify the saved content
        saved_content = prd_file.read_text()
        saved_data = json.loads(saved_content)
        assert saved_data == prd_data

    def test_json_file_ends_with_newline(self, tmp_path):
        """Test that saved JSON files end with a newline."""
        prd_data = {"project": "Test"}
        prd_file = tmp_path / "prd.json"

        save_prd(str(prd_file), prd_data)
        content = prd_file.read_text()
        assert content.endswith("\n")


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
class TestSavePrdYaml:
    """Tests for save_prd() with YAML files."""

    def test_save_valid_yaml(self, tmp_path):
        """Test saving a PRD to YAML format."""
        import yaml
        prd_data = {
            "project": "Test Project",
            "userStories": [
                {"id": "US-001", "title": "Test Story", "passes": False}
            ]
        }
        prd_file = tmp_path / "prd.yaml"

        result = save_prd(str(prd_file), prd_data)
        assert result is True

        # Verify the saved content
        saved_content = prd_file.read_text()
        saved_data = yaml.safe_load(saved_content)
        assert saved_data == prd_data

    def test_save_yml_format(self, tmp_path):
        """Test that .yml extension saves as YAML."""
        import yaml
        prd_data = {"project": "Test"}
        prd_file = tmp_path / "prd.yml"

        result = save_prd(str(prd_file), prd_data)
        assert result is True

        # Verify it's valid YAML
        saved_content = prd_file.read_text()
        saved_data = yaml.safe_load(saved_content)
        assert saved_data == prd_data

    def test_yaml_preserves_format_on_roundtrip(self, tmp_path):
        """Test that YAML files stay YAML after load/save cycle."""
        import yaml
        original_content = """project: Test Project
branchName: feature/test
userStories:
  - id: US-001
    title: First Story
    passes: false
  - id: US-002
    title: Second Story
    passes: true
"""
        prd_file = tmp_path / "prd.yaml"
        prd_file.write_text(original_content)

        # Load, modify, save
        prd_data = load_prd(str(prd_file))
        prd_data["userStories"][0]["passes"] = True
        save_prd(str(prd_file), prd_data)

        # Verify it's still valid YAML
        saved_content = prd_file.read_text()
        saved_data = yaml.safe_load(saved_content)
        assert saved_data["userStories"][0]["passes"] is True
        assert saved_data["project"] == "Test Project"


class TestCheckPrdValidJson:
    """Tests for check_prd_valid_json() function."""

    def test_valid_json_file(self, tmp_path):
        """Test validation of a valid JSON file."""
        prd_file = tmp_path / "prd.json"
        prd_file.write_text('{"project": "Test"}')

        check, data = check_prd_valid_json(str(prd_file))
        assert check.passed is True
        assert "valid JSON" in check.message
        assert data is not None
        assert data["project"] == "Test"

    def test_invalid_json_file(self, tmp_path):
        """Test validation of an invalid JSON file."""
        prd_file = tmp_path / "prd.json"
        prd_file.write_text("{ invalid }")

        check, data = check_prd_valid_json(str(prd_file))
        assert check.passed is False
        assert "Invalid" in check.message
        assert data is None

    def test_nonexistent_file(self, tmp_path):
        """Test validation of a non-existent file."""
        check, data = check_prd_valid_json(str(tmp_path / "missing.json"))
        assert check.passed is False
        assert "does not exist" in check.message
        assert data is None


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
class TestCheckPrdValidYaml:
    """Tests for check_prd_valid_json() with YAML files."""

    def test_valid_yaml_file(self, tmp_path):
        """Test validation of a valid YAML file."""
        prd_file = tmp_path / "prd.yaml"
        prd_file.write_text("project: Test\n")

        check, data = check_prd_valid_json(str(prd_file))
        assert check.passed is True
        assert "valid YAML" in check.message
        assert data is not None
        assert data["project"] == "Test"

    def test_invalid_yaml_file(self, tmp_path):
        """Test validation of an invalid YAML file."""
        prd_file = tmp_path / "prd.yaml"
        prd_file.write_text("project: [invalid\n")

        check, data = check_prd_valid_json(str(prd_file))
        assert check.passed is False
        assert data is None

    def test_yml_extension_uses_yaml_validation(self, tmp_path):
        """Test that .yml files use YAML validation."""
        prd_file = tmp_path / "prd.yml"
        prd_file.write_text("project: Test\n")

        check, data = check_prd_valid_json(str(prd_file))
        assert check.passed is True
        assert "YAML" in check.name
        assert data["project"] == "Test"


class TestFormatPreservation:
    """Tests for format preservation between load and save."""

    def test_json_stays_json(self, tmp_path):
        """Test that JSON files stay JSON after roundtrip."""
        prd_data = {"project": "Test", "value": 123}
        prd_file = tmp_path / "prd.json"
        prd_file.write_text(json.dumps(prd_data))

        # Load and save
        loaded = load_prd(str(prd_file))
        loaded["value"] = 456
        save_prd(str(prd_file), loaded)

        # Verify it's still JSON
        content = prd_file.read_text()
        parsed = json.loads(content)  # Should not raise
        assert parsed["value"] == 456

    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_yaml_stays_yaml(self, tmp_path):
        """Test that YAML files stay YAML after roundtrip."""
        import yaml
        prd_file = tmp_path / "prd.yaml"
        prd_file.write_text("project: Test\nvalue: 123\n")

        # Load and save
        loaded = load_prd(str(prd_file))
        loaded["value"] = 456
        save_prd(str(prd_file), loaded)

        # Verify it's still valid YAML
        content = prd_file.read_text()
        parsed = yaml.safe_load(content)
        assert parsed["value"] == 456

    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_yml_stays_yaml(self, tmp_path):
        """Test that .yml files stay YAML after roundtrip."""
        import yaml
        prd_file = tmp_path / "prd.yml"
        prd_file.write_text("project: Test\n")

        loaded = load_prd(str(prd_file))
        save_prd(str(prd_file), loaded)

        content = prd_file.read_text()
        parsed = yaml.safe_load(content)
        assert parsed["project"] == "Test"


class TestYamlAvailability:
    """Tests for YAML availability handling."""

    def test_yaml_available_flag_is_set(self):
        """Test that YAML_AVAILABLE flag is properly set."""
        # This test just verifies the flag exists and is a boolean
        assert isinstance(YAML_AVAILABLE, bool)

    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_yaml_can_be_imported(self):
        """Test that yaml module can be imported when available."""
        import yaml
        assert yaml is not None
