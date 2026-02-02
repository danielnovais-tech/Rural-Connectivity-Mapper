"""
Data pipeline connectors for Rural Connectivity Mapper.

This package contains connectors for various data sources including
ANATEL static data processing.
"""

from .anatel_static_connector import ANATELStaticConnector

__all__ = ['ANATELStaticConnector']
