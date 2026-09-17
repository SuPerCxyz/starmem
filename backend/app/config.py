from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="STARMEM_", extra="ignore")

    env: str = "development"
    database_url: str = "postgresql+psycopg://starmem:starmem@localhost:5432/starmem"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = "development-only-change-me"
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:8080,http://localhost:5173"
    rate_limit_per_minute: int = Field(default=120, ge=0)
    admin_email: str = "admin@starmem.local"
    admin_password: str = "change-this-password"
    chat_base_url: str = ""
    chat_model: str = ""
    chat_api_key: str = Field(default="", repr=False)
    chat_enable_thinking: bool = False
    chat_timeout_seconds: int = 45
    chat_max_retries: int = 2
    storage_path: str = "/var/lib/starmem/attachments"
    max_upload_bytes: int = Field(default=20_000_000, ge=1_024)
    max_url_bytes: int = Field(default=20_000_000, ge=1_024)
    max_pdf_pages: int = Field(default=500, ge=1, le=10_000)
    url_timeout_seconds: int = Field(default=20, ge=1, le=120)
    url_max_redirects: int = Field(default=3, ge=0, le=10)
    ocr_enabled: bool = True
    ocr_lang: str = "eng+chi_sim"
    ocr_timeout_seconds: int = Field(default=30, ge=1, le=180)
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dimensions: int = 512
    hybrid_keyword_weight: float = 0.55
    hybrid_semantic_weight: float = 0.45
    semantic_min_similarity: float = Field(default=0.35, ge=0.0, le=1.0)
    reranker_provider: str = "none"
    reranker_base_url: str = ""
    reranker_model: str = ""
    reranker_timeout_seconds: int = Field(default=10, ge=1, le=120)
    image_description_enabled: bool = False
    image_description_base_url: str = ""
    image_description_model: str = ""
    image_description_timeout_seconds: int = Field(default=30, ge=1, le=180)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
