# FME MCP - Installation & Setup Guide

**FME MCP** (`fme-mcp-ultra`) is designed for instant, frictionless deployment across enterprise GIS environments, developer workstations, and cloud infrastructure.

Whether you have a full Python development environment or a locked-down enterprise workstation with only Safe Software FME Form installed, **FME MCP** works immediately out of the box.

---

## 🚀 1-Command Universal Installation (Recommended)

The fastest and easiest way to install and configure **FME MCP** on your workstation. It requires **ZERO external dependencies** (no Python, no `uv`, and no `uvx` needed).

### Windows (PowerShell)

Open PowerShell (no administrator privileges required) and run:

```powershell
irm https://raw.githubusercontent.com/mwjouini/fme-mcp-ultra/main/scripts/install.ps1 | iex
```

### Linux / macOS (Bash)

Open your terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/mwjouini/fme-mcp-ultra/main/scripts/install.sh | bash
```

---

### ✨ How the Universal Installer Works

The 1-command installer automates the complete setup lifecycle in seconds:

1. **Zero External Dependencies**:
   - You do **NOT** need Python, `uv`, `pip`, or git pre-installed.
   - Everything runs in user-space (`%LOCALAPPDATA%\fme-mcp\bin` or `%LOCALAPPDATA%\mcp-fme\bin` on Windows, `~/.local/bin` on Linux/macOS) — **no administrator / UAC elevation required**.

2. **Native FME Form Engine Detection**:
   - Automatically queries the Windows Registry (`HKLM` and `HKCU` Safe Software keys), environment variables (`FME_HOME`, `FME_DIR`), and standard installation paths (`C:\Program Files\FME`, `/opt/fme`).
   - If a local FME Form (2018.0 through 2026+) is present, it directly hooks into FME's native Python runtime and `fmeobjects` C++ bindings, or installs the pre-compiled standalone binary.

3. **Automatic AI MCP Client Configuration**:
   - Automatically discovers your installed AI IDEs and assistants, writing and merging the correct MCP configuration without overwriting existing servers:
     - **Claude Desktop**: Configures `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS).
     - **Cursor**: Configures `~/.cursor/mcp.json`.
     - **Antigravity**: Configures your workspace and global Antigravity MCP settings.
     - **VS Code**: Configures Claude Code, Cline, or Roo Code MCP server definitions.
     - **Windsurf**: Configures `~/.codeium/windsurf/mcp_config.json`.

4. **Automated Verification**:
   - Executes `fme-mcp-ultra doctor` at the end of the installation to confirm FME Form licensing, build details, and tool availability.

---

## 📦 Standalone Binary Releases (No Python Required)

If you prefer to manually download the executable or run on an air-gapped machine:

1. Head to the [GitHub Releases](https://github.com/mwjouini/fme-mcp-ultra/releases/latest) page.
2. Download the pre-built single-file binary for your operating system:
   - **Windows (x64)**: `fme-mcp-ultra-windows-x64.exe` (or `fme-mcp-ultra.exe`)
   - **Linux (x64)**: `fme-mcp-ultra-linux-x64`
3. Place the binary in your `PATH` or in `%LOCALAPPDATA%\fme-mcp\bin`.
4. Test with:
   ```bash
   fme-mcp-ultra doctor
   ```

---

## ⚡ Developer & Package Manager Methods

If you are a Python or GIS developer with Python or `uv` already installed, you can run or install **FME MCP** via standard package managers.

### Option A: Ephemeral Execution with `uvx`

Run immediately without installing to your global environment:

```bash
uvx fme-mcp-ultra serve --transport stdio
```

To run diagnostics:
```bash
uvx fme-mcp-ultra doctor
```

### Option B: Standard `pip` Installation

Install into your active Python virtual environment or system Python:

```bash
pip install fme-mcp-ultra
```

Verify your installation:
```bash
fme-mcp-ultra doctor
```

---

## 🐳 Docker & Container Deployment

For enterprise servers, Kubernetes clusters, or FME Flow environments, deploy **FME MCP** using the official container image over Streamable HTTP (SSE):

```bash
docker run -d \
  --name fme-mcp \
  -p 8000:8000 \
  -e FME_MCP_TRANSPORT=streamable-http \
  -e FME_FLOW_URL="https://fme-flow.your-org.com" \
  -e FME_FLOW_TOKEN="your-fme-flow-api-token" \
  -e FME_MCP_ALLOWED_DIRS="/data;/workspaces" \
  ghcr.io/mwjouini/fme-mcp-ultra:latest
```

---

## 🔍 Verification: Running `fme-mcp-ultra doctor`

Run the built-in diagnostic tool to verify that your installation is healthy and ready to serve AI agents:

```bash
fme-mcp-ultra doctor
```

Example diagnostic output:

```text
============================================================
                   FME MCP - DIAGNOSTIC REPORT              
============================================================
[OK] Operating System: Windows 11 (x64)
[OK] FME Form Installation: C:\Program Files\FME (FME 2025.2 Build 25201)
[OK] License Status: FME Desktop Database Edition (Valid)
[OK] fmeobjects C++ Bindings: Available (High-performance in-memory mode active)
[OK] Discovered Transformers: 524 installed
[OK] PathGuard Sandbox: Active (Enforcing realpath containment)
[OK] CommandGuard: Active (Default-deny subprocess whitelist)
[OK] SSRF Guard: Active (Blocking loopback, private RFC1918, and metadata APIs)
[OK] MCP Clients Detected: Claude Desktop, Cursor, Antigravity, VS Code, Windsurf
============================================================
System status: READY TO SERVE
```

---

## 🔌 Manual Client Configuration Reference

If you did not use the 1-command installer or wish to manually configure your MCP clients, add the following snippets:

### Claude Desktop
Edit `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "fme-mcp-ultra",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

### Cursor & Windsurf
Add to `~/.cursor/mcp.json` or `~/.codeium/windsurf/mcp_config.json`:
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "fme-mcp-ultra",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

### Antigravity & VS Code (Cline / Roo Code)
Add to your MCP settings:
```json
{
  "mcpServers": {
    "fme-mcp": {
      "command": "fme-mcp-ultra",
      "args": ["serve", "--transport", "stdio"]
    }
  }
}
```

---

## 🛠️ Troubleshooting & FAQs

### PowerShell Execution Policy Error
If PowerShell blocks the installer script with an execution policy error (`running scripts is disabled on this system`), bypass it for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
irm https://raw.githubusercontent.com/mwjouini/fme-mcp-ultra/main/scripts/install.ps1 | iex
```

### FME Form in Non-Standard Path
If your FME Form is installed in a custom location, set the `FME_DIR` environment variable before running:

```powershell
$env:FME_DIR = "D:\CustomSoftware\FME"
irm https://raw.githubusercontent.com/mwjouini/fme-mcp-ultra/main/scripts/install.ps1 | iex
```

### Corporate Proxy Settings
If your organisation routes outbound traffic through an authenticated HTTP/HTTPS proxy:

```powershell
$env:HTTP_PROXY = "http://proxy.your-company.com:8080"
$env:HTTPS_PROXY = "http://proxy.your-company.com:8080"
irm https://raw.githubusercontent.com/mwjouini/fme-mcp-ultra/main/scripts/install.ps1 | iex
```

### No Administrator Rights
The 1-command installer does **not** require administrative privileges. It writes to user-level directories (`%LOCALAPPDATA%`, `%APPDATA%`) and updates the user's `PATH` variable safely.
