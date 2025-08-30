import subprocess
from pathlib import Path
import logging

from . import run_cmd  # your helper

logger = logging.getLogger(__name__)


class GitRepo:
    def __init__(self, repo_url: str, path: Path, dry: bool = False):
        self.repo_url = repo_url
        self.path = path.expanduser().resolve()
        self.dry = dry

    def exists(self) -> bool:
        return self.path.exists()

    def clone(self) -> int:
        logger.info(f"Cloning repo {self.repo_url} into {self.path}")
        if not self.dry:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        return run_cmd(["git", "clone", self.repo_url, str(self.path)], self.dry)

    def fetch(self) -> int:
        logger.info(f"Fetching updates in {self.path}")
        return run_cmd(
            ["git", "-C", str(self.path), "fetch", "--all", "--tags"], self.dry
        )

    def checkout(self, ref: str) -> int:
        logger.info(f"Checking out {ref} in {self.path}")
        return run_cmd(["git", "-C", str(self.path), "checkout", ref], self.dry)

    def reset_to_origin(self, branch: str) -> int:
        logger.info(f"Resetting {self.path} to origin/{branch}")
        return run_cmd(
            ["git", "-C", str(self.path), "reset", "--hard", f"origin/{branch}"],
            self.dry,
        )

    def get_sha_head(self) -> str:
        if not self.dry:
            result = subprocess.run(
                ["git", "-C", str(self.path), "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
            )
            git_hash = result.stdout.strip()
        else:
            git_hash = "DRY"
        return git_hash

    def ensure_ref(self, ref: str) -> int:
        """Clone or update repo and ensure it's at given ref (branch, tag, or commit)."""
        if self.exists():
            self.fetch()
        else:
            self.clone()

        self.checkout(ref)

        if not self.dry:
            branch_check = run_cmd(
                ["git", "-C", str(self.path), "rev-parse", "--verify", f"origin/{ref}"],
                self.dry,
            )
            if branch_check == 0:
                self.reset_to_origin(ref)

        return 0
