#!/usr/bin/env bash
# ==============================================================================
# FME MCP - Universal 1-Command Installer (Linux & macOS)
# Zero-dependency Model Context Protocol Server for Safe Software FME
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/mwjouini/fme-mcp/main/scripts/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/mwjouini/fme-mcp/main/scripts/install.sh | bash -s -- --dry-run
# ==============================================================================

set -e

# Default configurations
REPO="mwjouini/fme-mcp"
TAG="latest"
INSTALL_DIR="${HOME}/.local/share/fme-mcp/bin"
FME_DIR_OVERRIDE=""
DRY_RUN=false
FORCE=false
CONFIGURE_ALL=false
PREFER_FME_PYTHON=false

# ANSI color codes
COLOR_RESET="\033[0m"
COLOR_CYAN="\033[1;36m"
COLOR_GREEN="\033[1;32m"
COLOR_YELLOW="\033[1;33m"
COLOR_RED="\033[1;31m"
COLOR_GRAY="\033[0;37m"
COLOR_WHITE="\033[1;37m"
COLOR_MAGENTA="\033[1;35m"

# Print banner
print_banner() {
    echo ""
    echo -e "${COLOR_CYAN}==========================================================================${COLOR_RESET}"
    echo -e "${COLOR_WHITE}  FME MCP - Universal 1-Command Installer (Linux / macOS)                 ${COLOR_RESET}"
    echo -e "${COLOR_GRAY}  Model Context Protocol Server for Safe Software FME (2018.0 - 2026+)    ${COLOR_RESET}"
    echo -e "${COLOR_CYAN}==========================================================================${COLOR_RESET}"
    if [ "$DRY_RUN" = true ]; then
        echo -e "${COLOR_YELLOW}  *** DRY-RUN MODE: No files or configurations will be modified ***       ${COLOR_RESET}"
        echo -e "${COLOR_YELLOW}--------------------------------------------------------------------------${COLOR_RESET}"
    fi
    echo ""
}

print_step() {
    echo -e "${COLOR_CYAN}[•] $1${COLOR_RESET}"
}

print_success() {
    echo -e " ${COLOR_GREEN}[✓] $1${COLOR_RESET}"
}

print_warn() {
    echo -e " ${COLOR_YELLOW}[!] $1${COLOR_RESET}"
}

print_failure() {
    echo -e " ${COLOR_RED}[✗] $1${COLOR_RESET}"
}

print_detail() {
    echo -e "     ${COLOR_GRAY}- $1: ${COLOR_WHITE}$2${COLOR_RESET}"
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --configure-all)
            CONFIGURE_ALL=true
            shift
            ;;
        --prefer-fme-python)
            PREFER_FME_PYTHON=true
            shift
            ;;
        --install-dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --fme-dir)
            FME_DIR_OVERRIDE="$2"
            shift 2
            ;;
        --tag)
            TAG="$2"
            shift 2
            ;;
        --repo)
            REPO="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: install.sh [options]"
            echo "Options:"
            echo "  --dry-run             Simulate installation without touching disk"
            echo "  --force               Overwrite existing binary or configs"
            echo "  --configure-all       Configure all clients even if not detected"
            echo "  --prefer-fme-python   Prefer FME bundled python if available"
            echo "  --install-dir <path>  Target binary directory (default: ~/.local/share/fme-mcp/bin)"
            echo "  --fme-dir <path>      FME Form installation directory"
            echo "  --tag <tag>           Release tag (default: latest)"
            echo "  --help                Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_banner

# --- Step 1: Detect Safe Software FME Installation ---
print_step "1/4: Detecting Safe Software FME installation..."

FME_DIR=""
FME_PYTHON=""
FME_VERSION="FME Form (Linux)"

if [ -n "$FME_DIR_OVERRIDE" ] && [ -d "$FME_DIR_OVERRIDE" ]; then
    if [ -f "$FME_DIR_OVERRIDE/fme" ]; then
        FME_DIR="$FME_DIR_OVERRIDE"
    fi
fi

if [ -z "$FME_DIR" ] && [ -n "$FME_HOME" ] && [ -d "$FME_HOME" ]; then
    if [ -f "$FME_HOME/fme" ]; then
        FME_DIR="$FME_HOME"
    fi
fi

