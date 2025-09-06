import os
from pathlib import Path
from unittest.mock import patch

from composor import deploy_manager


env_files = ['env_20250831113433.env', 'env_20250830133324.env']

def setup_env_dir(tmp_path):
    env_dir = Path(tmp_path / "envs")
    os.mkdir(env_dir)
    for file in env_files:
        with open(Path(env_dir, file), "w+") as f:
            f.write('test')
    return env_dir

def test_list_env_correctly(tmp_path, capsys):
    env_dir = setup_env_dir(tmp_path)
    deploy_manager.main([
        "--env-dir", str(env_dir),
        "--list",
    ])
    captured = capsys.readouterr()
    out_list = captured.out.splitlines()
    assert len(out_list) == len(env_files)
    for index, item in enumerate(out_list):
        assert f"{index}: {env_files[index]}" == item

def test_rollback(tmp_path):
    env_dir = setup_env_dir(tmp_path)

    with patch("composor.utils.git.run_cmd") as mock_run, \
                patch("composor.deploy_manager.run_cmd") as mock_run2:
        mock_run.return_value = "git-hash-123"
        mock_run2.return_value = ""

        deploy_manager.main([
            "--env-dir", str(env_dir),
            "--reason", "reason of rollback",
            "--rollback"
        ])
        print(f"{mock_run2.call_args_list}")

        assert str(Path(env_dir, env_files[-1])) in mock_run2.call_args_list[0].args[0]
    assert deploy_manager.get_env_file(env_dir, 0).name == env_files[-1]

def test_rollback2(tmp_path):
    env_dir = setup_env_dir(tmp_path)

    with patch("composor.utils.git.run_cmd") as mock_run, \
                patch("composor.deploy_manager.run_cmd") as mock_run2:
        mock_run.return_value = "git-hash-123"
        mock_run2.return_value = ""

        deploy_manager.main([
            "--env-dir", str(env_dir),
            "--reason", "reason of rollback",
            "--rollback", "2"
        ])

        assert len(mock_run2.call_args_list) == 0
    assert len(list(env_dir.glob("env_*.env"))) == 0
    assert len(list(env_dir.glob("env_*.env.defect"))) == 2
