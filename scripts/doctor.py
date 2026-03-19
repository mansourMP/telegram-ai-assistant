import importlib
import json
import shutil
import subprocess
from pathlib import Path

from mansur_bot.config import REPO_ROOT, UNIVERSITY_DIR, load_project_env


def check_file(path: Path, label: str) -> bool:
    if path.exists():
        print(f"OK  {label}: {path}")
        return True
    print(f"ERR {label}: missing -> {path}")
    return False


def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        print(f"OK  import: {module_name}")
        return True
    except Exception as exc:
        print(f"ERR import: {module_name} ({exc})")
        return False


def check_command(name: str) -> bool:
    path = shutil.which(name)
    if path:
        print(f"OK  command: {name} -> {path}")
        return True
    print(f"WARN command: {name} not found")
    return False


def check_env() -> None:
    load_project_env()
    required = [
        "TELEGRAM_BOT_TOKEN",
        "DEEPSEEK_API_KEY",
    ]
    optional = [
        "TELEGRAM_CHAT_ID",
        "OPENAI_API_KEY",
    ]
    import os

    for key in required:
        if os.getenv(key):
            print(f"OK  env: {key}")
        else:
            print(f"WARN env: {key} not set")

    for key in optional:
        if os.getenv(key):
            print(f"OK  env: {key}")
        else:
            print(f"INFO env: {key} not set")


def check_json(path: Path) -> None:
    try:
        json.loads(path.read_text())
        print(f"OK  json: {path}")
    except Exception as exc:
        print(f"ERR json: {path} ({exc})")


def check_codex() -> None:
    if not shutil.which("codex"):
        print("INFO codex: CLI not installed")
        return
    print("OK  codex: CLI installed")
    try:
        result = subprocess.run(
            ["codex", "login", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("OK  codex: login status command works")
        else:
            print("WARN codex: login status returned non-zero")
    except Exception as exc:
        print(f"WARN codex: login status check failed ({exc})")


def main() -> None:
    print(f"Repo: {REPO_ROOT}")
    check_file(REPO_ROOT / "README.md", "README")
    check_file(REPO_ROOT / ".env.example", ".env.example")
    check_file(REPO_ROOT / "requirements.txt", "requirements.txt")
    check_file(REPO_ROOT / "src" / "mansur_bot" / "bot.py", "bot.py")
    
    # Check default content or configured content
    check_file(UNIVERSITY_DIR, "Content Directory")
    
    # Check environment variables
    print("\n--- Environment ---")
    load_project_env()
    import os
    required = ["TELEGRAM_BOT_TOKEN"]
    optional = ["DEEPSEEK_API_KEY", "UNIVERSITY_DIR"]

    for key in required:
        if os.getenv(key):
            print(f"OK  env: {key} (Set)")
        else:
            print(f"ERR env: {key} (Missing!)")

    for key in optional:
        if os.getenv(key):
            print(f"OK  env: {key} (Set)")
        else:
            print(f"INFO env: {key} (Not set)")

    print("\n--- Dependencies ---")
    for module_name in ["telebot", "openai", "dotenv", "requests", "PIL", "fpdf"]:
        if check_import(module_name):
            pass
        else:
            print(f"ERR module: {module_name} missing")

    print("\n--- System Tools ---")
    if check_command("tesseract"):
        print("OK  OCR ready")
    else:
        print("WARN OCR missing (image text extraction disabled)")

if __name__ == "__main__":
    main()
