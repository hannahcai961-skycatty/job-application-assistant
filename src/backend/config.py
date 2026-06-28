from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
FRONTEND_DIR = ROOT_DIR / "src" / "frontend"
TEMPLATES_DIR = ROOT_DIR / "templates"
PROMPTS_DIR = TEMPLATES_DIR / "prompts"
STATES_FILE = TEMPLATES_DIR / "states.yml"
REPORTS_DIR = ROOT_DIR / "reports"
OUTPUT_DIR = ROOT_DIR / "output"
JDS_DIR = ROOT_DIR / "jds"
CONFIG_DIR = ROOT_DIR / "config"
VOICE_DNA_FILE = ROOT_DIR / "voice-dna.md"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    host: str = "127.0.0.1"
    port: int = 8000


settings = Settings()
