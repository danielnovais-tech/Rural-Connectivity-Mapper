"""Machine Learning utilities for connectivity analysis and predictions."""

import logging
import math

# Optional numpy + sklearn imports - gracefully degrade if not available or incompatible
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except Exception:  # pragma: no cover
    np = None  # type: ignore[assignment]
    NUMPY_AVAILABLE = False

try:
    if not NUMPY_AVAILABLE:
        raise ImportError("numpy not available")
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


def calculate_distance_from_major_city(latitude: float, longitude: float) -> float:
    """Calculate approximate distance from nearest major Brazilian city.
    
    Uses simplified distances to major cities (São Paulo, Rio, Brasília, Salvador, Fortaleza).
    
    Args:
        latitude: Point latitude
        longitude: Point longitude
        
    Returns:
        float: Approximate distance in kilometers to nearest major city
    """
    # Major Brazilian cities (lat, lon)
    major_cities = [
        (-23.5505, -46.6333),  # São Paulo
        (-22.9068, -43.1729),  # Rio de Janeiro
        (-15.7939, -47.8828),  # Brasília
        (-12.9714, -38.5014),  # Salvador
        (-3.7172, -38.5434),   # Fortaleza
    ]
    
    min_distance = float('inf')
    
    for city_lat, city_lon in major_cities:
        # Haversine formula for great circle distance
        dlat = math.radians(city_lat - latitude)
        dlon = math.radians(city_lon - longitude)
        
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(math.radians(latitude)) * math.cos(math.radians(city_lat)) * 
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in km
        distance = 6371 * c
        min_distance = min(min_distance, distance)
    
    return round(min_distance, 2)


def extract_geospatial_features(data: list[dict]):
    """Extract geospatial features for ML models.
    
    Features include:
    - Latitude
    - Longitude
    - Distance from major city
    - Current quality score
    - Download speed
    - Upload speed
    - Latency
    
    Args:
        data: List of connectivity point dictionaries
        
    Returns:
        Feature matrix for ML models (NumPy array when available)
    """
    logger.info(f"Extracting geospatial features from {len(data)} points...")

    if not NUMPY_AVAILABLE or np is None:
        raise RuntimeError("NumPy is required for extract_geospatial_features")
    
    features = []
    
    for point in data:
        lat = point.get('latitude', 0)
        lon = point.get('longitude', 0)
        
        distance_from_city = calculate_distance_from_major_city(lat, lon)
        
        quality_score = point.get('quality_score', {}).get('overall_score', 0)
        speed_test = point.get('speed_test', {})
        
        feature_vector = [
            lat,
            lon,
            distance_from_city,
            quality_score,
            speed_test.get('download', 0),
            speed_test.get('upload', 0),
            speed_test.get('latency', 0),
        ]
        
        features.append(feature_vector)
    
    return np.array(features)


def predict_improvement_potential(data: list[dict]) -> list[dict]:
    """Predict improvement potential for each connectivity point using a rule-based score.
    
    Uses a heuristic formula based on geospatial features (e.g., distance from major cities)
    and current connectivity metrics (e.g., overall quality score) to estimate which areas
    have the highest potential for improvement. Rural areas far from major cities with poor
    connectivity receive higher improvement potential and priority scores.
    
    Args:
        data: List of connectivity point dictionaries
        
    Returns:
        List[Dict]: Data enriched with improvement potential scores and related metrics
    """
    try:
        logger.info("Predicting improvement potential with ML...")
        
        if len(data) < 3:
            logger.warning("Insufficient data for ML predictions (minimum 3 points required)")
            # Still provide basic enrichment for consistency
            enriched_data = []
            for point in data:
                enriched_point = point.copy()
                distance = calculate_distance_from_major_city(
                    point.get('latitude', 0), 
                    point.get('longitude', 0)
                )
                current_score = point.get('quality_score', {}).get('overall_score', 0)
                quality_gap = max(100 - current_score, 0)
                rural_factor = min(distance / 100, 2.0)
                potential = quality_gap * (1 + rural_factor * 0.5)
                
                enriched_point['ml_analysis'] = {
                    'improvement_potential': round(potential, 2),
                    'distance_from_city_km': round(distance, 2),
                    'is_rural': bool(distance > 100),
                    'priority_score': round(potential, 2) if potential > 0 else 0
                }
                enriched_data.append(enriched_point)
            return enriched_data
        
        # Extract features
        X = extract_geospatial_features(data)
        
        # Calculate improvement potential score (inverse of current quality, distance weighted)
        # Higher score = more potential for improvement
        improvement_scores = []
        for i, point in enumerate(data):
            current_score = point.get('quality_score', {}).get('overall_score', 0)
            distance = X[i, 2]  # Distance from major city
            
            # Rural areas (far from cities) with poor connectivity have high potential
            rural_factor = min(distance / 100, 2.0)  # Cap at 2x
            quality_gap = max(100 - current_score, 0)
            
            potential = quality_gap * (1 + rural_factor * 0.5)
            improvement_scores.append(potential)
        
        # Add predictions to data
        enriched_data = []
        max_score = max(improvement_scores) if improvement_scores else 1
        for i, point in enumerate(data):
            enriched_point = point.copy()
            priority = (improvement_scores[i] / max_score * 100) if max_score > 0 else 0
            enriched_point['ml_analysis'] = {
                'improvement_potential': round(improvement_scores[i], 2),
                'distance_from_city_km': round(X[i, 2], 2),
                'is_rural': bool(X[i, 2] > 100),  # >100km = rural
                'priority_score': round(priority, 2)
            }
            enriched_data.append(enriched_point)
        
        logger.info("ML predictions completed")
        return enriched_data
    
    except Exception as e:
        logger.error(f"Error in ML predictions: {e}")
        raise


