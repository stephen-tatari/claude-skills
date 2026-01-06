#!/usr/bin/env bash
# Jira CLI setup helper - idempotent, safe to run multiple times
# Supports both interactive and headless (env var) configuration

set -euo pipefail

CONFIG_FILE="$HOME/.config/.jira/.config.yml"
API_TOKEN_URL="https://id.atlassian.com/manage-profile/security/api-tokens"

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
    echo "Install with:"
    echo "  brew install ankitpokhrel/jira-cli/jira-cli"
    echo ""
    echo "Or:"
    echo "  go install github.com/ankitpokhrel/jira-cli/cmd/jira@latest"
    exit 1
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
if [[ -f "$CONFIG_FILE" ]]; then
    echo "jira-cli config found at $CONFIG_FILE"
    if validate_config; then
        exit 0
    fi
    if [[ "$VALIDATE_ONLY" == "true" ]]; then
        echo "Config exists but validation failed. Run setup.sh without --validate-only to reconfigure."
        exit 1
    fi
    echo "Re-running setup..."
fi

# In validate-only mode, exit if no valid config
if [[ "$VALIDATE_ONLY" == "true" ]]; then
    echo "No valid configuration found. Run setup.sh without --validate-only to configure."
    exit 1
fi

# Check for headless configuration via environment variables
if [[ -n "${JIRA_API_TOKEN:-}" && -n "${JIRA_BASE_URL:-}" && -n "${JIRA_AUTH_TYPE:-}" ]]; then
    echo "Configuring jira-cli from environment variables..."
    mkdir -p "$(dirname "$CONFIG_FILE")"

    # Create config file from env vars
    cat > "$CONFIG_FILE" <<EOF
server: ${JIRA_BASE_URL}
login: ${JIRA_LOGIN:-}
project: ${JIRA_PROJECT:-}
board: ${JIRA_BOARD:-}
installation: cloud
authentication:
  type: ${JIRA_AUTH_TYPE}
  login: ${JIRA_LOGIN:-}
  token: ${JIRA_API_TOKEN}
EOF

    echo "Config written. Validating..."
    if validate_config; then
        exit 0
    else
        echo "Error: Environment-based configuration failed validation."
        exit 1
    fi
fi

# Interactive setup
echo "Setting up jira-cli..."
echo ""
echo "You'll need an Atlassian API token."

# Try to open browser, but don't fail if it doesn't work
browser_opened=false
if command -v open &>/dev/null; then
    if open "$API_TOKEN_URL" 2>/dev/null; then
        browser_opened=true
    fi
elif command -v xdg-open &>/dev/null; then
    if xdg-open "$API_TOKEN_URL" 2>/dev/null; then
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

sleep 2
echo ""
echo "Create a new API token, then run 'jira init' and enter:"
echo "  - Your Jira server URL (e.g., https://yourcompany.atlassian.net)"
echo "  - Your email address"
echo "  - The API token you just created"
echo ""

# Run jira init (interactive)
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
