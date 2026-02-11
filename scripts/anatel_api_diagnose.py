"""
This module provides an improved diagnosis script for the ANATEL CKAN API.
It uses the status_show and package_search methods to find the top candidates
for the diagnosis criteria and outputs the results in a JSON report.

Dependencies: requests, json, datetime, pathlib

Usage: Run this script to generate a report based on the specified criteria.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests
import urllib3

# Disable SSL warnings when verify=False is used (for testing only)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_status(api_url):
    response = requests.get(f"{api_url}/status_show", timeout=30, verify=False)
    return response.json()


def package_search(api_url, query):
    response = requests.get(f"{api_url}/package_search", params={"q": query}, timeout=30, verify=False)
    return response.json()


def main(api_url, search_query):
    status = get_status(api_url)
    print("API Status:", status)
    packages = package_search(api_url, search_query)
    top_candidates = packages["results"][:5]  # Get top 5 candidates
    print("Top Candidates:", top_candidates)

    report = {"timestamp": str(datetime.now(timezone.utc)), "top_candidates": top_candidates}
    output_path = Path("output.json")
    with output_path.open("w") as outfile:
        json.dump(report, outfile, indent=4)
    print(f"Report written to {output_path}")


if __name__ == "__main__":
    api_url = "https://your-ckan-api-url"  # Replace with actual API URL
    search_query = "your-search-query"  # Replace with actual search query
    main(api_url, search_query)
