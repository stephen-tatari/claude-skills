---
name: jira
description: Manage Jira tickets via CLI - search issues, view details, create tickets, update status, and add comments. Use when user mentions ticket IDs (PROJ-123), asks about their tasks, work history, accomplishments, or wants to interact with Jira.
model: claude-haiku-4-5-20251001
allowed-tools:
  - Bash(acli:*)
  - Bash(./scripts/*)
  - Bash(rg:*)
---

# Jira Skill

Interact with Jira using Atlassian CLI (ACLI) for context-efficient ticket management.

## When to Use

Use this skill when:

- User mentions a ticket ID (e.g., PROJ-123, ABC-456)
- User asks about their assigned tickets or tasks
- User wants to create, update, or comment on Jira issues
- User asks about sprint or project status
- User asks about their work history or accomplishments
- User wants to review completed work
- Keywords: jira, ticket, issue, sprint, backlog, assigned to me

## Pre-flight Check

**Before running any acli command**, validate configuration:

```bash
./scripts/setup.sh --validate-only
```

- **Exit 0**: Configuration valid, proceed with acli commands
- **Exit non-zero**: Authentication required. Follow this flow:
  1. Show the user the output (which includes `acli jira auth login --web`)
  2. Use `AskUserQuestion` to ask: "Have you run the authentication command? Let me know when you're ready to continue."
  3. When user confirms, re-run `./scripts/setup.sh --validate-only`
  4. If validation passes, continue with the original Jira task
  5. If validation still fails, inform the user and offer to retry

The `--validate-only` flag prevents interactive prompts that would hang in automation.

## Read-Only Commands (Safe)

These commands only read data and are safe to run without confirmation.

Use `--fields` flag for searches to minimize token usage:

### Search Issues

```bash
# My assigned issues
acli jira workitem search --jql "assignee = currentUser()" --fields key,summary,status --limit 20

# Issues in a project
acli jira workitem search --jql "project = PROJ" --fields key,summary,status,assignee --limit 20

# Custom JQL query
acli jira workitem search --jql "project = PROJ AND status = 'In Progress'" --fields key,summary,status

# Issues updated recently
acli jira workitem search --jql "updated >= -7d" --fields key,summary,status --limit 20

# Issues with date range (JQL dates use yyyy-mm-dd format)
acli jira workitem search --jql "project = PROJ AND created >= 2025-07-01" --fields key,summary,status,assignee --limit 50

# Get all results with pagination
acli jira workitem search --jql "project = PROJ" --fields key,summary,status --paginate

# Filter by resolution/dates in JQL (filtering works, display limited to defaults)
acli jira workitem search --jql "project = PROJ AND resolution = Done AND created >= 2025-07-01" --fields key,summary,status

# Get full details including dates for specific issues
acli jira workitem view PROJ-123 --fields created,updated,resolution,resolutiondate --json
```

**Important:** The `--fields` flag for searches only supports default fields: `issuetype`, `key`, `assignee`, `priority`, `status`, `summary`. To filter by other fields (resolution, created, updated), use JQL. To display additional fields, use `workitem view`.

### View Issue Details

```bash
# View single issue (default fields)
acli jira workitem view PROJ-123

# View with all fields
acli jira workitem view PROJ-123 --fields "*all"

# View specific fields only
acli jira workitem view PROJ-123 --fields key,summary,status,description,comment

# JSON output for parsing
acli jira workitem view PROJ-123 --json
```

**Special field values for view:**
- `"*all"` - returns all fields (created, updated, resolution, custom fields, etc.)
- `"*navigable"` - returns navigable fields
- Prefix with `-` to exclude fields (e.g., `"*all,-comment"`)

### Sprint Information

```bash
# List sprints for a board (requires board ID)
acli jira board list-sprints --id <board-id>

# Active sprints only
acli jira board list-sprints --id <board-id> --state active

# Find boards
acli jira board search

# Issues in current sprint
acli jira workitem search --jql "sprint in openSprints() AND project = PROJ" --fields key,summary,status,assignee
```

### Project Information

```bash
# List available projects
acli jira project list

# Recent projects
acli jira project list --recent

# JSON output
acli jira project list --json
```

## Mutating Commands (Require Confirmation)

**IMPORTANT**: Before executing any mutating command, use `AskUserQuestion` to confirm the action with the user. Mutating commands modify Jira data and cannot be easily undone.

**Text Format**: ACLI expects plain text for descriptions and comments. Do not use markdown formatting (e.g., `**bold**`, `[links](url)`, `- lists`) as it will render literally in Jira.

### Create Issues

**Always confirm before creating:**

```bash
# Create task
acli jira workitem create --project PROJ --type Task --summary "Summary text"

# Create with description (use plain text, not markdown)
acli jira workitem create --project PROJ --type Task --summary "Summary" --description "Description body"

# Create bug assigned to self
acli jira workitem create --project PROJ --type Bug --summary "Bug summary" --assignee "@me"

# Create with labels
acli jira workitem create --project PROJ --type Task --summary "Summary" --label "bug,urgent"
```

### Update Issues

**Always confirm before updating:**

```bash
# Transition status
acli jira workitem transition --key "PROJ-123" --status "In Progress"
acli jira workitem transition --key "PROJ-123" --status "Done"

# Assign issue
acli jira workitem assign --key "PROJ-123" --assignee "user@company.com"

# Assign to current user
acli jira workitem assign --key "PROJ-123" --assignee "@me"

# Add comment (use plain text, not markdown)
acli jira workitem comment create --key "PROJ-123" --body "Comment text here"

# Edit summary
acli jira workitem edit --key "PROJ-123" --summary "New summary"

# Bulk transition via JQL
acli jira workitem transition --jql "project = PROJ AND status = 'To Do'" --status "In Progress" --yes
```

### Confirmation Pattern

Before any mutating action, prompt the user:

```text
About to [action] on [ticket]:
- [details of change]

Proceed? (This will modify Jira data)
```

## Natural Language Mapping

| User Says | Command | Requires Confirmation |
|-----------|---------|----------------------|
| "What are my tickets?" | `acli jira workitem search --jql "assignee = currentUser()" --fields key,summary,status --limit 20` | No |
| "Show me PROJ-123" | `acli jira workitem view PROJ-123` | No |
| "Create a task for X" | `acli jira workitem create --project PROJ --type Task --summary "X"` | **Yes** |
| "Move PROJ-123 to in progress" | `acli jira workitem transition --key "PROJ-123" --status "In Progress"` | **Yes** |
| "What's in the current sprint?" | `acli jira workitem search --jql "sprint in openSprints() AND project = PROJ" --fields key,summary,status` | No |
| "Add a comment to PROJ-123" | `acli jira workitem comment create --key "PROJ-123" --body "comment"` | **Yes** |
| "Assign PROJ-123 to me" | `acli jira workitem assign --key "PROJ-123" --assignee "@me"` | **Yes** |
| "What have I worked on since July?" | `acli jira workitem search --jql "assignee was currentUser() AND created >= 2025-07-01" --fields key,summary,status --limit 50` | No |

## Tips

- **Use `--fields` to limit output**: `--fields key,summary,status` returns only needed fields
- **Use `--json` for structured output**: Machine-readable, easy to parse
- **Use `@me` for self-assignment**: No need for subshell commands
- **JQL for complex queries**: `--jql` supports full Jira Query Language
- **Pagination**: Use `--limit N` to cap results, `--paginate` for all results
- **Bulk operations**: Most commands support `--jql` or `--filter` for batch actions
- **Getting dates/resolution**: Search can filter by any JQL field but only displays defaults. Use `view --fields "*all"` for created, updated, resolution, etc.
- **Plain text only**: ACLI sends text as-is. Markdown syntax will appear literally in Jira, not rendered.

## Configuration

Atlassian CLI uses OAuth for secure authentication.

```bash
# Authenticate via browser (recommended)
acli jira auth login --web

# Check authentication status
acli jira auth status

# Switch between accounts
acli jira auth switch

# Log out
acli jira auth logout
```

## Troubleshooting

### Authentication errors

Re-authenticate with OAuth:

```bash
acli jira auth logout
acli jira auth login --web
```

### Check auth status

```bash
acli jira auth status
```

### Unknown project

List available projects:

```bash
acli jira project list
```

### Invalid transition

Check available transitions by viewing the issue:

```bash
acli jira workitem view PROJ-123 --fields status
```

### Find board ID for sprints

```bash
acli jira board search
```

### Field not allowed in search

Search only displays default fields (`issuetype`, `key`, `assignee`, `priority`, `status`, `summary`). For additional field data:

1. Use JQL to filter: `--jql "resolution = Done AND created >= 2025-01-01"`
2. Get details via view: `acli jira workitem view PROJ-123 --fields "*all" --json`

### API Token Authentication (headless/CI only)

Only use if OAuth is not possible (e.g., CI pipelines, headless servers):

```bash
# Get token from: https://id.atlassian.com/manage-profile/security/api-tokens
echo "$JIRA_TOKEN" | acli jira auth login \
  --site "company.atlassian.net" \
  --email "user@company.com" \
  --token
```
