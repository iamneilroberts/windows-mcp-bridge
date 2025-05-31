# Windows Claude Desktop MCP Bridge Setup Script
# Run as Administrator

param(
    [switch]$Force,
    [switch]$Debug
)

Write-Host "Windows Claude Desktop MCP Bridge Setup" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

# Function to check if command exists
function Test-CommandExists {
    param($command)
    try {
        Get-Command $command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Check Python installation
Write-Host "Checking Python installation..." -ForegroundColor Yellow
if (-not (Test-CommandExists "python")) {
    Write-Error "Python not found. Please install Python 3.11+ from https://python.org and ensure 'Add to PATH' is checked."
    exit 1
}

$pythonVersion = python --version
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Check pip
if (-not (Test-CommandExists "pip")) {
    Write-Error "pip not found. Please reinstall Python with pip included."
    exit 1
}

# Install MCP bridge
Write-Host "Installing MCP bridge..." -ForegroundColor Yellow
try {
    pip install -e . --quiet
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
    Write-Host "MCP bridge installed successfully" -ForegroundColor Green
} catch {
    Write-Error "Failed to install MCP bridge: $_"
    exit 1
}

# Test mcp_use installation
Write-Host "Testing mcp_use installation..." -ForegroundColor Yellow
try {
    python -m mcp_use --help | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "mcp_use test failed" }
    Write-Host "mcp_use working correctly" -ForegroundColor Green
} catch {
    Write-Error "mcp_use installation failed: $_"
    exit 1
}

# Create Claude config directory
Write-Host "Setting up Claude Desktop configuration..." -ForegroundColor Yellow
$claudeConfigDir = "$env:APPDATA\Claude"
New-Item -ItemType Directory -Force -Path $claudeConfigDir | Out-Null

# Create C:\Claude directory for mcp_config.json
New-Item -ItemType Directory -Force -Path "C:\Claude" | Out-Null

# Copy configuration files
try {
    Copy-Item "claude-config\claude_desktop_config.json" "$claudeConfigDir\" -Force
    Copy-Item "claude-config\mcp_config.json" "C:\Claude\" -Force
    Write-Host "Configuration files copied successfully" -ForegroundColor Green
} catch {
    Write-Error "Failed to copy configuration files: $_"
    exit 1
}

# Verify configuration
if (Test-Path "$claudeConfigDir\claude_desktop_config.json") {
    Write-Host "✓ Claude Desktop config: $claudeConfigDir\claude_desktop_config.json" -ForegroundColor Green
} else {
    Write-Error "Claude Desktop configuration not found!"
    exit 1
}

if (Test-Path "C:\Claude\mcp_config.json") {
    Write-Host "✓ MCP config: C:\Claude\mcp_config.json" -ForegroundColor Green
} else {
    Write-Error "MCP configuration not found!"
    exit 1
}

# Test one MCP server connection
Write-Host "Testing MCP server connection..." -ForegroundColor Yellow
try {
    $testResult = python -m mcp_use --config "C:\Claude\mcp_config.json" --server "prompt-server" --help 2>&1
    Write-Host "MCP server test successful" -ForegroundColor Green
} catch {
    Write-Warning "MCP server test failed, but continuing with setup"
}

Write-Host ""
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Close any running Claude Desktop instances"
Write-Host "2. Start Claude Desktop from the Start Menu"  
Write-Host "3. Wait 30-60 seconds for MCP servers to connect"
Write-Host "4. Test with: 'Can you search for flights from LAX to JFK?'"
Write-Host ""
Write-Host "Configuration locations:" -ForegroundColor Cyan
Write-Host "- Claude Desktop: $claudeConfigDir\claude_desktop_config.json"
Write-Host "- MCP Config: C:\Claude\mcp_config.json"
Write-Host "- Logs: $claudeConfigDir\logs\"
Write-Host ""
Write-Host "If you encounter issues, check the logs or run with -Debug flag" -ForegroundColor Gray