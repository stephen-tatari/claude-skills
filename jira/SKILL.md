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
jira issue list -a"$(jira me)" --plain --columns key,summary,status --paginate 20

# Issues in a project
jira issue list -pPROJ --plain --columns key,summary,status,assignee --paginate 20

# Custom JQL query
jira issue list --jql "project = PROJ AND status = 'In Progress'" --plain --columns key,summary,status

# Issues updated recently (use --order-by flag, NOT ORDER BY in JQL)
jira issue list --jql "updated >= -7d" --order-by updated --plain --columns key,summary,status --paginate 20

# Issues with date range (JQL dates use yyyy-mm-dd format)
jira issue list -pPROJ --jql "project = PROJ AND created >= 2025-07-01" --plain --columns key,summary,status,assignee --paginate 50
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
# List available projects (note: --plain not supported for project list)
jira project list

# Filter projects by name
jira project list | grep -i "search-term"
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
| "What are my tickets?" | `jira issue list -a"$(jira me)" --plain --columns key,summary,status --paginate 20` | No |
| "Show me PROJ-123" | `jira issue view PROJ-123 --plain` | No |
| "Create a task for X" | `jira issue create -pPROJ -tTask -s"X"` | **Yes** |
| "Move PROJ-123 to in progress" | `jira issue move PROJ-123 "In Progress"` | **Yes** |
| "What's in the current sprint?" | `jira issue list --jql "sprint in openSprints() AND project = PROJ" --plain --columns key,summary,status` | No |
| "Add a comment to PROJ-123" | `jira issue comment add PROJ-123 "comment"` | **Yes** |
| "Assign PROJ-123 to me" | `jira issue assign PROJ-123 "$(jira me)"` | **Yes** |
| "What have I worked on since July?" | `jira issue list -pPROJ --jql "project = PROJ AND assignee was currentUser() AND created >= 2025-07-01" --plain --columns key,summary,status --paginate 50` | No |

## Tips

- **Always use `--plain`**: Reduces output tokens by 95%+ (note: not supported for `project list`)
- **Limit results**: Use `--paginate 20` for searches (not `--limit`)
- **Specify columns**: `--columns key,summary,status` returns only needed fields
- **JQL for complex queries**: `--jql` supports Jira Query Language, but do NOT include `ORDER BY` in JQL string
- **Ordering results**: Use `--order-by fieldname` flag instead of `ORDER BY` in JQL
- **Quote substitutions**: Always use `"$(jira me)"` with quotes to handle special characters
- **Date formats in JQL**: Use `yyyy-mm-dd` format (e.g., `created >= 2025-07-01`)

## Configuration

jira-cli uses macOS Keychain for secure token storage.

```bash
# 1. Get an API token from https://id.atlassian.com/manage-profile/security/api-tokens

# 2. Store token in macOS Keychain
security add-generic-password -a "your.email@company.com" -s "jira-cli" -w "your-api-token"

# 3. Run jira init (token is read from keychain automatically)
jira init
# Select: Cloud, your server URL, your email
```

To update an existing token:

```bash
security delete-generic-password -s "jira-cli"
security add-generic-password -a "your.email@company.com" -s "jira-cli" -w "new-token"
```

## Troubleshooting

### Authentication errors

Reset keychain entry and config:

```bash
# Remove old keychain entry
security delete-generic-password -s "jira-cli" 2>/dev/null

# Add fresh token
security add-generic-password -a "your.email@company.com" -s "jira-cli" -w "your-new-token"

# Remove old config and reinitialize
mkdir -p TRASH && mv ~/.config/.jira/.config.yml TRASH/jira-config-backup.yml
jira init
```

### Unknown project

List available projects:

```bash
jira project list
```

### JQL ORDER BY error

If you get `Expecting ',' but got 'ORDER'` error, do NOT include `ORDER BY` in the JQL string. Use the `--order-by` flag instead:

```bash
# Wrong - causes error
jira issue list --jql "project = PROJ ORDER BY updated DESC"

# Correct - use --order-by flag
jira issue list --jql "project = PROJ" --order-by updated
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
