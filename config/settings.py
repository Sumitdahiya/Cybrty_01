from pydantic import BaseModel
from typing import Optional
import os

class Settings(BaseModel):
    """Application settings"""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Ollama Configuration
    ollama_model: str = "deepseek-r1:1.5b"
    ollama_base_url: str = "http://localhost:11434"
    
    # Logging
    log_level: str = "INFO"
    
    # Optional API Keys
    serper_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    def __init__(self, **kwargs):
        # Load from environment variables
        env_values = {
            'api_host': os.getenv('API_HOST', '0.0.0.0'),
            'api_port': int(os.getenv('API_PORT', '8000')),
            'ollama_model': os.getenv('OLLAMA_MODEL', 'deepseek-r1:1.5b'),
            'ollama_base_url': os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'serper_api_key': os.getenv('SERPER_API_KEY'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
        }
        
        # Merge with provided kwargs
        env_values.update(kwargs)
        super().__init__(**env_values)

# Global settings instance
settings = Settings()
