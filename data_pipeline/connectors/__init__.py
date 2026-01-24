"""
Data pipeline connectors for Rural Connectivity Mapper.

This package contains connectors for various data sources including
ANATEL static data processing.
"""

from .anatel_static_connector import AnatelStaticConnector

__all__ = ['AnatelStaticConnector']
