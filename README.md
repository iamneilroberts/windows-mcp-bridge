# Windows Claude Desktop MCP Bridge

Complete setup for Claude Desktop with Cloudflare MCP servers on Windows.

## Quick Installation

```powershell
# 1. Clone this repository
git clone https://github.com/YOUR_USERNAME/windows-mcp-bridge.git
cd windows-mcp-bridge

# 2. Run the setup script as Administrator
.\setup-windows.ps1

# 3. Start Claude Desktop
```

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

## Manual Installation

If the script doesn't work, follow these steps:

### Prerequisites
- Python 3.11+ (with "Add to PATH" checked)
- Claude Desktop installed
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
- Ensure Python is in PATH
- Try full Python path in config

### "Authorization failed"
- Check auth tokens in mcp_config.json
- Verify server URLs are accessible

### "Connection timeout"
- Check internet connection
- Disable Windows Firewall temporarily

## Support

For issues, check the logs at `%APPDATA%\Claude\logs\`