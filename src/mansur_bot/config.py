import os
from pathlib import Path

from dotenv import load_dotenv

def get_repo_root() -> Path:
    # Handle cases where this might be installed as a package
    # but for now assume editable install or local run
    return Path(__file__).resolve().parents[2]

REPO_ROOT = get_repo_root()
DOCUMENTS_DIR = REPO_ROOT / "Documents"

def load_project_env() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)

load_project_env()

# Configurable paths
_univ_env = os.getenv("UNIVERSITY_DIR")
if _univ_env:
    UNIVERSITY_DIR = Path(_univ_env).resolve()
else:
    # Default to local University dir if it exists, else examples
    _local_univ = REPO_ROOT / "University"
    if _local_univ.exists():
        UNIVERSITY_DIR = _local_univ
    else:
        UNIVERSITY_DIR = REPO_ROOT / "examples" / "content"

# Ensure directories exist (or at least warn)
if not UNIVERSITY_DIR.exists():
    # Only print warning, don't crash yet as user might be setting up
    print(f"Warning: Content directory {UNIVERSITY_DIR} does not exist.")
