"""Analysis utilities for temporal evolution and trends."""

import logging
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

# Optional sklearn imports - gracefully degrade if not available
try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except Exception:  # pragma: no cover
    SKLEARN_AVAILABLE = False

from .i18n_utils import get_translation

logger = logging.getLogger(__name__)


def analyze_temporal_evolution(data: List[Dict], language: str = 'en') -> Dict:
    """Analyze temporal evolution of connectivity quality.
    
    Groups data by date and calculates statistics to identify trends.
    
    Args:
        data: List of connectivity point dictionaries
        language: Language code for insights (en, pt). Default: 'en'
        
    Returns:
        Dict: Analysis results with trends and insights
    """
    try:
        logger.info(f"Analyzing temporal evolution of {len(data)} points...")
        
        if not data:
            logger.warning("No data provided for temporal analysis")
            return {
                'total_points': 0,
                'date_range': {},
                'daily_averages': {},
                'trends': {},
                'insights': []
            }
        
        # Group data by date
        daily_data = defaultdict(list)
        
        for point in data:
            timestamp = point.get('timestamp')
            if not timestamp:
                continue
            
            try:
                # Parse timestamp and extract date
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                date_key = dt.date().isoformat()
                
                # Extract quality score
                qs = point.get('quality_score', {})
                overall_score = qs.get('overall_score', 0)
                
                daily_data[date_key].append({
                    'overall_score': overall_score,
                    'provider': point.get('provider', 'Unknown'),
                    'speed_test': point.get('speed_test', {})
                })
            except Exception as e:
                logger.warning(f"Error parsing timestamp '{timestamp}': {e}")
                continue
        
        # Calculate daily averages
        daily_averages = {}
        for date, points in daily_data.items():
            scores = [p['overall_score'] for p in points]
            downloads = [p['speed_test'].get('download', 0) for p in points]
            latencies = [p['speed_test'].get('latency', 0) for p in points]
            
            daily_averages[date] = {
                'count': len(points),
                'avg_quality_score': round(sum(scores) / len(scores), 2) if scores else 0,
                'avg_download': round(sum(downloads) / len(downloads), 2) if downloads else 0,
                'avg_latency': round(sum(latencies) / len(latencies), 2) if latencies else 0,
                'min_quality_score': round(min(scores), 2) if scores else 0,
                'max_quality_score': round(max(scores), 2) if scores else 0
            }
        
        # Calculate overall trends
        all_scores = [p.get('quality_score', {}).get('overall_score', 0) for p in data]
        all_downloads = [p.get('speed_test', {}).get('download', 0) for p in data]
        all_latencies = [p.get('speed_test', {}).get('latency', 0) for p in data]
        
        trends = {
            'avg_quality_score': round(sum(all_scores) / len(all_scores), 2) if all_scores else 0,
            'avg_download': round(sum(all_downloads) / len(all_downloads), 2) if all_downloads else 0,
            'avg_latency': round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 0,
            'min_quality_score': round(min(all_scores), 2) if all_scores else 0,
            'max_quality_score': round(max(all_scores), 2) if all_scores else 0
        }
        
        # Generate insights with translations
        insights = []
        
        if trends['avg_quality_score'] >= 80:
            insights.append(get_translation('insight_excellent_quality', language))
        elif trends['avg_quality_score'] >= 60:
            insights.append(get_translation('insight_good_quality', language))
        else:
            insights.append(get_translation('insight_poor_quality', language))
        
        if trends['avg_download'] >= 100:
            insights.append(get_translation('insight_download_excellent', language))
        elif trends['avg_download'] >= 50:
            insights.append(get_translation('insight_download_good', language))
        else:
            insights.append(get_translation('insight_download_poor', language))
        
        if trends['avg_latency'] <= 40:
            insights.append(get_translation('insight_latency_good', language))
        else:
            insights.append(get_translation('insight_latency_poor', language))
        
        # Analyze by provider
        provider_stats = defaultdict(list)
        for point in data:
            provider = point.get('provider', 'Unknown')
            score = point.get('quality_score', {}).get('overall_score', 0)
            provider_stats[provider].append(score)
        
        best_provider = None
        best_avg = 0
        for provider, scores in provider_stats.items():
            avg = sum(scores) / len(scores) if scores else 0
            if avg > best_avg:
                best_avg = avg
                best_provider = provider
        
        if best_provider:
            insights.append(get_translation('insight_best_provider', language, 
                                          provider=best_provider, score=f"{best_avg:.1f}"))
        
        # Prepare date range
        dates = sorted(daily_data.keys())
        date_range = {
            'start': dates[0] if dates else None,
            'end': dates[-1] if dates else None,
            'days': len(dates)
        }
        
        result = {
            'total_points': len(data),
            'date_range': date_range,
            'daily_averages': daily_averages,
            'trends': trends,
            'insights': insights,
            'provider_stats': {
                provider: {
                    'count': len(scores),
                    'avg_score': round(sum(scores) / len(scores), 2) if scores else 0
                }
                for provider, scores in provider_stats.items()
            }
        }
        
        logger.info("Temporal analysis completed")
        return result
    
    except Exception as e:
        logger.error(f"Error analyzing temporal evolution: {e}")
        raise



