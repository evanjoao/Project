"""
Vector store module using ChromaDB.

This module provides functionality for storing and retrieving
embeddings and their associated metadata.
"""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from datetime import datetime
from .config import config
from .embeddings import EmbeddingManager

class VectorStore:
    """Vector store for trading data using ChromaDB."""
    
    def __init__(self):
        """Initialize the vector store."""
        self.persist_dir = config.CHROMA_PERSIST_DIR
        self.collection_name = config.CHROMA_COLLECTION_NAME
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_dir,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": config.SIMILARITY_METRIC}
        )
        
        # Initialize embedding manager
        self.embedding_manager = EmbeddingManager()
    
    def add_market_data(self, market_data: Dict[str, Any]) -> str:
        """
        Add market data to the vector store.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            str: ID of the added document
        """
        # Generate embedding
        embedding = self.embedding_manager.generate_market_embedding(market_data)
        
        # Create metadata
        metadata = {
            "type": "market_data",
            "timestamp": datetime.now().isoformat(),
            "price": str(market_data.get('price')),
            "change_24h": str(market_data.get('change_24h')),
            "volume": str(market_data.get('volume')),
            "rsi": str(market_data.get('rsi'))
        }
        
        # Add to collection
        doc_id = f"market_{datetime.now().timestamp()}"
        self.collection.add(
            embeddings=[embedding],
            documents=[self.embedding_manager._market_data_to_text(market_data)],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def add_trading_signal(self, signal_data: Dict[str, Any]) -> str:
        """
        Add trading signal to the vector store.
        
        Args:
            signal_data: Dictionary containing signal data
            
        Returns:
            str: ID of the added document
        """
        # Generate embedding
        embedding = self.embedding_manager.generate_signal_embedding(signal_data)
        
        # Create metadata
        metadata = {
            "type": "trading_signal",
            "timestamp": datetime.now().isoformat(),
            "signal_type": signal_data.get('type'),
            "strength": str(signal_data.get('strength')),
            "direction": signal_data.get('direction'),
            "timeframe": signal_data.get('timeframe')
        }
        
        # Add to collection
        doc_id = f"signal_{datetime.now().timestamp()}"
        self.collection.add(
            embeddings=[embedding],
            documents=[self.embedding_manager._signal_data_to_text(signal_data)],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def find_similar_market_conditions(
        self,
        market_data: Dict[str, Any],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar market conditions.
        
        Args:
            market_data: Current market data
            n_results: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of similar market conditions
        """
        # Generate query embedding
        query_embedding = self.embedding_manager.generate_market_embedding(market_data)
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"type": "market_data"}
        )
        
        # Format results
        similar_conditions = []
        for i in range(len(results['ids'][0])):
            similar_conditions.append({
                'id': results['ids'][0][i],
                'metadata': results['metadatas'][0][i],
                'document': results['documents'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return similar_conditions
    
    def find_similar_signals(
        self,
        signal_data: Dict[str, Any],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar trading signals.
        
        Args:
            signal_data: Current signal data
            n_results: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of similar signals
        """
        # Generate query embedding
        query_embedding = self.embedding_manager.generate_signal_embedding(signal_data)
        
        # Search in collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"type": "trading_signal"}
        )
        
        # Format results
        similar_signals = []
        for i in range(len(results['ids'][0])):
            similar_signals.append({
                'id': results['ids'][0][i],
                'metadata': results['metadatas'][0][i],
                'document': results['documents'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return similar_signals 