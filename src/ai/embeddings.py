"""
Embeddings management module.

This module handles the generation and management of embeddings
for market data and trading signals.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
from .models import BGEModel
from .config import config

class EmbeddingManager:
    """Manager for generating and storing embeddings."""
    
    def __init__(self):
        """Initialize the embedding manager."""
        self.model = BGEModel()
    
    def generate_market_embedding(self, market_data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for market data.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            List[float]: The market data embedding
        """
        # Create a text representation of the market data
        text = self._market_data_to_text(market_data)
        return self.model.encode_query(text)
    
    def generate_signal_embedding(self, signal_data: Dict[str, Any]) -> List[float]:
        """
        Generate embedding for trading signals.
        
        Args:
            signal_data: Dictionary containing signal data
            
        Returns:
            List[float]: The signal embedding
        """
        # Create a text representation of the signal
        text = self._signal_data_to_text(signal_data)
        return self.model.encode_query(text)
    
    def find_similar_market_conditions(
        self,
        current_market: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar market conditions in historical data.
        
        Args:
            current_market: Current market data
            historical_data: List of historical market data
            top_k: Number of similar conditions to return
            
        Returns:
            List[Dict[str, Any]]: List of similar market conditions
        """
        # Generate embedding for current market
        current_embedding = self.generate_market_embedding(current_market)
        
        # Generate embeddings for historical data
        historical_texts = [self._market_data_to_text(data) for data in historical_data]
        historical_embeddings = self.model.encode(historical_texts)
        
        # Compute similarities
        similarities = []
        for hist_embedding in historical_embeddings:
            similarity = self._cosine_similarity(current_embedding, hist_embedding)
            similarities.append(similarity)
        
        # Get top k similar conditions
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        return [historical_data[i] for i in top_k_indices]
    
    def _market_data_to_text(self, market_data: Dict[str, Any]) -> str:
        """Convert market data to text representation."""
        return f"""
        Bitcoin Market Data:
        Price: {market_data.get('price')}
        24h Change: {market_data.get('change_24h')}%
        Volume: {market_data.get('volume')}
        RSI: {market_data.get('rsi')}
        MACD: {market_data.get('macd')}
        Bollinger Bands: {market_data.get('bollinger_bands')}
        """
    
    def _signal_data_to_text(self, signal_data: Dict[str, Any]) -> str:
        """Convert signal data to text representation."""
        return f"""
        Trading Signal:
        Type: {signal_data.get('type')}
        Strength: {signal_data.get('strength')}
        Direction: {signal_data.get('direction')}
        Timeframe: {signal_data.get('timeframe')}
        Indicators: {signal_data.get('indicators')}
        """
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))) 