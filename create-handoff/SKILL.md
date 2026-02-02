---
name: create-handoff
description: Create session handoff documents in ai_docs/handoffs/ for continuity between coding sessions. Captures current state, recent changes, learnings, and next steps. Use at stopping points or when handing off work.
allowed-tools:
  - Write
  - Read
  - Bash(mkdir:*)
  - Bash(git:*)
  - Skill
---

# Create Handoff Document

> Adapted from [humanlayer handoff pattern](https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/create_handoff.md)

Create a structured handoff document for session continuity. The goal is to compact and summarize context without losing key details.

## When to Use

- At natural stopping points in work
- Before context limits are reached
- When handing off to a different session or environment
- End of day or extended break

## Process

### Step 1: Initialize Directory Structure

First, invoke the `init-ai-docs` skill to ensure the directory structure exists:

```
/init-ai-docs
```

### Step 2: Detect Repository and Output Path

**IMPORTANT: Handoffs must be created in the main repository, never in worktrees.**

```bash
# Detect if in a worktree (worktrees have .git as a file, main repo has .git as directory)
if [[ -f .git ]]; then
  # In a worktree - find main repo
  MAIN_REPO=$(git rev-parse --git-common-dir | sed 's|/.git$||')
  HANDOFF_DIR="$MAIN_REPO/ai_docs/handoffs"
  echo "Detected worktree. Creating handoff in main repository at: $HANDOFF_DIR"
else
  # In main repo
  HANDOFF_DIR="ai_docs/handoffs"
fi
```

### Step 3: Generate Filename

```bash
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
# description should be brief kebab-case
FILENAME="$HANDOFF_DIR/${TIMESTAMP}_<description>.md"
```

Example: `ai_docs/handoffs/2026-02-02_14-30-45_oauth2-phase2.md`

### Step 4: Gather Git Metadata

```bash
BRANCH=$(git branch --show-current)
COMMIT=$(git rev-parse --short HEAD)
REPO=$(basename $(git rev-parse --show-toplevel))
```

### Step 5: Write the Handoff Document

```markdown
---
schema_version: 1
date: [ISO datetime with timezone, e.g., 2026-02-02T14:30:45-08:00]
type: handoff
status: active
topic: "[Feature/Task Name] Implementation"

# Accountability
author: ai-assisted
ai_assisted: true

# Git context
git_commit: [short hash]
branch: [branch name]
repository: [repo name]

# Classification
tags: [implementation, relevant-components]
---

# Handoff: [Very Concise Description]

## Task(s)

[Task descriptions with status: completed, in progress, planned.
If working from a plan, call out current phase.
Reference plan/research docs with @ai_docs/ prefix.]

## Critical References

[2-3 most important file paths - specs, designs, decisions.
Leave blank if none.]

## Recent Changes

[Recent codebase changes in file:line syntax]

## Learnings

[Important discoveries - patterns, bug root causes, key info.
Include explicit file paths.]

## Artifacts

[Exhaustive list of files produced/updated as paths or file:line refs]

## Action Items & Next Steps

[Prioritized list for next session to accomplish]

## Other Notes

[Additional context - relevant codebase sections, docs, etc.]
```

### Step 6: Create Directory and Save

```bash
mkdir -p "$HANDOFF_DIR"
# Write document to $HANDOFF_DIR/${TIMESTAMP}_description.md
```

## Response

After completion, inform the user:

```
Handoff created! Resume in a new session with:
/resume-handoff ai_docs/handoffs/<filename>.md
```

## Key Principles

- **More information, not less** - The template is a minimum; add more as needed
- **Be thorough and precise** - Include both top-level objectives and lower-level details
- **Avoid excessive code snippets** - Prefer `/path/to/file.ext:line` references
- **Handoffs go in main repo** - Never create in worktrees (they'll be lost on cleanup)

## Alternatives

For short breaks (same day), consider named sessions instead:

- Run `/rename <descriptive-name>` before ending
- Resume with `claude --resume <name>`

Use full handoff documents for:

- Multi-day breaks
- Handing to different environments
- Complex multi-phase work requiring artifact references

## Migrating from Personal Skills

If you have existing handoffs in `thoughts/shared/handoffs/`:

1. **Option A: Keep both** - `resume-handoff` searches both paths
2. **Option B: Migrate** - `mv thoughts/shared/handoffs/* ai_docs/handoffs/`
3. **Option C: Archive** - Keep old path read-only, use ai_docs/ for new

## Cross-Referencing

Reference other ai_docs using `@ai_docs/` prefix:

```markdown
Working on Phase 2 of @ai_docs/plans/2026-01-15-oauth2-impl.md
Based on decisions in @ai_docs/research/2026-01-10-auth-options.md
```
