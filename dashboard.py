#!/usr/bin/env python3
"""Streamlit Web Dashboard for Rural Connectivity Mapper 2026."""

import csv
import io
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.models import ConnectivityPoint, SpeedTest
from src.utils import (
    analyze_temporal_evolution,
    generate_map,
    generate_report,
    measure_speed,
    simulate_router_impact,
    validate_coordinates,
)

# Configuration constants
DATA_PATH = "src/data/pontos.json"
MAP_HEIGHT = 600  # Height in pixels for embedded maps
DOWNLOAD_MBPS_LABEL = "Download (Mbps)"
UPLOAD_MBPS_LABEL = "Upload (Mbps)"
COVERAGE_PERCENTAGE_LABEL = "Coverage %"


"""Streamlit dashboard for Rural Connectivity Mapper 2026.

This module provides an interactive web dashboard for visualizing and analyzing
connectivity data from ANATEL, IBGE, and Starlink.
"""

import sys
import uuid

import folium
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.analytics import compute_analytics_summary, timed_event, track_event
from src.utils.anatel_utils import (
    fetch_anatel_broadband_data,
    fetch_anatel_mobile_data,
    get_anatel_provider_stats,
)
from src.utils.country_config import get_country_config, get_latam_summary, get_supported_countries
from src.utils.data_utils import load_data, save_data
from src.utils.ibge_utils import (
    get_ibge_statistics_summary,
    get_rural_areas_needing_connectivity,
)
from src.utils.starlink_utils import (
    check_starlink_availability,
    get_starlink_coverage_map,
    get_starlink_service_plans,
)

# Page configuration
st.set_page_config(
    page_title="Rural Connectivity Mapper 2026", page_icon="🛰️", layout="wide", initial_sidebar_state="expanded"
)


# Custom CSS for better styling

# Custom CSS

st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {

        font-size: 1.2rem;
        color: #666;
        text-align: center;
        padding-bottom: 2rem;

        font-size: 1.5rem;
        font-weight: bold;
        color: #2ca02c;
        margin-top: 1rem;

    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;

        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;

        border-left: 4px solid #1f77b4;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);

    }
    </style>
