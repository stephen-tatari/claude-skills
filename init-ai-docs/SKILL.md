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

```bash
# Always use current repo root (works in both worktree and main repo)
REPO_ROOT=$(git rev-parse --show-toplevel)
AI_DOCS="$REPO_ROOT/ai_docs"
```

**Note:** In worktrees, ai_docs/ is created in the worktree directory. Documents committed there will merge to main with your branch.

### Step 2: Detect Mode and Create Directory Structure

Read the project's AGENTS.md (or CLAUDE.md) to determine the mode:

1. Read `$REPO_ROOT/AGENTS.md` (or `CLAUDE.md`)
2. Find the "Decision Records" section
3. If it references a central repo for plans/research → **central mode**
4. Otherwise → **local mode**

**Local mode** (plans/research stored in this repo):

```bash
mkdir -p "$AI_DOCS/plans"
mkdir -p "$AI_DOCS/research"
mkdir -p "$AI_DOCS/handoffs"
mkdir -p "$AI_DOCS/templates"
```

**Central mode** (plans/research in a separate repo):

```bash
# Only create handoffs locally — plans/research live in the central repo
mkdir -p "$AI_DOCS/handoffs"
```

After creating the local handoffs directory, verify the central repo:

1. Extract the central repo path from AGENTS.md (e.g., `../<ai-docs-repo>/`)
2. Check if the path exists
3. If it exists, check for expected structure: `plans/`, `research/`, `templates/`, `index.md`
4. If the path is missing or the structure is incomplete:
   - Warn user: "Central repo at `<path>` appears uninitialized or incomplete"
   - Suggest: "Run `/init-central-docs` in that repo to set it up"
5. Proceed with local setup regardless (handoffs are always local)

### Step 3: Suggest .gitignore for Handoffs

Check if `ai_docs/handoffs/` is already gitignored. If not, suggest adding:

```gitignore
# AI session handoffs — ephemeral by default
ai_docs/handoffs/
```

This keeps handoffs local by default. Users can force-add specific handoffs with `git add -f` when they want to preserve them.

### Step 4: Create index.md (if missing)

Only create if it doesn't exist. Ask the user for the project name first.

**Template for index.md:**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: index
status: active
topic: "[Project Name] Decision Records Index"
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true
ai_model:                                # optional: which model
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

### Step 5: Create Template Files (if missing)

Only create templates that don't already exist.

**templates/plan.md:**

````markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: plan
status: draft
topic: "[Feature Name] Implementation Plan"

# Accountability
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true
ai_model:                                # optional: which model

# Linking
related_prs: []
related_issue:

# Project
project:                                 # Logical project/service name
repo:                                    # GitHub org/repo
# repos: []                             # Uncomment for cross-repo docs

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
````

**templates/research.md:**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: research
status: draft
topic: "[Topic] Research"

# Accountability
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true
ai_model:                                # optional: which model

# Linking
related_prs: []
related_issue:

# Project
project:                                 # Logical project/service name
repo:                                    # GitHub org/repo
# repos: []                             # Uncomment for cross-repo docs

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
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true
ai_model:                                # optional: which model

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

### Step 6: Suggest AGENTS.md Integration

After creating the structure, suggest adding one of these to the project's AGENTS.md:

**Option A — Central repo** (when plans/research are centralized):

```markdown
## Decision Records

Plans and research for this project are centralized at:
**Repository:** ../<ai-docs-repo>/

Find this project's docs:
rg -l "repo: org/<this-repo>" ../<ai-docs-repo>/plans/

### Handoffs (Local)
Session handoffs live in `ai_docs/handoffs/` (gitignored by default).
```

**Option B — Local** (when plans/research are in this repo):

```markdown
## Decision Records

Before implementing significant changes, check `ai_docs/` for existing context:
- **Plans** (`ai_docs/plans/`): Active implementation plans
- **Research** (`ai_docs/research/`): Technical investigations and ADRs
- **Handoffs** (`ai_docs/handoffs/`): Session continuity notes (gitignored by default)

Start at `ai_docs/index.md` for project overview.
```

Ask the user which option applies to their setup.

## Idempotency

This skill is safe to run multiple times:

- Uses `mkdir -p` which succeeds if directory exists
- Only creates files if they don't exist (check with Read first)
- Never overwrites existing content

## Response

After completion, inform the user:

**Local mode:**

```text
ai_docs/ structure initialized at: $AI_DOCS

Created:
- ai_docs/index.md (edit to add project details)
- ai_docs/plans/
- ai_docs/research/
- ai_docs/handoffs/ (gitignored by default)
- ai_docs/templates/{plan,research,handoff}.md

Consider adding the Decision Records snippet to your AGENTS.md.
```

**Central mode:**

```text
ai_docs/ structure initialized at: $AI_DOCS

Created:
- ai_docs/handoffs/ (gitignored by default)

Plans and research are managed in the central repo.
Consider adding the Decision Records snippet to your AGENTS.md.
```
