<#
.SYNOPSIS
    blublu v1.0 — Cross-Platform Installer for Windows (PowerShell 5.1+ & Core)
    Installs persistent architectural memory skill and hooks for AI coding agents.

.DESCRIPTION
    Installs blublu into current project repository or global agent configurations.
    Supports Google Antigravity, Anthropic Claude Code, and OpenAI Codex.

.PARAMETER Scope
    Installation scope: 'project' (default) or 'global'.

.PARAMETER Agent
    Target agent environment: 'all' (default), 'codex', 'claude', or 'antigravity'.

.PARAMETER TargetDir
    Explicit custom target directory for skill files.

.PARAMETER DryRun
    Simulate installation actions without modifying the filesystem.

.PARAMETER Upgrade
    Safely overwrite existing skill files with the latest version.

.PARAMETER Help
    Show this help message.

.EXAMPLE
    .\scripts\install.ps1 -Scope project
    .\scripts\install.ps1 -Scope global -Agent antigravity
    .\scripts\install.ps1 -DryRun
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("project", "global", IgnoreCase = $true)]
    [string]$Scope = "project",

    [Parameter(Position = 1)]
    [ValidateSet("all", "codex", "claude", "antigravity", IgnoreCase = $true)]
    [string]$Agent = "all",

    [string]$TargetDir = "",
    [switch]$DryRun,
    [switch]$Upgrade,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# ------------------------------------------------------------------------------
