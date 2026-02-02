---
name: resume-handoff
description: Resume work from previous handoff documents in new sessions. Three-phase process - analyze handoff, present findings, then implement. Use when starting a session that continues previous work.
allowed-tools:
  - Read
  - Bash(git:*)
  - Bash(ls:*)
  - Grep
  - Glob
  - TodoWrite
---

# Resume Work from Handoff Document

> Adapted from [humanlayer handoff pattern](https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/resume_handoff.md)

Resume work based on a handoff document containing prior context and learnings.

## Input

The handoff file path is provided as: `$ARGUMENTS`

**IMPORTANT: Handoffs are always stored in the main repository, never in worktrees.**

### Path Detection

If you're in a worktree, adjust the path to search in the main repository:

```bash
# Detect if in a worktree
if [[ -f .git ]]; then
  # In a worktree - search main repo
  MAIN_REPO=$(git rev-parse --git-common-dir | sed 's|/.git$||')
  # Check ai_docs first (preferred), fall back to thoughts/shared (legacy)
  if [[ -d "$MAIN_REPO/ai_docs/handoffs" ]]; then
    HANDOFF_DIR="$MAIN_REPO/ai_docs/handoffs"
  elif [[ -d "$MAIN_REPO/thoughts/shared/handoffs" ]]; then
    HANDOFF_DIR="$MAIN_REPO/thoughts/shared/handoffs"
    echo "Note: Using legacy path. Run /init-ai-docs to migrate to ai_docs/"
  fi
else
  # In main repo
  if [[ -d "ai_docs/handoffs" ]]; then
    HANDOFF_DIR="ai_docs/handoffs"
  elif [[ -d "thoughts/shared/handoffs" ]]; then
    HANDOFF_DIR="thoughts/shared/handoffs"
    echo "Note: Using legacy path. Run /init-ai-docs to migrate to ai_docs/"
  fi
fi
```

If no path is provided, prompt the user:

- Ask for the path to the handoff file
- List available handoffs in `$HANDOFF_DIR` using `ls -t` (most recent first)

## Three-Phase Process

### Phase 1: Analysis

1. **Read the complete handoff document** - Do NOT delegate to sub-agent
2. **Read all referenced artifacts** - Any documents, plans, or specs mentioned
3. **Extract key information:**
   - Task statuses (completed, in progress, planned)
   - Learnings and insights
   - Recent changes made
   - Next steps identified
4. **Verify current state** - Check that codebase matches documentation:

   ```bash
   git status          # Current branch and changes
   git log -1          # Verify commit matches
   ```

   - Spot-check that documented changes exist

### Phase 2: Presentation

Present a synthesized analysis to the user:

```markdown
## Handoff Analysis

### Original Tasks

[List tasks from handoff with their documented statuses]

### Validated Learnings

[Key learnings verified against current codebase state]

### Verified Changes

[Recent changes confirmed to exist in the codebase]

### Artifact Review

[Summary of referenced documents/plans that were read]

### Recommended Actions

[Prioritized list of next steps based on handoff guidance]

### Potential Issues

[Any discrepancies between handoff state and current state, or blockers identified]
```

**Wait for user confirmation before proceeding to Phase 3.**

### Phase 3: Implementation

After user confirmation:

1. **Create a prioritized todo list** using TodoWrite based on Action Items & Next Steps
2. **Begin work** on the highest priority items
3. **Continuously reference** the handoff document for:
   - Documented patterns and approaches
   - Known pitfalls to avoid
   - Architectural decisions to follow

## Key Principles

- **Always verify** - Don't assume handoff state matches current reality
- **Present before acting** - Get user buy-in before starting work
- **Apply learnings** - The handoff contains valuable context; use it
- **Read directly** - Do NOT delegate critical file reading to sub-agents
- **Maintain continuity** - Use todo list to track progress against handoff goals

## Common Scenarios

### Clean Continuation

Handoff state matches current state exactly. Proceed with documented next steps.

### Diverged Codebase

Changes have been made since handoff. Note differences, ask user how to reconcile.

### Incomplete Work

Previous work was interrupted. Identify where to resume based on task statuses.

### Stale Handoff

Handoff is outdated (significant time passed, major changes). Recommend fresh assessment rather than following old guidance.

## Schema Compatibility

This skill handles both schema versions:

**New schema (ai_docs/):**

```yaml
schema_version: 1
type: handoff
# ... full schema fields
```

**Legacy schema (thoughts/shared/):**

```yaml
type: handoff
date: ...
topic: ...
# ... minimal fields
```

Both have `type: handoff` so detection works. The skill should not fail on missing fields - gracefully handle whatever is present.

## Migrating from Personal Skills

If you have existing handoffs in `thoughts/shared/handoffs/`:

1. **Option A: Keep both** - This skill searches both paths automatically
2. **Option B: Migrate** - `mv thoughts/shared/handoffs/* ai_docs/handoffs/`
3. **Option C: Archive** - Keep old path read-only, use ai_docs/ for new
