"""Confidence score calculation for measurements."""

from datetime import datetime, timezone
from typing import Dict, Optional
import math

from src.schemas import MeasurementSchema, SourceType, ConfidenceBreakdown


class SourceReliabilityWeights:
    """Configurable weights for source reliability scoring.
    
    Higher weight = more reliable source.
    """
    
    WEIGHTS: Dict[SourceType, float] = {
        SourceType.ANATEL: 0.95,      # Official regulatory data - highest trust
        SourceType.IBGE: 0.90,        # Government statistical data
        SourceType.STARLINK: 0.85,    # Direct from provider
        SourceType.SPEEDTEST: 0.75,   # Established testing platform
        SourceType.CROWDSOURCE: 0.60, # Community data - variable quality
        SourceType.MANUAL: 0.50,      # Manual entry - needs verification
        SourceType.OTHER: 0.40,       # Unknown source - lowest trust
    }
    
    @classmethod
    def get_weight(cls, source: SourceType) -> float:
        """Get reliability weight for a source type."""
        return cls.WEIGHTS.get(source, 0.40)


class ConfidenceCalculator:
    """Calculate confidence scores for connectivity measurements.
    
    Confidence score is calculated as a weighted average of:
    - Recency (40%): How recent is the measurement
    - Source Reliability (30%): How trustworthy is the data source
    - Consistency (20%): Outlier detection and validation
    - Completeness (10%): How complete is the metadata
    """
    
    # Component weights
    RECENCY_WEIGHT = 0.40
    SOURCE_WEIGHT = 0.30
    CONSISTENCY_WEIGHT = 0.20
    COMPLETENESS_WEIGHT = 0.10
    
    # Recency thresholds (in days)
    FRESH_THRESHOLD = 7      # Data < 7 days old = 100% score
    STALE_THRESHOLD = 365    # Data > 365 days old = 0% score
    
    # Validation ranges for outlier detection
    MIN_DOWNLOAD_MBPS = 0.1
    MAX_DOWNLOAD_MBPS = 10000.0
    MIN_UPLOAD_MBPS = 0.1
    MAX_UPLOAD_MBPS = 5000.0
    MIN_LATENCY_MS = 1.0
    MAX_LATENCY_MS = 2000.0
    
    @classmethod
    def calculate(
        cls,
        measurement: MeasurementSchema,
        current_time: Optional[datetime] = None
    ) -> tuple[float, ConfidenceBreakdown]:
        """Calculate confidence score and breakdown for a measurement.
        
        Args:
            measurement: The measurement to score
            current_time: Current time for recency calculation (default: now UTC)
            
        Returns:
            Tuple of (overall_score, breakdown)
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        # Calculate component scores
        recency_score = cls._calculate_recency_score(
            measurement.timestamp_utc, current_time
        )
        source_score = cls._calculate_source_score(measurement.source)
        consistency_score = cls._calculate_consistency_score(measurement)
        completeness_score = cls._calculate_completeness_score(measurement)
        
        # Calculate weighted overall score
        overall_score = (
            recency_score * cls.RECENCY_WEIGHT +
            source_score * cls.SOURCE_WEIGHT +
            consistency_score * cls.CONSISTENCY_WEIGHT +
            completeness_score * cls.COMPLETENESS_WEIGHT
        )
        
        breakdown = ConfidenceBreakdown(
            recency_score=round(recency_score, 2),
            source_reliability_score=round(source_score, 2),
            consistency_score=round(consistency_score, 2),
            completeness_score=round(completeness_score, 2),
        )
        
        return round(overall_score, 2), breakdown
    
    @classmethod
    def _calculate_recency_score(
        cls,
        timestamp: datetime,
        current_time: datetime
    ) -> float:
        """Calculate score based on measurement recency.
        
        Fresh data (< 7 days) gets 100%, linearly decaying to 0% at 365 days.
        """
        # Ensure both timestamps are timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        age_days = (current_time - timestamp).total_seconds() / 86400
        
        if age_days < 0:
            # Future timestamp - suspicious, give low score
            return 10.0
        elif age_days <= cls.FRESH_THRESHOLD:
            return 100.0
        elif age_days >= cls.STALE_THRESHOLD:
            return 0.0
        else:
            # Linear decay from 100 to 0
            score = 100.0 * (1 - (age_days - cls.FRESH_THRESHOLD) / 
                           (cls.STALE_THRESHOLD - cls.FRESH_THRESHOLD))
            return max(0.0, score)
    
    @classmethod
    def _calculate_source_score(cls, source: SourceType) -> float:
        """Calculate score based on source reliability.
        
        Returns weighted score (0-100) based on source type.
        """
        weight = SourceReliabilityWeights.get_weight(source)
        return weight * 100.0
    
    @classmethod
    def _calculate_consistency_score(cls, measurement: MeasurementSchema) -> float:
        """Calculate score based on measurement consistency/outlier detection.
        
        Checks if values are within reasonable ranges.
        """
        score = 100.0
        penalties = []
        
        # Check download speed
        if measurement.download_mbps is not None:
            if (measurement.download_mbps < cls.MIN_DOWNLOAD_MBPS or 
                measurement.download_mbps > cls.MAX_DOWNLOAD_MBPS):
                penalties.append(30.0)  # Major penalty for out-of-range
        
        # Check upload speed
        if measurement.upload_mbps is not None:
            if (measurement.upload_mbps < cls.MIN_UPLOAD_MBPS or 
                measurement.upload_mbps > cls.MAX_UPLOAD_MBPS):
                penalties.append(30.0)
        
        # Check latency
        if measurement.latency_ms is not None:
            if (measurement.latency_ms < cls.MIN_LATENCY_MS or 
                measurement.latency_ms > cls.MAX_LATENCY_MS):
                penalties.append(30.0)
        
        # Check for suspicious patterns
        if measurement.download_mbps is not None and measurement.upload_mbps is not None:
            # Upload typically shouldn't exceed download (except some fiber)
            if measurement.upload_mbps > measurement.download_mbps * 2:
                penalties.append(15.0)  # Moderate penalty for unusual ratio
        
        # Apply penalties (cap at 100 total)
        total_penalty = min(100.0, sum(penalties))
        score = max(0.0, score - total_penalty)
        
        return score
    
    @classmethod
    def _calculate_completeness_score(cls, measurement: MeasurementSchema) -> float:
        """Calculate score based on metadata completeness.
        
        More complete data = higher score.
        """
        score = 0.0
        total_fields = 0
        
        # Core fields (required)
        core_fields = ['id', 'lat', 'lon', 'timestamp_utc', 'source']
        total_fields += len(core_fields)
        score += len(core_fields) * 10  # Base score for having required fields
        
        # Metrics fields (weight more)
        metric_fields = ['download_mbps', 'upload_mbps', 'latency_ms']
        for field in metric_fields:
            total_fields += 1
            if getattr(measurement, field) is not None:
                score += 20  # Higher weight for metrics
        
        # Metadata fields
        meta_fields = ['technology', 'provider', 'country', 'region']
        for field in meta_fields:
            total_fields += 1
            value = getattr(measurement, field, None)
            if value is not None and value != "unknown":
                score += 10
        
        # Additional metadata
        if measurement.metadata and len(measurement.metadata) > 0:
            score += 10
        total_fields += 1
        
        # Normalize to 0-100
        max_score = 50 + (3 * 20) + (4 * 10) + 10  # 160 max
        normalized_score = (score / max_score) * 100.0
        
        return min(100.0, normalized_score)
