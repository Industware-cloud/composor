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
import subprocess
from pathlib import Path
from typing import Optional, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def check_docker_compose():
    """Check if docker compose or docker-compose is installed."""
    if shutil.which("docker-compose"):
        return "docker-compose"
    elif shutil.which("docker"):
        # Check if "docker compose" is available (newer plugin)
        try:
            subprocess.run(
                ["docker", "compose", "version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            return "docker compose"
        except subprocess.CalledProcessError:
            pass
    raise RuntimeError(
        "Neither `docker compose` nor `docker-compose` is installed on this system."
    )


def list_env_files(env_dir: Path) -> List[Path]:
    """Return sorted list of available env files."""
    return sorted(env_dir.glob("env_*.env"), key=os.path.getmtime)


def get_env_file(
    env_dir: Path, index: Optional[int] = None, file: Optional[str] = None
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

    if index is not None:
        if 0 <= index < len(env_files):
            return env_files[-(index + 1)]  # rollback
        logger.error("Invalid rollback index")
        return None

    return env_files[-1]  # latest


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


def main():
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

    parser.add_argument("--list", action="store_true", help="List available env files")
    parser.add_argument("--dry", action="store_true", help="Dry run mode")
    args = parser.parse_args()

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
    env_file = get_env_file(env_dir, env_deploy, args.file)
    if not env_file:
        logger.error("No env file found.")
        return

    deploy(env_file, args.compose, args.restart, args.stop, args.dry)


if __name__ == "__main__":
    main()
