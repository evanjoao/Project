"""
Data serialization and deserialization utilities for API responses and requests.
Provides a consistent way to convert between Python objects and JSON-compatible formats
with built-in validation and error handling.
"""

from typing import Any, Dict, List, Optional, Type, Union
from datetime import datetime
from marshmallow import Schema, fields, ValidationError, post_load

class BaseSerializer(Schema):
    """Base serializer class providing common functionality for all serializers."""
    
    id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    def handle_error(self, error: ValidationError, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Handle validation errors and return a consistent error response."""
        return {
            "success": False,
            "errors": error.messages
        }

    @post_load
    def make_object(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Convert deserialized data into a dictionary."""
        return data

class SerializerError(Exception):
    """Custom exception for serializer-specific errors."""
    pass

def serialize(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    serializer_class: Type[BaseSerializer],
    many: bool = False
) -> Dict[str, Any]:
    """
    Serialize data using the specified serializer.
    
    Args:
        data: Data to serialize (single object or list)
        serializer_class: Serializer class to use
        many: Whether to serialize multiple objects
        
    Returns:
        Dict containing serialized data or error information
    """
    try:
        serializer = serializer_class()
        result = serializer.dump(data, many=many)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "errors": str(e)}

def deserialize(
    data: Dict[str, Any],
    serializer_class: Type[BaseSerializer]
) -> Dict[str, Any]:
    """
    Deserialize and validate data using the specified serializer.
    
    Args:
        data: Data to deserialize
        serializer_class: Serializer class to use
        
    Returns:
        Dict containing deserialized data or error information
    """
    try:
        serializer = serializer_class()
        result = serializer.load(data)
        return {"success": True, "data": result}
    except ValidationError as e:
        return {"success": False, "errors": e.messages}
    except Exception as e:
        return {"success": False, "errors": str(e)} 