""",
    unsafe_allow_html=True,
)


def display_header():
    """Display dashboard header."""
    st.markdown('<div class="main-header">🌍 Rural Connectivity Mapper 2026</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Analyze and visualize rural internet connectivity across Brazil</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")


def display_statistics(data):
    """Display key statistics from connectivity data."""
    if not data:
        st.warning("No data available to display statistics.")
        return

    # Calculate statistics
    total_points = len(data)
    avg_quality = sum(point["quality_score"]["overall_score"] for point in data) / total_points
    avg_download = sum(point["speed_test"]["download"] for point in data) / total_points
    avg_upload = sum(point["speed_test"]["upload"] for point in data) / total_points
    avg_latency = sum(point["speed_test"]["latency"] for point in data) / total_points

    # Count ratings
    ratings = [point["quality_score"]["rating"] for point in data]
    excellent = ratings.count("Excellent")
    good = ratings.count("Good")
    fair = ratings.count("Fair")
    poor = ratings.count("Poor")

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Points", total_points)
        st.metric("Average Quality", f"{avg_quality:.1f}/100")

    with col2:
        st.metric("Avg Download", f"{avg_download:.1f} Mbps")
        st.metric("Avg Upload", f"{avg_upload:.1f} Mbps")

    with col3:
        st.metric("Avg Latency", f"{avg_latency:.1f} ms")
        st.metric("Excellent", excellent)

    with col4:
        st.metric("Good", good)
        st.metric("Fair/Poor", fair + poor)


def display_data_table(data):
    """Display connectivity data in a table."""
    if not data:
        st.warning("No data available to display.")
        return

    # Prepare data for display
    rows = []
    for point in data:
        row = {
            "Provider": point["provider"],
            "Latitude": point["latitude"],
            "Longitude": point["longitude"],
            DOWNLOAD_MBPS_LABEL: round(point["speed_test"]["download"], 2),
            UPLOAD_MBPS_LABEL: round(point["speed_test"]["upload"], 2),
            "Latency (ms)": round(point["speed_test"]["latency"], 2),
            "Quality Score": round(point["quality_score"]["overall_score"], 2),
            "Rating": point["quality_score"]["rating"],
            "Timestamp": point["timestamp"],
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)


def upload_csv_data():
    """Handle CSV file upload and data import."""
    st.subheader("📤 Upload Connectivity Data")

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload a CSV file with columns: latitude, longitude, provider, download, upload, latency, jitter, packet_loss",
    )

    if uploaded_file is not None:
        try:
            # Read CSV file
            content = uploaded_file.read().decode("utf-8")
            csv_reader = csv.DictReader(io.StringIO(content))

            points = []
            for row in csv_reader:
                # Validate coordinates
                lat = float(row["latitude"])
                lon = float(row["longitude"])

                if not validate_coordinates(lat, lon):
                    st.warning(f"Skipping row with invalid coordinates: {row}")
                    continue

                # Create SpeedTest
                speed_test = SpeedTest(
                    download=float(row["download"]),
                    upload=float(row["upload"]),
                    latency=float(row["latency"]),
                    jitter=float(row.get("jitter", 0)),
                    packet_loss=float(row.get("packet_loss", 0)),
                )

                # Create ConnectivityPoint
                point = ConnectivityPoint(
                    latitude=lat,
                    longitude=lon,
                    provider=row["provider"],
                    speed_test=speed_test,
                    timestamp=row.get("timestamp", datetime.now().isoformat()),
                    point_id=row.get("id"),
                )

                points.append(point.to_dict())

            if points:
                # Save to data file
                save_data(DATA_PATH, points)
                st.success(f"✅ Successfully imported {len(points)} connectivity points!")
                st.rerun()
            else:
                st.error("No valid data points found in the uploaded file.")

        except Exception as e:
            st.error(f"Error importing CSV: {e}")


def run_speed_test():
    """Run on-demand speed test."""
    st.subheader("🚀 On-Demand Speed Test")

    st.info("Click the button below to run a speed test on your current connection.")

    col1, col2, col3 = st.columns([1, 1, 2])

    session_id = st.session_state.get("session_id", str(uuid.uuid4()))

    with col1:
        if st.button("Run Speed Test", type="primary"):
            track_event(event_name="speed_test_started", session_id=session_id, context={"page": "Speed Test"})

            with st.spinner("Running speed test... This may take up to 60 seconds."):
                with timed_event("speed_test_completed", session_id, context={"page": "Speed Test"}):
                    result = measure_speed()

                if result:
                    st.session_state["speed_test_result"] = result
                else:
                    track_event(
                        event_name="error_shown",
                        session_id=session_id,
                        context={"page": "Speed Test"},
                        properties={"error_type": "speed_test_failed"},
                    )
                    st.error("Speed test failed. Please try again.")

    # Display results if available
    if "speed_test_result" in st.session_state:
        result = st.session_state["speed_test_result"]

        st.success("Speed test completed!")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Download", f"{result['download']:.2f} Mbps")
        with col2:
            st.metric("Upload", f"{result['upload']:.2f} Mbps")
        with col3:
            st.metric("Latency", f"{result['latency']:.2f} ms")
        with col4:
            st.metric("Stability", f"{result['stability']:.2f}%")


def visualize_map(data):
    """Display interactive map."""
    st.subheader("🗺️ Interactive Connectivity Map")

    if not data:
        st.warning("No data available for map visualization. Please upload data first.")
        return

    # Generate map
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tmp:
            map_path = generate_map(data, tmp.name)

            # Read and display the HTML map
            with open(map_path, encoding="utf-8") as f:
                map_html = f.read()

            components.html(map_html, height=MAP_HEIGHT, scrolling=True)

    except Exception as e:
        st.error(f"Error generating map: {e}")


def generate_reports(data):
    """Generate and download reports."""
    st.subheader("📊 Generate Reports")

    if not data:
        st.warning("No data available for report generation. Please upload data first.")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("JSON Report"):
            report_path = generate_report(data, "json", "dashboard_report.json")
            with open(report_path) as f:
                st.download_button(
                    "Download JSON", f.read(), file_name="connectivity_report.json", mime="application/json"
                )

    with col2:
        if st.button("CSV Report"):
            report_path = generate_report(data, "csv", "dashboard_report.csv")
            with open(report_path) as f:
                st.download_button("Download CSV", f.read(), file_name="connectivity_report.csv", mime="text/csv")

    with col3:
        if st.button("TXT Report"):
            report_path = generate_report(data, "txt", "dashboard_report.txt")
            with open(report_path) as f:
                st.download_button("Download TXT", f.read(), file_name="connectivity_report.txt", mime="text/plain")

    with col4:
        if st.button("HTML Report"):
            report_path = generate_report(data, "html", "dashboard_report.html")
            with open(report_path) as f:
                st.download_button("Download HTML", f.read(), file_name="connectivity_report.html", mime="text/html")


def simulate_improvements(data):
    """Simulate router impact on connectivity."""
    st.subheader("🔧 Router Impact Simulation")

    if not data:
        st.warning("No data available for simulation. Please upload data first.")
        return

    st.info("Simulate 15-25% quality improvement from router upgrades")

    if st.button("Run Simulation", type="primary"):
        with st.spinner("Running simulation..."):
            improved_data = simulate_router_impact(data)

            # Save improved data
            save_data(DATA_PATH, improved_data)

            st.success("✅ Simulation completed and saved!")
            st.rerun()


def analyze_trends(data):
    """Display temporal evolution analysis."""
    st.subheader("📈 Temporal Analysis")

    if not data:
        st.warning("No data available for analysis. Please upload data first.")
        return

    analysis = analyze_temporal_evolution(data)

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Points Analyzed", analysis["total_points"])
        st.metric("Average Quality Score", f"{analysis['trends']['avg_quality_score']}/100")
        st.metric("Average Download Speed", f"{analysis['trends']['avg_download']} Mbps")
        st.metric("Average Latency", f"{analysis['trends']['avg_latency']} ms")

    with col2:
        st.write("**Key Insights:**")
        for insight in analysis["insights"]:
            st.write(f"• {insight}")


def main():
    """Main dashboard application."""
    # Initialize session ID for analytics
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        track_event(
            event_name="app_loaded",
            session_id=st.session_state.session_id,
            context={"app": "streamlit_dashboard_legacy"},
        )

    session_id = st.session_state.session_id

    display_header()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["📊 Dashboard", "📤 Upload Data", "🚀 Speed Test", "🗺️ Map View", "📈 Analysis", "🔧 Simulation"],
    )

    # Track page selection
    if "last_page" not in st.session_state or st.session_state.last_page != page:
        track_event(event_name="page_selected", session_id=session_id, context={"page": page})
        st.session_state.last_page = page

    # Load data
    data = load_data(DATA_PATH)

    # Display selected page
    if page == "📊 Dashboard":
        st.header("Dashboard Overview")
        display_statistics(data)
        st.markdown("---")
        st.subheader("Connectivity Data")
        display_data_table(data)
        st.markdown("---")
        generate_reports(data)

    elif page == "📤 Upload Data":
        upload_csv_data()
        if data:
            st.markdown("---")
            st.subheader("Current Data")
            display_data_table(data)

    elif page == "🚀 Speed Test":
        run_speed_test()

    elif page == "🗺️ Map View":
        visualize_map(data)

    elif page == "📈 Analysis":
        analyze_trends(data)

    elif page == "🔧 Simulation":
        simulate_improvements(data)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "**Rural Connectivity Mapper 2026**\n\n"
        "Analyze and visualize rural internet connectivity "
        "across Brazil, aligned with Starlink's 2026 expansion roadmap."
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("🇧🇷 Made with ❤️ for improving rural connectivity in Brazil")


def main_alternative():
    """Main dashboard application."""

    # Initialize session ID for analytics
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        track_event(
            event_name="app_loaded", session_id=st.session_state.session_id, context={"app": "streamlit_dashboard"}
        )

    session_id = st.session_state.session_id

    # Header
    st.markdown('<div class="main-header">🛰️ Rural Connectivity Mapper 2026</div>', unsafe_allow_html=True)
    st.markdown("**Analyzing Starlink expansion and connectivity across Latin America**")

    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Connectivity+Mapper", use_container_width=True)
        st.markdown("---")

        # Country selection
        st.subheader("🌍 Country Selection")
        countries = get_supported_countries()
        country_names = {code: config.name for code in countries if (config := get_country_config(code)) is not None}
        selected_country = st.selectbox(
            "Select Country", options=countries, format_func=lambda x: f"{country_names[x]} ({x})", index=0
        )

        country_config = get_country_config(selected_country)
        if country_config:
            st.info(f"""
            **{country_config.name}**
            - 🏛️ Regulator: {country_config.telecom_regulator}
            - 📊 Stats Agency: {country_config.stats_agency}
            - 💱 Currency: {country_config.currency}
            - 🗣️ Language: {country_config.official_language}
            """)
        else:
            st.warning(f"Configuration not found for country: {selected_country}")

        st.markdown("---")

        # View selection
        st.subheader("📊 Dashboard Views")
        view = st.radio(
            "Select View",
            [
                "Overview",
                "ANATEL Data",
                "IBGE Demographics",
                "Starlink Availability",
                "LATAM Comparison",
                "Interactive Map",
                "📈 Beta Analytics",
            ],
        )

        # Track page selection
        if "last_view" not in st.session_state or st.session_state.last_view != view:
            track_event(event_name="page_selected", session_id=session_id, context={"page": view})
            st.session_state.last_view = view

        st.markdown("---")
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Main content based on selected view
    if view == "Overview":
        show_overview(selected_country)
    elif view == "ANATEL Data":
        show_anatel_data(selected_country)
    elif view == "IBGE Demographics":
        show_ibge_data(selected_country)
    elif view == "Starlink Availability":
        show_starlink_data(selected_country)
    elif view == "LATAM Comparison":
        show_latam_comparison()
    elif view == "Interactive Map":
        show_interactive_map(selected_country)
    elif view == "📈 Beta Analytics":
        show_beta_analytics()


def show_overview(country_code: str):
    """Show overview dashboard."""
    st.markdown('<div class="sub-header">📈 Connectivity Overview</div>', unsafe_allow_html=True)

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Providers", "12+", delta="3 new")
    with col2:
        st.metric("Avg Download Speed", "85.5 Mbps", delta="12.3 Mbps")
    with col3:
        st.metric("Coverage", "78.5%", delta="5.2%")
    with col4:
        st.metric("Starlink Users", "550K", delta="50K")

    st.markdown("---")

    # Two column layout
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Provider Market Share")
        provider_stats = get_anatel_provider_stats()

        if country_code == "BR" and provider_stats:
            df = pd.DataFrame([{"Provider": k, "Market Share": v["market_share"]} for k, v in provider_stats.items()])
            fig = px.pie(df, values="Market Share", names="Provider", title="Market Share by Provider")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🚀 Speed Distribution")
        speeds_data = {
            "Provider": ["Starlink", "Claro", "Vivo", "TIM", "Oi"],
            DOWNLOAD_MBPS_LABEL: [150, 95, 90, 85, 60],
            UPLOAD_MBPS_LABEL: [15, 14, 13, 12, 8],
        }
        df_speeds = pd.DataFrame(speeds_data)
        fig = go.Figure(
            data=[
                go.Bar(name="Download", x=df_speeds["Provider"], y=df_speeds[DOWNLOAD_MBPS_LABEL]),
                go.Bar(name="Upload", x=df_speeds["Provider"], y=df_speeds[UPLOAD_MBPS_LABEL]),
            ]
        )
        fig.update_layout(barmode="group", title="Speed Comparison")
        st.plotly_chart(fig, use_container_width=True)

    # IBGE Summary for Brazil
    if country_code == "BR":
        st.markdown("---")
        st.subheader("📊 IBGE Statistics Summary")
        ibge_summary = get_ibge_statistics_summary()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Municipalities", f"{ibge_summary['total_municipalities']:,}")
            st.metric("Rural Population", f"{ibge_summary['rural_population']:,}")
        with col2:
            st.metric("Rural Internet Access", f"{ibge_summary['rural_households_with_internet']}%")
            st.metric("Digital Divide", f"{ibge_summary['urban_rural_digital_divide_percentage']}%")
        with col3:
            st.metric("Low Coverage Areas", f"{ibge_summary['municipalities_with_low_coverage']:,}")
            st.metric("Priority States", len(ibge_summary["priority_states"]))


def show_anatel_data(country_code: str):
    """Show ANATEL data view."""
    st.markdown('<div class="sub-header">📡 ANATEL Connectivity Data</div>', unsafe_allow_html=True)

    if country_code != "BR":
        st.warning(
            f"ANATEL data is only available for Brazil. Showing data for {country_code}'s telecom regulator would be displayed here."
        )
        return

    # State filter
    states = ["All", "SP", "RJ", "MG", "BA", "CE", "DF"]
    selected_state = st.selectbox("Filter by State", states)
    state_filter = None if selected_state == "All" else selected_state

    # Fetch data
    broadband_data = fetch_anatel_broadband_data(state=state_filter)
    mobile_data = fetch_anatel_mobile_data(state=state_filter)

    # Display broadband data
    st.subheader("📶 Broadband Fixed Internet")
    if broadband_data:
        df_broadband = pd.DataFrame(broadband_data)
        st.dataframe(df_broadband, use_container_width=True)

        # Visualization
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                df_broadband, x="municipality", y="subscribers", color="provider", title="Subscribers by Municipality"
            )
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.scatter(
                df_broadband,
                x="avg_speed_mbps",
                y="coverage_percentage",
                size="subscribers",
                color="technology",
                hover_data=["municipality", "provider"],
                title="Speed vs Coverage",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Display mobile data
    st.subheader("📱 Mobile Coverage")
    if mobile_data:
        df_mobile = pd.DataFrame(mobile_data)
        st.dataframe(df_mobile, use_container_width=True)


def show_ibge_data(country_code: str):
    """Show IBGE demographic data."""
    st.markdown('<div class="sub-header">👥 IBGE Demographic Data</div>', unsafe_allow_html=True)

    if country_code != "BR":
        country_config = get_country_config(country_code)
        stats_agency = country_config.stats_agency if country_config else "the national statistics agency"
        st.warning(f"IBGE data is only available for Brazil. Data from {stats_agency} would be displayed here.")
        return

    # Rural areas needing connectivity
    st.subheader("🏘️ Priority Rural Areas")
    priority_areas = get_rural_areas_needing_connectivity()

    if priority_areas:
        df_priority = pd.DataFrame(priority_areas)
        st.dataframe(df_priority, use_container_width=True)

        # Visualization
        fig = px.scatter(
            df_priority,
            x="internet_coverage",
            y="priority_score",
            size="rural_population",
            color="state",
            hover_data=["municipality"],
            title="Priority Areas: Coverage vs Priority Score",
            labels={"internet_coverage": "Internet Coverage (%)", "priority_score": "Priority Score"},
        )
        st.plotly_chart(fig, use_container_width=True)

        # Download option
        csv = df_priority.to_csv(index=False)
        st.download_button(
            label="📥 Download Priority Areas Data (CSV)",
            data=csv,
            file_name=f"priority_rural_areas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )


def show_starlink_data(country_code: str):
    """Show Starlink availability data."""
    st.markdown('<div class="sub-header">🛰️ Starlink Availability</div>', unsafe_allow_html=True)

    # Coverage map
    st.subheader("📡 Coverage Map")
    coverage = get_starlink_coverage_map(country_code)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Service Status", coverage.get("service_status", "Unknown").title())
        st.metric("Coverage", f"{coverage.get('coverage_percentage', 0)}%")
    with col2:
        st.metric("Active Users", f"{coverage.get('active_users', 0):,}")
        st.metric("Ground Stations", coverage.get("ground_stations", 0))
    with col3:
        st.metric("Satellites Overhead", coverage.get("total_satellites_overhead", 0))
        if "launch_date" in coverage:
            st.metric("Launch Date", coverage["launch_date"])

    # Service plans
    st.markdown("---")
    st.subheader("💰 Service Plans")
    plans = get_starlink_service_plans()

    if plans:
        df_plans = pd.DataFrame(plans)
        st.dataframe(
            df_plans[["name", "price_brl_monthly", "hardware_cost_brl", "download_speed", "latency", "suitable_for"]],
            use_container_width=True,
        )

    # Availability checker
    st.markdown("---")
    st.subheader("📍 Check Availability at Location")

    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input("Latitude", value=-15.7801, format="%.4f")
    with col2:
        lon = st.number_input("Longitude", value=-47.9292, format="%.4f")

    if st.button("Check Availability"):
        session_id = st.session_state.get("session_id", str(uuid.uuid4()))
        with st.spinner("Checking Starlink availability..."):
            with timed_event(
                "starlink_availability_check",
                session_id,
                context={"page": "Starlink Availability"},
                geo={"lat": round(lat, 2), "lon": round(lon, 2)},
            ):
                availability = check_starlink_availability(lat, lon)

            if availability["service_available"]:
                st.success(f"✅ Starlink is available at ({lat}, {lon})")
            else:
                st.warning(f"⏳ Starlink status: {availability['status']}")

            st.json(availability)


def show_latam_comparison():
    """Show LATAM countries comparison."""
    st.markdown('<div class="sub-header">🌎 LATAM Countries Comparison</div>', unsafe_allow_html=True)

    # Get summary
    summary = get_latam_summary()

    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Countries", summary["total_countries"])
    with col2:
        st.metric("Unique Providers", summary["unique_providers_count"])
    with col3:
        st.metric("Languages", len(summary["languages"]))
    with col4:
        st.metric("Currencies", len(summary["currencies"]))

    # Country details
    st.subheader("📊 Country Details")
    countries_df = pd.DataFrame(
        [
            {
                "Code": code,
                "Country": data["name"],
                "Language": data["language"],
                "Currency": data["currency"],
                "Providers": data["providers_count"],
            }
            for code, data in summary["countries"].items()
        ]
    )
    st.dataframe(countries_df, use_container_width=True)

    # Starlink coverage comparison
    st.subheader("🛰️ Starlink Coverage Across LATAM")

    coverage_data = []
    for country_code in get_supported_countries():
        coverage = get_starlink_coverage_map(country_code)
        if coverage.get("coverage_percentage"):
            coverage_data.append(
                {
                    "Country": coverage.get("country_name", country_code),
                    COVERAGE_PERCENTAGE_LABEL: coverage.get("coverage_percentage", 0),
                    "Active Users": coverage.get("active_users", 0),
                    "Ground Stations": coverage.get("ground_stations", 0),
                }
            )

    if coverage_data:
        df_coverage = pd.DataFrame(coverage_data)
        fig = px.bar(
            df_coverage,
            x="Country",
            y=COVERAGE_PERCENTAGE_LABEL,
            title="Starlink Coverage by Country",
            color=COVERAGE_PERCENTAGE_LABEL,
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig, use_container_width=True)


def show_interactive_map(country_code: str):
    """Show interactive map."""
    st.markdown('<div class="sub-header">🗺️ Interactive Connectivity Map</div>', unsafe_allow_html=True)

    # Get country center
    country_config = get_country_config(country_code)
    if country_config is None:
        st.error(f"Configuration not found for country: {country_code}")
        return
    center_lat, center_lon = country_config.coordinates_center

    # Create map
    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

    # Add markers for sample data
    if country_code == "BR":
        # Add ANATEL data points
        broadband_data = fetch_anatel_broadband_data()
        for record in broadband_data:
            # Get coordinates (simplified)
            coords_map = {
                "São Paulo": (-23.5505, -46.6333),
                "Rio de Janeiro": (-22.9068, -43.1729),
                "Belo Horizonte": (-19.9167, -43.9345),
                "Salvador": (-12.9714, -38.5014),
                "Fortaleza": (-3.7172, -38.5433),
            }
            coords = coords_map.get(record["municipality"])
            if coords:
                folium.Marker(
                    coords,
                    popup=f"<b>{record['municipality']}</b><br>"
                    f"Provider: {record['provider']}<br>"
                    f"Speed: {record['avg_speed_mbps']} Mbps<br>"
                    f"Coverage: {record['coverage_percentage']}%",
                    tooltip=record["municipality"],
                    icon=folium.Icon(color="blue", icon="info-sign"),
                ).add_to(m)

    # Display map
    st_folium(m, width=1200, height=600)

    st.info("💡 Click on markers to see connectivity details for each location")


def show_beta_analytics():
    """Show beta analytics dashboard with tracked metrics."""
    st.markdown('<div class="sub-header">📈 Beta Analytics Dashboard</div>', unsafe_allow_html=True)

    st.info(
        "**Privacy Notice:** All analytics are collected locally without third-party services. "
        "Geographic data is rounded to ~1km precision. No personally identifiable information is stored."
    )

    try:
        # Compute analytics summary
        summary = compute_analytics_summary()

        # Display overview metrics
        st.subheader("📊 Overview Metrics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Events", summary["total_events"])
        with col2:
            st.metric("Unique Sessions", summary["unique_sessions"])
        with col3:
            recommendations = summary["event_counts"].get("recommendation_api_called", 0)
            st.metric("Recommendations", recommendations)
        with col4:
            page_views = summary["event_counts"].get("page_selected", 0)
            st.metric("Page Views", page_views)

        st.markdown("---")

        # Event type distribution
        st.subheader("📌 Event Distribution")
        if summary["event_counts"]:
            event_df = pd.DataFrame(
                [{"Event Type": k, "Count": v} for k, v in summary["event_counts"].items()]
            ).sort_values("Count", ascending=False)

            fig = px.bar(
                event_df,
                x="Event Type",
                y="Count",
                title="Events by Type",
                color="Count",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No events tracked yet. Start using the dashboard to see analytics!")

        st.markdown("---")

        # Time-to-recommendation metrics
        st.subheader("⚡ Performance Metrics")
        if summary["time_to_recommendation"]:
            col1, col2, col3 = st.columns(3)

            ttr = summary["time_to_recommendation"]
            with col1:
                st.metric("Median Time to Recommendation", f"{ttr.get('median_ms', 0):.0f} ms")
            with col2:
                st.metric("P90 Time to Recommendation", f"{ttr.get('p90_ms', 0):.0f} ms")
            with col3:
                st.metric("Total Recommendations", ttr.get("count", 0))
        else:
            st.info("No recommendation timing data available yet.")

        st.markdown("---")

        # CTR metrics
        st.subheader("🎯 Engagement Metrics")
        if summary["ctr"]:
            col1, col2, col3 = st.columns(3)

            ctr = summary["ctr"]
            with col1:
                st.metric("CTA Clicks", ctr.get("cta_clicked", 0))
            with col2:
                st.metric("Recommendations Rendered", ctr.get("recommendation_rendered", 0))
            with col3:
                st.metric("Click-Through Rate", f"{ctr.get('rate', 0):.1f}%")
        else:
            st.info("No CTR data available yet. Track 'recommendation_rendered' and 'cta_clicked' events.")

        st.markdown("---")

        # Export analytics
        st.subheader("📥 Export Analytics")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 Download Summary (JSON)"):
                import json

                summary_json = json.dumps(summary, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=summary_json,
                    file_name=f"analytics_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

        with col2:
            if st.button("📋 Download Raw Events (CSV)"):
                from src.utils.analytics import read_events

                events = read_events(limit=1000)
                if events:
                    events_df = pd.DataFrame(events)
                    csv = events_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"analytics_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )
                else:
                    st.warning("No events to export.")

    except Exception as e:
        st.error(f"Error loading analytics: {e}")
        st.info(
            "This might be because no analytics events have been tracked yet. "
            "Use the dashboard to generate some events!"
        )


if __name__ == "__main__":
    main_alternative()
