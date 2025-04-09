"""Unit tests for the serializers module."""

import pytest
from typing import Any, Dict, Type
from src.api.serializers import serialize, deserialize
from src.api.tests.conftest import SampleSerializer

def test_serialize_valid_data(
    test_serializer: Type[SampleSerializer],
    valid_serializer_data: Dict[str, Any]
) -> None:
    """Test serialization of valid data."""
    result = serialize(valid_serializer_data, test_serializer)
    assert result["success"]
    assert result["data"]["name"] == valid_serializer_data["name"]
    assert result["data"]["age"] == valid_serializer_data["age"]
    assert result["data"]["email"] == valid_serializer_data["email"]

def test_deserialize_valid_data(
    test_serializer: Type[SampleSerializer],
    valid_serializer_data: Dict[str, Any]
) -> None:
    """Test deserialization of valid data."""
    result = deserialize(valid_serializer_data, test_serializer)
    assert result["success"]
    assert result["data"]["name"] == valid_serializer_data["name"]
    assert result["data"]["age"] == valid_serializer_data["age"]
    assert result["data"]["email"] == valid_serializer_data["email"]

def test_deserialize_invalid_data(
    test_serializer: Type[SampleSerializer],
    invalid_serializer_data: Dict[str, Any]
) -> None:
    """Test deserialization of invalid data."""
    result = deserialize(invalid_serializer_data, test_serializer)
    assert not result["success"]
    assert "errors" in result

def test_serialize_multiple_objects(
    test_serializer: Type[SampleSerializer],
    valid_serializer_data: Dict[str, Any]
) -> None:
    """Test serialization of multiple objects."""
    data = [valid_serializer_data, valid_serializer_data]
    result = serialize(data, test_serializer, many=True)
    assert result["success"]
    assert len(result["data"]) == 2 