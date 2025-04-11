"""
Configuration settings for the AI/ML module.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os

@dataclass
class AIConfig:
    """Configuration for AI/ML components."""
    
    # Ollama settings
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "deepseek-coder:7b")
    OLLAMA_TEMPERATURE: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
    OLLAMA_MAX_TOKENS: int = int(os.getenv("OLLAMA_MAX_TOKENS", "2000"))
    
    # BGE settings
    BGE_MODEL_NAME: str = os.getenv("BGE_MODEL_NAME", "BAAI/bge-large-en-v1.5")
    BGE_DEVICE: str = os.getenv("BGE_DEVICE", "cuda")
    BGE_BATCH_SIZE: int = int(os.getenv("BGE_BATCH_SIZE", "32"))
    
    # ChromaDB settings
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "data/chroma")
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "trading_data")
    
    # LangChain settings
    LANGCHAIN_TRACING: bool = os.getenv("LANGCHAIN_TRACING", "false").lower() == "true"
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "bitcoin_trading")
    
    # Vector store settings
    VECTOR_DIMENSION: int = 1024  # BGE-large dimension
    SIMILARITY_METRIC: str = "cosine"
    TOP_K_RESULTS: int = 5
    
    # Trading context settings
    MAX_HISTORY_LENGTH: int = 1000  # Maximum number of historical data points to consider
    CONTEXT_WINDOW: int = 100  # Number of recent data points to include in context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {k: v for k, v in self.__dict__.items() 
                if not k.startswith('_') and not callable(v)}

# Create a global instance
config = AIConfig() 