import logging
import subprocess

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