if [ -z "$FME_DIR" ] && [ -n "$FME_DIR" ] && [ -d "$FME_DIR" ]; then
    if [ -f "$FME_DIR/fme" ]; then
        FME_DIR="$FME_DIR"
    fi
fi

if [ -z "$FME_DIR" ]; then
    for d in /opt/fme* /usr/local/fme* /opt/safe/fme* /Library/FME*; do
        if [ -d "$d" ] && [ -f "$d/fme" ]; then
            FME_DIR="$d"
            break
        fi
    done
fi

if [ -z "$FME_DIR" ]; then
    if command -v fme >/dev/null 2>&1; then
        FME_EXEC=$(command -v fme)
        FME_DIR=$(dirname "$FME_EXEC")
    fi
fi

if [ -n "$FME_DIR" ]; then
    print_success "FME Installation Detected!"
    print_detail "Home Directory" "$FME_DIR"

    for pydir in "$FME_DIR"/fmepython* "$FME_DIR"/python; do
        if [ -x "$pydir/bin/python3" ]; then
            FME_PYTHON="$pydir/bin/python3"
            break
        elif [ -x "$pydir/python" ]; then
            FME_PYTHON="$pydir/python"
            break
        fi
    done

    if [ -n "$FME_PYTHON" ]; then
        PY_VER=$("$FME_PYTHON" --version 2>&1 || echo "Python 3")
        print_detail "Bundled Python" "$FME_PYTHON ($PY_VER)"
    else
        print_detail "Bundled Python" "fme CLI bridge"
    fi
else
    print_warn "FME Form was not detected in standard Linux / macOS paths."
    print_detail "Note" "FME MCP will run standalone; FME Form can be linked anytime via FME_DIR."
fi

echo ""

# --- Step 2: Resolve Standalone Binary Runtime ---
print_step "2/4: Resolving FME MCP runtime (zero dependencies)..."

TARGET_EXE="${INSTALL_DIR}/fme-mcp"
OS_TYPE=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH_TYPE=$(uname -m)

case "$ARCH_TYPE" in
    x86_64|amd64)
        ARCH="x64"
        ;;
    aarch64|arm64)
        ARCH="arm64"
        ;;
    *)
        ARCH="$ARCH_TYPE"
        ;;
esac

PRIMARY_URL="https://github.com/${REPO}/releases/download/${TAG}/fme-mcp-linux-${ARCH}"
FALLBACK_URL="https://github.com/${REPO}/releases/latest/download/fme-mcp"
FALLBACK_URL_LEGACY="https://github.com/${REPO}/releases/latest/download/fme-mcp-ultra"

if [ "$DRY_RUN" = true ]; then
    print_detail "Target Binary" "$TARGET_EXE"
    print_detail "Primary URL" "$PRIMARY_URL"
    print_detail "Action (Dry-Run)" "Would download standalone binary (zero python dependencies required)"
else
    mkdir -p "$INSTALL_DIR"

    if [ -f "$TARGET_EXE" ] && [ "$FORCE" = false ]; then
        print_success "Existing standalone binary found at $TARGET_EXE (Use --force to overwrite)"
    elif [ -f "${INSTALL_DIR}/fme-mcp-ultra" ] && [ "$FORCE" = false ]; then
        cp -f "${INSTALL_DIR}/fme-mcp-ultra" "$TARGET_EXE"
        chmod +x "$TARGET_EXE"
        print_success "Upgraded standalone binary to $TARGET_EXE"
    else
        DOWNLOAD_OK=false
        TMP_FILE=$(mktemp)

        for url in "$PRIMARY_URL" "$FALLBACK_URL" "$FALLBACK_URL_LEGACY"; do
            print_step "Downloading standalone binary from $url..."
            if command -v curl >/dev/null 2>&1; then
                if curl -fsSL -A "fme-mcp-installer" "$url" -o "$TMP_FILE" 2>/dev/null; then
                    DOWNLOAD_OK=true
                    break
                fi
            elif command -v wget >/dev/null 2>&1; then
                if wget -q -U "fme-mcp-installer" "$url" -O "$TMP_FILE" 2>/dev/null; then
                    DOWNLOAD_OK=true
                    break
                fi
            fi
        done

        if [ "$DOWNLOAD_OK" = true ] && [ -s "$TMP_FILE" ]; then
            mv "$TMP_FILE" "$TARGET_EXE"
            chmod +x "$TARGET_EXE"
            print_success "Successfully installed FME MCP standalone binary to $TARGET_EXE"
        else
            rm -f "$TMP_FILE"
            print_warn "Prebuilt release binary could not be fetched from GitHub (network offline or release pending)."
            print_warn "Generating a lightweight fallback launcher shim at $TARGET_EXE..."

            cat << 'EOF' > "$TARGET_EXE"