def identify_expansion_zones(data: list[dict], n_zones: int = 3) -> dict:
    """Identify optimal zones for Starlink expansion using clustering.
    
    Uses K-means clustering to identify geographic zones that would benefit most
    from Starlink expansion based on connectivity gaps and rural characteristics.
    
    Args:
        data: List of connectivity point dictionaries
        n_zones: Number of expansion zones to identify
        
    Returns:
        Dict: Analysis of expansion zones with recommendations
    """
    try:
        logger.info(f"Identifying {n_zones} optimal expansion zones...")
        
        if len(data) < n_zones:
            logger.warning(f"Insufficient data for {n_zones} zones (have {len(data)} points)")
            n_zones = max(1, len(data))
        
        # Extract geographic and quality features
        features = []
        for point in data:
            lat = point.get('latitude', 0)
            lon = point.get('longitude', 0)
            quality = point.get('quality_score', {}).get('overall_score', 0)
            distance = calculate_distance_from_major_city(lat, lon)
            
            # Weight by quality gap and rurality
            quality_gap = 100 - quality
            rural_weight = min(distance / 100, 2.0)
            
            features.append([lat, lon, quality_gap * rural_weight])
        
        X = np.array(features)
        
        # Apply K-means clustering
        kmeans = KMeans(n_clusters=n_zones, random_state=42, n_init='auto')
        clusters = kmeans.fit_predict(X)
        
        # Analyze each zone
        zones = {}
        for zone_id in range(n_zones):
            zone_points = [data[i] for i, c in enumerate(clusters) if c == zone_id]
            
            if not zone_points:
                continue
            
            # Calculate zone statistics
            avg_quality = np.mean([p.get('quality_score', {}).get('overall_score', 0) 
                                   for p in zone_points])
            avg_distance = np.mean([calculate_distance_from_major_city(
                                    p.get('latitude', 0), p.get('longitude', 0)) 
                                   for p in zone_points])
            
            center_lat = kmeans.cluster_centers_[zone_id][0]
            center_lon = kmeans.cluster_centers_[zone_id][1]
            
            # Calculate priority (higher for rural areas with poor connectivity)
            rural_factor = min(avg_distance / 100, 2.0)
            quality_gap = max(100 - avg_quality, 0)
            priority = quality_gap * (1 + rural_factor)
            
            zones[f'zone_{zone_id + 1}'] = {
                'center': {
                    'latitude': round(center_lat, 4),
                    'longitude': round(center_lon, 4)
                },
                'point_count': int(len(zone_points)),
                'avg_quality_score': round(avg_quality, 2),
                'avg_distance_from_city_km': round(avg_distance, 2),
                'is_primarily_rural': bool(avg_distance > 100),
                'priority_score': round(priority, 2),
                'recommendation': _generate_zone_recommendation(float(avg_quality), float(avg_distance))
            }
        
        # Sort zones by priority
        sorted_zones = dict(sorted(zones.items(), 
                                   key=lambda x: x[1]['priority_score'], 
                                   reverse=True))
        
        result = {
            'total_zones': len(sorted_zones),
            'zones': sorted_zones,
            'top_priority_zone': list(sorted_zones.keys())[0] if sorted_zones else None
        }
        
        logger.info(f"Identified {len(sorted_zones)} expansion zones")
        return result
    
    except Exception as e:
        logger.error(f"Error identifying expansion zones: {e}")
        raise


def _generate_zone_recommendation(avg_quality: float, avg_distance: float) -> str:
    """Generate recommendation text for an expansion zone.
    
    Args:
        avg_quality: Average quality score in zone
        avg_distance: Average distance from major city in km
        
    Returns:
        str: Recommendation text
    """
    is_rural = avg_distance > 100
    
    if is_rural and avg_quality < 60:
        return "HIGH PRIORITY: Rural area with poor connectivity - ideal for Starlink expansion"
    elif is_rural and avg_quality < 80:
        return "MEDIUM PRIORITY: Rural area with moderate connectivity - good Starlink candidate"
    elif not is_rural and avg_quality < 60:
        return "MEDIUM PRIORITY: Urban area with poor connectivity - consider infrastructure upgrade"
    elif is_rural:
        return "LOW PRIORITY: Rural area with good connectivity - monitor for degradation"
    else:
        return "LOW PRIORITY: Urban area with good connectivity - maintain current service"


