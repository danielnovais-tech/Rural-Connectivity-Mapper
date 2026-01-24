"""Gold layer: aggregated and analysis-ready data."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from src.schemas import MeasurementSchema


class GoldLayer:
    """Gold layer handles data aggregation for consumption.
    
    Creates aggregated views optimized for:
    - Geographic analysis (by H3 cell)
    - Temporal analysis (by time period)
    - Technology comparison
    - Provider comparison
    """
    
    def __init__(self, gold_dir: Path):
        """Initialize gold layer.
        
        Args:
            gold_dir: Path to gold data directory
        """
        self.gold_dir = Path(gold_dir)
        self.gold_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, silver_measurements: List[MeasurementSchema]) -> Dict[str, Path]:
        """Process silver data into gold layer aggregations.
        
        Args:
            silver_measurements: Enriched measurements from silver layer
            
        Returns:
            Dictionary mapping aggregation type to file path
        """
        print(f"\n🏆 Processing {len(silver_measurements)} measurements into gold layer...")
        
        created_files = {}
        
        # Aggregation 1: Geographic (H3 cells)
        geo_file = self._aggregate_geographic(silver_measurements)
        created_files['geographic'] = geo_file
        print(f"  ✓ Geographic aggregation → {geo_file}")
        
        # Aggregation 2: By source
        source_file = self._aggregate_by_source(silver_measurements)
        created_files['by_source'] = source_file
        print(f"  ✓ Source aggregation → {source_file}")
        
        # Aggregation 3: Full dataset (for consumption)
        full_file = self._save_full_dataset(silver_measurements)
        created_files['full_dataset'] = full_file
        print(f"  ✓ Full dataset → {full_file}")
        
        return created_files
    
    def _aggregate_geographic(self, measurements: List[MeasurementSchema]) -> Path:
        """Aggregate measurements by H3 cell.
        
        For each H3 cell, calculates:
        - Average speeds
        - Average latency
        - Count of measurements
        - Average confidence score
        - Technology distribution
        """
        h3_aggregates = defaultdict(lambda: {
            'measurements': [],
            'download_sum': 0.0,
            'download_count': 0,
            'upload_sum': 0.0,
            'upload_count': 0,
            'latency_sum': 0.0,
            'latency_count': 0,
            'confidence_sum': 0.0,
            'confidence_count': 0,
            'technologies': defaultdict(int),
        })
        
        for m in measurements:
            if not m.h3_index:
                continue
            
            agg = h3_aggregates[m.h3_index]
            agg['measurements'].append(m.id)
            
            if m.download_mbps is not None:
                agg['download_sum'] += m.download_mbps
                agg['download_count'] += 1
            
            if m.upload_mbps is not None:
                agg['upload_sum'] += m.upload_mbps
                agg['upload_count'] += 1
            
            if m.latency_ms is not None:
                agg['latency_sum'] += m.latency_ms
                agg['latency_count'] += 1
            
            if m.confidence_score is not None:
                agg['confidence_sum'] += m.confidence_score
                agg['confidence_count'] += 1
            
            agg['technologies'][m.technology.value] += 1
        
        # Calculate averages
        aggregated = {}
        for h3_index, agg in h3_aggregates.items():
            aggregated[h3_index] = {
                'h3_index': h3_index,
                'measurement_count': len(agg['measurements']),
                'avg_download_mbps': round(
                    agg['download_sum'] / agg['download_count'], 2
                ) if agg['download_count'] > 0 else None,
                'avg_upload_mbps': round(
                    agg['upload_sum'] / agg['upload_count'], 2
                ) if agg['upload_count'] > 0 else None,
                'avg_latency_ms': round(
                    agg['latency_sum'] / agg['latency_count'], 2
                ) if agg['latency_count'] > 0 else None,
                'avg_confidence_score': round(
                    agg['confidence_sum'] / agg['confidence_count'], 2
                ) if agg['confidence_count'] > 0 else None,
                'technologies': dict(agg['technologies']),
            }
        
        # Save
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.gold_dir / f"geographic_h3_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump({
                'aggregation_type': 'geographic_h3',
                'timestamp': datetime.utcnow().isoformat(),
                'cell_count': len(aggregated),
                'total_measurements': len(measurements),
                'cells': aggregated,
            }, f, indent=2)
        
        return filepath
    
    def _aggregate_by_source(self, measurements: List[MeasurementSchema]) -> Path:
        """Aggregate measurements by data source.
        
        For each source, calculates summary statistics.
        """
        source_aggregates = defaultdict(lambda: {
            'count': 0,
            'avg_confidence': 0.0,
            'confidence_sum': 0.0,
            'measurements': [],
        })
        
        for m in measurements:
            source = m.source.value
            agg = source_aggregates[source]
            agg['count'] += 1
            agg['measurements'].append(m.id)
            
            if m.confidence_score is not None:
                agg['confidence_sum'] += m.confidence_score
        
        # Calculate averages
        for source, agg in source_aggregates.items():
            agg['avg_confidence'] = round(
                agg['confidence_sum'] / agg['count'], 2
            ) if agg['count'] > 0 else 0.0
            del agg['confidence_sum']  # Remove intermediate sum
        
        # Save
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.gold_dir / f"by_source_{timestamp}.json"
        
        with open(filepath, 'w') as f:
            json.dump({
                'aggregation_type': 'by_source',
                'timestamp': datetime.utcnow().isoformat(),
                'sources': dict(source_aggregates),
            }, f, indent=2)
        
        return filepath
    
    def _save_full_dataset(self, measurements: List[MeasurementSchema]) -> Path:
        """Save complete enriched dataset for consumption.
        
        This is the primary consumption endpoint with all enrichments applied.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filepath = self.gold_dir / f"full_dataset_{timestamp}.json"
        
        data = {
            'dataset_type': 'full_enriched',
            'timestamp': datetime.utcnow().isoformat(),
            'count': len(measurements),
            'measurements': [m.to_dict() for m in measurements]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return filepath
    
    def read_latest(self, aggregation_type: str = 'full_dataset') -> Dict[str, Any]:
        """Read latest gold data.
        
        Args:
            aggregation_type: Type of aggregation to read
            
        Returns:
            Aggregated data dictionary
        """
        pattern = f"{aggregation_type}_*.json"
        files = sorted(self.gold_dir.glob(pattern), reverse=True)
        
        if not files:
            return {}
        
        with open(files[0], 'r') as f:
            return json.load(f)
