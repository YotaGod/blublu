#!/usr/bin/env bash
# ==============================================================================
# blublu v1.0 — Cross-Platform Installer (Linux & macOS)
# Maintains persistent architectural memory for AI coding agents
# ==============================================================================

set -euo pipefail

# ------------------------------------------------------------------------------
# Color and formatting definitions
# ------------------------------------------------------------------------------
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
    printf "${COLOR_BLUE}ℹ${COLOR_RESET} %s\n" "$1"
}

log_success() {
    printf "${COLOR_GREEN}✔${COLOR_RESET} %s\n" "$1"
}

log_warning() {
    printf "${COLOR_YELLOW}⚠${COLOR_RESET} %s\n" "$1"
}

log_error() {
    printf "${COLOR_RED}✖ Error:${COLOR_RESET} %s\n" "$1" >&2
}

log_dryrun() {
    printf "${COLOR_CYAN}[DRY-RUN]${COLOR_RESET} %s\n" "$1"
}

# ------------------------------------------------------------------------------
# Default settings
# ------------------------------------------------------------------------------
SCOPE="project"
AGENT="all"
CUSTOM_TARGET_DIR=""
DRY_RUN=false
UPGRADE=false
REPO_RAW_BASE="https://raw.githubusercontent.com/blublu/blublu/main"

# Skill source relative paths
SKILL_REL_DIR="skills/blublu"
SKILL_FILES=(
    "SKILL.md"
    "references/blueprint-template.md"
    "references/mapping-rules.md"
    "references/update-rules.md"
    "references/validation-rules.md"
)

# ------------------------------------------------------------------------------
# Help message
# ------------------------------------------------------------------------------
show_help() {
    cat << EOF
${COLOR_BOLD}blublu v1.0 Installer${COLOR_RESET} — AI Codebase Memory & Architecture Tracking System

${COLOR_BOLD}USAGE:${COLOR_RESET}
    ./install.sh [OPTIONS]
    curl -fsSL ${REPO_RAW_BASE}/scripts/install.sh | bash -s -- [OPTIONS]

${COLOR_BOLD}OPTIONS:${COLOR_RESET}
    --scope <project|global>    Installation scope (default: project)
                                  project: Installs in current working repository
                                  global:  Installs in user's home configuration
    --agent <all|codex|claude|antigravity>
                                Target agent environment (default: all)
    --target-dir <path>         Specify an explicit custom target directory
    --dry-run                   Preview actions without modifying the filesystem
    --upgrade                   Safely overwrite existing skill files with latest version
    -h, --help                  Show this help message and exit

${COLOR_BOLD}EXAMPLES:${COLOR_RESET}
    ./scripts/install.sh --scope project
    ./scripts/install.sh --scope global --agent antigravity
    ./scripts/install.sh --scope project --upgrade --agent claude
    curl -fsSL ${REPO_RAW_BASE}/scripts/install.sh | bash -s -- --dry-run
EOF
}

# ------------------------------------------------------------------------------
# Argument parsing
# ------------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --scope)
            if [[ -z "${2:-}" ]]; then log_error "--scope requires an argument"; exit 1; fi
            SCOPE="$(echo "$2" | tr '[:upper:]' '[:lower:]')"
            shift 2
            ;;
        --agent)
            if [[ -z "${2:-}" ]]; then log_error "--agent requires an argument"; exit 1; fi
            AGENT="$(echo "$2" | tr '[:upper:]' '[:lower:]')"
            shift 2
            ;;
        --target-dir)
            if [[ -z "${2:-}" ]]; then log_error "--target-dir requires a path argument"; exit 1; fi
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

# Validate scope
if [[ "$SCOPE" != "project" && "$SCOPE" != "global" ]]; then
    log_error "Invalid scope '$SCOPE'. Must be 'project' or 'global'."
    exit 1
fi

# Validate agent
if [[ "$AGENT" != "all" && "$AGENT" != "codex" && "$AGENT" != "claude" && "$AGENT" != "antigravity" ]]; then
    log_error "Invalid agent '$AGENT'. Must be 'all', 'codex', 'claude', or 'antigravity'."
    exit 1
fi

# ------------------------------------------------------------------------------
# Source locator: Detect local repo clone vs remote one-liner
# ------------------------------------------------------------------------------
SCRIPT_DIR=""
if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

LOCAL_SOURCE_DIR=""
if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../${SKILL_REL_DIR}/SKILL.md" ]; then
    LOCAL_SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -f "./${SKILL_REL_DIR}/SKILL.md" ]; then
    LOCAL_SOURCE_DIR="$(pwd)"
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

    if [ -n "$LOCAL_SOURCE_DIR" ]; then
        local src_file="${LOCAL_SOURCE_DIR}/${SKILL_REL_DIR}/${rel_file}"
        local src_real
        local dest_real
        src_real="$(cd "$(dirname "$src_file")" 2>/dev/null && pwd)/$(basename "$src_file")" || src_real="$src_file"
        dest_real="$(cd "$dest_dir" 2>/dev/null && pwd)/$(basename "$dest_file")" || dest_real="$dest_file"
        if [ "$src_real" = "$dest_real" ]; then
            log_info "Source and destination are identical: $rel_file"
            return 0
        fi
        cp "$src_file" "$dest_file"
    else
        local remote_url="${REPO_RAW_BASE}/${SKILL_REL_DIR}/${rel_file}"
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

# ------------------------------------------------------------------------------
# Determine installation directories
# ------------------------------------------------------------------------------
HOME_DIR="${HOME:-~}"
INSTALL_DIRS=()

if [ -n "$CUSTOM_TARGET_DIR" ]; then
    INSTALL_DIRS+=("$CUSTOM_TARGET_DIR")
