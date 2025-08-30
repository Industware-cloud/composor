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
import subprocess
import sys
from typing import Optional

import yaml
from pathlib import Path
from datetime import datetime
from .utils import run_cmd

logger = logging.getLogger(__name__)


def clone_or_update_repo(app, base_dir, dry=False) -> int:
    repo_url = app["repo"]
    app_name = app["name"]
    app_path = Path(app.get("path") or Path(base_dir) / app_name).expanduser().resolve()

    if app_path.exists():
        logger.info(f"Updating existing repo for {app_name} at {app_path}")
        return run_cmd(["git", "-C", str(app_path), "pull"], dry)
    else:
        logger.info(f"Cloning repo for {app_name} into {app_path}")
        if not dry:
            app_path.parent.mkdir(parents=True, exist_ok=True)
        return run_cmd(["git", "clone", repo_url, str(app_path)], dry)


def build_docker_image(app, base_dir, dry=False) -> str:
    app_name = app["name"]
    app_path = Path(app.get("path") or Path(base_dir) / app_name).expanduser().resolve()

    if not dry:
        result = subprocess.run(
            ["git", "-C", str(app_path), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
        )
        git_hash = result.stdout.strip()
    else:
        git_hash = "DRY"

    image_tag = f"{app_name}:{git_hash}"
    logger.info(f"Building Docker image {image_tag}")
    run_cmd(["docker", "build", "-t", image_tag, str(app_path)], dry)

    return image_tag


def create_consolidated_env(app_images, env_dir, timestamp, dry=False) -> Path:
    env_dir = Path(env_dir).expanduser().resolve()
    if not dry:
        env_dir.mkdir(parents=True, exist_ok=True)
    env_file = env_dir / f"env_{timestamp}.env"

    logger.info(f"Creating consolidated env file {env_file}")
    lines = [f"{name.upper()}_IMAGE={tag}" for name, tag in app_images.items()]
    if not dry:
        env_file.write_text("\n".join(lines) + "\n")
    return env_file


def generate_consolidated_report(
    app_images, env_file, timestamp, report_dir="./reports", dry=False
) -> Path:
    report_dir = Path(report_dir).resolve()
    if not dry:
        report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"report_{timestamp}.yaml"

    report_data = {
        "timestamp": timestamp,
        "env_file": str(env_file),
        "apps": [{"name": name, "image_tag": tag} for name, tag in app_images.items()],
    }

    logger.info(f"Writing consolidated report to {report_file}")
    if not dry:
        with open(report_file, "w") as f:
            yaml.safe_dump(report_data, f)

    return report_file


def main(arg_list: Optional[list[str]] = None):
    parser = argparse.ArgumentParser(description="Build manager for Docker apps")
    parser.add_argument(
        "--config", default="apps.yaml", help="Path to apps config YAML"
    )
    parser.add_argument(
        "--base-dir", default="~/projects", help="Base directory for repos"
    )
    parser.add_argument(
        "--env-dir", default="./envs", help="Directory to save env files"
    )
    parser.add_argument("--dry", action="store_true", help="Dry run")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args(arg_list)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    config_file = Path(args.config).resolve()
    if not config_file.exists():
        logger.error(f"Config file does not exist: {config_file}")
        sys.exit(1)

    with open(config_file) as f:
        config = yaml.safe_load(f)

    app_images = {}
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    for app in config.get("apps", []):
        clone_or_update_repo(app, args.base_dir, dry=args.dry)
        image_tag = build_docker_image(app, args.base_dir, dry=args.dry)
        app_images[app["name"]] = image_tag

    if not app_images:
        logger.error(f"Config file {config_file} does not contain any app")
        sys.exit(1)

    env_file = create_consolidated_env(
        app_images, args.env_dir, timestamp, dry=args.dry
    )
    generate_consolidated_report(
        app_images, env_file, timestamp, report_dir=args.env_dir, dry=args.dry
    )


if __name__ == "__main__":
    main()
