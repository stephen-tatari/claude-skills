#!/usr/bin/env bash
# Atlassian CLI (ACLI) setup helper - idempotent, safe to run multiple times
# Uses OAuth for authentication (browser-based)

set -euo pipefail

# Parse arguments
VALIDATE_ONLY=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --validate-only)
            VALIDATE_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: setup.sh [--validate-only]"
            exit 1
            ;;
    esac
done

# Check if acli is installed
if ! command -v acli &>/dev/null; then
    echo "Error: Atlassian CLI (acli) is not installed."
    echo ""

    # Check if we can auto-install
    if [[ "$VALIDATE_ONLY" != "true" ]] && [[ -t 0 ]] && command -v brew &>/dev/null; then
        echo "Would you like to install it now via Homebrew? [y/N]"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "Installing Atlassian CLI..."
            brew tap atlassian/homebrew-acli
            brew install acli
            echo "Installation complete."
        else
            echo "Skipping installation."
            exit 1
        fi
    else
        echo "Install with Homebrew:"
        echo "  brew tap atlassian/homebrew-acli"
        echo "  brew install acli"
        echo ""
        echo "Or download manually from:"
        echo "  https://developer.atlassian.com/cloud/acli/guides/install-macos/"
        exit 1
    fi
fi

# Validate existing configuration
validate_config() {
    local output
    local exit_code
    output=$(acli jira auth status 2>&1) && exit_code=0 || exit_code=$?
    if [[ $exit_code -eq 0 ]] && [[ ! "$output" =~ "not logged in" ]]; then
        echo "Configuration validated successfully."
        return 0
    else
        echo "Validation failed: $output"
        return 1
    fi
}

# Check if already configured and valid
if validate_config 2>/dev/null; then
    exit 0
fi

# In validate-only mode, exit if no valid config
if [[ "$VALIDATE_ONLY" == "true" ]]; then
    echo "No valid configuration found. Run setup.sh without --validate-only to configure."
    exit 1
fi

# Non-interactive context - exit with instructions
if [[ ! -t 0 ]]; then
    echo "=============================================="
    echo "ACTION REQUIRED (run in your terminal)"
    echo "=============================================="
    echo "Authenticate with Jira using OAuth:"
    echo "  acli jira auth login --web"
    echo ""
    echo "This will open your browser for secure authentication."
    echo "Then re-run this script to validate."
    exit 2
fi

# Interactive setup with OAuth
echo "Setting up Atlassian CLI for Jira..."
echo ""
echo "This will open your browser for OAuth authentication."
echo "Press Enter to continue..."
read -r

acli jira auth login --web

# Validate setup
echo ""
echo "Validating setup..."
if validate_config; then
    echo "Setup complete! Atlassian CLI is ready to use."
    exit 0
else
    echo "Error: Setup validation failed. Please try again."
    exit 1
fi
