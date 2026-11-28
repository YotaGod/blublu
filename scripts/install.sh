#!/usr/bin/env bash
# ==============================================================================
# blublu v2.0 - Universal Cross-Platform Installer (Linux & macOS)
# Installs persistent architectural memory skill and CLI for AI coding agents.
# ==============================================================================

set -euo pipefail

if [ -t 1 ]; then
    COLOR_RESET="\033[0m"
    COLOR_BOLD="\033[1m"
    COLOR_GREEN="\033[32m"
    COLOR_BLUE="\033[34m"
    COLOR_YELLOW="\033[33m"
    COLOR_RED="\033[31m"
    COLOR_CYAN="\033[36m"
else
    COLOR_RESET=""
    COLOR_BOLD=""
    COLOR_GREEN=""
    COLOR_BLUE=""
    COLOR_YELLOW=""
    COLOR_RED=""
    COLOR_CYAN=""
fi

log_info() {
    printf "${COLOR_BLUE} [INFO] ${COLOR_RESET}%s\n" "$1"
}

log_success() {
    printf "${COLOR_GREEN} [OK]   ${COLOR_RESET}%s\n" "$1"
}

log_warning() {
    printf "${COLOR_YELLOW} [WARN] ${COLOR_RESET}%s\n" "$1"
}

log_error() {
    printf "${COLOR_RED} [ERR]  ${COLOR_RESET}%s\n" "$1" >&2
}

log_dryrun() {
    printf "${COLOR_CYAN} [DRY]  ${COLOR_RESET}%s\n" "$1"
}

SCOPE="all"
AGENT="all"
CUSTOM_TARGET_DIR=""
DRY_RUN=false
UPGRADE=false
REPO_RAW_BASE="https://raw.githubusercontent.com/YotaGod/blublu/main"

SKILL_REL_DIR="skills/blublu"
SKILL_FILES=(
    "SKILL.md"
    "references/blueprint-template.md"
    "references/mapping-rules.md"
    "references/update-rules.md"
    "references/validation-rules.md"
)

CLI_FILES=(
    "scripts/blublu"
    "scripts/blublu.cmd"
    "scripts/blublu.ps1"
    "scripts/blublu.py"
    "scripts/validate-blueprint.py"
    "scripts/scanner.py"
    "scripts/watcher.py"
    "scripts/graph_export.py"
)

show_help() {
    cat << EOF
${COLOR_BOLD}blublu v2.0 Installer${COLOR_RESET} - AI Codebase Memory System

${COLOR_BOLD}USAGE:${COLOR_RESET}
    curl -fsSL ${REPO_RAW_BASE}/install.sh | bash
    ./install.sh [OPTIONS]

${COLOR_BOLD}OPTIONS:${COLOR_RESET}
    --scope <all|global|project>  Installation scope (default: all)
    --agent <all|codex|claude|antigravity> Target agent (default: all)
    --target-dir <path>           Specify custom target directory
    --dry-run                     Preview actions without modifying disk
    --upgrade                     Safely overwrite existing files
    -h, --help                    Show this help message and exit
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        --scope)
            SCOPE="$2"
            shift 2
            ;;
        --agent)
            AGENT="$2"
            shift 2
            ;;
        --target-dir)
            CUSTOM_TARGET_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --upgrade)
            UPGRADE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

printf "\n${COLOR_CYAN}==========================================================${COLOR_RESET}\n"
printf "${COLOR_CYAN}          blublu v2.0 - AI Codebase Memory System         ${COLOR_RESET}\n"
printf "${COLOR_CYAN}==========================================================${COLOR_RESET}\n\n"

# Source detection
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

LOCAL_SOURCE_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/${SKILL_REL_DIR}/SKILL.md" ]; then
    LOCAL_SOURCE_DIR="$SCRIPT_DIR"
elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../${SKILL_REL_DIR}/SKILL.md" ]; then
    LOCAL_SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -f "./${SKILL_REL_DIR}/SKILL.md" ]; then
    LOCAL_SOURCE_DIR="$(pwd)"
fi

if [ -n "$LOCAL_SOURCE_DIR" ]; then
    log_info "Source: Local repository (${LOCAL_SOURCE_DIR})"
