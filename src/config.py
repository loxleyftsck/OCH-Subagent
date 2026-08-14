from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Configuration
    API_BASE_URL: str = "http://10.7.1.21/v1"
    API_KEY: str = "sk-c1PP5Ngd9Dh7q2ZjiwZAIg"

    # Model Registry
    OCR_MODEL: str = "ocr-lighton"
    TEXT_MODEL: str = "qwen-35b"
    CHAT_MODEL: str = "qwen-35b"
    ROUTER_MODEL: str = "nemotron-35"
    VISION_MODEL: str = "qwen-35b-vision"

    # Shared Safety Controls
    TEAM_SHARED_MODE: bool = True
    MAX_CONCURRENT_REQUESTS: int = 1
    OCR_INTERVAL_SECONDS: float = 30.0
    GENERAL_INTERVAL_SECONDS: float = 2.0
    MAX_DAILY_LOCAL_OCR_CALLS: int = 25
    ENABLE_LOCAL_CACHE: bool = True
    MOCK_MODE: bool = False

    # 429 Retry Strategy
    RETRY_MAX_ATTEMPTS: int = 4
    RETRY_BASE_BACKOFF_SECONDS: float = 15.0
    RETRY_JITTER_MAX_SECONDS: float = 5.0

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Field(default_factory=lambda: Path("data"))
    CACHE_DIR: Path = Field(default_factory=lambda: Path("data/cache"))
    PDF_DIR: Path = Field(default_factory=lambda: Path("data/govdocs"))

    # Server
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    def ensure_directories(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.PDF_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