elif [ "$SCOPE" = "project" ]; then
    # In project scope, standard Agent Skills are stored in ./skills/blublu
    INSTALL_DIRS+=("./skills/blublu")
    # If Claude specific directory is requested
    if [ "$AGENT" = "claude" ]; then
        INSTALL_DIRS=("./.claude/skills/blublu")
    fi
else
    # Global scope
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

# ------------------------------------------------------------------------------
# Safe Non-Destructive Bootstrap Block
# ------------------------------------------------------------------------------
BOOTSTRAP_MARKER_START="<!-- blublu:start -->"
BOOTSTRAP_MARKER_END="<!-- blublu:end -->"

BOOTSTRAP_CONTENT="${BOOTSTRAP_MARKER_START}
## Codebase Architecture & Memory (blublu)
This project uses **blublu** to maintain persistent architectural memory in \`.agents/codebase-map.md\`.
- Before modifying or analyzing code, read \`.agents/codebase-map.md\` to orient with current architecture, module boundaries, and conventions.
- Respect registered layer boundaries, export contracts, and dependency flows.
- When architectural changes occur (new modules, deleted components, schema shifts, or routing alterations), update the blueprint.
- For complete operational protocols and commands (initialize, update, rebuild, validate, impact, status), consult \`skills/blublu/SKILL.md\`.
${BOOTSTRAP_MARKER_END}"

apply_bootstrap_instructions() {
    local target_file="$1"

    if [ "$DRY_RUN" = true ]; then
        log_dryrun "Bootstrap instructions in $target_file"
        return 0
    fi

    if [ ! -f "$target_file" ]; then
        printf "%s\n" "$BOOTSTRAP_CONTENT" > "$target_file"
        log_success "Created and bootstrapped $target_file"
        return 0
    fi

    if grep -qF "$BOOTSTRAP_MARKER_START" "$target_file"; then
        if [ "$UPGRADE" = true ]; then
            # Replace existing marker block safely
            local tmp_file
            tmp_file="$(mktemp)"
            awk -v start="$BOOTSTRAP_MARKER_START" -v end="$BOOTSTRAP_MARKER_END" -v content="$BOOTSTRAP_CONTENT" '
                $0 ~ start { in_block=1; print content; next }
                $0 ~ end { in_block=0; next }
                !in_block { print $0 }
            ' "$target_file" > "$tmp_file"
            mv "$tmp_file" "$target_file"
            log_success "Updated existing blublu bootstrap block in $target_file"
        else
            log_info "Bootstrap block already present in $target_file (use --upgrade to refresh)"
        fi
    else
        # Append to existing file without altering user content
        printf "\n\n%s\n" "$BOOTSTRAP_CONTENT" >> "$target_file"
        log_success "Appended blublu bootstrap block to existing $target_file"
    fi
}

# ------------------------------------------------------------------------------
# Execution Banner
# ------------------------------------------------------------------------------
printf "\n${COLOR_BOLD}${COLOR_BLUE}=== blublu v1.0 Installer ===${COLOR_RESET}\n"
log_info "Scope:       ${COLOR_BOLD}$SCOPE${COLOR_RESET}"
log_info "Agent:       ${COLOR_BOLD}$AGENT${COLOR_RESET}"
log_info "Upgrade:     $UPGRADE"
log_info "Dry Run:     $DRY_RUN"
if [ -n "$LOCAL_SOURCE_DIR" ]; then
    log_info "Source:      Local repository (${LOCAL_SOURCE_DIR})"
else
    log_info "Source:      Remote repository (${REPO_RAW_BASE})"
fi
printf "\n"

# ------------------------------------------------------------------------------
# Install skills into target directories
# ------------------------------------------------------------------------------
for target_dir in "${INSTALL_DIRS[@]}"; do
    if [ -d "$target_dir" ] && [ "$UPGRADE" != true ]; then
        log_warning "Skill directory already exists: $target_dir"
        log_info "Skipping install to $target_dir. Pass --upgrade to overwrite files."
        continue
    fi

    log_info "Installing blublu skill to: ${COLOR_BOLD}$target_dir${COLOR_RESET}"

    for skill_file in "${SKILL_FILES[@]}"; do
        dest_path="${target_dir}/${skill_file}"
        fetch_or_copy_file "$skill_file" "$dest_path"
    done

    if [ "$DRY_RUN" != true ]; then
        log_success "Installed skill files to $target_dir"
    fi
done

# ------------------------------------------------------------------------------
# Bootstrap instruction files if in project scope
# ------------------------------------------------------------------------------
if [ "$SCOPE" = "project" ]; then
    if [ "$AGENT" = "all" ] || [ "$AGENT" = "codex" ]; then
        apply_bootstrap_instructions "AGENTS.md"
    fi

    if [ "$AGENT" = "all" ] || [ "$AGENT" = "claude" ]; then
        apply_bootstrap_instructions "CLAUDE.md"
    fi
fi

# ------------------------------------------------------------------------------
# Completion Summary
# ------------------------------------------------------------------------------
printf "\n${COLOR_GREEN}${COLOR_BOLD}✔ blublu v1.0 installation completed successfully!${COLOR_RESET}\n\n"
cat << EOF
${COLOR_BOLD}Next Steps:${COLOR_RESET}
1. Open your AI coding agent (Antigravity, Claude Code, or Codex).
2. To initialize your project architecture blueprint, send:
   ${COLOR_CYAN}"Initialize blublu on this codebase"${COLOR_RESET}
3. The agent will read ${COLOR_BOLD}skills/blublu/SKILL.md${COLOR_RESET} and create ${COLOR_BOLD}.agents/codebase-map.md${COLOR_RESET}.

EOF
