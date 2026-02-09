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

```text
/init-ai-docs
```

### Step 2: Detect Repository and Output Path

```bash
# Always use current repo location (works in both worktree and main repo)
HANDOFF_DIR="ai_docs/handoffs"
```

**Note:** Handoffs are gitignored by default. They are ephemeral session context, not permanent documentation.

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
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true
ai_model:                                # optional: which model

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

After completion, inform the user (where `<full-path>` is the absolute path to the current working directory):

```text
Handoff created at: <full-path>/ai_docs/handoffs/<filename>.md

Handoffs are gitignored by default. To preserve beyond this session:
git add -f ai_docs/handoffs/<filename>.md && git commit -m "docs: add handoff for <description>"

Resume in a new session with:
/resume-handoff <full-path>/ai_docs/handoffs/<filename>.md
```

## Key Principles

- **More information, not less** - The template is a minimum; add more as needed
- **Be thorough and precise** - Include both top-level objectives and lower-level details
- **Avoid excessive code snippets** - Prefer `/path/to/file.ext:line` references
- **Handoffs are gitignored by default** - Commit when context is worth preserving

## Alternatives

For short breaks (same day), consider named sessions instead:

- Run `/rename <descriptive-name>` before ending
- Resume with `claude --resume <name>`

Use full handoff documents for:

- Multi-day breaks
- Handing to different environments
- Complex multi-phase work requiring artifact references

## Cross-Referencing

Reference other decision records depending on mode:

**Local mode** — use `@ai_docs/` prefix:

```markdown
Working on Phase 2 of @ai_docs/plans/2026-01-15-oauth2-impl.md
Based on decisions in @ai_docs/research/2026-01-10-auth-options.md
```

**Central mode** — use relative sibling paths:

```markdown
Working on Phase 2 of ../<ai-docs-repo>/plans/2026-01-15-oauth2-impl.md
Based on decisions in ../<ai-docs-repo>/research/2026-01-10-auth-options.md
```
