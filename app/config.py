from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_provider: str = Field(
        "openai",
        description="LLM provider: 'openai' or 'gemini'",
    )
    openai_api_key: str | None = Field(None, description="OpenAI API key (required if llm_provider=openai)")
    openai_model: str = Field("gpt-4o-mini", description="OpenAI chat model identifier")
    openai_embedding_model: str = Field(
        "text-embedding-3-small", description="OpenAI embedding model identifier"
    )
    gemini_api_key: str | None = Field(None, description="Google/Gemini API key (required if llm_provider=gemini)")
    gemini_model: str = Field("gemini-1.5-flash", description="Gemini model identifier (e.g. gemini-1.5-flash, gemini-1.5-pro)")

    property_id: str = Field(
        "mohegan_sun", description="Property directory name to load"
    )

    log_level: str = Field("INFO", description="Logging level")

    chunk_size: int = Field(800, description="Text splitter chunk size in characters")
    chunk_overlap: int = Field(200, description="Text splitter chunk overlap")
    retrieval_k: int = Field(6, description="Number of documents to retrieve")

    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent / "data" / "properties",
        description="Root directory for property data files",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @model_validator(mode="after")
    def validate_api_key(self) -> "Settings":
        if self.llm_provider.lower() == "gemini":
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        elif self.llm_provider.lower() == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return self

    @property
    def property_data_dir(self) -> Path:
        return self.data_dir / self.property_id


def get_settings() -> Settings:
    return Settings()
