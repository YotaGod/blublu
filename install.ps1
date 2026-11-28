<#
.SYNOPSIS
    blublu v2.0 - Universal Windows Installer (PowerShell 5.1+ & Core)
    Installs persistent architectural memory skill and CLI for AI coding agents.

.EXAMPLE
    iwr -useb https://raw.githubusercontent.com/YotaGod/blublu/main/install.ps1 | iex
    irm https://raw.githubusercontent.com/YotaGod/blublu/main/install.ps1 | iex
    .\install.ps1 -Scope project
#>

function Install-Blublu {
    [CmdletBinding()]
    param(
        [Parameter(Position = 0)]
        [ValidateSet("all", "global", "project", IgnoreCase = $true)]
        [string]$Scope = "all",

        [Parameter(Position = 1)]
        [ValidateSet("all", "codex", "claude", "antigravity", IgnoreCase = $true)]
        [string]$Agent = "all",

        [string]$TargetDir = "",
        [switch]$DryRun,
        [switch]$Upgrade,
        [switch]$Help
    )

    if ($Help) {
        Write-Host ""
        Write-Host "blublu v2.0 Installer - AI Codebase Memory System" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "USAGE:"
        Write-Host "    iwr -useb https://raw.githubusercontent.com/YotaGod/blublu/main/install.ps1 | iex"
        Write-Host "    .\install.ps1 [OPTIONS]"
        Write-Host ""
        Write-Host "OPTIONS:"
        Write-Host "    -Scope <all|global|project>  Installation scope (default: all)"
        Write-Host "    -Agent <all|codex|claude|antigravity> Target agent (default: all)"
        Write-Host "    -Upgrade                     Overwrite existing files"
        Write-Host "    -DryRun                      Preview without modifying disk"
        Write-Host "    -Help                        Display this help"
        Write-Host ""
        return
    }

    $Scope = $Scope.ToLowerInvariant()
    $Agent = $Agent.ToLowerInvariant()

    # Enable TLS 1.2
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    } catch {}

    function Write-Ok($msg)   { Write-Host " [OK]   " -ForegroundColor Green -NoNewline; Write-Host $msg }
    function Write-Info($msg) { Write-Host " [INFO] " -ForegroundColor Blue -NoNewline; Write-Host $msg }
    function Write-Warn($msg) { Write-Host " [WARN] " -ForegroundColor Yellow -NoNewline; Write-Host $msg }
    function Write-Err($msg)  { Write-Host " [ERR]  " -ForegroundColor Red -NoNewline; Write-Host $msg }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "          blublu v2.0 - AI Codebase Memory System         " -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host ""

    $RepoRawBase = "https://raw.githubusercontent.com/YotaGod/blublu/main"
    $SkillRelDir = "skills/blublu"
    $SkillFiles = @(
        "SKILL.md",
        "references/blueprint-template.md",
        "references/mapping-rules.md",
        "references/update-rules.md",
        "references/validation-rules.md"
    )

    $CliFiles = @(
        "scripts/blublu.cmd",
        "scripts/blublu.ps1",
        "scripts/blublu.py",
        "scripts/blublu",
        "scripts/validate-blueprint.py",
        "scripts/scanner.py",
        "scripts/watcher.py",
        "scripts/graph_export.py"
    )

    # Detect local repo vs remote download
    $LocalSourceDir = $null
    if ($PSScriptRoot) {
        $candidate = (Resolve-Path "$PSScriptRoot" -ErrorAction SilentlyContinue)
        if ($candidate -and (Test-Path "$candidate\$SkillRelDir\SKILL.md")) {
            $LocalSourceDir = $candidate.Path
        } else {
            $parent = (Resolve-Path "$PSScriptRoot\.." -ErrorAction SilentlyContinue)
            if ($parent -and (Test-Path "$parent\$SkillRelDir\SKILL.md")) {
                $LocalSourceDir = $parent.Path
            }
        }
    }
    if (-not $LocalSourceDir -and (Test-Path ".\$SkillRelDir\SKILL.md")) {
        $LocalSourceDir = (Get-Item ".").FullName
    }

    if ($LocalSourceDir) {
        Write-Info "Source: Local repository ($LocalSourceDir)"
    } else {
        Write-Info "Source: Remote repository ($RepoRawBase)"
    }

    function Copy-Or-FetchFile($relPath, $destinationPath) {
        $destFolder = [System.IO.Path]::GetDirectoryName($destinationPath)
        if (-not (Test-Path $destFolder)) {
            New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
        }

        if ($LocalSourceDir) {
            $localPath = Join-Path $LocalSourceDir $relPath
            if (Test-Path $localPath) {
                $destFull = [System.IO.Path]::GetFullPath($destinationPath)
                $srcFull = [System.IO.Path]::GetFullPath($localPath)
                if ($srcFull.TrimEnd('\') -ne $destFull.TrimEnd('\')) {
                    Copy-Item -Path $srcFull -Destination $destFull -Force
                }
                return
            }
        }

        # Fallback to remote download
        $url = "$RepoRawBase/$relPath"
        try {
            Invoke-WebRequest -Uri $url -OutFile $destinationPath -UseBasicParsing
        } catch {
            Write-Err "Failed to download $url : $_"
            throw
        }
    }

    # 1. Install CLI tools to User Profile (~/.blublu/bin)
    $UserHome = $env:USERPROFILE
    $CliBinDir = Join-Path $UserHome ".blublu\bin"

    Write-Info "Installing blublu CLI to: $CliBinDir"
    if (-not (Test-Path $CliBinDir)) {
        New-Item -ItemType Directory -Path $CliBinDir -Force | Out-Null
    }

    foreach ($file in $CliFiles) {
        $fileName = [System.IO.Path]::GetFileName($file)
        $destPath = Join-Path $CliBinDir $fileName
        Copy-Or-FetchFile $file $destPath
    }
    Write-Ok "CLI tools installed to $CliBinDir"

    # Add to User PATH if not present
    try {
        $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
        $pathList = ($userPath -split ';') | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        $alreadyInPath = $false
        foreach ($p in $pathList) {
            if ($p.TrimEnd('\') -ieq $CliBinDir.TrimEnd('\')) {
                $alreadyInPath = $true
                break
            }
        }
        if (-not $alreadyInPath) {
            $newUserPath = if ([string]::IsNullOrWhiteSpace($userPath)) { $CliBinDir } else { "$userPath;$CliBinDir" }
            [Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")
            Write-Ok "Added $CliBinDir to user PATH permanently"
        } else {
            Write-Info "$CliBinDir is already in user PATH"
        }
        # Update current process PATH
        if (($env:PATH -split ';') -notcontains $CliBinDir) {
            $env:PATH = "$CliBinDir;$env:PATH"
        }
    } catch {
        Write-Warn "Could not update user PATH automatically. You can add '$CliBinDir' to PATH manually."
    }

    # 2. Determine target directories for Agent Skills
    $InstallDirs = @()
    if ($TargetDir) {
        $InstallDirs += $TargetDir
    } else {
        if ($Scope -eq "all" -or $Scope -eq "global") {
            switch ($Agent) {
                "all" {
                    $InstallDirs += Join-Path $UserHome ".agents\skills\blublu"
                    $InstallDirs += Join-Path $UserHome ".claude\skills\blublu"
                    $InstallDirs += Join-Path $UserHome ".gemini\antigravity\skills\blublu"
                }
                "codex" {
                    $InstallDirs += Join-Path $UserHome ".agents\skills\blublu"
                }
                "claude" {
                    $InstallDirs += Join-Path $UserHome ".claude\skills\blublu"
                }
                "antigravity" {
                    $InstallDirs += Join-Path $UserHome ".gemini\antigravity\skills\blublu"
                }
            }
        }
        if ($Scope -eq "all" -or $Scope -eq "project") {
            # Only install to project if current folder is a project/repo
            $isProject = (Test-Path ".\.git") -or (Test-Path ".\package.json") -or (Test-Path ".\pyproject.toml") -or (Test-Path ".\skills") -or ($Scope -eq "project")
            if ($isProject) {
                $InstallDirs += ".\skills\blublu"
            }
        }
    }

    # Install skill files
    foreach ($target in $InstallDirs) {
        Write-Info "Installing skill to: $target"
        foreach ($file in $SkillFiles) {
            $rel = "$SkillRelDir/$file"
            $dest = Join-Path $target $file
            Copy-Or-FetchFile $rel $dest
        }
        Write-Ok "Installed skill files to $target"
    }

    # 3. Bootstrap instructions in project AGENTS.md / CLAUDE.md if applicable
    $MarkerStart = "<!-- blublu:start -->"
    $MarkerEnd   = "<!-- blublu:end -->"
    $BootstrapBlock = @"
$MarkerStart
## Codebase Architecture & Memory (blublu v2.0.0)
This project uses **blublu** to maintain persistent architectural memory using a 4-level hierarchical blueprint system.

### Mandatory Loading Protocol
1. **ALWAYS read ``.agents/codebase-map.md`` first** (Level 1 - Global Architecture).
2. **Identify the domain** touched by the current task from the Sub-Blueprints Index.
3. **Load ONLY ``.agents/sub-blueprints/<domain>.md``** (Level 2) for the relevant domain. Never load all domains.
4. **Load ``.agents/sub-blueprints/<domain>/<module>.md``** (Level 3) ONLY if making interface/contract-level changes.
5. **Level 4 detail** is loaded ONLY on explicit user request for implementation details.

### Operational Rules
- Respect registered layer boundaries, export contracts, and dependency flows.
- Record cross-service dependencies with Confidence labels: Confirmed | Inferred | Unverified.
- Flag circular dependencies as [CIRCULAR DEPENDENCY - REVIEW REQUIRED].
- Never auto-apply destructive blueprint changes from drift detection reports.

### CLI Tools Available
- ``blublu status`` - Architecture health summary and mode detection.
- ``blublu validate --check-drift`` - Drift detection across all modules.
- ``blublu analyze <module>`` - Hierarchical context for a specific module.
- ``blublu dependencies [--module <name>]`` - Full dependency map.
- For complete protocols, consult ``skills/blublu/SKILL.md``.
$MarkerEnd
"@

    function Apply-Bootstrap($filePath) {
        if (-not (Test-Path $filePath)) {
            Set-Content -Path $filePath -Value $BootstrapBlock -Encoding UTF8
            Write-Ok "Created and bootstrapped $filePath"
            return
        }
        $existing = Get-Content -Path $filePath -Raw -Encoding UTF8
        if ($existing -match [regex]::Escape($MarkerStart)) {
            $pattern = "(?s)" + [regex]::Escape($MarkerStart) + ".*?" + [regex]::Escape($MarkerEnd)
            $newContent = [regex]::Replace($existing, $pattern, $BootstrapBlock)
            Set-Content -Path $filePath -Value $newContent -Encoding UTF8
            Write-Ok "Updated blublu instructions in $filePath"
        } else {
            $appended = $existing.TrimEnd() + "`r`n`r`n" + $BootstrapBlock + "`r`n"
            Set-Content -Path $filePath -Value $appended -Encoding UTF8
            Write-Ok "Added blublu instructions to $filePath"
        }
    }

    if (($Scope -eq "all" -or $Scope -eq "project") -and ((Test-Path ".\.git") -or ($Scope -eq "project"))) {
        Apply-Bootstrap "AGENTS.md"
        Apply-Bootstrap "CLAUDE.md"
    }

    # 4. Check Python 3
    Write-Host ""
    $pythonCmd = Get-Command python, python3 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pythonCmd) {
        Write-Ok "Python detected: $($pythonCmd.Source)"
    } else {
        Write-Warn "Python 3 is not yet detected on PATH."
        Write-Warn "To run the blublu CLI, install Python 3 from https://www.python.org or run:"
        Write-Host "    winget install Python.Python.3.11" -ForegroundColor Cyan
    }

    # 5. Success summary
    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host "     [SUCCESS] blublu installation completed!             " -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Quick Start Guide:" -ForegroundColor White
    Write-Host ""
    Write-Host "1. In Terminal / Command Prompt:" -ForegroundColor Cyan
    Write-Host "   Open a new terminal window and run:"
    Write-Host "     blublu status" -ForegroundColor Yellow
    Write-Host "     blublu init" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. In your AI Coding Agent (Antigravity / Claude Code / Codex / Cursor):" -ForegroundColor Cyan
    Write-Host "   Simply send a natural prompt such as:"
    Write-Host "     `"Initialize blublu on this codebase`"" -ForegroundColor Yellow
    Write-Host "     `"Check architecture drift with blublu`"" -ForegroundColor Yellow
    Write-Host ""
}

# Execute installer with passed arguments (safe for Invoke-Expression / iex)
Install-Blublu @args
