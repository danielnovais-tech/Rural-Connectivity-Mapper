"""Canonical schema for connectivity measurements."""

from datetime import datetime
from enum import Enum

try:
    from enum import StrEnum
except ImportError:  # Python < 3.11
    class StrEnum(str, Enum):
        pass
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(StrEnum):
    """Enumeration of data source types."""

    CROWDSOURCE = "crowdsource"
    ANATEL = "anatel"
    IBGE = "ibge"
    STARLINK = "starlink"
    SPEEDTEST = "speedtest"
    MANUAL = "manual"
    OTHER = "other"


class TechnologyType(StrEnum):
    """Enumeration of connectivity technology types."""

    FIBER = "fiber"
    CABLE = "cable"
    DSL = "dsl"
    SATELLITE = "satellite"
    MOBILE_4G = "mobile_4g"
    MOBILE_5G = "mobile_5g"
    FIXED_WIRELESS = "fixed_wireless"
    OTHER = "other"
    UNKNOWN = "unknown"


class ConfidenceBreakdown(BaseModel):
    """Breakdown of confidence score components."""

    model_config = ConfigDict(extra="forbid")

    recency_score: float = Field(ge=0.0, le=100.0, description="Score based on measurement recency (0-100)")
    source_reliability_score: float = Field(
        ge=0.0, le=100.0, description="Score based on data source reliability (0-100)"
    )
    consistency_score: float = Field(
        ge=0.0, le=100.0, description="Score based on measurement consistency/outlier detection (0-100)"
    )
    completeness_score: float = Field(ge=0.0, le=100.0, description="Score based on metadata completeness (0-100)")

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "recency_score": self.recency_score,
            "source_reliability_score": self.source_reliability_score,
            "consistency_score": self.consistency_score,
            "completeness_score": self.completeness_score,
        }


class MeasurementSchema(BaseModel):
    """Canonical schema for connectivity measurements.

    This schema represents the "source of truth" for all connectivity
    measurements in the pipeline, regardless of source.
    """

    model_config = ConfigDict(extra="allow", validate_assignment=True)

    # Identity
    id: str = Field(description="Unique identifier for the measurement")

    # Location (required)
    lat: float = Field(ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    lon: float = Field(ge=-180.0, le=180.0, description="Longitude in decimal degrees")

    # Temporal
    timestamp_utc: datetime = Field(description="Measurement timestamp in UTC")

    # Connectivity metrics
    download_mbps: float | None = Field(default=None, ge=0.0, description="Download speed in Mbps")
    upload_mbps: float | None = Field(default=None, ge=0.0, description="Upload speed in Mbps")
    latency_ms: float | None = Field(default=None, ge=0.0, description="Latency in milliseconds")

    # Technology & Source
    technology: TechnologyType = Field(default=TechnologyType.UNKNOWN, description="Connection technology type")
    source: SourceType = Field(description="Data source identifier")
    provider: str | None = Field(default=None, description="Internet service provider name")

    # Quality & Confidence (populated in silver/gold layers)
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall confidence score (0-100)",
    )
    confidence_breakdown: ConfidenceBreakdown | None = Field(
        default=None,
        description="Breakdown of confidence score components",
    )

    # Additional metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional source-specific metadata")

    # Optional fields
    country: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code (e.g., 'BR', 'US')",
    )
    region: str | None = Field(
        default=None,
        description="Region or state identifier",
    )
    h3_index: str | None = Field(
        default=None,
        description="H3 geospatial index for aggregation",
    )

    @field_validator("timestamp_utc", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        """Parse timestamp from various formats."""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                # Try other common formats
                from datetime import datetime as dt

                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                    try:
                        return dt.strptime(v, fmt)
                    except ValueError:
                        continue
        raise ValueError(f"Unable to parse timestamp: {v}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with proper serialization."""
        data = self.model_dump()
        # Convert datetime to ISO format
        if isinstance(data.get("timestamp_utc"), datetime):
            data["timestamp_utc"] = data["timestamp_utc"].isoformat()
        # Convert enums to values
        if isinstance(data.get("technology"), TechnologyType):
            data["technology"] = data["technology"].value
        if isinstance(data.get("source"), SourceType):
            data["source"] = data["source"].value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MeasurementSchema":
        """Create instance from dictionary."""
        return cls(**data)
