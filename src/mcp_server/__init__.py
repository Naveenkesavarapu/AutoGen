"""
MCP Server package for Jira to TestRail integration.
"""

from .server import app, start_server
from .jira_client import JiraClient
from .testrail_client import TestRailClient
from .test_generator import TestCaseGenerator

__version__ = '0.1.0'
__all__ = ['app', 'start_server', 'JiraClient', 'TestRailClient', 'TestCaseGenerator'] 