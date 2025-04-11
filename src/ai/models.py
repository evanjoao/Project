"""
AI models integration module.

This module provides integration with Ollama for the language model
and BGE for embeddings.
"""

from typing import List, Dict, Any, Optional
import ollama
from sentence_transformers import SentenceTransformer
from .config import config

class OllamaModel:
    """Wrapper for Ollama language model."""
    
    def __init__(self):
        """Initialize the Ollama model."""
        self.host = config.OLLAMA_HOST
        self.model = config.OLLAMA_MODEL
        self.temperature = config.OLLAMA_TEMPERATURE
        self.max_tokens = config.OLLAMA_MAX_TOKENS
        
        # Initialize the client
        self.client = ollama.Client(host=self.host)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the Ollama model.
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters for generation
            
        Returns:
            str: The generated text
        """
        response = await self.client.generate(
            model=self.model,
            prompt=prompt,
            temperature=kwargs.get('temperature', self.temperature),
            max_tokens=kwargs.get('max_tokens', self.max_tokens)
        )
        return response['response']
    
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and provide trading insights.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dict[str, Any]: Analysis results and recommendations
        """
        prompt = self._create_market_analysis_prompt(market_data)
        analysis = await self.generate(prompt)
        return self._parse_analysis(analysis)
    
    def _create_market_analysis_prompt(self, market_data: Dict[str, Any]) -> str:
        """Create a prompt for market analysis."""
        return f"""
        Analyze the following Bitcoin market data and provide trading insights:
        
        Current Price: {market_data.get('price')}
        24h Change: {market_data.get('change_24h')}%
        Volume: {market_data.get('volume')}
        RSI: {market_data.get('rsi')}
        
        Please provide:
        1. Market sentiment analysis
        2. Key support and resistance levels
        3. Trading recommendation
        4. Risk assessment
        """
    
    def _parse_analysis(self, analysis: str) -> Dict[str, Any]:
        """Parse the model's analysis into structured data."""
        # TODO: Implement proper parsing of the analysis
        return {
            'raw_analysis': analysis,
            'sentiment': 'neutral',  # Placeholder
            'recommendation': 'hold',  # Placeholder
            'confidence': 0.5  # Placeholder
        }

class BGEModel:
    """Wrapper for BGE embedding model."""
    
    def __init__(self):
        """Initialize the BGE model."""
        self.model_name = config.BGE_MODEL_NAME
        self.device = config.BGE_DEVICE
        self.batch_size = config.BGE_BATCH_SIZE
        
        # Initialize the model
        self.model = SentenceTransformer(
            model_name_or_path=self.model_name,
            device=self.device
        )
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for the input texts.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            List[List[float]]: List of embeddings
        """
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True
        ).tolist()
    
    def encode_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            query: The query text
            
        Returns:
            List[float]: The query embedding
        """
        return self.encode([query])[0]
    
    def compute_similarity(self, query: str, texts: List[str]) -> List[float]:
        """
        Compute similarity scores between query and texts.
        
        Args:
            query: The query text
            texts: List of texts to compare against
            
        Returns:
            List[float]: Similarity scores
        """
        query_embedding = self.encode_query(query)
        text_embeddings = self.encode(texts)
        
        # Compute cosine similarity
        similarities = []
        for text_embedding in text_embeddings:
            similarity = self._cosine_similarity(query_embedding, text_embedding)
            similarities.append(similarity)
        
        return similarities
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)) 