else
    log_info "Source: Remote repository (${REPO_RAW_BASE})"
fi

fetch_or_copy_file() {
    local rel_file="$1"
    local dest_file="$2"
    local dest_dir
    dest_dir="$(dirname "$dest_file")"

    if [ "$DRY_RUN" = true ]; then
        log_dryrun "Write $dest_file"
        return 0
    fi

    mkdir -p "$dest_dir"

    if [ -n "$LOCAL_SOURCE_DIR" ] && [ -f "${LOCAL_SOURCE_DIR}/${rel_file}" ]; then
        local src_file="${LOCAL_SOURCE_DIR}/${rel_file}"
        if [ "$src_file" != "$dest_file" ]; then
            cp "$src_file" "$dest_file"
        fi
    else
        local remote_url="${REPO_RAW_BASE}/${rel_file}"
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$remote_url" -o "$dest_file"
        elif command -v wget >/dev/null 2>&1; then
            wget -q "$remote_url" -O "$dest_file"
        else
            log_error "Neither curl nor wget is available to fetch remote files."
            exit 1
        fi
    fi
}

# 1. Install CLI
HOME_DIR="${HOME:-~}"
CLI_BIN_DIR="${HOME_DIR}/.blublu/bin"
log_info "Installing blublu CLI to: ${CLI_BIN_DIR}"
mkdir -p "$CLI_BIN_DIR"

for cli_file in "${CLI_FILES[@]}"; do
    base_name="$(basename "$cli_file")"
    dest_path="${CLI_BIN_DIR}/${base_name}"
    fetch_or_copy_file "$cli_file" "$dest_path"
    chmod +x "$dest_path" 2>/dev/null || true
done
log_success "CLI tools installed to ${CLI_BIN_DIR}"

# Add CLI_BIN_DIR to PATH in shell profile if missing
add_to_path() {
    local profile_file="$1"
    local export_line="export PATH=\"\$HOME/.blublu/bin:\$PATH\""
    if [ -f "$profile_file" ]; then
        if ! grep -qF ".blublu/bin" "$profile_file"; then
            printf "\n# blublu CLI\n%s\n" "$export_line" >> "$profile_file"
            log_success "Added blublu to PATH in $profile_file"
        fi
    fi
}
add_to_path "${HOME_DIR}/.bashrc"
add_to_path "${HOME_DIR}/.zshrc"

# 2. Install Skills
INSTALL_DIRS=()
if [ -n "$CUSTOM_TARGET_DIR" ]; then
    INSTALL_DIRS+=("$CUSTOM_TARGET_DIR")
else
    if [ "$SCOPE" = "all" ] || [ "$SCOPE" = "global" ]; then
        case "$AGENT" in
            all)
                INSTALL_DIRS+=(
                    "$HOME_DIR/.agents/skills/blublu"
                    "$HOME_DIR/.claude/skills/blublu"
                    "$HOME_DIR/.gemini/antigravity/skills/blublu"
                )
                ;;
            codex)
                INSTALL_DIRS+=("$HOME_DIR/.agents/skills/blublu")
                ;;
            claude)
                INSTALL_DIRS+=("$HOME_DIR/.claude/skills/blublu")
                ;;
            antigravity)
                INSTALL_DIRS+=("$HOME_DIR/.gemini/antigravity/skills/blublu")
                ;;
        esac
    fi
    if [ "$SCOPE" = "all" ] || [ "$SCOPE" = "project" ]; then
        if [ -d "./.git" ] || [ -f "./package.json" ] || [ -f "./pyproject.toml" ] || [ "$SCOPE" = "project" ]; then
            INSTALL_DIRS+=("./skills/blublu")
        fi
    fi
fi

for target_dir in "${INSTALL_DIRS[@]}"; do
    log_info "Installing blublu skill to: ${target_dir}"
    for skill_file in "${SKILL_FILES[@]}"; do
        rel_path="${SKILL_REL_DIR}/${skill_file}"
        dest_path="${target_dir}/${skill_file}"
        fetch_or_copy_file "$rel_path" "$dest_path"
    done
    log_success "Installed skill files to ${target_dir}"
