# Windows Claude Desktop MCP Bridge

Complete setup for Claude Desktop with Cloudflare MCP servers on Windows.

## For Claude Code Users

**If you're using Claude Code on Windows**, follow these instructions to get the same MCP servers and tools working in Claude Desktop:

### Quick Installation

```powershell
# 1. Clone this repository
git clone https://github.com/iamneilroberts/windows-mcp-bridge.git
cd windows-mcp-bridge

# 2. Run the setup script as Administrator
.\setup-windows.ps1

# 3. Close Claude Code temporarily
# 4. Start Claude Desktop from Start Menu
# 5. Test with: "Can you search for flights from LAX to JFK?"
```

**Note**: This configures Claude Desktop (the desktop app), not Claude Code (the CLI). Both can run simultaneously with the same MCP servers once configured.

### Why Use Claude Desktop Instead of Claude Code?

Claude Desktop provides:
- ✅ **Visual Interface** - Better for complex workflows
- ✅ **File Uploads** - Drag and drop images, documents
- ✅ **Conversation History** - Persistent chat sessions
- ✅ **MCP Server Management** - Built-in server status and debugging
- ✅ **Same Tools** - All 30+ MCP tools work identically

You can use both Claude Code and Claude Desktop with the same MCP backend!

## What This Does

- ✅ Installs Python dependencies
- ✅ Sets up custom MCP bridge
- ✅ Configures Claude Desktop
- ✅ Connects to 8 Cloudflare MCP servers
- ✅ Provides 30+ tools for travel assistance

## Included MCP Servers

1. **amadeus-api** - Flight search, hotel search, POI recommendations
2. **google-places-api** - Place search, photo downloads, details
3. **d1-database** - Client data, activity logging, database operations
4. **r2-storage** - Image gallery, file storage, presigned URLs
5. **template-document** - Itinerary, packing lists, budget documents
6. **mobile-interaction** - WhatsApp, Telegram, SMS integration
7. **prompt-server** - Dynamic instructions, mode detection
8. **sequential-thinking** - Step-by-step reasoning chains

## Understanding the Setup

This repository provides the **same MCP servers and tools** that are working in your current Claude Code environment. The difference is:

- **Claude Code** (CLI) - what you're using now
- **Claude Desktop** (GUI app) - what this sets up

Both use the same underlying MCP protocol and can access the same 8 Cloudflare servers with identical tools.

## Manual Installation

If the automated script doesn't work, follow these steps:

### Prerequisites
- Python 3.11+ (with "Add to PATH" checked)
- Claude Desktop installed (download from https://claude.ai/download)
- Git for Windows
- Administrator PowerShell access

### Steps
1. Install the MCP bridge:
```powershell
pip install -e .
```

2. Create Claude config directory:
```powershell
mkdir "$env:APPDATA\Claude" -Force
```

3. Copy configuration:
```powershell
Copy-Item "claude-config\claude_desktop_config.json" "$env:APPDATA\Claude\"
Copy-Item "claude-config\mcp_config.json" "C:\Claude\"
```

4. Start Claude Desktop

## Troubleshooting

### "spawn python ENOENT"
- Ensure Python is in PATH: `python --version`
- Try full Python path in claude_desktop_config.json

### "Authorization failed"
- Auth tokens are pre-configured and working
- Verify internet connection to *.somotravel.workers.dev

### "Connection timeout"
- Check internet connection
- Disable Windows Firewall temporarily
- Some corporate networks block WebSocket connections

### MCP Servers show "Disconnected"
- Check logs at `%APPDATA%\Claude\logs\`
- Restart Claude Desktop
- Verify Python installation: `python -m mcp_use --help`

## Credentials and Authentication

This setup uses the **same production authentication tokens** as your current working Claude Code environment. All 8 servers are pre-configured with working credentials.

## Support

- **Logs**: `%APPDATA%\Claude\logs\`
- **Config**: `%APPDATA%\Claude\claude_desktop_config.json`
- **MCP Config**: `C:\Claude\mcp_config.json`
- **Repository**: https://github.com/iamneilroberts/windows-mcp-bridge