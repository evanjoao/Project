"""
Tests for the websocket client implementation.
"""

import pytest
import json
from unittest.mock import patch, AsyncMock
from ..websocket_client import WebSocketClient, WebSocketMessage

@pytest.fixture
def websocket_client():
    return WebSocketClient(url="wss://test.com/ws")

@pytest.mark.asyncio
async def test_connect(websocket_client):
    with patch('websockets.connect', new_callable=AsyncMock) as mock_connect:
        await websocket_client.connect()
        mock_connect.assert_called_once_with("wss://test.com/ws")
        assert websocket_client.is_connected()

@pytest.mark.asyncio
async def test_close(websocket_client):
    mock_ws = AsyncMock()
    websocket_client.ws = mock_ws
    websocket_client.connected = True
    
    await websocket_client.close()
    mock_ws.close.assert_called_once()
    assert not websocket_client.is_connected()
    assert websocket_client.ws is None

@pytest.mark.asyncio
async def test_send_message(websocket_client):
    mock_ws = AsyncMock()
    websocket_client.ws = mock_ws
    websocket_client.connected = True
    
    message = WebSocketMessage(method="test", params={"key": "value"}, id=1)
    await websocket_client.send(message)
    mock_ws.send.assert_called_once_with(message.to_json())

@pytest.mark.asyncio
async def test_receive_message(websocket_client):
    mock_ws = AsyncMock()
    mock_ws.recv.return_value = json.dumps({
        "method": "test",
        "params": {"key": "value"},
        "id": 1
    })
    websocket_client.ws = mock_ws
    websocket_client.connected = True
    
    message = await websocket_client.receive()
    assert message["method"] == "test"  # type: ignore
    assert message["params"] == {"key": "value"}  # type: ignore
    assert message["id"] == 1  # type: ignore

@pytest.mark.asyncio
async def test_subscribe(websocket_client):
    with patch.object(websocket_client, 'send', new_callable=AsyncMock) as mock_send:
        await websocket_client.subscribe("BTC/USDT", "ticker")
        mock_send.assert_called_once()
        sent_message = mock_send.call_args[0][0]
        assert isinstance(sent_message, WebSocketMessage)
        assert sent_message.method == "subscribe"
        assert sent_message.params == ["BTC/USDT", "ticker"]
        assert sent_message.id == 1

@pytest.mark.asyncio
async def test_message_handler(websocket_client):
    mock_handler = AsyncMock()
    websocket_client.set_message_handler(mock_handler)
    
    mock_ws = AsyncMock()
    mock_ws.recv.return_value = json.dumps({
        "method": "test",
        "params": {"key": "value"},
        "id": 1
    })
    websocket_client.ws = mock_ws
    websocket_client.connected = True
    
    await websocket_client.receive()
    mock_handler.assert_called_once_with({
        "method": "test",
        "params": {"key": "value"},
        "id": 1
    })
