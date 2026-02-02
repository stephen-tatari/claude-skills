---
name: create-plan
description: Create implementation plan documents in ai_docs/plans/ following decision record schema. Generates YYYY-MM-DD-<feature>.md with phases, alternatives, and success criteria. Use before starting significant feature work.
allowed-tools:
  - Write
  - Read
  - Bash(mkdir:*)
  - Bash(date:*)
  - Bash(git:*)
  - Skill
---

# Create Implementation Plan

Create structured implementation plan documents in `ai_docs/plans/` following the [Decision Records with AI Assistance](https://github.com/stephen-tatari/coding-agent-documentation) schema.

## When to Use

- Before starting significant feature work
- When planning multi-phase implementations
- When you need to document alternatives considered
- When work requires human review before proceeding

## Process

### Step 1: Initialize Directory Structure

First, invoke the `init-ai-docs` skill to ensure the directory structure exists:

```
/init-ai-docs
```

This is idempotent and safe to run even if structure already exists.

### Step 2: Gather Context

Ask the user for:

1. **Feature name**: Brief, descriptive name (will become filename)
2. **Overview**: What does this plan achieve?
3. **Constraints**: Technical or business constraints
4. **Alternatives**: What options were considered?

### Step 3: Generate Filename

```bash
DATE=$(date +%Y-%m-%d)
# Convert feature name to kebab-case
FILENAME="ai_docs/plans/${DATE}-<feature-name>.md"
```

Example: `ai_docs/plans/2026-02-02-oauth2-implementation.md`

### Step 4: Write the Plan Document

Use this template:

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: plan
status: draft
topic: "[Feature Name] Implementation Plan"

# Accountability
author: ai-assisted
reviewed_by:                    # Required before merging
ai_assisted: true

# Linking
related_pr:
related_issue:

# Classification
tags: [relevant, tags]
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

**Goal:** [What this phase achieves]

**Tasks:**

- [ ] Task 1
- [ ] Task 2

**Success Criteria:**

- [Automated] `command to verify`
- [Manual] Description of manual check

## Verification

**Automated checks:**

```bash
# Commands to verify implementation
```

**Manual verification:**

- [ ] Check 1
- [ ] Check 2

## Critical Files

- `path/to/file.ext` - Description of relevance
```

### Step 5: Remind About Review Requirement

After creating the plan, remind the user:

```
Plan created at: ai_docs/plans/YYYY-MM-DD-feature-name.md

IMPORTANT: The `reviewed_by` field is required before merging.
A human reviewer must attest that the plan reflects the team's intent.

Next steps:
1. Review and refine the plan
2. Add reviewer name to `reviewed_by` field
3. Begin implementation (consider using /create-handoff at stopping points)
```

## Quality Checklist

Before finalizing the plan, verify:

- [ ] Assumptions are explicitly listed
- [ ] Alternatives were considered with pros/cons
- [ ] Each phase has clear success criteria
- [ ] No secrets or sensitive data included
- [ ] Claims are linked to sources where applicable

## Cross-Referencing

Reference other ai_docs using `@ai_docs/` prefix:

```markdown
Based on constraints in @ai_docs/research/2026-01-10-auth-options.md
```

This syntax is grep-able and parseable by AI agents.