def analyze_starlink_roi(data: list[dict]) -> dict:
    """Analyze ROI for Starlink deployment using ML-enhanced metrics.
    
    Evaluates potential return on investment for Starlink expansion by analyzing
    connectivity gaps, rural population proxy, and improvement potential.
    
    Args:
        data: List of connectivity point dictionaries
        
    Returns:
        Dict: ROI analysis with recommendations
    """
    try:
        logger.info("Analyzing Starlink ROI with ML metrics...")
        
        if not data:
            return {
                'total_points': 0,
                'rural_points': 0,
                'high_priority_points': 0,
                'recommendations': []
            }
        
        # Enrich data with ML predictions
        enriched_data = predict_improvement_potential(data)
        
        # Categorize points
        rural_points = []
        high_priority_points = []
        total_improvement_potential = 0
        
        for point in enriched_data:
            ml = point.get('ml_analysis', {})
            
            if ml.get('is_rural', False):
                rural_points.append(point)
            
            if ml.get('priority_score', 0) > 70:
                high_priority_points.append(point)
            
            total_improvement_potential += ml.get('improvement_potential', 0)
        
        # Calculate ROI metrics
        avg_current_quality = np.mean([p.get('quality_score', {}).get('overall_score', 0) 
                                       for p in data])
        
        rural_percentage = (len(rural_points) / len(data)) * 100 if data else 0
        
        # Generate recommendations
        recommendations = []
        
        if rural_percentage > 50:
            recommendations.append(
                "STRONG FIT: Over 50% of points are in rural areas - excellent market for Starlink"
            )
        elif rural_percentage > 30:
            recommendations.append(
                "GOOD FIT: Significant rural population - viable Starlink market"
            )
        
        if avg_current_quality < 60:
            recommendations.append(
                "HIGH OPPORTUNITY: Average quality below 60 - significant room for improvement"
            )
        
        if len(high_priority_points) > len(data) * 0.3:
            recommendations.append(
                f"URGENT ACTION: {len(high_priority_points)} high-priority areas need immediate attention"
            )
        
        if not recommendations:
            recommendations.append(
                "MONITOR: Current connectivity is adequate - focus on maintenance and monitoring"
            )
        
        result = {
            'total_points': len(data),
            'rural_points': len(rural_points),
            'rural_percentage': round(rural_percentage, 2),
            'high_priority_points': len(high_priority_points),
            'avg_current_quality': round(avg_current_quality, 2),
            'total_improvement_potential': round(total_improvement_potential, 2),
            'avg_improvement_potential': round(total_improvement_potential / len(data), 2) if data else 0,
            'recommendations': recommendations,
            'starlink_suitability_score': round(
                (rural_percentage / 100 * 50) + 
                ((100 - avg_current_quality) / 100 * 50), 2
            )
        }
        
        logger.info("ROI analysis completed")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing Starlink ROI: {e}")
        raise


def generate_ml_report(data: list[dict]) -> dict:
    """Generate comprehensive ML-enhanced analysis report.
    
    Combines all ML analysis functions to provide a complete picture of
    connectivity status, improvement potential, and expansion opportunities.
    
    Args:
        data: List of connectivity point dictionaries
        
    Returns:
        Dict: Comprehensive ML analysis report
    """
    try:
        logger.info("Generating comprehensive ML report...")
        
        # Handle empty input early to avoid unnecessary ML processing
        if not data:
            logger.warning("No data provided for ML report generation")
            empty_report = {
                'summary': {
                    'total_points_analyzed': 0,
                    'ml_model_version': '1.0.0',
                    'analysis_date': 'Real-time'
                },
                'roi_analysis': {},
                'expansion_zones': {},
                'top_priority_areas': [],
                'enriched_data': []
            }
            return empty_report
        
        # Get ML predictions for each point
        enriched_data = predict_improvement_potential(data)
        
        # Identify expansion zones
        expansion_zones = identify_expansion_zones(enriched_data, n_zones=3)
        
        # Analyze ROI
        roi_analysis = analyze_starlink_roi(enriched_data)
        
        # Extract top priority points
        sorted_points = sorted(enriched_data, 
                              key=lambda x: x.get('ml_analysis', {}).get('priority_score', 0),
                              reverse=True)
        
        top_priorities = []
        for point in sorted_points[:5]:  # Top 5
            ml = point.get('ml_analysis', {})
            top_priorities.append({
                'provider': point.get('provider', 'Unknown'),
                'latitude': point.get('latitude', 0),
                'longitude': point.get('longitude', 0),
                'current_quality': point.get('quality_score', {}).get('overall_score', 0),
                'priority_score': ml.get('priority_score', 0),
                'distance_from_city_km': ml.get('distance_from_city_km', 0),
                'is_rural': ml.get('is_rural', False)
            })
        
        report = {
            'summary': {
                'total_points_analyzed': len(data),
                'ml_model_version': '1.0.0',
                'analysis_date': 'Real-time'
            },
            'roi_analysis': roi_analysis,
            'expansion_zones': expansion_zones,
            'top_priority_areas': top_priorities,
            'enriched_data': enriched_data
        }
        
        logger.info("ML report generation completed")
        return report
    
    except Exception as e:
        logger.error(f"Error generating ML report: {e}")
        raise
