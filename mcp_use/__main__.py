#!/usr/bin/env python3
"""
MCP-Use for Claude Desktop Integration

This module provides the main entry point for mcp-use, bridging Claude Desktop
to remote MCP servers via HTTP/SSE connections.
"""

from .bridge import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())