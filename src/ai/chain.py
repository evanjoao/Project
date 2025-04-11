"""
Trading chain module using LangChain.

This module provides a chain of operations for analyzing market data
and generating trading decisions using LangChain.
"""

from typing import List, Dict, Any, Optional
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.callbacks import StdOutCallbackHandler
from .models import OllamaModel
from .vector_store import VectorStore
from .config import config

class TradingChain:
    """Chain for trading analysis and decision making."""
    
    def __init__(self):
        """Initialize the trading chain."""
        self.llm = OllamaModel()
        self.vector_store = VectorStore()
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize the chain
        self.chain = self._create_chain()
    
    def _create_chain(self) -> LLMChain:
        """Create the LangChain chain."""
        # Define the prompt template
        template = """
        You are an expert Bitcoin trading analyst. Use the following information to make trading decisions:
        
        Current Market Data:
        {market_data}
        
        Similar Historical Conditions:
        {similar_conditions}
        
        Previous Analysis:
        {chat_history}
        
        Based on this information, provide:
        1. Market Analysis
        2. Trading Recommendation
        3. Risk Assessment
        4. Key Support/Resistance Levels
        
        Your response should be detailed and include specific price levels and reasoning.
        """
        
        prompt = PromptTemplate(
            input_variables=["market_data", "similar_conditions", "chat_history"],
            template=template
        )
        
        # Create the chain
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            memory=self.memory,
            verbose=config.DEBUG
        )
    
    async def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market data and generate trading insights.
        
        Args:
            market_data: Dictionary containing market data
            
        Returns:
            Dict[str, Any]: Analysis results and recommendations
        """
        # Find similar market conditions
        similar_conditions = self.vector_store.find_similar_market_conditions(
            market_data,
            n_results=config.TOP_K_RESULTS
        )
        
        # Format similar conditions for the prompt
        similar_conditions_text = self._format_similar_conditions(similar_conditions)
        
        # Run the chain
        response = await self.chain.arun(
            market_data=self._format_market_data(market_data),
            similar_conditions=similar_conditions_text
        )
        
        # Parse the response
        analysis = self._parse_analysis(response)
        
        # Store the market data and analysis in the vector store
        self.vector_store.add_market_data(market_data)
        
        return analysis
    
    def _format_market_data(self, market_data: Dict[str, Any]) -> str:
        """Format market data for the prompt."""
        return f"""
        Price: {market_data.get('price')}
        24h Change: {market_data.get('change_24h')}%
        Volume: {market_data.get('volume')}
        RSI: {market_data.get('rsi')}
        MACD: {market_data.get('macd')}
        Bollinger Bands: {market_data.get('bollinger_bands')}
        """
    
    def _format_similar_conditions(self, conditions: List[Dict[str, Any]]) -> str:
        """Format similar conditions for the prompt."""
        if not conditions:
            return "No similar historical conditions found."
        
        formatted = "Similar Historical Conditions:\n"
        for i, condition in enumerate(conditions, 1):
            formatted += f"\n{i}. {condition['document']}\n"
            formatted += f"   Similarity: {1 - condition['distance']:.2%}\n"
        
        return formatted
    
    def _parse_analysis(self, response: str) -> Dict[str, Any]:
        """Parse the chain's response into structured data."""
        # TODO: Implement proper parsing of the analysis
        # For now, return a simple structure
        return {
            'raw_analysis': response,
            'sentiment': 'neutral',  # Placeholder
            'recommendation': 'hold',  # Placeholder
            'confidence': 0.5,  # Placeholder
            'support_levels': [],  # Placeholder
            'resistance_levels': []  # Placeholder
        } 