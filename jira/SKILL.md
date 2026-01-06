---
name: jira
description: Manage Jira tickets via CLI - search issues, view details, create tickets, update status, and add comments. Use when user mentions ticket IDs (PROJ-123), asks about their tasks, or wants to interact with Jira.
---

# Jira Skill

Interact with Jira using the lightweight jira-cli tool for context-efficient ticket management.

## When to Use

Use this skill when:

- User mentions a ticket ID (e.g., PROJ-123, ABC-456)
- User asks about their assigned tickets or tasks
- User wants to create, update, or comment on Jira issues
- User asks about sprint or project status
- Keywords: jira, ticket, issue, sprint, backlog, assigned to me

## Pre-flight Check

**Before running any jira command**, ensure jira-cli is configured:

```bash
./jira/scripts/setup.sh
```

If the script exits non-zero, show the error to the user and stop. If it exits 0, proceed with jira commands.

## Context-Efficient Commands

Always use `--plain` and `--columns` flags for searches to minimize token usage:

### Search Issues

```bash
# My assigned issues
jira issue list -a$(jira me) --plain --columns key,summary,status --limit 20

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

### Create Issues

```bash
# Create task
jira issue create -pPROJ -tTask -s"Summary text" -yHigh

# Create with description
jira issue create -pPROJ -tTask -s"Summary" -b"Description body"

# Create bug
jira issue create -pPROJ -tBug -s"Bug summary" -yHighest
```

### Update Issues

```bash
# Transition status
jira issue move PROJ-123 "In Progress"
jira issue move PROJ-123 "Done"

# Assign issue
jira issue assign PROJ-123 username

# Add comment
jira issue comment add PROJ-123 "Comment text here"

# Edit summary
jira issue edit PROJ-123 -s"New summary"
```

### Sprint Information

```bash
# List sprints
jira sprint list -pPROJ --plain

# Issues in active sprint
jira sprint list -pPROJ --current --plain
```

## Natural Language Mapping

| User Says | Command |
|-----------|---------|
| "What are my tickets?" | `jira issue list -a$(jira me) --plain --columns key,summary,status --limit 20` |
| "Show me PROJ-123" | `jira issue view PROJ-123 --plain` |
| "Create a task for X" | `jira issue create -pPROJ -tTask -s"X"` |
| "Move PROJ-123 to in progress" | `jira issue move PROJ-123 "In Progress"` |
| "What's in the current sprint?" | `jira sprint list -pPROJ --current --plain` |
| "Add a comment to PROJ-123" | `jira issue comment add PROJ-123 "comment"` |
| "Assign PROJ-123 to me" | `jira issue assign PROJ-123 $(jira me)` |

## Tips

- **Always use `--plain`**: Reduces output tokens by 95%+
- **Limit results**: Use `--limit 20` for searches
- **Specify columns**: `--columns key,summary,status` returns only needed fields
- **JQL for complex queries**: `--jql` supports full Jira Query Language

## Troubleshooting

### Authentication errors

Re-run setup to reconfigure:

```bash
rm -f ~/.config/.jira/.config.yml
./jira/scripts/setup.sh
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
