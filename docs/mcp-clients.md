# MCP Client Integration Guide

Step-by-step configuration for leading Model Context Protocol clients.

`fme-mcp` features zero-configuration auto-detection for FME Form installations (`C:\Program Files\FME`, `/opt/fme`, or system `PATH`) and automatically grants access to the user's working and home directories.

---

## 1. Claude Desktop

Locate your configuration file:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Method A: With `uvx` (No installation needed if uv is installed)
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "uvx",
      "args": ["fme-mcp", "serve", "--transport", "stdio"]
    }
  }
}
```

### Method B: With Standard Python (After `py -m pip install fme-mcp`)
For Windows users with Python installed (uses the built-in Windows `py` launcher):
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "py",
      "args": ["-m", "fme_mcp.cli.main", "serve", "--transport", "stdio"]
    }
  }
}
```

### Method C: Standalone FME Form Engine (Locked Enterprise Machines)
Uses FME Form's own embedded Python runtime directly without requiring external Python:
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "C:\\Program Files\\FME\\fme.exe",
      "args": ["python", "-m", "fme_mcp.cli.main", "serve", "--transport", "stdio"]
    }
  }
}
```

### Advanced Setup (Custom Directories & FME Flow)
If FME is installed in a non-standard path, or if you wish to restrict/allow explicit directories or connect to FME Flow:
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "uvx",
      "args": ["fme-mcp", "serve", "--transport", "stdio"],
      "env": {
        "FME_MCP_FME_DIR": "C:\\Program Files\\FME",
        "FME_MCP_ALLOWED_DIRS": "C:\\Workspaces;D:\\GIS_Data",
        "FME_MCP_FME_FLOW_URL": "https://fme-flow.yourcompany.org",
        "FME_MCP_FME_FLOW_TOKEN": "your-token-here"
      }
    }
  }
}
```

---

## 2. Cursor & Windsurf

In Cursor Settings (`Features -> MCP Servers`), add:
- **Name**: `fme-mcp`
- **Type**: `command`
- **Command**: `fme-mcp serve --transport stdio`

*(Or with uvx: `uvx fme-mcp serve --transport stdio`)*

---

## 3. Antigravity & VS Code (Cline / Roo Code)

In your agent configuration file:
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "fme-mcp",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

