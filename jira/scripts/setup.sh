#!/usr/bin/env bash
# Jira CLI setup helper - idempotent, safe to run multiple times
# Uses macOS Keychain for secure token storage

set -euo pipefail

API_TOKEN_URL="https://id.atlassian.com/manage-profile/security/api-tokens"
KEYCHAIN_SERVICE="jira-cli"

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

# Check if jira-cli is installed
if ! command -v jira &>/dev/null; then
    echo "Error: jira-cli is not installed."
    echo ""

    # Check if we can auto-install
    if [[ "$VALIDATE_ONLY" != "true" ]] && [[ -t 0 ]] && command -v brew &>/dev/null; then
        echo "Would you like to install it now via Homebrew? [y/N]"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "Installing jira-cli..."
            brew install ankitpokhrel/jira-cli/jira-cli
            echo "Installation complete."
        else
            echo "Skipping installation."
            exit 1
        fi
    else
        echo "Install with:"
        echo "  brew install ankitpokhrel/jira-cli/jira-cli"
        echo ""
        echo "Or:"
        echo "  go install github.com/ankitpokhrel/jira-cli/cmd/jira@latest"
        exit 1
    fi
fi

# Validate existing configuration
validate_config() {
    local output
    local exit_code
    output=$(jira me 2>&1) && exit_code=0 || exit_code=$?
    if [[ $exit_code -eq 0 ]]; then
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

# Check if token exists in keychain
check_keychain_token() {
    security find-generic-password -s "$KEYCHAIN_SERVICE" &>/dev/null
}

# Interactive setup
echo "Setting up jira-cli..."
echo ""
echo "You'll need an Atlassian API token stored in macOS Keychain."

# Try to open browser, but don't fail if it doesn't work
browser_opened=false
if command -v open &>/dev/null; then
    if open "$API_TOKEN_URL" 2>/dev/null; then
        browser_opened=true
    fi
fi

if [[ "$browser_opened" == "true" ]]; then
    echo "Opening token management page in your browser..."
else
    echo ""
    echo "Please open this URL to create an API token:"
    echo "  $API_TOKEN_URL"
fi

echo ""
echo "Setup Steps:"
echo "  1. Create API token (label: 'jira-cli')"
echo "  2. Store in keychain:"
echo "     security add-generic-password -a 'your.email@company.com' -s 'jira-cli' -w 'your-token'"
echo "  3. Run: jira init"
echo "     - Installation type: Cloud"
echo "     - Server URL: https://yourcompany.atlassian.net"
echo "     - Login email: your Atlassian account email"
echo ""

# Non-interactive context - exit with instructions
if [[ ! -t 0 ]]; then
    echo "=============================================="
    echo "ACTION REQUIRED (run in your terminal)"
    echo "=============================================="
    echo "1. security add-generic-password -a 'your.email' -s 'jira-cli' -w 'your-token'"
    echo "2. jira init"
    echo ""
    echo "Then re-run this script to validate."
    exit 2
fi

# Interactive - check for keychain token
if ! check_keychain_token; then
    echo "ERROR: No token found in keychain."
    echo ""
    echo "Add your token first:"
    echo "  security add-generic-password -a 'your.email@company.com' -s 'jira-cli' -w 'your-token'"
    exit 1
fi

echo "Token found in keychain. Running jira init..."
jira init

# Validate setup
echo ""
echo "Validating setup..."
if validate_config; then
    echo "Setup complete! jira-cli is ready to use."
    exit 0
else
    echo "Error: Setup validation failed. Please try again."
    exit 1
fi
