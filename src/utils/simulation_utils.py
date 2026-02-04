"""Simulation utilities for router impact analysis."""

import logging
import random

logger = logging.getLogger(__name__)


def simulate_router_impact(data: list[dict]) -> list[dict]:
    """Simulate the impact of router improvements on quality scores.
    
    Applies a random improvement of 15-25% to quality scores to simulate
    the effect of router upgrades or optimizations.
    
    Args:
        data: List of connectivity point dictionaries
        
    Returns:
        List[Dict]: Updated data with improved quality scores
    """
    try:
        logger.info(f"Simulating router impact on {len(data)} points...")
        
        improved_data = []
        
        for point in data:
            # Create a copy to avoid modifying original
            improved_point = point.copy()
            
            # Generate random improvement factor between 15% and 25%
            improvement_factor = random.uniform(1.15, 1.25)
            
            # Update quality score if present
            if 'quality_score' in improved_point:
                qs = improved_point['quality_score'].copy()
                
                # Apply improvement to all score components
                qs['overall_score'] = min(100, qs.get('overall_score', 0) * improvement_factor)
                qs['speed_score'] = min(100, qs.get('speed_score', 0) * improvement_factor)
                qs['latency_score'] = min(100, qs.get('latency_score', 0) * improvement_factor)
                qs['stability_score'] = min(100, qs.get('stability_score', 0) * improvement_factor)
                
                # Update rating based on new overall score
                overall = qs['overall_score']
                if overall >= 80:
                    qs['rating'] = "Excellent"
                elif overall >= 60:
                    qs['rating'] = "Good"
                elif overall >= 40:
                    qs['rating'] = "Fair"
                else:
                    qs['rating'] = "Poor"
                
                # Round scores to 2 decimal places
                qs['overall_score'] = round(qs['overall_score'], 2)
                qs['speed_score'] = round(qs['speed_score'], 2)
                qs['latency_score'] = round(qs['latency_score'], 2)
                qs['stability_score'] = round(qs['stability_score'], 2)
                
                improved_point['quality_score'] = qs
                
                logger.debug(
                    f"Point {point.get('id', 'N/A')}: "
                    f"{point['quality_score'].get('overall_score', 0):.1f} -> "
                    f"{qs['overall_score']:.1f} "
                    f"(+{(improvement_factor - 1) * 100:.1f}%)"
                )
            
            improved_data.append(improved_point)
        
        logger.info("Router impact simulation completed")
        return improved_data
    
    except Exception as e:
        logger.error(f"Error simulating router impact: {e}")
        raise
