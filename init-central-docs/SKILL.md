---
name: init-central-docs
description: Bootstrap a central AI documentation repository for decision records. Creates plans/, research/, templates/ directories with index.md, AGENTS.md, and document templates. Use when setting up a centralized repo for plans and research across multiple projects.
allowed-tools:
  - Write
  - Read
  - Bash(mkdir:*)
  - Bash(ls:*)
  - Bash(git:*)
  - Bash(gh:*)
---

# Initialize Central Documentation Repository

Bootstrap a central AI documentation repository following the [Decision Records with AI Assistance](https://github.com/stephen-tatari/coding-agent-documentation) convention.

A central docs repo stores plans and research for multiple projects in one place. Handoffs remain local to each project repo.

**Announce at start:** "I'm using the init-central-docs skill to bootstrap a central documentation repository."

## When to Use

- Setting up a new centralized repo for plans and research across multiple projects
- When `init-ai-docs` warns that a referenced central repo appears uninitialized
- Migrating from per-project ai_docs/ to a shared documentation repository

## Process

### Step 1: Verify or Create Repository

Check if we're inside a git repository:

```bash
git rev-parse --show-toplevel 2>/dev/null
```

**If no git repo exists**, offer to create one:

1. Ask the user for a repo name (suggest `ai-docs` or `<org>-ai-docs`)
2. Offer two options:
   - **Local only:** `git init <repo-name> && cd <repo-name>`
   - **GitHub:** `gh repo create <org>/<repo-name> --private --clone && cd <repo-name>`
3. Proceed in the newly created repo

**If a git repo exists**, confirm it's intended as a central docs repo, not a code project:

- Check for code project indicators (`src/`, `lib/`, `app/`, `pkg/` directories)
- If found, warn: "This looks like a code project, not a docs repo. Central docs repos are typically standalone. Continue anyway?"

### Step 2: Create Directory Structure

```bash
mkdir -p plans research templates
```

### Step 3: Create index.md

Ask the user for the organization or team name.

**Template for index.md:**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: index
status: active
topic: "[Org/Team Name] Central Decision Records Index"
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true
ai_model:                                # optional: which model
---

# Central Docs: [Org/Team Name]

## Overview

Central repository for decision records (plans, research, ADRs) across multiple projects.

## Projects

<!-- Add projects that store docs here -->
<!-- Example: ### project-name -->
<!-- Find docs: rg -l "repo: org/project-name" plans/ research/ -->

## Active Decisions

<!-- Add links to active research/ADRs here -->
<!-- Example: @research/YYYY-MM-DD-decision-name.md - One-line summary -->

## Current Plans

<!-- Add links to active plans here -->
<!-- Example: @plans/YYYY-MM-DD-feature-name.md - Status: planning|in-progress|blocked -->

## Conventions

- Plans and research follow the Decision Records schema (schema_version: 1)
- Each document includes `project` and `repo` fields to associate it with a codebase
- Filenames use `YYYY-MM-DD-<project>-<topic>.md` format for project-specific docs
- Handoffs are always stored locally in each project's `ai_docs/handoffs/`
```

### Step 4: Create AGENTS.md

Create `AGENTS.md` and symlink `CLAUDE.md -> AGENTS.md`.

**Template for AGENTS.md:**

```markdown
# Central Documentation Repository

This repository stores decision records (plans, research, ADRs) for multiple projects following the [Decision Records with AI Assistance](https://github.com/stephen-tatari/coding-agent-documentation) convention.

## Directory Structure

- `plans/` — Implementation plans with phases, alternatives, and success criteria
- `research/` — Technical investigations, ADRs, and research notes
- `templates/` — Document templates for consistent formatting
- `index.md` — Catalog of all projects and active documents

## Document Schema

All documents use YAML frontmatter with these required fields:

```yaml
schema_version: 1
date: YYYY-MM-DD
type: plan | research
status: draft | active | completed | superseded
topic: "Descriptive title"

# Accountability
author: git-user-name
ai_assisted: true | false
ai_model:                    # optional

# Linking
related_prs: []
related_issue:
superseded_by:               # Link to replacement doc

# Project
project:                     # Logical project/service name
repo:                        # GitHub org/repo

# Classification
tags: []
data_sensitivity: internal
```

## Quality Constraints

Before committing documents:

- Claims linked to sources
- Assumptions explicitly listed
- Alternatives considered (for plans and research)
- No secrets or sensitive data
- `project` and `repo` fields filled in

## Naming Convention

- `YYYY-MM-DD-<topic>.md` for cross-cutting docs
- `YYYY-MM-DD-<project>-<topic>.md` for project-specific docs (recommended)

## Cross-Referencing

From project repos, reference docs here using relative paths:
```
../<this-repo>/plans/2026-01-15-auth-redesign.md
```

From docs here, reference project code using org/repo notation:
```
See implementation in org/project-name src/auth/handler.ts
```
```

```bash
# Create symlink
ln -sf AGENTS.md CLAUDE.md
```

### Step 5: Create Template Files

Only create templates that don't already exist.

<!-- Keep in sync: templates also appear in init-ai-docs, init-central-docs, and create-*/SKILL.md -->
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
superseded_by:                           # Link to replacement doc if superseded

# Project
project:                                 # Logical project/service name
repo:                                    # GitHub org/repo
# repos: []                             # Uncomment for cross-repo docs

# Git Context
git_commit: [short-sha]
branch: [branch name]
repository: [repo name]

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

<!-- Keep in sync: templates also appear in init-ai-docs, init-central-docs, and create-*/SKILL.md -->
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
superseded_by:                           # Link to replacement doc if superseded

# Project
project:                                 # Logical project/service name
repo:                                    # GitHub org/repo
# repos: []                             # Uncomment for cross-repo docs

# Git Context
git_commit: [short-sha]
branch: [branch name]
repository: [repo name]

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

<!-- Keep in sync: templates also appear in init-ai-docs, init-central-docs, and create-*/SKILL.md -->
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

### Step 6: Suggest Pre-Commit Config

Ask the user if they want a `.pre-commit-config.yaml` with markdownlint. If yes, create:

```yaml
repos:
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.43.0
    hooks:
      - id: markdownlint
        args: ["--fix"]
```

If the user declines, skip this step.

### Step 7: Suggest CI Checks

Print guidance for recommended CI checks (do not auto-create workflow files):

```text
Recommended CI checks for this repo:

1. Index freshness — verify index.md references match actual files
   rg -l "status: active" plans/ research/ | while read f; do
     grep -q "$(basename $f)" index.md || echo "Missing from index: $f"
   done

2. Frontmatter validation — ensure required fields are present
   Check each .md file for: schema_version, date, type, status, topic, author

3. Link checking — verify cross-references resolve
   Use markdown-link-check or similar tool

4. No secrets — scan for patterns like API keys, tokens, passwords
   Use trufflehog, gitleaks, or similar
```

### Step 8: Response

Summarize what was created:

```text
Central docs repo initialized at: $REPO_ROOT

Created:
- plans/                       (implementation plans)
- research/                    (research notes and ADRs)
- templates/{plan,research,handoff}.md
- index.md                     (edit to add project details)
- AGENTS.md + CLAUDE.md symlink

Next steps:
1. Edit index.md with your team/org details
2. In each project repo, add a Decision Records section to AGENTS.md
   pointing to this repo (see init-ai-docs for the template)
3. Run /init-ai-docs in project repos to set up local ai_docs/handoffs/
```

## Idempotency

This skill is safe to run multiple times:

- Uses `mkdir -p` which succeeds if directory exists
- Only creates files if they don't exist (check with Read first)
- Never overwrites existing content
