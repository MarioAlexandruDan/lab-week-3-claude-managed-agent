"""Environment configuration and constants loaded from .env at import time."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"Error: {name} environment variable is not set.")
        sys.exit(1)
    return value

ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
GITHUB_TOKEN = _require("GITHUB_TOKEN")
REPO_URL = os.environ.get("REPO_URL", "https://github.com/MarioAlexandruDan/lab-week-3-task-manager")
# "owner/repo" extracted from the full URL — used wherever gh CLI needs --repo
REPO_SLUG = "/".join(REPO_URL.rstrip("/").split("/")[-2:])
CONFIG_FILE = Path("agent.json")