def cluster_connectivity_points(data: List[Dict], n_clusters: int = 3) -> Dict:
    """Cluster connectivity points using K-Means based on quality metrics.
    
    Groups connectivity points into clusters based on download speed, upload speed,
    latency, and quality score to identify patterns and similar connectivity profiles.
    
    Args:
        data: List of connectivity point dictionaries
        n_clusters: Number of clusters to create (default: 3)
        
    Returns:
        Dict: Clustering results with cluster assignments and centroids
    """
    if not SKLEARN_AVAILABLE:
        logger.warning("Clustering not available - sklearn not installed")
        return {
            'clusters': {},
            'cluster_labels': [],
            'cluster_stats': {},
            'n_clusters': 0,
            'features_used': [],
            'error': 'sklearn not available'
        }
    
    try:
        logger.info(f"Clustering {len(data)} connectivity points into {n_clusters} clusters...")
        
        if not data or len(data) < n_clusters:
            logger.warning(f"Insufficient data for clustering (need at least {n_clusters} points)")
            return {
                'clusters': {},
                'cluster_labels': [],
                'cluster_stats': {},
                'n_clusters': 0,
                'features_used': []
            }
        
        # Extract features for clustering
        features = []
        point_ids = []
        
        for idx, point in enumerate(data):
            speed_test = point.get('speed_test', {})
            quality_score = point.get('quality_score', {})
            
            # Feature vector: [download, upload, latency, overall_score]
            feature_vector = [
                speed_test.get('download', 0),
                speed_test.get('upload', 0),
                speed_test.get('latency', 0),
                quality_score.get('overall_score', 0)
            ]
            
            features.append(feature_vector)
            point_ids.append(point.get('id', f'point_{idx}'))
        
        # Convert to numpy array
        X = np.array(features)
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Perform K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        cluster_labels = kmeans.fit_predict(X_scaled)
        
        # Inverse transform centroids to original scale
        centroids_scaled = kmeans.cluster_centers_
        centroids = scaler.inverse_transform(centroids_scaled)
        
        # Organize results by cluster
        clusters = defaultdict(list)
        for idx, label in enumerate(cluster_labels):
            clusters[int(label)].append({
                'id': point_ids[idx],
                'data': data[idx],
                'feature_idx': idx  # Store feature index for efficient lookup
            })
        
        # Calculate cluster statistics
        cluster_stats = {}
        feature_names = ['download', 'upload', 'latency', 'quality_score']
        
        for cluster_id, points in clusters.items():
            # Use stored feature index for efficient lookup
            cluster_features = [features[p['feature_idx']] for p in points]
            cluster_array = np.array(cluster_features)
            
            cluster_stats[cluster_id] = {
                'count': len(points),
                'centroid': {
                    feature_names[i]: round(centroids[cluster_id][i], 2)
                    for i in range(len(feature_names))
                },
                'avg_metrics': {
                    feature_names[i]: round(np.mean(cluster_array[:, i]), 2)
                    for i in range(len(feature_names))
                },
                'std_metrics': {
                    feature_names[i]: round(np.std(cluster_array[:, i]), 2)
                    for i in range(len(feature_names))
                }
            }
        
        result = {
            'clusters': dict(clusters),
            'cluster_labels': cluster_labels.tolist(),
            'cluster_stats': cluster_stats,
            'n_clusters': n_clusters,
            'features_used': feature_names
        }
        
        logger.info(f"Clustering completed with {n_clusters} clusters")
        return result
    
    except Exception as e:
        logger.error(f"Error clustering connectivity points: {e}")
        raise


