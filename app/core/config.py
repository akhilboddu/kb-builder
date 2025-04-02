import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from dotenv import load_dotenv
from pydantic import field_validator

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_ANON_KEY: str = ""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    
    # Application Settings
    APP_ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # File Upload Settings
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ["pdf"]
    
    # Parse ALLOWED_EXTENSIONS from env if it's a simple string
    @field_validator('ALLOWED_EXTENSIONS', mode='before')
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str) and not v.startswith('['):
            # If it's a simple string like "pdf", convert to list
            return [ext.strip() for ext in v.split(',')]
        return v
    
    # RAG Settings
    MAX_CHUNK_SIZE: int = 1000
    DEFAULT_RETRIEVAL_COUNT: int = 5
    DEFAULT_HANDOVER_THRESHOLD: float = 0.7
    
    # Vector DB Settings
    CHROMA_PERSIST_DIRECTORY: str = "./chromadb"
    
    # Embedding Model Settings
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS: int = 1536
    
    # LLM Settings
    LLM_MODEL: str = "gpt-4"
    
    # Rate Limiting
    RATE_LIMIT_CALLS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # in seconds
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

# Create settings instance
settings = Settings()