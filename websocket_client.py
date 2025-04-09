"""
WebSocket client implementation for real-time market data.
"""

import json
import asyncio
import websockets
from typing import Dict, Any, Optional, Callable, Awaitable, Union, List, cast

class WebSocketMessage:
    """Represents a WebSocket message."""
    
    def __init__(self, method: str, params: Union[List, Dict[str, Any]], id: Optional[int] = None):
        """Initialize a WebSocket message.
        
        Args:
            method: Message method/type
            params: Message parameters
            id: Optional message ID
        """
        self.method = method
        self.params = params
        self.id = id
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            "method": self.method,
            "params": self.params,
            "id": self.id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WebSocketMessage':
        """Create a message from JSON string."""
        data = json.loads(json_str)
        return cls(
            method=data.get("method", ""),
            params=data.get("params", {}),
            id=data.get("id")
        )

class WebSocketClient:
    """Client for WebSocket connections."""
    
    def __init__(self, url: str):
        """Initialize the WebSocket client.
        
        Args:
            url: WebSocket server URL
        """
        self.url = url
        self.ws = None
        self.connected = False
        self.message_handler: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
    
    async def connect(self) -> None:
        """Establish WebSocket connection."""
        if not self.connected:
            self.ws = await websockets.connect(self.url)
            self.connected = True
    
    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self.connected and self.ws:
            await self.ws.close()
            self.connected = False
            self.ws = None
    
    def is_connected(self) -> bool:
        """Check if the client is connected."""
        return self.connected
    
    async def send(self, message: Union[WebSocketMessage, Dict[str, Any]]) -> None:
        """Send a message through the WebSocket.
        
        Args:
            message: Message to send
        """
        if not self.connected:
            await self.connect()
        
        if self.ws is None:
            raise RuntimeError("WebSocket connection not established")
        
        if isinstance(message, dict):
            message = WebSocketMessage(
                method=message.get("method", ""),
                params=message.get("params", {}),
                id=message.get("id")
            )
        
        await self.ws.send(message.to_json())
    
    async def receive(self) -> Dict[str, Any]:
        """Receive a message from the WebSocket.
        
        Returns:
            Received message as dictionary
        """
        if not self.connected:
            await self.connect()
        
        if self.ws is None:
            raise RuntimeError("WebSocket connection not established")
        
        message_str = await self.ws.recv()
        message = WebSocketMessage.from_json(cast(str, message_str))
        
        if self.message_handler:
            await self.message_handler({
                "method": message.method,
                "params": message.params,
                "id": message.id
            })
        
        return {
            "method": message.method,
            "params": message.params,
            "id": message.id
        }
    
    async def subscribe(self, symbol: str, channel: str) -> None:
        """Subscribe to a channel.
        
        Args:
            symbol: Trading pair symbol
            channel: Channel name
        """
        message = WebSocketMessage(
            method="subscribe",
            params=[symbol, channel],
            id=1
        )
        await self.send(message)
    
    def set_message_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Set a message handler function.
        
        Args:
            handler: Async function to handle received messages
        """
        self.message_handler = handler 