def forecast_quality_scores(data: List[Dict], forecast_horizon: int = 5) -> Dict:
    """Forecast future quality scores based on historical connectivity data.
    
    Uses historical patterns and clustering to predict future quality scores
    for connectivity points. Implements a simple trend-based forecasting approach
    combined with cluster-based predictions.
    
    Args:
        data: List of connectivity point dictionaries with historical data
        forecast_horizon: Number of future periods to forecast (default: 5)
        
    Returns:
        Dict: Forecast results with predicted quality scores and confidence metrics
    """
    try:
        logger.info(f"Forecasting quality scores for {forecast_horizon} future periods...")
        
        if not data:
            logger.warning("No data provided for forecasting")
            return {
                'forecasts': [],
                'baseline_score': 0,
                'trend': 'stable',
                'confidence': 'low'
            }
        
        # Sort data by timestamp
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''))
        
        # Extract historical quality scores
        historical_scores = []
        timestamps = []
        
        for point in sorted_data:
            quality_score = point.get('quality_score', {})
            overall_score = quality_score.get('overall_score', 0)
            timestamp = point.get('timestamp', '')
            
            if overall_score > 0 and timestamp:
                historical_scores.append(overall_score)
                timestamps.append(timestamp)
        
        if len(historical_scores) < 2:
            logger.warning("Insufficient historical data for forecasting")
            baseline = historical_scores[0] if historical_scores else 0
            return {
                'forecasts': [baseline] * forecast_horizon,
                'baseline_score': baseline,
                'trend': 'stable',
                'confidence': 'low'
            }
        
        # Calculate baseline statistics
        baseline_score = np.mean(historical_scores)
        score_std = np.std(historical_scores)
        
        # Determine trend
        if len(historical_scores) >= 3:
            # Simple linear trend
            recent_avg = np.mean(historical_scores[-3:])
            older_avg = np.mean(historical_scores[:-3]) if len(historical_scores) > 3 else historical_scores[0]
            trend_direction = recent_avg - older_avg
            
            if trend_direction > 5:
                trend = 'improving'
                trend_factor = 1.02  # 2% improvement per period
            elif trend_direction < -5:
                trend = 'declining'
                trend_factor = 0.98  # 2% decline per period
            else:
                trend = 'stable'
                trend_factor = 1.0
        else:
            trend = 'stable'
            trend_factor = 1.0
        
        # Generate forecasts
        forecasts = []
        last_score = historical_scores[-1]
        
        for i in range(forecast_horizon):
            # Apply trend factor
            predicted_score = last_score * (trend_factor ** (i + 1))
            
            # Add some regression to mean (scores tend to stabilize)
            predicted_score = 0.7 * predicted_score + 0.3 * baseline_score
            
            # Ensure score stays in valid range [0, 100]
            predicted_score = max(0, min(100, predicted_score))
            forecasts.append(round(predicted_score, 2))
        
        # Determine confidence based on historical variance
        if score_std < 5:
            confidence = 'high'
        elif score_std < 15:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        # Optional cluster-based enhancement for larger datasets
        # Only use clustering if we have sufficient data and it would be meaningful
        if len(data) >= 5:
            try:
                clustering_result = cluster_connectivity_points(data, n_clusters=min(3, len(data)))
                # Use cluster centroids to refine forecasts
                cluster_stats = clustering_result.get('cluster_stats', {})
                if cluster_stats:
                    cluster_quality_scores = [
                        stats['centroid'].get('quality_score', baseline_score)
                        for stats in cluster_stats.values()
                    ]
                    cluster_avg = np.mean(cluster_quality_scores)
                    # Blend cluster-based prediction with trend-based (lighter weight)
                    forecasts = [
                        round(0.7 * f + 0.3 * cluster_avg, 2)
                        for f in forecasts
                    ]
            except Exception as e:
                logger.warning(f"Could not use clustering for forecast enhancement: {e}")
        
        result = {
            'forecasts': forecasts,
            'baseline_score': round(baseline_score, 2),
            'trend': trend,
            'confidence': confidence,
            'historical_mean': round(np.mean(historical_scores), 2),
            'historical_std': round(score_std, 2),
            'forecast_horizon': forecast_horizon
        }
        
        logger.info(f"Forecasting completed: trend={trend}, confidence={confidence}")
        return result
    
    except Exception as e:
        logger.error(f"Error forecasting quality scores: {e}")
        return {
            'forecasts': [],
            'baseline_score': 0.0,
            'trend': 'unknown',
            'confidence': 'low',
            'historical_mean': 0.0,
            'historical_std': 0.0,
            'forecast_horizon': 0
        }


