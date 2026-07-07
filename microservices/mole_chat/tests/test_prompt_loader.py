"""Tests for prompt_loader (I-09 coverage)."""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import tempfile
import yaml
from unittest.mock import patch

from app.infrastructure.adapters.prompt_loader import load_prompt, PROMPTS_DIR


@pytest.fixture
def temp_prompt_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("app.infrastructure.adapters.prompt_loader.PROMPTS_DIR", tmpdir):
            yield tmpdir


def test_load_prompt_string(temp_prompt_dir):
    path = os.path.join(temp_prompt_dir, "test.yaml")
    with open(path, "w") as f:
        f.write("Hello world")
    result = load_prompt("test")
    assert result == "Hello world"


def test_load_prompt_dict(temp_prompt_dir):
    path = os.path.join(temp_prompt_dir, "test.yaml")
    with open(path, "w") as f:
        yaml.dump({"system_prompt": "Hello from dict"}, f)
    result = load_prompt("test")
    assert result == "Hello from dict"


def test_load_prompt_not_found(temp_prompt_dir):
    with pytest.raises(FileNotFoundError):
        load_prompt("nonexistent")


def test_load_prompt_empty_dict(temp_prompt_dir):
    path = os.path.join(temp_prompt_dir, "test.yaml")
    with open(path, "w") as f:
        yaml.dump({"other_key": "val"}, f)
    result = load_prompt("test")
    assert result == ""


def test_load_prompt_invalid_yaml(temp_prompt_dir):
    path = os.path.join(temp_prompt_dir, "test.yaml")
    with open(path, "w") as f:
        f.write("{invalid: yaml: broken")
    with pytest.raises(yaml.YAMLError):
        load_prompt("test")
