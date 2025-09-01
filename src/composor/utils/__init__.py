import logging
import subprocess
import re

logger = logging.getLogger(__name__)


def run_cmd(
    cmd, dry: bool = False, capture_output: bool = False, text: bool = True
) -> int | str:
    """
    Run a system command.

    Args:
        cmd (list[str]): Command to run as a list of strings.
        dry (bool): If True, logs the command but does not execute.
        capture_output (bool): If True, return stdout instead of exit code.
        text (bool): If True, decode output as text (default).

    Returns:
        int | str: Exit code (default) or stdout string if capture_output=True.
    """
    if dry:
        logger.info(f"[DRY] Would run: {' '.join(cmd)}")
        return "" if capture_output else 0

    logger.info("Running command: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        check=True,
        capture_output=capture_output,
        text=text,
    )

    if capture_output:
        return result.stdout.strip()
    return result.returncode


def normalize_name(name: str) -> str:
    """
    Normalize app name so it is safe for environment variables:
    - Replace spaces and dashes with underscores
    - Remove invalid characters
    - Uppercase everything
    """
    # Replace spaces and dashes with underscores
    norm = re.sub(r"[\s\-]+", "_", name)
    # Remove anything not alphanumeric or underscore
    norm = re.sub(r"[^0-9A-Za-z_]", "", norm)
    # Ensure it’s uppercase for ENV style
    return norm.upper()
