# Instructions for Claude Code Users on Windows

## Quick Setup

Since you're already using Claude Code, you understand MCP servers and tools. This repository sets up **the same 8 MCP servers** in Claude Desktop (the GUI version) using **identical credentials**.

### One-Command Installation

```powershell
# Run in PowerShell as Administrator
git clone https://github.com/iamneilroberts/windows-mcp-bridge.git
cd windows-mcp-bridge
.\setup-windows.ps1
```

### What You Get

**Same MCP Servers as Your Current Claude Code Setup:**
- `amadeus-api` - Flight search, hotel booking, POI recommendations
- `google-places-api` - Place search, photo downloads, place details  
- `d1-database` - Client data storage, activity logging
- `r2-storage` - Image gallery, file storage, presigned URLs
- `template-document` - Itinerary, packing lists, budget documents
- `mobile-interaction` - WhatsApp, Telegram, SMS integration
- `prompt-server` - Dynamic instructions, mode switching
- `sequential-thinking` - Step-by-step reasoning chains

**Same Authentication:** Uses the production `*.somotravel.workers.dev` auth tokens you're currently using.

## Why Add Claude Desktop?

You can run **both Claude Code and Claude Desktop simultaneously**:

| Feature | Claude Code (CLI) | Claude Desktop (GUI) |
|---------|------------------|---------------------|
| MCP Tools | ✅ Same 30+ tools | ✅ Same 30+ tools |
| File Operations | Terminal only | Drag & drop interface |
| Image Handling | Text descriptions | Visual display |
| Conversation History | Session-based | Persistent history |
| Debugging | Log files | Built-in MCP status |
| Multitasking | One conversation | Multiple tabs |

## Technical Details

**What This Installs:**
- Custom MCP bridge (`mcp_use` package) - same as your Linux environment
- Claude Desktop configuration pointing to Cloudflare Workers
- Production authentication tokens (Bearer tokens)
- All Python dependencies and connectors

**Configuration Files:**
- `%APPDATA%\Claude\claude_desktop_config.json` - Claude Desktop MCP servers
- `C:\Claude\mcp_config.json` - Server URLs and auth headers

**How It Works:**
```
Claude Desktop ← MCP stdio → mcp_use bridge ← SSE → Cloudflare Workers
```

Same architecture as your Claude Code setup, just different frontend.

## After Installation

1. **Keep using Claude Code** for terminal/scripting tasks
2. **Use Claude Desktop** for:
   - Travel planning with visual maps
   - Image analysis and storage  
   - Document generation with formatting
   - Multi-conversation workflows

## Troubleshooting

**Common Issues:**
- "spawn python ENOENT" → Ensure Python in PATH
- "Authorization failed" → Auth tokens are pre-configured, check internet
- "Connection timeout" → Corporate firewall blocking WebSocket connections

**Verification:**
```powershell
# Test MCP bridge directly
python -m mcp_use --config "C:\Claude\mcp_config.json" --server "prompt-server" --help

# Check Claude Desktop logs
Get-Content "$env:APPDATA\Claude\logs\*.log" | Select-Object -Last 50
```

**Both Environments Working:**
- Claude Code: Your current setup (keep using it!)
- Claude Desktop: New GUI setup with same backend servers

You now have the best of both worlds! 🎉