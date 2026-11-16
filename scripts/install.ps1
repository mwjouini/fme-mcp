# MCP FME - Universal 1-Command Installer
# Model Context Protocol Server for Safe Software FME (2018.0 - 2026+)
# Usage:
#   irm https://raw.githubusercontent.com/mwjouini/fme-mcp-ultra/main/scripts/install.ps1 | iex

& {
    function Start-Installer {
        [CmdletBinding()]
        param(
            [Parameter(Position = 0)]
            [string]$InstallDir = "$env:LOCALAPPDATA\mcp-fme\bin",

            [string]$Repo = "mwjouini/fme-mcp-ultra",
            [string]$Tag = "latest",
            [string]$FmeDir = "",
            [switch]$PreferFmePython,
            [switch]$ConfigureAll,
            [switch]$DryRun,
            [switch]$Force,
            [switch]$Help
        )

        $ErrorActionPreference = "Stop"

        # Check environment, global, or caller flags for DryRun
        if (-not $DryRun) {
            $callerDryRun = Get-Variable -Name "DryRun" -Scope 1 -ValueOnly -ErrorAction SilentlyContinue
            if (-not $callerDryRun) {
                $callerDryRun = Get-Variable -Name "DryRun" -Scope 2 -ValueOnly -ErrorAction SilentlyContinue
            }
            if ($env:DRY_RUN -eq "1" -or $global:DryRun -or ($callerDryRun -eq $true)) {
                $DryRun = [System.Management.Automation.SwitchParameter]::Present
            }
        }

        if ($Help) {
            Write-Host "MCP FME - Universal 1-Command Installer`n"
            Write-Host "Usage:"
            Write-Host "    irm https://raw.githubusercontent.com/mwjouini/fme-mcp-ultra/main/scripts/install.ps1 | iex`n"
            Write-Host "Parameters:"
            Write-Host "    -InstallDir <path>   Destination directory for standalone binary (default: `$env:LOCALAPPDATA\mcp-fme\bin)"
            Write-Host "    -Repo <repo>         GitHub repository owner/repo (default: mwjouini/fme-mcp-ultra)"
            Write-Host "    -Tag <tag>           Release tag to install (default: latest)"
            Write-Host "    -FmeDir <path>       Manual override path for FME Form installation"
            Write-Host "    -PreferFmePython     Use FME's bundled Python interpreter if available"
            Write-Host "    -ConfigureAll        Configure all supported MCP clients even if not currently detected"
            Write-Host "    -DryRun              Simulate installation and configuration without modifying system"
            Write-Host "    -Force               Overwrite existing binary and configurations without prompting"
            Write-Host "    -Help                Display this help message"
            return
        }

        # Ensure TLS 1.2 and TLS 1.3 are enabled for secure downloads
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
            if ([Net.SecurityProtocolType].GetMember("Tls13").Count -gt 0) {
                [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls13
            }
        } catch {
            # Ignore if TLS 1.3 is not supported by current .NET runtime
        }

        # --- Console Output Helpers (Pure ASCII for PS 5.1 / Windows-1252 compatibility) ---
        function Write-Banner {
            Write-Host ""
            Write-Host "==========================================================================" -ForegroundColor Cyan
            Write-Host "  MCP FME - Universal 1-Command Installer                                " -ForegroundColor White
            Write-Host "  Model Context Protocol Server for Safe Software FME (2018.0 - 2026+)    " -ForegroundColor Gray
            Write-Host "==========================================================================" -ForegroundColor Cyan
            if ($DryRun) {
                Write-Host "  *** DRY-RUN MODE: No files or configurations will be modified ***       " -ForegroundColor Yellow
                Write-Host "--------------------------------------------------------------------------" -ForegroundColor Yellow
            }
            Write-Host ""
        }

        function Write-Step {
            param([string]$Message)
            Write-Host "[*] $Message" -ForegroundColor Cyan
        }

        function Write-Success {
            param([string]$Message)
            Write-Host " [+] $Message" -ForegroundColor Green
        }

        function Write-Warn {
            param([string]$Message)
            Write-Host " [!] $Message" -ForegroundColor Yellow
        }

        function Write-Failure {
            param([string]$Message)
            Write-Host " [x] $Message" -ForegroundColor Red
        }

        function Write-Detail {
            param([string]$Key, [string]$Value)
            Write-Host ("     - {0}: " -f $Key) -ForegroundColor Gray -NoNewline
            Write-Host "$Value" -ForegroundColor White
        }

        # --- Step 1: Detect Safe Software FME Form Installation ---
        function Find-FmeInstallation {
            param([string]$OverridePath)

            # 1. Explicit parameter or environment variable
            if ($OverridePath -and (Test-Path $OverridePath)) {
                if (Test-Path (Join-Path $OverridePath "fme.exe")) {
                    return (Resolve-Path $OverridePath).Path
                }
            }

            foreach ($varName in @("FME_DIR", "FME_HOME", "SAFE_FME_HOME")) {
                $envVal = [Environment]::GetEnvironmentVariable($varName, "Process")
                if (-not $envVal) { $envVal = [Environment]::GetEnvironmentVariable($varName, "User") }
                if (-not $envVal) { $envVal = [Environment]::GetEnvironmentVariable($varName, "Machine") }
                if ($envVal -and (Test-Path (Join-Path $envVal "fme.exe"))) {
                    return (Resolve-Path $envVal).Path
                }
            }

            # 2. Windows Registry checks (HKLM and HKCU, 64-bit and 32-bit WOW64)
            $regKeys = @(
                "HKLM:\SOFTWARE\Safe Software Inc.\Feature Manipulation Engine",
                "HKLM:\SOFTWARE\Safe Software Inc.\Installation",
                "HKLM:\SOFTWARE\Safe Software Inc.\FME Form",
                "HKLM:\SOFTWARE\Safe Software Inc.\FME Desktop",
                "HKLM:\SOFTWARE\Safe Software Inc.\FME Suite",
                "HKCU:\SOFTWARE\Safe Software Inc.\Feature Manipulation Engine",
                "HKCU:\SOFTWARE\Safe Software Inc.\FME Form",
                "HKCU:\SOFTWARE\Safe Software Inc.\FME Desktop",
                "HKLM:\SOFTWARE\WOW6432Node\Safe Software Inc.\Feature Manipulation Engine"
            )

            foreach ($rk in $regKeys) {
                if (Test-Path $rk) {
                    $props = Get-ItemProperty -Path $rk -ErrorAction SilentlyContinue
                    if ($props) {
                        foreach ($propName in @("FME_HOME_LAST_INSTALLED", "FME_HOME", "InstallDir", "Path", "DestinationFolder")) {
                            $val = $props.$propName
                            if ($val -and (Test-Path (Join-Path $val "fme.exe"))) {
                                return (Resolve-Path $val).Path
                            }
                        }
                    }
                    # Also search subkeys (e.g. Safe Software Inc.\FME Desktop\2024.1)
                    $subkeys = Get-ChildItem -Path $rk -ErrorAction SilentlyContinue
                    if ($subkeys) {
                        foreach ($sk in $subkeys) {
                            $subProps = Get-ItemProperty -Path $sk.PSPath -ErrorAction SilentlyContinue
                            if ($subProps) {
                                foreach ($propName in @("FME_HOME", "InstallDir", "Path", "(default)")) {
                                    $val = $subProps.$propName
                                    if ($val -and (Test-Path (Join-Path $val "fme.exe"))) {
                                        return (Resolve-Path $val).Path
                                    }
                                }
                            }
                        }
                    }
                }
            }

            # 3. System PATH search
            $cmd = Get-Command fme.exe -ErrorAction SilentlyContinue
            if ($cmd -and $cmd.Source) {
                $parent = Split-Path -Parent $cmd.Source
                if (Test-Path (Join-Path $parent "fme.exe")) {
                    return (Resolve-Path $parent).Path
                }
            }

            # 4. Standard installation directories
            $dirPatterns = @(
                "$env:ProgramFiles\FME*",
                "${env:ProgramFiles(x86)}\FME*",
                "C:\Program Files\FME*",
                "C:\Program Files (x86)\FME*",
                "C:\apps\FME*",
                "C:\FME*"
            )
            foreach ($pattern in $dirPatterns) {
                $parentDir = Split-Path -Parent $pattern
                $leafPattern = Split-Path -Leaf $pattern
                if (Test-Path $parentDir) {
                    $matched = Get-ChildItem -Path $parentDir -Filter $leafPattern -Directory -ErrorAction SilentlyContinue |
                        Sort-Object Name -Descending
                    foreach ($m in $matched) {
                        if (Test-Path (Join-Path $m.FullName "fme.exe")) {
                            return (Resolve-Path $m.FullName).Path
                        }
                    }
                }
            }

            return $null
        }

        function Find-FmeBundledPython {
            param([string]$FmeDirectory)

            if (-not $FmeDirectory -or -not (Test-Path $FmeDirectory)) {
                return $null
            }

            # Check fmepython subdirectories (sort descending to get newest e.g. fmepython313 > fmepython312 > fmepython310)
            $pyDirs = Get-ChildItem -Path $FmeDirectory -Directory -Filter "fmepython*" -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending
            foreach ($d in $pyDirs) {
                $pyExe = Join-Path $d.FullName "python.exe"
                if (Test-Path $pyExe) {
                    return $pyExe
                }
            }

            # Standard python subfolder
            $stdPy = Join-Path $FmeDirectory "python\python.exe"
            if (Test-Path $stdPy) {
                return $stdPy
            }

            return $null
        }

        function Get-FmeVersionInfo {
            param([string]$FmeDirectory)

            $info = @{
                Installed = $false
                Version = "Not Detected"
                Build = ""
                Executable = ""
            }

            if (-not $FmeDirectory) { return $info }

            $fmeExe = Join-Path $FmeDirectory "fme.exe"
            if (Test-Path $fmeExe) {
                $info.Installed = $true
                $info.Executable = $fmeExe
                try {
                    $verOutput = & $fmeExe INFO JSON 2>$null
                    if ($verOutput) {
                        $rawStr = [string]$verOutput
                        $idx = $rawStr.IndexOf('{')
                        if ($idx -ge 0) {
                            $jsonStr = $rawStr.Substring($idx)
                            $parsed = $jsonStr | ConvertFrom-Json -ErrorAction SilentlyContinue
                            if ($parsed -and $parsed.Version) {
                                $info.Version = $parsed.Version
                                $info.Build = $parsed.Build
                                return $info
                            }
                        }
                    }
                } catch {
                    # Fallback to file version info
                }

                # Fallback to assembly/file info
                try {
                    $fvi = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($fmeExe)
                    if ($fvi -and $fvi.FileVersion) {
                        $info.Version = "FME Form $($fvi.FileVersion)"
                    } else {
                        $info.Version = "FME Form"
                    }
                } catch {
                    $info.Version = "FME Form"
                }
            }

            return $info
        }

        # --- Step 2: Binary Installation / Runtime Resolver ---
        function Install-StandaloneBinary {
            param(
                [string]$TargetDir,
                [string]$Repository,
                [string]$ReleaseTag,
                [switch]$DryRunMode,
                [switch]$ForceOverwrite
            )

            $targetExe = Join-Path $TargetDir "fme-mcp-ultra.exe"
            $aliasExe = Join-Path $TargetDir "mcp-fme.exe"

            if (-not $DryRunMode) {
                if (-not (Test-Path $TargetDir)) {
                    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
                }
            }

            # Check if existing standalone binary is already installed and valid
            if ((Test-Path $targetExe) -and (-not $ForceOverwrite)) {
                Write-Success "Existing standalone binary found at $targetExe (Use -Force to overwrite)"
                if (-not (Test-Path $aliasExe)) {
                    try {
                        Copy-Item -Path $targetExe -Destination $aliasExe -Force -ErrorAction SilentlyContinue
                    } catch { }
                }
                return $targetExe
            }

            # If running from local repository build or dist directory, prefer local binary if available
            $repoRoot = $PSScriptRoot
            if (-not $repoRoot) {
                $repoRoot = (Get-Location).Path
            }
            if ($repoRoot) {
                $localDistBin = Join-Path $repoRoot "dist\fme-mcp-ultra.exe"
                if (-not (Test-Path $localDistBin)) {
                    $localDistBin = Join-Path (Split-Path -Parent $repoRoot) "dist\fme-mcp-ultra.exe"
                }
                if (Test-Path $localDistBin) {
                    Write-Success "Found locally built binary: $localDistBin"
                    if ($DryRunMode) {
                        Write-Detail "Action (Dry-Run)" "Would copy $localDistBin -> $targetExe"
                        return $targetExe
                    }
                    try {
                        Copy-Item -Path $localDistBin -Destination $targetExe -Force
                    } catch {
                        Write-Warn "Target binary is currently in use by an active MCP client. Keeping active binary."
                    }
                    try {
                        Copy-Item -Path $localDistBin -Destination $aliasExe -Force
                    } catch { }
                    Write-Success "Installed MCP FME binary to $targetExe"
                    return $targetExe
                }
            }

            # Download prebuilt standalone binary from GitHub Releases
            $downloadUrls = @(
                "https://github.com/$Repository/releases/download/$ReleaseTag/fme-mcp-ultra.exe",
                "https://github.com/$Repository/releases/download/$ReleaseTag/fme-mcp-ultra-windows-x64.exe",
                "https://github.com/$Repository/releases/latest/download/fme-mcp-ultra.exe",
                "https://github.com/$Repository/releases/latest/download/fme-mcp-ultra-windows-x64.exe"
            )

            if ($DryRunMode) {
                Write-Detail "Target Binary" "$targetExe"
                Write-Detail "Primary URL" "$($downloadUrls[0])"
                Write-Detail "Action (Dry-Run)" "Would download standalone binary (zero python dependencies required)"
                return $targetExe
            }

            $downloadSuccess = $false
            foreach ($url in $downloadUrls) {
                try {
                    Write-Step "Downloading standalone binary from $url..."
                    $webClient = New-Object System.Net.WebClient
                    $webClient.Headers.Add("User-Agent", "mcp-fme-installer")
                    $tempFile = [System.IO.Path]::GetTempFileName()
                    $webClient.DownloadFile($url, $tempFile)

                    # Basic validation: ensure file size is > 1 MB
                    $fileSize = (Get-Item $tempFile).Length
                    if ($fileSize -gt 1000000) {
                        try {
                            Move-Item -Path $tempFile -Destination $targetExe -Force
                            Copy-Item -Path $targetExe -Destination $aliasExe -Force -ErrorAction SilentlyContinue
                        } catch {
                            Write-Warn "Binary at $targetExe is currently locked by a running process. Retaining active binary."
                        }
                        $downloadSuccess = $true
                        $sizeMb = [math]::Round($fileSize / 1MB, 2)
                        Write-Success "Successfully downloaded and verified standalone binary ($sizeMb MB)"
                        break
                    } else {
                        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
                    }
                } catch {
                    # Try next fallback URL
                }
            }

            if (-not $downloadSuccess) {
                if (Test-Path $targetExe) {
                    Write-Warn "GitHub Release download was unavailable, but existing binary at $targetExe is retained."
                    return $targetExe
                } else {
                    Write-Warn "Prebuilt release binary could not be fetched from GitHub (network offline or release pending)."
                    Write-Warn "Generating a lightweight fallback launcher shim at $targetExe..."
                    
                    $shimLines = @(
                        "@echo off",
                        "REM MCP FME Launcher Shim",
                        "where fme-mcp-ultra >nul 2>&1",
                        "if %ERRORLEVEL% EQU 0 (",
                        "    fme-mcp-ultra %*",
                        "    exit /b %ERRORLEVEL%",
                        ")",
                        "python -m fme_mcp_ultra %* 2>nul",
                        "if %ERRORLEVEL% EQU 0 exit /b 0",
                        "uvx fme-mcp-ultra %*",
                        "exit /b %ERRORLEVEL%"
                    )
                    $cmdShim = Join-Path $TargetDir "fme-mcp-ultra.cmd"
                    $shimLines | Set-Content -Path $cmdShim -Encoding ASCII
                    $aliasShim = Join-Path $TargetDir "mcp-fme.cmd"
                    $shimLines | Set-Content -Path $aliasShim -Encoding ASCII
                    Write-Success "Installed fallback launcher shim: $cmdShim & $aliasShim"
                    return $cmdShim
                }
            }

            return $targetExe
        }

        # --- Step 3: MCP Clients Auto-Detection & Configuration ---
        function Update-McpClientConfig {
            param(
                [string]$ClientName,
                [string]$ConfigFilePath,
                [string]$ServerCommand,
                [string[]]$ServerArgs,
                [hashtable]$ServerEnv,
                [switch]$DryRunMode
            )

            $parentDir = Split-Path -Parent $ConfigFilePath

            $serverDef = [PSCustomObject]@{
                command = $ServerCommand
                args = @($ServerArgs)
                env = [PSCustomObject]$ServerEnv
            }

            if ($DryRunMode) {
                Write-Success "[$ClientName] Configuration preview:"
                Write-Detail "File Path" $ConfigFilePath
                Write-Detail "Command" $ServerCommand
                Write-Detail "Args" ($ServerArgs -join " ")
                if ($ServerEnv.FME_DIR) {
                    Write-Detail "FME_DIR" $ServerEnv.FME_DIR
                }
                return $true
            }

            try {
                if (-not (Test-Path $parentDir)) {
                    New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
                }

                $configObj = $null
                if (Test-Path $ConfigFilePath) {
                    $rawContent = Get-Content -Path $ConfigFilePath -Raw -ErrorAction SilentlyContinue
                    if ($rawContent -and $rawContent.Trim()) {
                        try {
                            $configObj = $rawContent | ConvertFrom-Json
                        } catch {
                            $bakFile = "$ConfigFilePath.bak.$(Get-Date -Format 'yyyyMMddHHmmss')"
                            Copy-Item -Path $ConfigFilePath -Destination $bakFile -Force
                            Write-Warn "Existing $ClientName config had syntax errors. Backed up to $bakFile."
                            $configObj = $null
                        }
                    }
                }

                if (-not $configObj) {
                    $configObj = [PSCustomObject]@{}
                }

                if (-not $configObj.mcpServers) {
                    $configObj | Add-Member -MemberType NoteProperty -Name "mcpServers" -Value ([PSCustomObject]@{}) -Force
                }

                # Register both mcp-fme and fme-mcp-ultra for complete interoperability
                $configObj.mcpServers | Add-Member -MemberType NoteProperty -Name "mcp-fme" -Value $serverDef -Force
                $configObj.mcpServers | Add-Member -MemberType NoteProperty -Name "fme-mcp-ultra" -Value $serverDef -Force

                $jsonOutput = $configObj | ConvertTo-Json -Depth 10
                Set-Content -Path $ConfigFilePath -Value $jsonOutput -Encoding UTF8 -Force
                Write-Success "[$ClientName] Configured: $ConfigFilePath"
                return $true
            } catch {
                Write-Failure "[$ClientName] Failed to update config: $_"
                return $false
            }
        }

        # --- Main Execution Flow ---
        Write-Banner

        # 1. Detect FME Form
        Write-Step "1/4: Detecting Safe Software FME Form installation..."
        $detectedFmeDir = Find-FmeInstallation -OverridePath $FmeDir
        $detectedFmePython = $null
        $fmeInfo = Get-FmeVersionInfo -FmeDirectory $detectedFmeDir

        if ($detectedFmeDir) {
            $detectedFmePython = Find-FmeBundledPython -FmeDirectory $detectedFmeDir
            Write-Success "FME Form Detected!"
            Write-Detail "Home Directory" $detectedFmeDir
            Write-Detail "Version" $fmeInfo.Version
            if ($detectedFmePython) {
                $pyVer = & $detectedFmePython --version 2>&1
                Write-Detail "Bundled Python" "$detectedFmePython ($pyVer)"
            } else {
                Write-Detail "Bundled Python" "fme.exe python CLI bridge"
            }
        } else {
            Write-Warn "FME Form was not detected in standard registry or system paths."
            Write-Detail "Note" "MCP FME will run standalone; FME Form can be linked anytime via FME_DIR."
        }

        Write-Host ""

        # 2. Resolve Runtime / Standalone Binary
        Write-Step "2/4: Resolving MCP FME runtime (zero dependencies)..."

        $finalServerCommand = ""
        $finalServerArgs = @("serve", "--transport", "stdio")
        $envSettings = @{
            "PYTHONIOENCODING" = "utf-8"
            "PYTHONUNBUFFERED" = "1"
        }

        if ($detectedFmeDir) {
            $envSettings["FME_DIR"] = $detectedFmeDir
        }

        if ($PreferFmePython -and $detectedFmePython) {
            Write-Step "Checking FME bundled Python for fme-mcp-ultra..."
            $fmeHasPackage = $false
            try {
                $check = & $detectedFmePython -c "import fme_mcp_ultra; print('OK')" 2>$null
                if ($check -match "OK") { $fmeHasPackage = $true }
            } catch { }

            if ($fmeHasPackage) {
                Write-Success "Using FME's bundled Python interpreter as runtime."
                $finalServerCommand = $detectedFmePython
                $finalServerArgs = @("-m", "fme_mcp_ultra", "serve", "--transport", "stdio")
            } else {
                Write-Warn "fme-mcp-ultra is not installed inside FME Python. Proceeding with Standalone Binary."
                $finalServerCommand = Install-StandaloneBinary -TargetDir $InstallDir -Repository $Repo -ReleaseTag $Tag -DryRunMode:$DryRun -ForceOverwrite:$Force
            }
        } else {
            $finalServerCommand = Install-StandaloneBinary -TargetDir $InstallDir -Repository $Repo -ReleaseTag $Tag -DryRunMode:$DryRun -ForceOverwrite:$Force
        }

        # Add InstallDir to current session PATH
        if (-not $DryRun -and (Test-Path $InstallDir)) {
            if ($env:PATH -notlike "*$InstallDir*") {
                $env:PATH = "$InstallDir;$env:PATH"
            }
        }

        Write-Host ""

        # 3. Detect and Configure AI Agent MCP Clients
        Write-Step "3/4: Detecting and configuring AI Agent MCP clients..."

        $clients = @(
            @{
                Name = "Claude Desktop"
                ConfigFile = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
                Detected = (
                    (Test-Path (Join-Path $env:APPDATA "Claude")) -or
                    (Test-Path (Join-Path $env:LOCALAPPDATA "Programs\Claude")) -or
                    (Get-Process "Claude" -ErrorAction SilentlyContinue)
                )
            },
            @{
                Name = "Cursor"
                ConfigFile = Join-Path $env:USERPROFILE ".cursor\mcp.json"
                Detected = (
                    (Test-Path (Join-Path $env:USERPROFILE ".cursor")) -or
                    (Test-Path (Join-Path $env:LOCALAPPDATA "Programs\cursor")) -or
                    (Get-Command "cursor" -ErrorAction SilentlyContinue) -or
                    (Get-Process "Cursor" -ErrorAction SilentlyContinue)
                )
            },
            @{
                Name = "Antigravity / Gemini"
                ConfigFile = Join-Path $env:USERPROFILE ".gemini\config\mcp_config.json"
                Detected = (
                    (Test-Path (Join-Path $env:USERPROFILE ".gemini")) -or
                    (Test-Path (Join-Path $env:USERPROFILE ".gemini\config"))
                )
            },
            @{
                Name = "VS Code"
                ConfigFile = Join-Path $env:APPDATA "Code\User\mcp.json"
                Detected = (
                    (Test-Path (Join-Path $env:APPDATA "Code")) -or
                    (Test-Path (Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code")) -or
                    (Get-Command "code" -ErrorAction SilentlyContinue) -or
                    (Get-Process "Code" -ErrorAction SilentlyContinue)
                )
            },
            @{
                Name = "Windsurf"
                ConfigFile = Join-Path $env:USERPROFILE ".codeium\windsurf\mcp_config.json"
                Detected = (
                    (Test-Path (Join-Path $env:USERPROFILE ".codeium\windsurf")) -or
                    (Test-Path (Join-Path $env:USERPROFILE ".windsurf")) -or
                    (Test-Path (Join-Path $env:APPDATA "Windsurf")) -or
                    (Get-Process "Windsurf" -ErrorAction SilentlyContinue)
                )
            }
        )

        $configuredCount = 0
        foreach ($client in $clients) {
            $shouldConfigure = $ConfigureAll -or $client.Detected

            if ($shouldConfigure) {
                $statusStr = if ($client.Detected) { "DETECTED" } else { "EXPLICIT" }
                Write-Host "  -> Found $($client.Name) ($statusStr)" -ForegroundColor Magenta
                $ok = Update-McpClientConfig -ClientName $client.Name `
                                             -ConfigFilePath $client.ConfigFile `
                                             -ServerCommand $finalServerCommand `
                                             -ServerArgs $finalServerArgs `
                                             -ServerEnv $envSettings `
                                             -DryRunMode:$DryRun
                if ($ok) { $configuredCount++ }
            } else {
                Write-Detail "Skipped $($client.Name)" "Not currently installed (use -ConfigureAll to force)"
            }
        }

        # If no clients were detected at all (e.g. fresh VM), configure Claude Desktop and Cursor by default
        if ($configuredCount -eq 0 -and -not $ConfigureAll) {
            Write-Warn "No active AI clients detected. Configuring Claude Desktop and Cursor by default..."
            foreach ($client in ($clients | Where-Object { $_.Name -in @("Claude Desktop", "Cursor") })) {
                Update-McpClientConfig -ClientName $client.Name `
                                       -ConfigFilePath $client.ConfigFile `
                                       -ServerCommand $finalServerCommand `
                                       -ServerArgs $finalServerArgs `
                                       -ServerEnv $envSettings `
                                       -DryRunMode:$DryRun | Out-Null
            }
        }

        Write-Host ""

        # 4. Summary & Verification
        Write-Step "4/4: Installation Summary & Next Steps"
        Write-Host "==========================================================================" -ForegroundColor Green
        Write-Host "  MCP FME INSTALLATION SUMMARY                                            " -ForegroundColor White
        Write-Host "==========================================================================" -ForegroundColor Green
        Write-Detail "Server Command" $finalServerCommand
        Write-Detail "Server Args" ($finalServerArgs -join " ")
        if ($detectedFmeDir) {
            Write-Detail "FME Form Status" "Bound to $detectedFmeDir"
        } else {
            Write-Detail "FME Form Status" "Unbound (Standalone / Cloud mode)"
        }
        Write-Detail "Configured Clients" "$configuredCount client(s) updated successfully"
        Write-Host ""
        Write-Host "Next Steps:" -ForegroundColor Cyan
        Write-Host "  1. Restart your AI client (Claude, Cursor, Antigravity, VS Code, Windsurf)." -ForegroundColor White
        Write-Host "  2. Open chat and ask: 'List available FME tools' or 'Audit my workspace'." -ForegroundColor White
        Write-Host "  3. Enjoy high-speed, secure FME Form spatial engineering in your AI workflow!" -ForegroundColor White
        Write-Host "==========================================================================" -ForegroundColor Green
        Write-Host ""
    }

    Start-Installer @args
}