# Help Screen
# ------------------------------------------------------------------------------
if ($Help) {
    Write-Host @"
blublu v1.0 Installer — AI Codebase Memory & Architecture Tracking System

USAGE:
    .\scripts\install.ps1 [OPTIONS]
    & { iwr -useb https://raw.githubusercontent.com/blublu/blublu/main/scripts/install.ps1 } [OPTIONS]

OPTIONS:
    -Scope <project|global>                 Installation scope (default: project)
                                              project: Current repository
                                              global:  User home configuration
    -Agent <all|codex|claude|antigravity>   Target agent environment (default: all)
    -TargetDir <path>                       Explicit custom target directory
    -DryRun                                 Preview changes without modifying disk
    -Upgrade                                Safely overwrite existing skill files
    -Help                                   Display this help screen

EXAMPLES:
    .\scripts\install.ps1 -Scope project
    .\scripts\install.ps1 -Scope global -Agent antigravity
    .\scripts\install.ps1 -Upgrade -Agent claude
    .\scripts\install.ps1 -DryRun
"@
    exit 0
}

# Normalize case
$Scope = $Scope.ToLowerInvariant()
$Agent = $Agent.ToLowerInvariant()

# ------------------------------------------------------------------------------
# Logging Functions
# ------------------------------------------------------------------------------
function Write-LogInfo ($message) {
    Write-Host " [INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $message
}

function Write-LogSuccess ($message) {
    Write-Host " [OK]   " -ForegroundColor Green -NoNewline
    Write-Host $message
}

function Write-LogWarning ($message) {
    Write-Host " [WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $message
}

function Write-LogError ($message) {
    Write-Host " [ERR]  " -ForegroundColor Red -NoNewline
    Write-Host $message
}

function Write-LogDryRun ($message) {
    Write-Host " [DRY]  " -ForegroundColor Cyan -NoNewline
    Write-Host $message
}

# ------------------------------------------------------------------------------
# Paths and File Declarations
# ------------------------------------------------------------------------------
$RepoRawBase = "https://raw.githubusercontent.com/blublu/blublu/main"
$SkillRelDir = "skills/blublu"
$SkillFiles = @(
    "SKILL.md",
    "references/blueprint-template.md",
    "references/mapping-rules.md",
    "references/update-rules.md",
    "references/validation-rules.md"
)

# ------------------------------------------------------------------------------
# Locate Source: Local Repo clone vs Remote Web Fetch
# ------------------------------------------------------------------------------
$LocalSourceDir = $null
if ($PSScriptRoot) {
    $parentCandidate = (Resolve-Path "$PSScriptRoot\.." -ErrorAction SilentlyContinue)
    if ($parentCandidate -and (Test-Path "$parentCandidate\$SkillRelDir\SKILL.md")) {
        $LocalSourceDir = $parentCandidate.Path
    }
}

if (-not $LocalSourceDir -and (Test-Path ".\$SkillRelDir\SKILL.md")) {
    $LocalSourceDir = (Get-Item ".").FullName
}

function Copy-Or-FetchSkillFile ($relPath, $destinationPath) {
    $destFolder = [System.IO.Path]::GetDirectoryName($destinationPath)

    if ($DryRun) {
        Write-LogDryRun "Write $destinationPath"
        return
    }

    if (-not (Test-Path $destFolder)) {
        New-Item -ItemType Directory -Path $destFolder -Force | Out-Null
    }

    if ($LocalSourceDir) {
        $localFile = (Resolve-Path (Join-Path $LocalSourceDir "$SkillRelDir/$relPath") -ErrorAction SilentlyContinue)
        $localPath = if ($localFile) { $localFile.Path } else { Join-Path $LocalSourceDir "$SkillRelDir/$relPath" }
        $destFull = [System.IO.Path]::GetFullPath($destinationPath)
        if ($localPath.TrimEnd('\') -eq $destFull.TrimEnd('\')) {
            Write-LogInfo "Source and destination are identical: $relPath"
            return
        }
        Copy-Item -Path $localPath -Destination $destinationPath -Force
    } else {
        $url = "$RepoRawBase/$SkillRelDir/$relPath"
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $url -OutFile $destinationPath -UseBasicParsing
        } catch {
            Write-LogError "Failed to download $url : $_"
            throw
        }
    }
}

# ------------------------------------------------------------------------------
# Determine Target Installation Directories
# ------------------------------------------------------------------------------
$UserHome = $env:USERPROFILE
$InstallDirs = @()

if ($TargetDir) {
    $InstallDirs += $TargetDir
} elseif ($Scope -eq "project") {
    $InstallDirs += ".\skills\blublu"
    if ($Agent -eq "claude") {
        $InstallDirs = @(".\.claude\skills\blublu")
    }
} else {
    # Global Scope
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

# ------------------------------------------------------------------------------
# Bootstrap Logic (Non-destructive instruction injection)
# ------------------------------------------------------------------------------
$MarkerStart = "<!-- blublu:start -->"
$MarkerEnd   = "<!-- blublu:end -->"

$BootstrapBlock = @"
$MarkerStart
## Codebase Architecture & Memory (blublu)
This project uses **blublu** to maintain persistent architectural memory in ``.agents/codebase-map.md``.
- Before modifying or analyzing code, read ``.agents/codebase-map.md`` to orient with current architecture, module boundaries, and conventions.
- Respect registered layer boundaries, export contracts, and dependency flows.
- When architectural changes occur (new modules, deleted components, schema shifts, or routing alterations), update the blueprint.
- For complete operational protocols and commands (initialize, update, rebuild, validate, impact, status), consult ``skills/blublu/SKILL.md``.
$MarkerEnd
"@

function Apply-BootstrapInstructions ($filePath) {
    if ($DryRun) {
        Write-LogDryRun "Bootstrap instructions in $filePath"
        return
    }

    if (-not (Test-Path $filePath)) {
        Set-Content -Path $filePath -Value $BootstrapBlock -Encoding UTF8
        Write-LogSuccess "Created and bootstrapped $filePath"
        return
    }

    $existingContent = Get-Content -Path $filePath -Raw -Encoding UTF8

    if ($existingContent -match [regex]::Escape($MarkerStart)) {
        if ($Upgrade) {
            $pattern = "(?s)" + [regex]::Escape($MarkerStart) + ".*?" + [regex]::Escape($MarkerEnd)
            $newContent = [regex]::Replace($existingContent, $pattern, $BootstrapBlock)
            Set-Content -Path $filePath -Value $newContent -Encoding UTF8
            Write-LogSuccess "Updated existing blublu bootstrap block in $filePath"
        } else {
            Write-LogInfo "Bootstrap block already present in $filePath (use -Upgrade to refresh)"
        }
    } else {
        $appended = $existingContent.TrimEnd() + "`r`n`r`n" + $BootstrapBlock + "`r`n"
        Set-Content -Path $filePath -Value $appended -Encoding UTF8
        Write-LogSuccess "Appended blublu bootstrap block to $filePath"
    }
}

# ------------------------------------------------------------------------------
# Main Execution
# ------------------------------------------------------------------------------
Write-Host ""
Write-Host "=== blublu v1.0 PowerShell Installer ===" -ForegroundColor Cyan
Write-LogInfo "Scope:   $Scope"
Write-LogInfo "Agent:   $Agent"
Write-LogInfo "Upgrade: $Upgrade"
Write-LogInfo "DryRun:  $DryRun"
if ($LocalSourceDir) {
    Write-LogInfo "Source:  Local repository ($LocalSourceDir)"
} else {
    Write-LogInfo "Source:  Remote repository ($RepoRawBase)"
}
Write-Host ""

# Copy skills
foreach ($targetDir in $InstallDirs) {
    if ((Test-Path $targetDir) -and -not $Upgrade) {
        Write-LogWarning "Skill directory already exists: $targetDir"
        Write-LogInfo "Skipping. Pass -Upgrade to overwrite skill files."
        continue
    }

    Write-LogInfo "Installing blublu skill to: $targetDir"

    foreach ($file in $SkillFiles) {
        $dest = Join-Path $targetDir $file
        Copy-Or-FetchSkillFile $file $dest
    }

    if (-not $DryRun) {
        Write-LogSuccess "Installed skill files to $targetDir"
    }
}

# Apply bootstrap in project scope
if ($Scope -eq "project") {
    if ($Agent -eq "all" -or $Agent -eq "codex") {
        Apply-BootstrapInstructions "AGENTS.md"
    }
    if ($Agent -eq "all" -or $Agent -eq "claude") {
        Apply-BootstrapInstructions "CLAUDE.md"
    }
}

Write-Host ""
Write-Host " [SUCCESS] blublu v1.0 installation completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "1. Open your AI coding agent (Antigravity, Claude Code, or Codex)."
Write-Host "2. To initialize your project architecture blueprint, send:"
Write-Host "   `"Initialize blublu on this codebase`"" -ForegroundColor Cyan
Write-Host "3. The agent will read skills/blublu/SKILL.md and generate .agents/codebase-map.md."
Write-Host ""
