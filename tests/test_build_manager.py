import tempfile
import yaml
import os
from pathlib import Path
import pytest
from unittest.mock import patch

from composor import build_manager


def test_build_creates_env_and_report(tmp_path):
    # Fake config
    config_path = tmp_path / "apps.yaml"
    config_data = {
        "apps": [
            {"name": "app1", "repo": "https://fake.repo/app1.git", "path": None, "ref": "main",
             "build_cmd": "echo build_app1"}
        ]
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    env_dir = tmp_path / "envs"
    # Mock run_cmd to avoid running actual git/docker
    with patch("composor.utils.git.run_cmd") as mock_run, \
        patch("composor.build_manager.run_cmd") as mock_run2:
        mock_run.return_value = "git-hash-123"
        mock_run2.return_value = ""

        build_manager.main([
            "--config", str(config_path),
            "--base-dir", str(tmp_path),
            "--env-dir", str(env_dir),
        ])
        clone_calls = [
            c for c in mock_run2.call_args_list
            if c.args and isinstance(c.args[0], list) and "docker" in c.args[0] and "build" in c.args[0]
        ]
        assert len(clone_calls) == 1 # build should be performed

    # Check env file
    env_files = list(env_dir.glob("*.env"))
    assert len(env_files) == 1
    env_content = env_files[0].read_text()
    assert "APP1_IMAGE" in env_content

    # Check report file
    report_files = list(env_dir.glob("*.yaml"))
    assert len(report_files) == 1
    report_content = yaml.safe_load(report_files[0].read_text())
    assert "apps" in report_content
    assert report_content["apps"][0]["name"] == "app1"


def test_build_skipped(tmp_path):
    # Fake config
    config_path = tmp_path / "apps.yaml"
    config_data = {
        "apps": [
            {"name": "app1", "repo": "https://fake.repo/app1.git", "path": None, "ref": "main",
             "build_cmd": "echo build_app1"}
        ]
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    env_dir = tmp_path / "envs"
    # Mock run_cmd to avoid running actual git/docker
    with patch("composor.utils.git.run_cmd") as mock_run, \
        patch("composor.build_manager.run_cmd") as mock_run2:
        mock_run.return_value = "git-hash-123"
        mock_run2.return_value = "git-hash-123"

        build_manager.main([
            "--config", str(config_path),
            "--base-dir", str(tmp_path),
            "--env-dir", str(env_dir),
        ])
        print(f"{mock_run2.call_args_list}")
        clone_calls = [
            c for c in mock_run2.call_args_list
            if c.args and isinstance(c.args[0], list) and "docker" in c.args[0] and "build" in c.args[0]
        ]
        assert len(clone_calls) == 0 # build should be skipped


def test_build_creates_env_and_report_dry(tmp_path):
    # Fake config
    config_path = tmp_path / "apps.yaml"
    config_data = {
        "apps": [
            {"name": "app1", "repo": "https://fake.repo/app1.git", "path": None, "ref": "main",
             "build_cmd": "echo build_app1"}
        ]
    }
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    env_dir = tmp_path / "envs"
    # Mock run_cmd to avoid running actual git/docker
    with patch("composor.utils.git.run_cmd") as mock_run:
        mock_run.return_value = "git-hash-123"

        build_manager.main([
            "--config", str(config_path),
            "--base-dir", str(tmp_path),
            "--env-dir", str(env_dir),
            "--dry"
        ])

    env_files = list(env_dir.glob("*.env"))
    assert len(env_files) == 0

    # Check report file
    report_files = list(env_dir.glob("*.yaml"))
    assert len(report_files) == 0

def test_main_calls_git_clone(tmp_path):
    # Prepare a temporary apps.yaml
    config_path = tmp_path / "apps.yaml"
    apps_config = {
        "apps": [
            {"name": "app1", "repo": "https://github.com/example/repo.git", "path": None, "ref": "main",
             "build_cmd": "echo build_app1"}
        ]
    }

    config_path.write_text(yaml.safe_dump(apps_config))

    env_dir = tmp_path / "envs"
    env_dir.mkdir()

    with patch("composor.utils.git.run_cmd") as mock_run:
        # call main with arguments
        build_manager.main([
            "--config", str(config_path),
            "--base-dir", str(tmp_path),
            "--env-dir", str(env_dir),
            "--dry"  # optional, to avoid real builds
        ])

        # Check that git clone was attempted
        clone_calls = [
            c for c in mock_run.call_args_list
            if c.args and isinstance(c.args[0], list) and "git" in c.args[0] and "clone" in c.args[0]
        ]
        assert len(clone_calls) == 1
        assert "https://github.com/example/repo.git" in clone_calls[0].args[0]