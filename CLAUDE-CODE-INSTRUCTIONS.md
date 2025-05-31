# Instructions for Claude Code on Windows

You are Claude Code running on a Windows machine. The human wants you to set up Claude Desktop with MCP servers using this repository. Follow these steps exactly:

## Task Overview

Set up Claude Desktop on Windows with 8 Cloudflare MCP servers using a custom MCP bridge. This will give Claude Desktop the same tools and capabilities that are working in the Linux environment.

## Step 1: Clone Repository and Examine Contents

```bash
# Clone the repository
git clone https://github.com/iamneilroberts/windows-mcp-bridge.git
cd windows-mcp-bridge

# Examine the structure
ls -la
```

## Step 2: Install the MCP Bridge Package

```bash
# Install as editable Python package
pip install -e .

# Verify installation
python -m mcp_use --help
```

## Step 3: Create Claude Desktop Configuration Directory

```bash
# Create Claude config directory (Windows path)
mkdir -p "$env:APPDATA/Claude"

# Create MCP config directory
mkdir -p "C:/Claude"
```

## Step 4: Copy Configuration Files

```bash
# Copy Claude Desktop configuration
cp claude-config/claude_desktop_config.json "$env:APPDATA/Claude/"

# Copy MCP server configuration  
cp claude-config/mcp_config.json "C:/Claude/"
```

## Step 5: Verify Configuration Files

```bash
# Check Claude Desktop config exists
ls "$env:APPDATA/Claude/claude_desktop_config.json"

# Check MCP config exists
ls "C:/Claude/mcp_config.json"

# Show Claude Desktop config content
cat "$env:APPDATA/Claude/claude_desktop_config.json"
```

## Step 6: Test MCP Bridge Installation

```bash
# Test one MCP server connection
python -m mcp_use --config "C:/Claude/mcp_config.json" --server "prompt-server" --help

# If that works, test amadeus-api
python -m mcp_use --config "C:/Claude/mcp_config.json" --server "amadeus-api" --help
```

## Step 7: Final Verification

```bash
# Check all files are in place
echo "Checking Claude Desktop config:"
ls -la "$env:APPDATA/Claude/"

echo "Checking MCP config:"  
ls -la "C:/Claude/"

echo "Testing mcp_use package:"
python -c "import mcp_use; print('mcp_use package installed successfully')"
```

## Expected Results

After completing these steps:

1. **Files in place:**
   - `%APPDATA%/Claude/claude_desktop_config.json` - Claude Desktop MCP server configuration
   - `C:/Claude/mcp_config.json` - MCP server URLs and authentication tokens

2. **Package installed:**
   - `mcp_use` Python package installed and working
   - Can run `python -m mcp_use --help` successfully

3. **Ready for Claude Desktop:**
   - Configuration points to 8 Cloudflare MCP servers
   - Authentication tokens are pre-configured
   - When Claude Desktop starts, it will connect to all servers

## What This Accomplishes

- ✅ Installs custom MCP bridge package (45 Python files)
- ✅ Configures Claude Desktop for 8 MCP servers
- ✅ Sets up authentication for somotravel.workers.dev servers
- ✅ Provides 30+ tools: flight search, image storage, document generation, etc.
- ✅ Uses same backend as working Linux environment

## Next Steps for Human

After you complete these steps:
1. Close any running Claude Desktop instances
2. Start Claude Desktop from Windows Start Menu
3. Wait 30-60 seconds for MCP servers to connect
4. Test with: "Can you search for flights from LAX to JFK?"
5. Check MCP server status in Claude Desktop Settings → Developer

## Troubleshooting

If any step fails:
1. Check Python installation: `python --version` (need 3.11+)
2. Check pip works: `pip --version`
3. Check git works: `git --version`
4. Look for error messages and report them to the human

## Important Notes

- This configures Claude Desktop (GUI app), not Claude Code (CLI)
- Both can run simultaneously with same MCP backend
- All authentication tokens are pre-configured
- Repository contains working production setup

Execute these steps in order and report the results of each step.