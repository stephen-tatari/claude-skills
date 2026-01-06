---
name: jira
description: Manage Jira tickets via CLI - search issues, view details, create tickets, update status, and add comments. Use when user mentions ticket IDs (PROJ-123), asks about their tasks, work history, accomplishments, or wants to interact with Jira.
---

# Jira Skill

Interact with Jira using the lightweight jira-cli tool for context-efficient ticket management.

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

**Before running any jira command**, validate configuration:

```bash
./scripts/setup.sh --validate-only
```

- Exit 0: Configuration valid, proceed with jira commands
- Exit non-zero: Show error to user. If interactive session available, run `./scripts/setup.sh` (without flag) to configure

The `--validate-only` flag prevents interactive prompts that would hang in automation.

## Read-Only Commands (Safe)

These commands only read data and are safe to run without confirmation.

Always use `--plain` and `--columns` flags for searches to minimize token usage:

### Search Issues

```bash
# My assigned issues
jira issue list -a"$(jira me)" --plain --columns key,summary,status --limit 20

# Issues in a project
jira issue list -pPROJ --plain --columns key,summary,status,assignee --limit 20

# Custom JQL query
jira issue list --jql "project = PROJ AND status = 'In Progress'" --plain --columns key,summary,status

# Issues updated recently
jira issue list --jql "updated >= -7d ORDER BY updated DESC" --plain --columns key,summary,status --limit 20
```

### View Issue Details

```bash
# View single issue (full details)
jira issue view PROJ-123 --plain

# View with comments
jira issue view PROJ-123 --plain --comments 5
```

### Sprint Information

```bash
# List sprints in a project
jira sprint list -pPROJ --plain

# View active sprint details
jira sprint list -pPROJ --state active --plain

# Issues in current sprint (requires board ID)
jira issue list --jql "sprint in openSprints() AND project = PROJ" --plain --columns key,summary,status,assignee
```

### Project Information

```bash
# List available projects
jira project list --plain
```

## Mutating Commands (Require Confirmation)

**IMPORTANT**: Before executing any mutating command, use `AskUserQuestion` to confirm the action with the user. Mutating commands modify Jira data and cannot be easily undone.

### Create Issues

**Always confirm before creating:**

```bash
# Create task
jira issue create -pPROJ -tTask -s"Summary text" -yHigh

# Create with description
jira issue create -pPROJ -tTask -s"Summary" -b"Description body"

# Create bug
jira issue create -pPROJ -tBug -s"Bug summary" -yHighest
```

### Update Issues

**Always confirm before updating:**

```bash
# Transition status
jira issue move PROJ-123 "In Progress"
jira issue move PROJ-123 "Done"

# Assign issue
jira issue assign PROJ-123 username

# Assign to current user
jira issue assign PROJ-123 "$(jira me)"

# Add comment
jira issue comment add PROJ-123 "Comment text here"

# Edit summary
jira issue edit PROJ-123 -s"New summary"
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
| "What are my tickets?" | `jira issue list -a"$(jira me)" --plain --columns key,summary,status --limit 20` | No |
| "Show me PROJ-123" | `jira issue view PROJ-123 --plain` | No |
| "Create a task for X" | `jira issue create -pPROJ -tTask -s"X"` | **Yes** |
| "Move PROJ-123 to in progress" | `jira issue move PROJ-123 "In Progress"` | **Yes** |
| "What's in the current sprint?" | `jira issue list --jql "sprint in openSprints() AND project = PROJ" --plain --columns key,summary,status` | No |
| "Add a comment to PROJ-123" | `jira issue comment add PROJ-123 "comment"` | **Yes** |
| "Assign PROJ-123 to me" | `jira issue assign PROJ-123 "$(jira me)"` | **Yes** |

## Tips

- **Always use `--plain`**: Reduces output tokens by 95%+
- **Limit results**: Use `--limit 20` for searches
- **Specify columns**: `--columns key,summary,status` returns only needed fields
- **JQL for complex queries**: `--jql` supports full Jira Query Language
- **Quote substitutions**: Always use `"$(jira me)"` with quotes to handle special characters

## Headless/CI Configuration

For non-interactive environments, set these environment variables before running setup:

```bash
export JIRA_BASE_URL="https://yourcompany.atlassian.net"
export JIRA_LOGIN="your.email@company.com"
export JIRA_API_TOKEN="your-api-token"
export JIRA_AUTH_TYPE="bearer"  # or "basic"
export JIRA_PROJECT="PROJ"      # optional: default project
./scripts/setup.sh
```

## Troubleshooting

### Authentication errors

Move old config and re-run setup:

```bash
mkdir -p TRASH && mv ~/.config/jira/config.yaml TRASH/jira-config-backup.yaml
./scripts/setup.sh
```

### Unknown project

List available projects:

```bash
jira project list --plain
```

### Invalid transition

List available transitions for an issue:

```bash
jira issue view PROJ-123 --plain | grep -A10 "Transitions"
```

### Validation fails but config exists

Check the specific error:

```bash
jira me
```

Common causes:

- API token expired (regenerate at Atlassian)
- Network connectivity issues
- Server URL changed
