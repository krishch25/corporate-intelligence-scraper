import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM settings
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    eyq_incubator_endpoint: str = os.getenv("EYQ_INCUBATOR_ENDPOINT", "")
    eyq_incubator_key: str = os.getenv("EYQ_INCUBATOR_KEY", "")
    eyq_model: str = os.getenv("EYQ_MODEL", "gpt-5.1")
    eyq_api_version: str = os.getenv("EYQ_API_VERSION", "2024-02-15-preview")
    
    # DB settings
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    
    # Execution Sandbox
    docker_host: str = os.getenv("DOCKER_HOST", "unix://var/run/docker.sock")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()
