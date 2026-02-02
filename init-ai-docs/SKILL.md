---
name: init-ai-docs
description: Bootstrap ai_docs/ directory structure for decision records. Creates plans/, research/, handoffs/, and templates/ directories with index.md. Idempotent - safe to run multiple times. Use before creating plans, research, or handoffs.
allowed-tools:
  - Write
  - Read
  - Bash(mkdir:*)
  - Bash(ls:*)
  - Bash(git:*)
---

# Initialize AI Docs Directory

Bootstrap the `ai_docs/` directory structure for decision records following the [Decision Records with AI Assistance](https://github.com/stephen-tatari/coding-agent-documentation) convention.

## When to Use

- Starting a new project that will use decision records
- Before creating your first plan, research note, or handoff
- When `/create-plan`, `/create-research`, or `/create-handoff` is invoked (they call this automatically)

## Process

### Step 1: Detect Repository Root

Handle both main repos and worktrees:

```bash
# Detect if in a worktree (worktrees have .git as a file, main repo has .git as directory)
if [[ -f .git ]]; then
  # In a worktree - find main repo
  REPO_ROOT=$(git rev-parse --git-common-dir | sed 's|/.git$||')
  echo "Detected worktree. Creating ai_docs in main repository at: $REPO_ROOT"
else
  # In main repo
  REPO_ROOT=$(git rev-parse --show-toplevel)
fi
AI_DOCS="$REPO_ROOT/ai_docs"
```

### Step 2: Create Directory Structure

Create directories idempotently:

```bash
mkdir -p "$AI_DOCS/plans"
mkdir -p "$AI_DOCS/research"
mkdir -p "$AI_DOCS/handoffs"
mkdir -p "$AI_DOCS/templates"
```

### Step 3: Create index.md (if missing)

Only create if it doesn't exist. Ask the user for the project name first.

**Template for index.md:**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: index
status: active
topic: "[Project Name] Decision Records Index"
author: ai-assisted
ai_assisted: true
---

# Project: [Project Name]

## Overview

[2-3 sentence project description. What problem does it solve? Who uses it?]

## Key Terminology

| Term | Definition |
|------|------------|
| [Domain term] | [Clear definition] |

## Architecture

[Brief description of system structure]

## Active Decisions

<!-- Add links to active research/ADRs here -->
<!-- Example: @ai_docs/research/YYYY-MM-DD-decision-name.md - One-line summary -->

## Current Plans

<!-- Add links to active plans here -->
<!-- Example: @ai_docs/plans/YYYY-MM-DD-feature-name.md - Status: planning|in-progress|blocked -->

## Conventions

- [Key coding convention or pattern]
- [Testing approach]

## Out of Scope

- [What this project explicitly doesn't handle]
```

### Step 4: Create Template Files (if missing)

Only create templates that don't already exist.

**templates/plan.md:**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: plan
status: draft
topic: "[Feature Name] Implementation Plan"

# Accountability
author: [your-name or ai-assisted]
reviewed_by:                    # Required before merging
ai_assisted: true

# Linking
related_pr:
related_issue:

# Classification
tags: []
data_sensitivity: internal
---

# Plan: [Feature Name]

## Overview

[1-2 paragraph summary of what this plan achieves]

## Assumptions

- [Assumption 1]
- [Assumption 2]

## Constraints

- [Constraint 1]
- [Constraint 2]

## Alternatives Considered

### Option A: [Name]

**Pros:** [benefits]
**Cons:** [drawbacks]

### Option B: [Name]

**Pros:** [benefits]
**Cons:** [drawbacks]

**Decision:** [Which option and why]

## Implementation Phases

### Phase 1: [Name]

**Goal:** [What this phase achieves]

**Tasks:**

- [ ] Task 1
- [ ] Task 2

**Success Criteria:**

- [Automated] `command to verify`
- [Manual] Description of manual check

### Phase 2: [Name]

...

## Verification

**Automated checks:**

```bash
# Commands to verify implementation
```

**Manual verification:**

- [ ] Check 1
- [ ] Check 2
```

**templates/research.md:**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: research
status: draft
topic: "[Topic] Research"

# Accountability
author: [your-name or ai-assisted]
reviewed_by:                    # Required before merging
ai_assisted: true

# Linking
related_pr:
related_issue:

# Classification
tags: []
data_sensitivity: internal
---

# Research: [Topic]

## Context

[What prompted this research? What question are we trying to answer?]

## Findings

### [Finding 1]

[Details with links to sources]

### [Finding 2]

[Details with links to sources]

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| [Option A] | [benefits] | [drawbacks] |
| [Option B] | [benefits] | [drawbacks] |

## Decision

[If this is an ADR: What was decided and why?]
[If exploratory: What are the key takeaways?]

## Consequences

[What are the implications of this decision/finding?]

## Open Questions

- [Question 1]
- [Question 2]

## Sources

- [Link to source 1]
- [Link to source 2]
```

**templates/handoff.md:**

```markdown
---
schema_version: 1
date: [ISO datetime with timezone]
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
tags: []
---

# Handoff: [Brief Description]

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

### Step 5: Suggest AGENTS.md Integration

After creating the structure, suggest adding this to the project's AGENTS.md:

```markdown
## Decision Records

Before implementing significant changes, check `ai_docs/` for existing context:

- **Plans** (`ai_docs/plans/`): Active implementation plans. Check before starting work on a feature area.
- **Research** (`ai_docs/research/`): Technical investigations and ADRs. Check before making architectural decisions.
- **Handoffs** (`ai_docs/handoffs/`): Session continuity notes. Check when resuming paused work.

Start at `ai_docs/index.md` for project overview and active documents.
```

## Idempotency

This skill is safe to run multiple times:

- Uses `mkdir -p` which succeeds if directory exists
- Only creates files if they don't exist (check with Read first)
- Never overwrites existing content

## Response

After completion, inform the user:

```
ai_docs/ structure initialized at: $AI_DOCS

Created:
- ai_docs/index.md (edit to add project details)
- ai_docs/plans/
- ai_docs/research/
- ai_docs/handoffs/
- ai_docs/templates/{plan,research,handoff}.md

Consider adding the Decision Records snippet to your AGENTS.md.
```
