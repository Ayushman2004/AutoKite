import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

load_dotenv()


class EmailConfig(BaseModel):
    email: str = Field(..., env='GMAIL_EMAIL')
    password: str = Field(..., env='GMAIL_APP_PASSWORD')
    imap_server: str = Field(default='imap.gmail.com')
    imap_port: int = Field(default=993)
    
    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError('Invalid email address')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not v:
            raise ValueError('Gmail app password is required')
        return v


class OllamaConfig(BaseModel):
    model: str = Field(default='phi3.5', env='OLLAMA_MODEL')
    host: str = Field(default='http://localhost:11434', env='OLLAMA_HOST')
    temperature: float = Field(default=0.1)  
    
    
class ChromaConfig(BaseModel):
    persist_directory: Path = Field(
        default=Path('./chroma_db'),
        env='CHROMA_PERSIST_DIRECTORY'
    )
    collection_name: str = Field(default='email_buckets')
    
    @validator('persist_directory')
    def create_directory(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v


class AppConfig(BaseModel):
    email: EmailConfig
    ollama: OllamaConfig
    chroma: ChromaConfig
    
    class Config:
        arbitrary_types_allowed = True


def load_config() -> AppConfig:
    try:
        return AppConfig(
            email=EmailConfig(
                email=os.getenv('GMAIL_EMAIL', ''),
                password=os.getenv('GMAIL_APP_PASSWORD', '')
            ),
            ollama=OllamaConfig(
                model=os.getenv('OLLAMA_MODEL', 'phi3.5'),
                host=os.getenv('OLLAMA_HOST', 'http://localhost:11434')
            ),
            chroma=ChromaConfig(
                persist_directory=Path(os.getenv('CHROMA_PERSIST_DIRECTORY', './chroma_db'))
            )
        )
    except Exception as e:
        raise ValueError(f"Configuration error: {str(e)}")


_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config