#!/usr/bin/env bash
if command -v fme-mcp >/dev/null 2>&1; then
    exec fme-mcp "$@"
elif command -v python3 >/dev/null 2>&1 && python3 -c "import fme_mcp_ultra" 2>/dev/null; then
    exec python3 -m fme_mcp_ultra "$@"
elif command -v uvx >/dev/null 2>&1; then
    exec uvx fme-mcp "$@"
else
    echo "[!] fme-mcp is not yet available in PATH." >&2
    exit 1
fi
EOF
            chmod +x "$TARGET_EXE"
            cp -f "$TARGET_EXE" "$ALIAS_EXE" 2>/dev/null || true
            chmod +x "$ALIAS_EXE" 2>/dev/null || true
            cp -f "$TARGET_EXE" "$ALIAS_EXE2" 2>/dev/null || true
            chmod +x "$ALIAS_EXE2" 2>/dev/null || true
            print_success "Installed fallback launcher shim: $TARGET_EXE"
        fi
    fi
fi

echo ""

# --- Step 3: MCP Clients Auto-Detection & Configuration ---
print_step "3/4: Detecting and configuring AI Agent MCP clients..."

update_json_client() {
    local client_name="$1"
    local config_file="$2"
    local server_cmd="$3"
    local fme_dir_val="$4"
    local dry_run_mode="$5"

    local parent_dir
    parent_dir=$(dirname "$config_file")

    if [ "$dry_run_mode" = true ]; then
        print_success "[$client_name] Configuration preview:"
        print_detail "File Path" "$config_file"
        print_detail "Command" "$server_cmd"
        print_detail "Args" "serve --transport stdio"
        if [ -n "$fme_dir_val" ]; then
            print_detail "FME_DIR" "$fme_dir_val"
        fi
        return 0
    fi

    mkdir -p "$parent_dir"

    if command -v python3 >/dev/null 2>&1; then
        python3 - << PYEOF
import json
import os

path = "$config_file"
cmd = "$server_cmd"
fme_dir = "$fme_dir_val"

data = {}
if os.path.exists(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

if "mcpServers" not in data:
    data["mcpServers"] = {}

server_entry = {
    "command": cmd,
    "args": ["serve", "--transport", "stdio"],
    "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1"
    }
}
if fme_dir:
    server_entry["env"]["FME_DIR"] = fme_dir

# Remove legacy entries (mcp-fme, fme-mcp-ultra) if present
data["mcpServers"].pop("mcp-fme", None)
data["mcpServers"].pop("fme-mcp-ultra", None)

# Register exclusively fme-mcp
data["mcpServers"]["fme-mcp"] = server_entry

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
PYEOF
        print_success "[$client_name] Configured: $config_file"
    else
        cat << JSONEOF > "$config_file"
{
  "mcpServers": {
    "fme-mcp": {
      "command": "$server_cmd",
      "args": ["serve", "--transport", "stdio"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1"$([ -n "$fme_dir_val" ] && echo -e ",\n        \"FME_DIR\": \"$fme_dir_val\"")
      }
    }
  }
}
JSONEOF
        print_success "[$client_name] Configured: $config_file"
    fi
}

if [ "$OS_TYPE" = "darwin" ]; then
    CLAUDE_CONFIG="${HOME}/Library/Application Support/Claude/claude_desktop_config.json"
    VSCODE_CONFIG="${HOME}/Library/Application Support/Code/User/mcp.json"
else
    CLAUDE_CONFIG="${HOME}/.config/Claude/claude_desktop_config.json"
    VSCODE_CONFIG="${HOME}/.config/Code/User/mcp.json"
fi

CURSOR_CONFIG="${HOME}/.cursor/mcp.json"
ANTIGRAVITY_CONFIG="${HOME}/.gemini/config/mcp_config.json"
WINDSURF_CONFIG="${HOME}/.codeium/windsurf/mcp_config.json"

CONFIGURED_COUNT=0