def compare_providers(data: List[Dict]) -> Dict:
    """Compare ISP performance with detailed metrics analysis.
    
    Analyzes and compares providers including satellite-specific metrics
    like jitter, packet loss, and obstruction for Starlink comparisons.
    
    Args:
        data: List of connectivity point dictionaries
        
    Returns:
        Dict: Detailed provider comparison with metrics breakdown
    """
    try:
        logger.info(f"Comparing providers across {len(data)} points...")
        
        if not data:
            logger.warning("No data provided for provider comparison")
            return {'providers': {}}
        
        # Collect metrics by provider
        provider_metrics = defaultdict(lambda: {
            'quality_scores': [],
            'download_speeds': [],
            'upload_speeds': [],
            'latencies': [],
            'jitters': [],
            'packet_losses': [],
            'obstructions': [],
            'stabilities': []
        })
        
        for point in data:
            provider = point.get('provider', 'Unknown')
            quality_score = point.get('quality_score', {})
            speed_test = point.get('speed_test', {})
            
            provider_metrics[provider]['quality_scores'].append(
                quality_score.get('overall_score', 0)
            )
            provider_metrics[provider]['download_speeds'].append(
                speed_test.get('download', 0)
            )
            provider_metrics[provider]['upload_speeds'].append(
                speed_test.get('upload', 0)
            )
            provider_metrics[provider]['latencies'].append(
                speed_test.get('latency', 0)
            )
            provider_metrics[provider]['jitters'].append(
                speed_test.get('jitter', 0)
            )
            provider_metrics[provider]['packet_losses'].append(
                speed_test.get('packet_loss', 0)
            )
            provider_metrics[provider]['obstructions'].append(
                speed_test.get('obstruction', 0)
            )
            provider_metrics[provider]['stabilities'].append(
                speed_test.get('stability', 0)
            )
        
        # Calculate statistics for each provider
        providers_summary = {}
        
        def calculate_avg(lst):
            """Helper to calculate average of a list."""
            return round(sum(lst) / len(lst), 2) if lst else 0
        
        def calculate_max(lst):
            """Helper to calculate max of a list."""
            return round(max(lst), 2) if lst else 0
        
        def calculate_min(lst):
            """Helper to calculate min of a list."""
            return round(min(lst), 2) if lst else 0
        
        for provider, metrics in provider_metrics.items():
            providers_summary[provider] = {
                'count': len(metrics['quality_scores']),
                'quality_score': {
                    'avg': calculate_avg(metrics['quality_scores']),
                    'min': calculate_min(metrics['quality_scores']),
                    'max': calculate_max(metrics['quality_scores'])
                },
                'download': {
                    'avg': calculate_avg(metrics['download_speeds']),
                    'min': calculate_min(metrics['download_speeds']),
                    'max': calculate_max(metrics['download_speeds'])
                },
                'upload': {
                    'avg': calculate_avg(metrics['upload_speeds']),
                    'min': calculate_min(metrics['upload_speeds']),
                    'max': calculate_max(metrics['upload_speeds'])
                },
                'latency': {
                    'avg': calculate_avg(metrics['latencies']),
                    'min': calculate_min(metrics['latencies']),
                    'max': calculate_max(metrics['latencies'])
                },
                'jitter': {
                    'avg': calculate_avg(metrics['jitters']),
                    'min': calculate_min(metrics['jitters']),
                    'max': calculate_max(metrics['jitters'])
                },
                'packet_loss': {
                    'avg': calculate_avg(metrics['packet_losses']),
                    'min': calculate_min(metrics['packet_losses']),
                    'max': calculate_max(metrics['packet_losses'])
                },
                'obstruction': {
                    'avg': calculate_avg(metrics['obstructions']),
                    'min': calculate_min(metrics['obstructions']),
                    'max': calculate_max(metrics['obstructions'])
                },
                'stability': {
                    'avg': calculate_avg(metrics['stabilities']),
                    'min': calculate_min(metrics['stabilities']),
                    'max': calculate_max(metrics['stabilities'])
                }
            }
        
        # Identify satellite providers (Starlink variants, Viasat, HughesNet)
        satellite_providers = [
            p for p in providers_summary.keys() 
            if any(sat in p for sat in ['Starlink', 'Viasat', 'HughesNet'])
        ]
        
        # Generate insights
        insights = []
        
        # Find best provider overall
        best_provider = max(
            providers_summary.items(),
            key=lambda x: x[1]['quality_score']['avg']
        )
        insights.append(
            f"{best_provider[0]} leads with {best_provider[1]['quality_score']['avg']}/100 average quality score"
        )
        
        # Compare Starlink variants if present
        starlink_variants = [p for p in satellite_providers if 'Starlink' in p]
        if len(starlink_variants) >= 2:
            starlink_comparison = {
                p: providers_summary[p] for p in starlink_variants
            }
            best_starlink = max(
                starlink_comparison.items(),
                key=lambda x: x[1]['quality_score']['avg']
            )
            insights.append(
                f"Among Starlink options, {best_starlink[0]} performs best with "
                f"{best_starlink[1]['download']['avg']} Mbps avg download and "
                f"{best_starlink[1]['obstruction']['avg']}% avg obstruction"
            )
        
        # Satellite vs terrestrial comparison
        if satellite_providers:
            terrestrial_providers = [
                p for p in providers_summary.keys() 
                if p not in satellite_providers
            ]
            
            if terrestrial_providers:
                sat_avg_latency = calculate_avg([
                    providers_summary[p]['latency']['avg'] 
                    for p in satellite_providers
                ])
                terr_avg_latency = calculate_avg([
                    providers_summary[p]['latency']['avg'] 
                    for p in terrestrial_providers
                ])
                
                if sat_avg_latency < terr_avg_latency:
                    insights.append(
                        f"Satellite providers show lower latency ({sat_avg_latency} ms) "
                        f"compared to terrestrial ({terr_avg_latency} ms)"
                    )
                else:
                    insights.append(
                        f"Terrestrial providers have lower latency ({terr_avg_latency} ms) "
                        f"vs satellite ({sat_avg_latency} ms)"
                    )
        
        result = {
            'total_providers': len(providers_summary),
            'providers': providers_summary,
            'satellite_providers': satellite_providers,
            'insights': insights
        }
        
        logger.info("Provider comparison completed")
        return result
    
    except Exception as e:
        logger.error(f"Error comparing providers: {e}")

        raise
