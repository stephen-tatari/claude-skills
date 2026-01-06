#!/usr/bin/env bash
# Jira CLI setup helper - idempotent, safe to run multiple times

set -euo pipefail

CONFIG_FILE="$HOME/.config/.jira/.config.yml"
API_TOKEN_URL="https://id.atlassian.com/manage-profile/security/api-tokens"

# Check if jira-cli is installed
if ! command -v jira &>/dev/null; then
    echo "Error: jira-cli is not installed."
    echo ""
    echo "Install with:"
    echo "  brew install ankitpokhrel/jira-cli/jira-cli"
    echo ""
    echo "Or:"
    echo "  go install github.com/ankitpokhrel/jira-cli/cmd/jira@latest"
    exit 1
fi

# Check if already configured
if [[ -f "$CONFIG_FILE" ]]; then
    echo "jira-cli is already configured."
    # Validate the config works
    if jira me &>/dev/null; then
        echo "Configuration validated successfully."
        exit 0
    else
        echo "Warning: Config exists but validation failed. Re-running setup..."
    fi
fi

echo "Setting up jira-cli..."
echo ""
echo "You'll need an Atlassian API token. Opening the token management page..."
sleep 2

# Open API token page in browser
if command -v open &>/dev/null; then
    open "$API_TOKEN_URL"
elif command -v xdg-open &>/dev/null; then
    xdg-open "$API_TOKEN_URL"
else
    echo "Please open this URL manually: $API_TOKEN_URL"
fi

echo ""
echo "Create a new API token, then run 'jira init' and enter:"
echo "  - Your Jira server URL (e.g., https://yourcompany.atlassian.net)"
echo "  - Your email address"
echo "  - The API token you just created"
echo ""

# Run jira init
jira init

# Validate setup
echo ""
echo "Validating setup..."
if jira me &>/dev/null; then
    echo "Setup complete! jira-cli is ready to use."
    exit 0
else
    echo "Error: Setup validation failed. Please try again."
    exit 1
fi
