#!/usr/bin/env bash
# Claude Skills Library - One-Line Installer
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/SaucySlang/claude-skills/main/install.sh | bash
#   curl -sSL https://raw.githubusercontent.com/SaucySlang/claude-skills/main/install.sh | bash -s -- --agent cursor
#   curl -sSL https://raw.githubusercontent.com/SaucySlang/claude-skills/main/install.sh | bash -s -- --help
#
# Options:
#   --agent <name>    Target agent: claude (default), cursor, vscode, gemini, codex, openclaw
#   --target <dir>    Override install destination directory
#   --dry-run         Show what would be installed without making changes
#   --help            Show this help message
#
# Examples:
#   # Install to Claude Code (default)
#   curl -sSL .../install.sh | bash
#
#   # Install to Cursor
#   curl -sSL .../install.sh | bash -s -- --agent cursor
#
#   # Dry run to preview changes
#   curl -sSL .../install.sh | bash -s -- --dry-run

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────

REPO_URL="https://github.com/SaucySlang/claude-skills.git"
REPO_BRANCH="main"
TMPDIR_PREFIX="claude-skills-install"

# ── Colors ───────────────────────────────────────────────────────────────────

if [ -t 1 ]; then
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  RED='\033[0;31m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN='' YELLOW='' BLUE='' RED='' BOLD='' NC=''
fi

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()      { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()     { echo -e "${RED}[ERR]${NC}   $*" >&2; }
header()  { echo -e "\n${BOLD}$*${NC}"; }

# ── Help ─────────────────────────────────────────────────────────────────────

usage() {
  cat <<'EOF'

Claude Skills Library — One-Line Installer
==========================================

Usage:
  curl -sSL https://raw.githubusercontent.com/SaucySlang/claude-skills/main/install.sh | bash
  curl -sSL .../install.sh | bash -s -- [OPTIONS]

Options:
  --agent <name>    Target agent (default: claude)
                    Supported: claude, cursor, vscode, gemini, codex, openclaw
  --target <dir>    Override install destination directory
  --dry-run         Preview what would be installed without making changes
  --help            Show this help message

Agent Install Locations:
  claude    ~/.claude/skills/
  cursor    .cursor/skills/          (current directory)
  vscode    .github/skills/          (current directory)
  gemini    ~/.gemini/skills/
  codex     ~/.codex/skills/
  openclaw  ~/.openclaw/skills/

Examples:
  # Install all skills to Claude Code
  curl -sSL .../install.sh | bash

  # Install to Cursor in current project
  curl -sSL .../install.sh | bash -s -- --agent cursor

  # Preview what would be installed
  curl -sSL .../install.sh | bash -s -- --dry-run

  # Install to a custom directory
  curl -sSL .../install.sh | bash -s -- --target /opt/my-skills

EOF
}

# ── Argument Parsing ─────────────────────────────────────────────────────────

AGENT="claude"
TARGET=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      err "Unknown option: $1"
      usage
      exit 1
      ;;
  esac
done

# ── Resolve Install Destination ───────────────────────────────────────────────

resolve_dest() {
  if [[ -n "$TARGET" ]]; then
    echo "$TARGET"
    return
  fi
  case "$AGENT" in
    claude)   echo "${HOME}/.claude/skills" ;;
    cursor)   echo "${PWD}/.cursor/skills" ;;
    vscode)   echo "${PWD}/.github/skills" ;;
    gemini)   echo "${HOME}/.gemini/skills" ;;
    codex)    echo "${HOME}/.codex/skills" ;;
    openclaw) echo "${HOME}/.openclaw/skills" ;;
    *)
      err "Unknown agent: ${AGENT}"
      err "Supported agents: claude, cursor, vscode, gemini, codex, openclaw"
      exit 1
      ;;
  esac
}

DEST="$(resolve_dest)"

# ── Prerequisite Checks ───────────────────────────────────────────────────────

check_prereqs() {
  local missing=()

  if ! command -v git &>/dev/null; then
    missing+=("git")
  fi

  if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing required tools: ${missing[*]}"
    err "Install them and retry."
    exit 1
  fi
}

# ── Skill Domain Folders ──────────────────────────────────────────────────────

SKILL_DOMAINS=(
  "engineering-team"
  "engineering"
  "marketing-skill"
  "c-level-advisor"
  "product-team"
  "project-management"
  "ra-qm-team"
  "business-growth"
  "finance"
  "agents"
  "commands"
)

# ── Clone Repository to Temp Dir ──────────────────────────────────────────────

clone_repo() {
  local tmpdir
  tmpdir="$(mktemp -d -t "${TMPDIR_PREFIX}.XXXXXX")"
  info "Cloning Claude Skills Library..."
  git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$tmpdir" --quiet
  echo "$tmpdir"
}

# ── Install Skills ────────────────────────────────────────────────────────────

install_skills() {
  local src_root="$1"
  local total_installed=0
  local total_skipped=0

  header "Installing to: ${DEST}"

  if $DRY_RUN; then
    warn "DRY RUN — no files will be written"
  fi

  if ! $DRY_RUN; then
    mkdir -p "$DEST"
  fi

  for domain in "${SKILL_DOMAINS[@]}"; do
    local domain_src="${src_root}/${domain}"

    if [[ ! -d "$domain_src" ]]; then
      warn "Domain not found, skipping: ${domain}"
      continue
    fi

    # Iterate skill subdirectories within each domain
    for skill_dir in "$domain_src"/*/; do
      [[ -d "$skill_dir" ]] || continue

      local skill_name
      skill_name="$(basename "$skill_dir")"
      local skill_dest="${DEST}/${skill_name}"

      # Only install directories that contain SKILL.md, a README, or known metadata
      if [[ ! -f "${skill_dir}/SKILL.md" ]] && \
         [[ ! -f "${skill_dir}/README.md" ]] && \
         [[ ! -f "${skill_dir}/agent.md" ]]; then
        continue
      fi

      if $DRY_RUN; then
        info "[DRY RUN] Would install: ${domain}/${skill_name} -> ${skill_dest}"
        ((total_installed++)) || true
        continue
      fi

      if [[ -e "$skill_dest" ]]; then
        rm -rf "$skill_dest"
        ((total_skipped++)) || true
      fi

      cp -r "$skill_dir" "$skill_dest"
      ((total_installed++)) || true
    done
  done

  echo ""
  if $DRY_RUN; then
    ok "DRY RUN complete — ${total_installed} skills would be installed to ${DEST}"
  else
    ok "Installed ${total_installed} skills to ${DEST}"
    if [[ $total_skipped -gt 0 ]]; then
      info "Updated ${total_skipped} existing skills"
    fi
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────

main() {
  header "Claude Skills Library — Installer"
  info "Agent:   ${AGENT}"
  info "Target:  ${DEST}"
  if $DRY_RUN; then
    info "Mode:    dry run"
  fi

  check_prereqs

  local tmpdir
  tmpdir="$(clone_repo)"

  # Ensure cleanup on exit
  # shellcheck disable=SC2064
  trap "rm -rf '${tmpdir}'" EXIT

  install_skills "$tmpdir"

  echo ""
  ok "Done! Skills are ready in: ${DEST}"
  if [[ "$AGENT" == "claude" ]]; then
    info "Restart Claude Code to pick up new skills."
  fi
}

main "$@"
