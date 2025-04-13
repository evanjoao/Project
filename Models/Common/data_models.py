from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator

class DataSourceType(str, Enum):
    """Types of data sources supported by the system"""
    API = "api"
    DATABASE = "database"
    FILE = "file"

class DataSourceStatus(str, Enum):
    """Possible states of a data source"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class DataSource(BaseModel):
    """
    Represents a data source in the system.
    
    Attributes:
        name: Unique identifier for the data source
        type: Type of data source (api, database, file)
        connection_params: Configuration parameters for connecting to the source
        update_frequency: How often to update data in seconds
        last_update: Timestamp of the last successful update
        status: Current operational status of the data source
    """
    name: str = Field(..., min_length=1, description="Unique identifier for the data source")
    type: DataSourceType = Field(..., description="Type of data source")
    connection_params: Dict[str, Any] = Field(..., description="Configuration parameters for the connection")
    update_frequency: int = Field(..., gt=0, description="Update frequency in seconds")
    last_update: datetime = Field(default_factory=datetime.utcnow, description="Last successful update timestamp")
    status: DataSourceStatus = Field(default=DataSourceStatus.INACTIVE, description="Current operational status")

    @field_validator("connection_params")
    @classmethod
    def validate_connection_params(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that connection parameters contain required fields based on type"""
        if not v:
            raise ValueError("Connection params cannot be empty")
        return v

    def is_active(self) -> bool:
        """Check if the data source is currently active"""
        return self.status == DataSourceStatus.ACTIVE

    def needs_update(self) -> bool:
        """Check if the data source needs to be updated based on frequency"""
        if not self.last_update:
            return True
        time_since_update = (datetime.utcnow() - self.last_update).total_seconds()
        return time_since_update >= self.update_frequency

class DataCache(BaseModel):
    """
    Represents a cache of data with time-based expiration.
    
    Attributes:
        symbol: Identifier for the cached data
        data_type: Type of data being cached
        start_time: Start of the cached time range
        end_time: End of the cached time range
        data: The actual cached data
        last_updated: Timestamp of the last cache update
        ttl: Time-to-live in seconds
    """
    symbol: str = Field(..., min_length=1, description="Identifier for the cached data")
    data_type: str = Field(..., min_length=1, description="Type of data being cached")
    start_time: datetime = Field(..., description="Start of the cached time range")
    end_time: datetime = Field(..., description="End of the cached time range")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="The cached data")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last cache update timestamp")
    ttl: int = Field(..., gt=0, description="Time-to-live in seconds")

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: datetime, info) -> datetime:
        """Validate that end_time is after start_time"""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v

    def is_expired(self) -> bool:
        """Check if the cache has expired based on TTL"""
        time_since_update = (datetime.utcnow() - self.last_updated).total_seconds()
        return time_since_update >= self.ttl

    def get_data_in_time_range(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """
        Get cached data within a specific time range.
        
        Args:
            start: Start of the requested time range
            end: End of the requested time range
            
        Returns:
            List of data points within the requested time range
        """
        return [
            item for item in self.data
            if start <= item.get("timestamp", datetime.min) <= end
        ] 