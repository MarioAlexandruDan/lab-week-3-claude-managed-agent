"""GitHub helpers: create pull requests and delete branches via the gh CLI."""
import os
import subprocess
from config import GITHUB_TOKEN, REPO_SLUG


def create_pr(title: str, body: str, branch: str) -> tuple[str, bool]:
    """Create a PR and return (pr_url, True) on success or (error_message, False) on failure."""
    result = subprocess.run(
        [
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--base", "master",
            "--head", branch,
            "--repo", REPO_SLUG,
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": GITHUB_TOKEN},
    )
    output = result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    return output, result.returncode == 0


def delete_branch(branch: str) -> None:
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{REPO_SLUG}/git/refs/heads/{branch}",
            "--method", "DELETE",
        ],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": GITHUB_TOKEN},
    )
    if result.returncode == 0:
        print(f"Branch '{branch}' deleted.")
    else:
        print(f"Failed to delete branch: {result.stderr.strip()}")
