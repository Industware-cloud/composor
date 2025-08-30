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

from composor.utils.git import GitRepo
from .utils import run_cmd

logger = logging.getLogger(__name__)


def image_exists(image_tag: str, dry: bool = False) -> bool:
    cmd = ["docker", "images", "-q", f"{image_tag}"]
    result = run_cmd(cmd, dry, capture_output=True)
    return bool(result.strip())


def build_docker_image(app, app_path: Path, dry=False) -> str:
    app_name = app["name"]
    ref = app["ref"]

    repo = GitRepo(app["repo"], app_path, dry=dry)
    repo.ensure_ref(ref)
    git_hash = repo.get_sha_head()

    image_tag = f"{app_name}:{git_hash}"

    if image_exists(image_tag, dry):
        logger.info(f"Image {image_tag} already exists, skipping build.")
    else:
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
        # Determine app_path
        if "path" in app and app["path"]:
            app_path = Path(app["path"]).expanduser().resolve() / app["name"]
        else:
            app_path = Path(args.base_dir).expanduser().resolve() / app["name"]
        image_tag = build_docker_image(app, app_path, dry=args.dry)
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