check_and_configure() {
    local name="$1"
    local cfg="$2"
    local detected="$3"

    if [ "$CONFIGURE_ALL" = true ] || [ "$detected" = true ]; then
        local status_str="DETECTED"
        [ "$detected" != true ] && status_str="EXPLICIT"
        echo -e "  -> Found ${COLOR_MAGENTA}${name}${COLOR_RESET} (${status_str})"
        update_json_client "$name" "$cfg" "$TARGET_EXE" "$FME_DIR" "$DRY_RUN"
        CONFIGURED_COUNT=$((CONFIGURED_COUNT + 1))
    else
        print_detail "Skipped $name" "Not detected (use --configure-all to force)"
    fi
}

# Claude Desktop
CLAUDE_DETECTED=false
[ -d "$(dirname "$CLAUDE_CONFIG")" ] || [ -d "/Applications/Claude.app" ] && CLAUDE_DETECTED=true
check_and_configure "Claude Desktop" "$CLAUDE_CONFIG" "$CLAUDE_DETECTED"

# Cursor
CURSOR_DETECTED=false
[ -d "${HOME}/.cursor" ] || [ -d "/Applications/Cursor.app" ] || command -v cursor >/dev/null 2>&1 && CURSOR_DETECTED=true
check_and_configure "Cursor" "$CURSOR_CONFIG" "$CURSOR_DETECTED"

# Antigravity / Gemini
ANTIGRAVITY_DETECTED=false
[ -d "${HOME}/.gemini" ] && ANTIGRAVITY_DETECTED=true
check_and_configure "Antigravity / Gemini" "$ANTIGRAVITY_CONFIG" "$ANTIGRAVITY_DETECTED"

# VS Code
VSCODE_DETECTED=false
[ -d "$(dirname "$VSCODE_CONFIG")" ] || [ -d "/Applications/Visual Studio Code.app" ] || command -v code >/dev/null 2>&1 && VSCODE_DETECTED=true
check_and_configure "VS Code" "$VSCODE_CONFIG" "$VSCODE_DETECTED"

# Windsurf
WINDSURF_DETECTED=false
[ -d "${HOME}/.codeium/windsurf" ] || [ -d "${HOME}/.windsurf" ] || [ -d "/Applications/Windsurf.app" ] && WINDSURF_DETECTED=true
check_and_configure "Windsurf" "$WINDSURF_CONFIG" "$WINDSURF_DETECTED"

if [ "$CONFIGURED_COUNT" -eq 0 ] && [ "$CONFIGURE_ALL" = false ]; then
    print_warn "No active AI clients detected. Configuring Claude Desktop and Cursor by default..."
    update_json_client "Claude Desktop" "$CLAUDE_CONFIG" "$TARGET_EXE" "$FME_DIR" "$DRY_RUN"
    update_json_client "Cursor" "$CURSOR_CONFIG" "$TARGET_EXE" "$FME_DIR" "$DRY_RUN"
    CONFIGURED_COUNT=2
fi

echo ""

# --- Step 4: Summary & Verification ---
print_step "4/4: Installation Summary & Next Steps"
echo -e "${COLOR_GREEN}==========================================================================${COLOR_RESET}"
echo -e "${COLOR_WHITE}  FME MCP INSTALLATION SUMMARY                                            ${COLOR_RESET}"
echo -e "${COLOR_GREEN}==========================================================================${COLOR_RESET}"
print_detail "Server Command" "$TARGET_EXE"
print_detail "Server Args" "serve --transport stdio"
if [ -n "$FME_DIR" ]; then
    print_detail "FME Form Status" "Bound to $FME_DIR"
else
    print_detail "FME Form Status" "Unbound (Standalone / Cloud mode)"
fi
print_detail "Configured Clients" "$CONFIGURED_COUNT client(s) updated successfully"
echo ""
echo -e "${COLOR_CYAN}Next Steps:${COLOR_RESET}"
echo -e "${COLOR_WHITE}  1. Restart your AI client (Claude, Cursor, Antigravity, VS Code, Windsurf).${COLOR_RESET}"
echo -e "${COLOR_WHITE}  2. Open chat and ask: 'List available FME tools' or 'Audit my workspace'.${COLOR_RESET}"
echo -e "${COLOR_WHITE}  3. Enjoy high-speed, secure FME Form spatial engineering in your AI workflow!${COLOR_RESET}"
echo -e "${COLOR_GREEN}==========================================================================${COLOR_RESET}"
echo ""