done

# 3. Bootstrap instructions
BOOTSTRAP_MARKER_START="<!-- blublu:start -->"
BOOTSTRAP_MARKER_END="<!-- blublu:end -->"
BOOTSTRAP_CONTENT="${BOOTSTRAP_MARKER_START}
## Codebase Architecture & Memory (blublu v2.0.0)
This project uses **blublu** to maintain persistent architectural memory using a 4-level hierarchical blueprint system.

### Mandatory Loading Protocol
1. **ALWAYS read \`.agents/codebase-map.md\` first** (Level 1 - Global Architecture).
2. **Identify the domain** touched by the current task from the Sub-Blueprints Index.
3. **Load ONLY \`.agents/sub-blueprints/<domain>.md\`** (Level 2) for the relevant domain. Never load all domains.
4. **Load \`.agents/sub-blueprints/<domain>/<module>.md\`** (Level 3) ONLY if making interface/contract-level changes.
5. **Level 4 detail** is loaded ONLY on explicit user request for implementation details.

### Operational Rules
- Respect registered layer boundaries, export contracts, and dependency flows.
- Record cross-service dependencies with Confidence labels: Confirmed | Inferred | Unverified.
- Flag circular dependencies as [CIRCULAR DEPENDENCY - REVIEW REQUIRED].
- Never auto-apply destructive blueprint changes from drift detection reports.

### CLI Tools Available
- \`blublu status\` - Architecture health summary and mode detection.
- \`blublu validate --check-drift\` - Drift detection across all modules.
- \`blublu analyze <module>\` - Hierarchical context for a specific module.
- \`blublu dependencies [--module <name>]\` - Full dependency map.
- For complete protocols, consult \`skills/blublu/SKILL.md\`.
${BOOTSTRAP_MARKER_END}"

apply_bootstrap() {
    local target_file="$1"
    if [ ! -f "$target_file" ]; then
        printf "%s\n" "$BOOTSTRAP_CONTENT" > "$target_file"
        log_success "Created and bootstrapped $target_file"
        return 0
    fi
    if grep -qF "$BOOTSTRAP_MARKER_START" "$target_file"; then
        local tmp_file
        tmp_file="$(mktemp)"
        awk -v start="$BOOTSTRAP_MARKER_START" -v end="$BOOTSTRAP_MARKER_END" -v content="$BOOTSTRAP_CONTENT" '
            $0 ~ start { in_block=1; print content; next }
            $0 ~ end { in_block=0; next }
            !in_block { print $0 }
        ' "$target_file" > "$tmp_file"
        mv "$tmp_file" "$target_file"
        log_success "Updated blublu instructions in $target_file"
    else
        printf "\n\n%s\n" "$BOOTSTRAP_CONTENT" >> "$target_file"
        log_success "Added blublu instructions to $target_file"
    fi
}

if [ "$SCOPE" = "all" ] || [ "$SCOPE" = "project" ]; then
    if [ -d "./.git" ] || [ "$SCOPE" = "project" ]; then
        apply_bootstrap "AGENTS.md"
        apply_bootstrap "CLAUDE.md"
    fi
fi

# 4. Check Python
if command -v python3 >/dev/null 2>&1; then
    log_success "Python detected: $(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    log_success "Python detected: $(command -v python)"
else
    log_warning "Python 3 is not yet detected on PATH. Please install python3 to run the CLI."
fi

printf "\n${COLOR_GREEN}==========================================================${COLOR_RESET}\n"
printf "${COLOR_GREEN}     [SUCCESS] blublu installation completed!             ${COLOR_RESET}\n"
printf "${COLOR_GREEN}==========================================================${COLOR_RESET}\n\n"
printf "Next Steps:\n"
printf "  1. Restart your terminal (or run: export PATH=\"\$HOME/.blublu/bin:\$PATH\")\n"
printf "  2. Run: ${COLOR_CYAN}blublu status${COLOR_RESET}\n"
printf "  3. In your AI agent, prompt: ${COLOR_CYAN}\"Initialize blublu on this codebase\"${COLOR_RESET}\n\n"
