"""QualityScore model for connectivity quality assessment."""

from .SpeedTest import SpeedTest


class QualityScore:
    """Represents the quality score of a connectivity point.
    
    Attributes:
        overall_score (float): Overall quality score (0-100)
        speed_score (float): Speed component score (0-100)
        latency_score (float): Latency component score (0-100)
        stability_score (float): Stability component score (0-100)
        rating (str): Quality rating (Excellent/Good/Fair/Poor)
    """

    # Weight distribution for overall score calculation
    SPEED_WEIGHT = 0.40
    LATENCY_WEIGHT = 0.30
    STABILITY_WEIGHT = 0.30

    # Starlink 2026 target metrics
    TARGET_DOWNLOAD = 200.0  # Mbps
    TARGET_UPLOAD = 20.0     # Mbps
    TARGET_LATENCY = 20.0    # ms (lower is better)

    def __init__(
        self,
        overall_score: float,
        speed_score: float,
        latency_score: float,
        stability_score: float
    ):
        """Initialize QualityScore instance.

        Args:
            overall_score: Overall quality score (0-100)
            speed_score: Speed component score (0-100)
            latency_score: Latency component score (0-100)
            stability_score: Stability component score (0-100)
        """
        self.overall_score = overall_score
        self.speed_score = speed_score
        self.latency_score = latency_score
        self.stability_score = stability_score
        self.rating = self.get_rating()

    @classmethod
    def calculate(cls, speed_test: SpeedTest) -> 'QualityScore':
        """Calculate quality score from speed test results.

        Args:
            speed_test: SpeedTest instance containing measurements

        Returns:
            QualityScore: Calculated quality score
        """
        # Calculate speed score (average of download and upload percentages)
        download_pct = min(100, (speed_test.download / cls.TARGET_DOWNLOAD) * 100)
        upload_pct = min(100, (speed_test.upload / cls.TARGET_UPLOAD) * 100)
        speed_score = (download_pct + upload_pct) / 2

        # Calculate latency score (inverse - lower latency is better)
        # Perfect score at target latency or below
        if speed_test.latency <= cls.TARGET_LATENCY:
            latency_score = 100.0
        else:
            # Degrade score as latency increases
            # At 100ms latency, score is ~50
            latency_score = max(0, 100 - (speed_test.latency - cls.TARGET_LATENCY) * 1.25)

        # Stability score is directly from speed test
        stability_score = speed_test.stability

        # Calculate overall weighted score
        overall_score = (
            speed_score * cls.SPEED_WEIGHT
            + latency_score * cls.LATENCY_WEIGHT
            + stability_score * cls.STABILITY_WEIGHT
        )

        return cls(
            overall_score=round(overall_score, 2),
            speed_score=round(speed_score, 2),
            latency_score=round(latency_score, 2),
            stability_score=round(stability_score, 2)
        )
    
    def get_rating(self) -> str:
        """Get quality rating based on overall score.

        Returns:
            str: Rating string (Excellent/Good/Fair/Poor)
        """
        if self.overall_score >= 80:
            return "Excellent"
        elif self.overall_score >= 60:
            return "Good"
        elif self.overall_score >= 40:
            return "Fair"
        else:
            return "Poor"

    def to_dict(self) -> dict:
        """Convert QualityScore to dictionary representation.

        Returns:
            Dict: Dictionary containing all quality metrics
        """
        return {
            'overall_score': self.overall_score,
            'speed_score': self.speed_score,
            'latency_score': self.latency_score,
            'stability_score': self.stability_score,
            'rating': self.rating
        }

    def __repr__(self) -> str:
        """String representation of QualityScore.

        Returns:
            str: Formatted string representation
        """
        return (
            f"QualityScore(overall={self.overall_score:.1f}, "
            f"rating={self.rating})"
        )
