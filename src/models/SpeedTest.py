"""SpeedTest model for connectivity measurements."""


class SpeedTest:
    """Represents a speed test measurement with all metrics.

    Attributes:
        download (float): Download speed in Mbps
        upload (float): Upload speed in Mbps
        latency (float): Latency in milliseconds
        jitter (float): Jitter in milliseconds
        packet_loss (float): Packet loss percentage
        obstruction (float): Obstruction percentage (for satellite connections, 0-100)
        stability (float): Connection stability score (0-100)
    """

    def __init__(
        self,
        download: float,
        upload: float,
        latency: float,
        jitter: float = 0.0,
        packet_loss: float = 0.0,
        obstruction: float = 0.0,
        stability: float | None = None
    ):
        """Initialize SpeedTest instance.

        Args:
            download: Download speed in Mbps
            upload: Upload speed in Mbps
            latency: Latency in milliseconds
            jitter: Jitter in milliseconds (default: 0.0)
            packet_loss: Packet loss percentage (default: 0.0)
            obstruction: Obstruction percentage for satellite (default: 0.0)
            stability: Connection stability score, auto-calculated if None
        """
        self.download = download
        self.upload = upload
        self.latency = latency
        self.jitter = jitter
        self.packet_loss = packet_loss
        self.obstruction = obstruction
        self.stability = stability if stability is not None else self.calculate_stability()

    def calculate_stability(self) -> float:
        """Calculate connection stability score based on jitter, packet loss, and obstruction.

        Returns:
            float: Stability score from 0 to 100 (higher is better)
        """
        # Base score starts at 100
        score = 100.0

        # Reduce score based on jitter (higher jitter = lower stability)
        # Jitter penalty: -2 points per ms of jitter, capped at 40 points
        jitter_penalty = min(self.jitter * 2, 40)
        score -= jitter_penalty

        # Reduce score based on packet loss
        # Packet loss penalty: -10 points per 1% packet loss, capped at 40 points
        packet_loss_penalty = min(self.packet_loss * 10, 40)
        score -= packet_loss_penalty

        # Reduce score based on obstruction (for satellite connections)
        # Obstruction penalty: -0.2 points per 1% obstruction, capped at 20 points
        obstruction_penalty = min(self.obstruction * 0.2, 20)
        score -= obstruction_penalty

        # Ensure score is between 0 and 100
        return max(0.0, min(100.0, score))

    def to_dict(self) -> dict:
        """Convert SpeedTest to dictionary representation.

        Returns:
            dict: Dictionary containing all speed test metrics
        """
        return {
            'download': self.download,
            'upload': self.upload,
            'latency': self.latency,
            'jitter': self.jitter,
            'packet_loss': self.packet_loss,
            'obstruction': self.obstruction,
            'stability': self.stability
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SpeedTest':
        """Create SpeedTest instance from dictionary.

        Args:
            data: Dictionary containing speed test metrics

        Returns:
            SpeedTest: New SpeedTest instance
        """
        return cls(
            download=data.get('download', 0.0),
            upload=data.get('upload', 0.0),
            latency=data.get('latency', 0.0),
            jitter=data.get('jitter', 0.0),
            packet_loss=data.get('packet_loss', 0.0),
            obstruction=data.get('obstruction', 0.0),
            stability=data.get('stability')
        )

    def __repr__(self) -> str:
        """String representation of SpeedTest.

        Returns:
            str: Formatted string representation
        """
        return (
            f"SpeedTest(download={self.download:.1f}Mbps, "
            f"upload={self.upload:.1f}Mbps, "
            f"latency={self.latency:.1f}ms, "
            f"stability={self.stability:.1f})"
        )
