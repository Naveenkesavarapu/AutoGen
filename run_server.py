"""
Run script for MCP server.
"""
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from mcp_server.server import start_server

if __name__ == '__main__':
    start_server() 