"""Starts the consolidated Flask backend service."""

from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback keeps dev startup forgiving.
    load_dotenv = None


def _load_simple_env(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            import os

            os.environ.setdefault(key, value)


def load_environment():
    project_root = Path(__file__).resolve().parents[1]
    env_files = [project_root / ".env.local", project_root / ".env"]
    for env_file in env_files:
        if load_dotenv is not None:
            load_dotenv(env_file)
        else:
            _load_simple_env(env_file)


def main():
    load_environment()

    from flask_service.main import create_app

    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
