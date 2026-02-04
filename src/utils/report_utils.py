"""Report generation utilities for multi-format output."""

import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

from .i18n_utils import get_rating_translation, get_translation

logger = logging.getLogger(__name__)


def _get_default_blackbox_settings_path() -> Path:
    """Return the default global settings path for Blackbox-style ignores.

    Default location: ~/.blackbox/settings.json
    You can override it for testing via BLACKBOX_SETTINGS_PATH.
    """
    overridden = os.environ.get("BLACKBOX_SETTINGS_PATH")
    if overridden:
        return Path(overridden).expanduser()
    return Path.home() / ".blackbox" / "settings.json"


def getCustomExcludes(config_path: str | None = None) -> list[str]:
    """Read global exclude patterns from settings.json.

    The intended default location is ~/.blackbox/settings.json.
    Expected JSON schema:

        {
          "globalExcludes": ["dist/", "build/", "*.pyc", "__pycache__/"]
        }

    Args:
        config_path: Optional explicit settings.json path.

    Returns:
        List[str]: Exclude patterns, or an empty list if missing/invalid.
    """
    settings_path = Path(config_path).expanduser() if config_path else _get_default_blackbox_settings_path()

    if not settings_path.exists():
        return []

    try:
        with open(settings_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    patterns = data.get("globalExcludes", [])
    if not isinstance(patterns, list):
        return []

    # Keep only string patterns.
    return [p for p in patterns if isinstance(p, str)]


def getCombinedExcludes(
    project_excludes: list[str] | None = None,
    config_path: str | None = None,
) -> list[str]:
    """Combine built-in excludes with optional project + global excludes.

    This is intended for any code that scans the filesystem to build reports.
    """
    combined: list[str] = []

    # Built-in defaults that are generally noisy across projects.
    built_in = [
        ".git/",
        "node_modules/",
        "__pycache__/",
        "*.pyc",
    ]

    for pattern in built_in:
        if pattern not in combined:
            combined.append(pattern)

    if project_excludes:
        for pattern in project_excludes:
            if pattern not in combined:
                combined.append(pattern)

    for pattern in getCustomExcludes(config_path=config_path):
        if pattern not in combined:
            combined.append(pattern)

    return combined


def generate_report(data: list[dict], report_format: str, output_path: str | None = None, language: str = 'en') -> str:
    """Generate report in specified format.
    
    Args:
        data: List of connectivity point dictionaries
        report_format: Report format (json, csv, txt, html)
        output_path: Optional output file path
        language: Language code for report (en, pt). Default: 'en'
        
    Returns:
        str: Path to generated report file or report content
        
    Raises:
        ValueError: If format is not supported
    """
    report_format = report_format.lower()
    
    if report_format == 'json':
        return _generate_json_report(data, output_path)
    elif report_format == 'csv':
        return _generate_csv_report(data, output_path)
    elif report_format == 'txt':
        return _generate_txt_report(data, output_path, language)
    elif report_format == 'html':
        return _generate_html_report(data, output_path, language)
    else:
        raise ValueError(
            f"Unsupported format: {report_format}. Use json, csv, txt, or html."
        )


def _generate_json_report(data: list[dict], output_path: str | None = None) -> str:
    """Generate JSON format report."""
    try:
        if output_path is None:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report generated: {path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error generating JSON report: {e}")
        raise


def _generate_csv_report(data: list[dict], output_path: str | None = None) -> str:
    """Generate CSV format report."""
    try:
        if output_path is None:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not data:
            logger.warning("No data to write to CSV")
            with open(path, 'w', encoding='utf-8') as f:
                f.write("")
            return str(path)
        
        # Flatten nested dictionaries for CSV
        flattened_data = []
        for point in data:
            flat = {
                'id': point.get('id', ''),
                'latitude': point.get('latitude', ''),
                'longitude': point.get('longitude', ''),
                'provider': point.get('provider', ''),
                'timestamp': point.get('timestamp', ''),
            }
            
            # Add speed test data
            if 'speed_test' in point:
                st = point['speed_test']
                flat.update({
                    'download': st.get('download', ''),
                    'upload': st.get('upload', ''),
                    'latency': st.get('latency', ''),
                    'jitter': st.get('jitter', ''),
                    'packet_loss': st.get('packet_loss', ''),
                    'obstruction': st.get('obstruction', ''),
                    'stability': st.get('stability', ''),
                })
            
            # Add quality score data
            if 'quality_score' in point:
                qs = point['quality_score']
                flat.update({
                    'overall_score': qs.get('overall_score', ''),
                    'speed_score': qs.get('speed_score', ''),
                    'latency_score': qs.get('latency_score', ''),
                    'stability_score': qs.get('stability_score', ''),
                    'rating': qs.get('rating', ''),
                })
            
            flattened_data.append(flat)
        
        # Write CSV
        with open(path, 'w', encoding='utf-8', newline='') as f:
            if flattened_data:
                writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                writer.writeheader()
                writer.writerows(flattened_data)
        
        logger.info(f"CSV report generated: {path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error generating CSV report: {e}")
        raise


def _generate_txt_report(data: list[dict], output_path: str | None = None, language: str = 'en') -> str:
    """Generate TXT format report with color and translations.
    
    Args:
        data: List of connectivity point dictionaries
        output_path: Optional output file path
        language: Language code (en, pt)
    """
    try:
        if output_path is None:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        lines.append("=" * 80)
        lines.append(get_translation('report_title', language))
        lines.append(f"{get_translation('generated', language)}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append(f"\n{get_translation('total_points', language)}: {len(data)}\n")
        
        for i, point in enumerate(data, 1):
            lines.append(f"\n--- {get_translation('point', language)} {i} ---")
            lines.append(f"ID: {point.get('id', 'N/A')}")
            lines.append(f"{get_translation('location', language)}: ({point.get('latitude', 'N/A')}, {point.get('longitude', 'N/A')})")
            lines.append(f"{get_translation('provider', language)}: {point.get('provider', 'N/A')}")
            lines.append(f"{get_translation('timestamp', language)}: {point.get('timestamp', 'N/A')}")
            
            if 'speed_test' in point:
                st = point['speed_test']

                lines.append(f"\n{get_translation('speed_test', language)}:")
                lines.append(f"  {get_translation('download', language)}: {st.get('download', 'N/A')} {get_translation('mbps', language)}")
                lines.append(f"  {get_translation('upload', language)}: {st.get('upload', 'N/A')} {get_translation('mbps', language)}")
                lines.append(f"  {get_translation('latency', language)}: {st.get('latency', 'N/A')} {get_translation('ms', language)}")
                lines.append(f"  {get_translation('stability', language)}: {st.get('stability', 'N/A')}/100")
                lines.append("\nSpeed Test:")
                lines.append(f"  Download: {st.get('download', 'N/A')} Mbps")
                lines.append(f"  Upload: {st.get('upload', 'N/A')} Mbps")
                lines.append(f"  Latency: {st.get('latency', 'N/A')} ms")
                lines.append(f"  Jitter: {st.get('jitter', 'N/A')} ms")
                lines.append(f"  Packet Loss: {st.get('packet_loss', 'N/A')}%")
                obstruction = st.get('obstruction', 0.0)
                if obstruction > 0:
                    lines.append(f"  Obstruction: {obstruction}% (satellite)")
                lines.append(f"  Stability: {st.get('stability', 'N/A')}/100")

            
            if 'quality_score' in point:
                qs = point['quality_score']
                lines.append(f"\n{get_translation('quality_score', language)}:")
                lines.append(f"  {get_translation('overall', language)}: {qs.get('overall_score', 'N/A')}/100")
                rating = qs.get('rating', 'N/A')
                translated_rating = get_rating_translation(rating, language) if rating != 'N/A' else 'N/A'
                lines.append(f"  {get_translation('rating', language)}: {translated_rating}")
        
        lines.append("\n" + "=" * 80)
        
        report_text = "\n".join(lines)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        # Print colored version to console if colorama is available
        if COLORAMA_AVAILABLE:
            print(Fore.CYAN + report_text)
        
        logger.info(f"TXT report generated: {path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error generating TXT report: {e}")
        raise


def _generate_html_report(data: list[dict], output_path: str | None = None, language: str = 'en') -> str:
    """Generate HTML format report with translations.
    
    Args:
        data: List of connectivity point dictionaries
        output_path: Optional output file path
        language: Language code (en, pt)
    """
    try:
        if output_path is None:
            output_path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("<meta charset='utf-8'>")
        html.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append(f"<title>{get_translation('report_title', language)}</title>")
        html.append("<style>")
        html.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html.append("h1 { color: #2c3e50; }")
        html.append("table { border-collapse: collapse; width: 100%; margin-top: 20px; }")
        html.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html.append("th { background-color: #3498db; color: white; }")
        html.append("tr:nth-child(even) { background-color: #f2f2f2; }")
        html.append(".excellent { color: green; font-weight: bold; }")
        html.append(".good { color: blue; font-weight: bold; }")
        html.append(".fair { color: orange; font-weight: bold; }")
        html.append(".poor { color: red; font-weight: bold; }")
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")
        html.append(f"<h1>{get_translation('report_title', language)}</h1>")
        html.append(f"<p>{get_translation('generated', language)}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")
        html.append(f"<p>{get_translation('total_points', language)}: {len(data)}</p>")
        
        html.append("<table>")
        html.append("<tr>")
        html.append(f"<th>{get_translation('provider', language)}</th>")
        html.append(f"<th>{get_translation('location', language)}</th>")
        html.append(f"<th>{get_translation('download', language)} ({get_translation('mbps', language)})</th>")
        html.append(f"<th>{get_translation('upload', language)} ({get_translation('mbps', language)})</th>")
        html.append(f"<th>{get_translation('latency', language)} ({get_translation('ms', language)})</th>")
        html.append(f"<th>{get_translation('overall_score', language)}</th>")
        html.append(f"<th>{get_translation('rating', language)}</th>")
        html.append("</tr>")
        
        for point in data:
            html.append("<tr>")
            html.append(f"<td>{point.get('provider', 'N/A')}</td>")
            html.append(f"<td>{point.get('latitude', 'N/A')}, {point.get('longitude', 'N/A')}</td>")
            
            st = point.get('speed_test', {})
            html.append(f"<td>{st.get('download', 'N/A')}</td>")
            html.append(f"<td>{st.get('upload', 'N/A')}</td>")
            html.append(f"<td>{st.get('latency', 'N/A')}</td>")
            
            qs = point.get('quality_score', {})
            html.append(f"<td>{qs.get('overall_score', 'N/A')}</td>")
            
            rating = qs.get('rating', 'N/A')
            rating_class = rating.lower() if rating != 'N/A' else ''
            translated_rating = get_rating_translation(rating, language) if rating != 'N/A' else 'N/A'
            html.append(f"<td class='{rating_class}'>{translated_rating}</td>")
            
            html.append("</tr>")
        
        html.append("</table>")
        html.append("</body>")
        html.append("</html>")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write("\n".join(html))
        
        logger.info(f"HTML report generated: {path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")
        raise
