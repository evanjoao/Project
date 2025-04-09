from datetime import datetime
from typing import Optional, List, Dict, Any, Type, ClassVar, TypeVar, cast
from pydantic import BaseModel, Field, validator
from dateutil.parser import parse

T = TypeVar('T', bound='TimeRange')

class TimeRange(BaseModel):
    """Time range for filtering data."""
    start_time: datetime = Field(..., description="Start time of the range")
    end_time: datetime = Field(..., description="End time of the range")

    @validator('end_time')
    def end_time_must_be_after_start_time(cls: Any, v: datetime, values: Dict[str, Any]) -> datetime:
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class PaginationParams(BaseModel):
    """Parameters for paginated API responses."""
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=10, ge=1, le=100, description="Items per page")

class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error message")
    code: int = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class ValidationError(ErrorResponse):
    """Validation error response."""
    errors: List[Dict[str, str]] = Field(..., description="List of validation errors")

def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string into datetime object."""
    try:
        return parse(dt_str)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {dt_str}") from e
