#!/usr/bin/env python3
"""
MCP Bridge for Claude Desktop Integration

This module creates a proper MCP server that bridges Claude Desktop 
to remote MCP servers via HTTP/SSE connections using mcp-use.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .client import MCPClient
from .logging import logger


class MCPBridge:
    """Bridge between Claude Desktop and remote MCP servers."""
    
    def __init__(self, config_path: str, server_name: str):
        self.config_path = config_path
        self.server_name = server_name
        self.client = None
        self.session = None
        self.server = Server("mcp-use-bridge")
        
    async def initialize(self):
        """Initialize the MCP client connection."""
        try:
            self.client = MCPClient.from_config_file(self.config_path)
            self.session = await self.client.create_session(self.server_name)
            logger.info(f"Bridge initialized for server: {self.server_name}")
        except Exception as e:
            logger.error(f"Failed to initialize bridge: {e}")
            raise
    
    async def list_tools(self) -> List[types.Tool]:
        """List available tools from the remote server."""
        if not self.session:
            raise RuntimeError("Bridge not initialized")
        
        try:
            tools = await self.session.connector.list_tools()
            
            # Convert mcp-use tools to MCP protocol tools
            mcp_tools = []
            for tool in tools:
                # Use annotations if available (contains the full schema), otherwise fallback to inputSchema
                schema = {"type": "object"}
                if hasattr(tool, 'annotations') and tool.annotations:
                    # Convert ToolAnnotations object to dictionary
                    if hasattr(tool.annotations, 'model_dump'):
                        schema = tool.annotations.model_dump(exclude_none=True)
                    elif hasattr(tool.annotations, 'dict'):
                        schema = tool.annotations.dict(exclude_none=True)
                    else:
                        # Fallback: manually extract the schema
                        schema = {
                            "type": getattr(tool.annotations, 'type', 'object'),
                            "properties": getattr(tool.annotations, 'properties', {}),
                            "required": getattr(tool.annotations, 'required', [])
                        }
                        if hasattr(tool.annotations, 'additionalProperties'):
                            schema["additionalProperties"] = tool.annotations.additionalProperties
                    logger.debug(f"Using annotations schema for {tool.name}: {schema}")
                elif hasattr(tool, 'inputSchema') and tool.inputSchema:
                    schema = tool.inputSchema
                    logger.debug(f"Using inputSchema for {tool.name}: {schema}")
                else:
                    logger.warning(f"No schema found for tool {tool.name}, using default")
                
                mcp_tool = types.Tool(
                    name=tool.name,
                    description=tool.description or f"Tool: {tool.name}",
                    inputSchema=schema
                )
                mcp_tools.append(mcp_tool)
            
            logger.debug(f"Listed {len(mcp_tools)} tools from {self.server_name}")
            return mcp_tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Call a tool on the remote server."""
        if not self.session:
            raise RuntimeError("Bridge not initialized")
        
        try:
            logger.info(f"Bridge calling tool {name} with args: {arguments}")
            result = await self.session.connector.call_tool(name, arguments)
            logger.info(f"Bridge received result: {result}")
            
            # Convert result to MCP protocol format
            if isinstance(result, str):
                content = result
            elif hasattr(result, 'content') and isinstance(result.content, list):
                # Handle mcp-use ToolResult format
                content = "\n".join([str(item.text) if hasattr(item, 'text') else str(item) for item in result.content])
            else:
                content = str(result)
            
            return [types.TextContent(type="text", text=content)]
            
        except Exception as e:
            logger.error(f"Failed to call tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def cleanup(self):
        """Clean up resources."""
        if self.client:
            await self.client.close_all_sessions()


async def main():
    """Main entry point for the MCP bridge."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Bridge for mcp-use")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--server", required=True, help="Server name to bridge")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Create the bridge
    bridge = MCPBridge(args.config, args.server)
    
    # Set up MCP server handlers
    @bridge.server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        return await bridge.list_tools()
    
    @bridge.server.call_tool()
    async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        return await bridge.call_tool(name, arguments)
    
    # Initialize bridge
    await bridge.initialize()
    
    # Run the MCP server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        try:
            await bridge.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=f"mcp-use-{args.server}",
                    server_version="1.0.0",
                    capabilities=bridge.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
        finally:
            await bridge.cleanup()


if __name__ == "__main__":
    asyncio.run(main())