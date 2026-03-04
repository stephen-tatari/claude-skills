---
name: pr-status
description: "Analyze PR merge readiness and diagnose blockers — CI failures, review status, missing checks, bot error comments, merge conflicts, draft state. Use when user asks about PR status, why a PR can't merge, CI failures, merge blockers, check status, review status, GitHub Actions failures, missing checks, bot comments, or pastes a github.com/*/pull/* URL."
model: claude-haiku-4-5-20251001
allowed-tools:
  - Bash(gh:*)
  - Bash(git:*)
  - Read
  - Grep
---

# PR Status Analyzer

This skill diagnoses why a PR can't merge and reports actionable blockers.

## When to Use This Skill

- User pastes a GitHub PR URL (`github.com/owner/repo/pull/123`)
- User asks "why can't this merge", "check my PR", "PR status", "merge blockers"
- User asks about CI failures, workflow logs, Actions status
- User asks about review status, pending checks, missing checks
- User asks about bot comments or error messages on a PR

## Prerequisites

Verify `gh` CLI is available and authenticated:

```bash
scripts/pr_status.py check-cli
```

### Authentication and Account Switching

The `check-cli` command validates authentication and repo access. In interactive terminals, it detects access issues and prompts for account switching. In non-interactive environments, it displays an error with manual instructions.

Common authentication issues:

- **Wrong account**: Authenticated with personal account but repo is in organization
- **Multiple accounts**: Need to switch using `gh auth switch`
- **Missing permissions**: Need `gh auth refresh -s repo` for branch protection access

## Primary Workflow: Diagnose PR

The `diagnose` command is the main entry point. It runs all checks and produces a structured blocker report:

```bash
scripts/pr_status.py diagnose 123
scripts/pr_status.py diagnose https://github.com/org/repo/pull/456
scripts/pr_status.py diagnose  # detect from current branch
```

### What Diagnose Covers

1. **Draft status** — whether PR is marked as draft
2. **Merge state** — CLEAN/DIRTY/BEHIND/BLOCKED/UNSTABLE/UNKNOWN with actionable message
3. **Review decision** — APPROVED/CHANGES_REQUESTED/REVIEW_REQUIRED with reviewer names
4. **Unresolved review threads** — count of unresolved conversations
5. **Stale approvals** — approvals older than the latest push
6. **CI checks** — pass/fail/pending counts, failing check names
7. **Missing required checks** — required by branch protection but not present
8. **Bot comments** — count and summary of bot comments mentioning errors
9. **Actionable next steps** for each blocker found

### Exit Codes

- `0` — PR is ready to merge (no blockers)
- `1` — blockers found
- `2` — auth or runtime error

## Drilling Into Specific Areas

After running `diagnose`, use these commands for deeper investigation:

### CI Failures

```bash
# Get run IDs from failed checks
scripts/pr_status.py failed-runs 123

# Analyze logs for a specific run (pass PR URL for cross-repo context)
scripts/pr_status.py analyze-logs 789012 https://github.com/org/repo/pull/123
# or: scripts/pr_status.py analyze-logs --repo org/repo 789012
```

### Review and Comment Context

```bash
# All comments and reviews
scripts/pr_status.py comments 123

# Bot comments only (renovate[bot], dependabot[bot], etc.)
scripts/pr_status.py bot-comments 123
```

### Check Details

```bash
# Full check results with required vs optional
scripts/pr_status.py checks 123

# Branch protection required checks
scripts/pr_status.py required-checks 123

# Compare required vs actual — find what's missing
scripts/pr_status.py missing-checks 123
```

### PR Metadata

```bash
scripts/pr_status.py status 123
```

## Cross-Repo Support

Pass `--repo owner/repo` for PRs in different repos, or use a full URL:

```bash
scripts/pr_status.py diagnose --repo org/other-repo 42
scripts/pr_status.py diagnose https://github.com/org/other-repo/pull/42
```

## Output Formats

Use `--format json` for machine-readable output (default is `text`):

```bash
scripts/pr_status.py diagnose 123 --format json
```

## Utility Commands

```bash
# Verify gh auth and repo access
scripts/pr_status.py check-cli

# Detect GitHub repo from git remote
scripts/pr_status.py detect-repo
```

## Standalone Workflow Functions

For CI troubleshooting outside of PR context:

```bash
# Analyze a specific GitHub Actions run
scripts/pr_status.py analyze-logs <run-id>

# For runs in a different repo than CWD, pass repo context
scripts/pr_status.py analyze-logs <run-id> https://github.com/org/repo/pull/123
scripts/pr_status.py analyze-logs --repo org/repo <run-id>
```

This downloads failed logs, truncates to 500 lines per failed step, and pattern-matches common errors (permission denied, test failures, timeouts, OOM, network errors, syntax errors).

## Error Handling

### Rate Limiting

```bash
gh api rate_limit
```

### Private Repositories

```bash
gh auth refresh -s read:org,repo
```

### Branch Protection API Errors

- **404**: No branch protection configured (reported as info, not error)
- **403**: Insufficient token scope — fix with `gh auth refresh -s repo`
