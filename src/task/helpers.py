from pathlib import Path

from dotenv import load_dotenv


def load_env(path: str = ".env") -> None:
    _ = load_dotenv(path)

def get_env_path() -> Path:
    ROOT = Path(__file__).resolve().parent.parent.parent
    return ROOT / ".env"

def get_logs_dir() -> str:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    return str(PROJECT_ROOT / "logs" / "app.log")
