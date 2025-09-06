# ----------------------------------------------------------------------
# Copyright (c) 2025 Tomas Krcka <tomas.krcka@industware.cloud>
#
# This file is part of Composor.
# Licensed under the MIT License.
# See the LICENSE file in the project root for full license text.
# ----------------------------------------------------------------------
#!/usr/bin/env python3
import argparse
import logging
import os
import shutil
from pathlib import Path
from typing import Optional, List

import yaml

from composor.utils import run_cmd, get_timestamp

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def check_docker_compose():
    """Check if docker compose or docker-compose is installed."""
    if shutil.which("docker-compose"):
        return "docker-compose"
    elif shutil.which("docker"):
        # Check if "docker compose" is available (newer plugin)
        try:
            run_cmd(["docker", "compose", "version"], capture_output=True, text=True)
            return "docker compose"
        except FileNotFoundError:
            pass
    raise RuntimeError(
        "Neither `docker compose` nor `docker-compose` is installed on this system."
    )


def list_env_files(env_dir: Path) -> List[Path]:
    """Return sorted list of available env files."""
    return sorted(env_dir.glob("env_*.env"), reverse=True)


def update_yaml_report(env_file: Path, reason: str, dry_run: bool):
    timestamp = env_file.stem.replace("env_", "", 1)
    new_name = f"report_{timestamp}.yaml"
    yaml_file = env_file.with_name(new_name)

    if not yaml_file.exists():
        logger.info(f"Not updating report, {yaml_file} does not exist")
        return

    with open(yaml_file, "r") as f:
        data = yaml.safe_load(f)

    if not data and not isinstance(data, dict):
        logger.warning(
            f"Not updating report, {yaml_file} has no data or invalid yaml file"
        )
        return

    data.update({"rollback": {"timestamp": get_timestamp(), "reason": reason}})
    if dry_run:
        logger.info(f"Dry run: writing to {yaml_file}")
        return

    logger.debug(f"Updating {yaml_file}")
    with open(yaml_file, "w") as f:
        yaml.dump(data, f)
    yaml_file.rename(yaml_file.with_suffix(yaml_file.suffix + ".defect"))


def mark_defective(env_file: Path, dry_run: bool):
    """Rename to .env.defect"""
    defective = env_file.with_suffix(env_file.suffix + ".defect")
    if dry_run:
        logger.info(f"Dry run: rename {env_file} to {defective}")
    else:
        env_file.rename(defective)


def get_env_file(
    env_dir: Path,
    index: int,
    file: Optional[str] = None,
    rollback: bool = False,
    reason: Optional[str] = None,
    dry_run: bool = False,
) -> Optional[Path]:
    """Pick an env file by index (rollback) or exact filename, otherwise latest."""
    env_files = list_env_files(env_dir)
    if not env_files:
        return None

    if file:
        path = env_dir / file
        if path.exists():
            return path
        logger.error(f"Specified env file does not exist: {path}")
        return None

    if rollback:
        for f in env_files[0:index]:
            mark_defective(f, dry_run)
            update_yaml_report(f, reason, dry_run)

    if 0 <= index < len(env_files):
        return env_files[index]

    logger.error("Invalid deployment index")
    return None


def deploy(
    env_file: Path,
    compose_files: List[str],
    restart: bool,
    stop: bool = False,
    dry: bool = False,
):
    """Run docker compose up/down based on env file."""
    compose_cmd = check_docker_compose()

    cmd = [compose_cmd]
    for f in compose_files:
        cmd.extend(["-f", f])
    cmd.extend(["--env-file", str(env_file)])

    if restart:
        cmd.extend(["up", "-d", "--force-recreate"])
    elif stop:
        cmd.extend(["down"])
    else:
        cmd.extend(["up", "-d"])

    logger.info(f"Using env: {env_file}")
    logger.info("Running: " + " ".join(cmd))

    if not dry:
        run_cmd(cmd)


def main(arg_list: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(description="Deploy Manager")
    parser.add_argument(
        "--env-dir", default=".", help="Directory containing .env.* files"
    )
    parser.add_argument("--file", help="Use specific env file name")
    parser.add_argument(
        "--rollback",
        type=int,
        nargs="?",
        const=1,
        default=None,
        help="Rollback index (1 = previous (default), 2 = before that, ...)",
    )
    parser.add_argument(
        "--switch",
        type=int,
        nargs="?",
        const=1,
        default=None,
        help="Deploy based on index",
    )
    parser.add_argument(
        "--compose",
        nargs="+",
        default=["docker-compose.yml"],
        help="Compose YAML files",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart containers with --force-recreate",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all containers",
    )

    parser.add_argument(
        "--reason",
        type=str,
        default=None,
        help="Reason for rollback (required for --rollback)",
    )

    parser.add_argument("--list", action="store_true", help="List available env files")
    parser.add_argument("--dry", action="store_true", help="Dry run mode")
    args = parser.parse_args(arg_list)

    if args.rollback and not args.reason:
        logger.error("--reason is required when --rollback")
        return

    if args.rollback and args.switch:
        logger.error("--rollback and --switch are mutually exclusive")
        return

    env_dir = Path(args.env_dir)
    envs = list_env_files(env_dir)
    if not envs:
        logger.info(f"No any env files in {env_dir}. Nothing to deploy")
        return

    if args.list:
        envs = list_env_files(env_dir)
        for idx, e in enumerate(envs):
            print(f"{idx}: {e.name}")
        return

    env_deploy = args.rollback if args.rollback else 0
    env_deploy = args.switch if args.switch else env_deploy
    env_file = get_env_file(
        env_dir,
        env_deploy,
        args.file,
        rollback=args.rollback,
        reason=args.reason,
        dry_run=args.dry,
    )
    if not env_file:
        logger.error("No env file found.")
        return

    deploy(env_file, args.compose, args.restart, args.stop, args.dry)


if __name__ == "__main__":
    main()
