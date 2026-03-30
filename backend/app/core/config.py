import os
from pathlib import Path
from typing import Any
import yaml
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _load_yaml() -> dict[str, Any]:
    config_path = BASE_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


_cfg = _load_yaml()


class Settings:
    # LLM
    llm_config: dict = _cfg.get("llm", {})
    default_model: str = _cfg.get("llm", {}).get("default_model", "anthropic/claude-sonnet-4-20250514")
    llm_models: dict = _cfg.get("llm", {}).get("models", {})
    fallback_model: str = _cfg.get("llm", {}).get("fallback_model", "ollama/llama3")

    # Whisper
    whisper_model_size: str = _cfg.get("whisper", {}).get("model_size", "base")
    whisper_device: str = _cfg.get("whisper", {}).get("device", "cpu")
    whisper_compute_type: str = _cfg.get("whisper", {}).get("compute_type", "int8")

    # Storage
    media_dir: Path = BASE_DIR / _cfg.get("storage", {}).get("media_dir", "./data/media").lstrip("./")
    db_path: Path = BASE_DIR / _cfg.get("storage", {}).get("db_path", "./data/coach.db").lstrip("./")

    # CORS
    cors_origins: list[str] = ["https://localhost:3000", "http://localhost:3000"]

    def get_model_for_task(self, task: str) -> str:
        return self.llm_models.get(task, self.default_model)


settings = Settings()
settings.media_dir.mkdir(parents=True, exist_ok=True)
settings.db_path.parent.mkdir(parents=True, exist_ok=True)
