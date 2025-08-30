import logging
import subprocess

logger = logging.getLogger(__name__)

def run_cmd(cmd, dry=False) -> int:
    logger.info("Running command: %s", " ".join(cmd))
    if dry:
        logger.info("Dry run, skipping execution")
        return 0
    result = subprocess.run(cmd)
    if result.returncode != 0:
        logger.error("Command failed: %s", " ".join(cmd))
    return result.returncode
