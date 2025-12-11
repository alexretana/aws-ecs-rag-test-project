import json
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment and AWS Secrets Manager."""
    
    # App settings
    environment: str = "dev"
    aws_region: str = "us-east-1"
    log_level: str = "INFO"
    
    # Database settings (loaded from secrets)
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_username: str = ""
    db_password: str = ""
    
    # Bedrock settings
    embedding_model_id: str = "amazon.titan-embed-text-v1"
    llm_model_id: str = "meta.llama3-8b-instruct-v1:0"
    
    # RAG settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    
    class Config:
        env_prefix = ""


def load_db_credentials() -> dict:
    """Load database credentials from AWS Secrets Manager."""
    secret_json = os.environ.get("DB_SECRET")
    if secret_json:
        return json.loads(secret_json)
    return {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    settings = Settings()
    
    # Load DB credentials from Secrets Manager
    db_creds = load_db_credentials()
    if db_creds:
        settings.db_host = db_creds.get("host", "")
        settings.db_port = db_creds.get("port", 5432)
        settings.db_name = db_creds.get("dbname", "")
        settings.db_username = db_creds.get("username", "")
        settings.db_password = db_creds.get("password", "")
    
    return settings