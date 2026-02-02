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
  - Task
  - Glob
  - Grep
---

# Create Implementation Plan

Create structured implementation plan documents in `ai_docs/plans/` following the [Decision Records with AI Assistance](https://github.com/stephen-tatari/coding-agent-documentation) schema.

**Announce at start:** "I'm using the create-plan skill to create an implementation plan."

## When to Use

- Before starting significant feature work
- When planning multi-phase implementations
- When you need to document alternatives considered
- When work requires human review before proceeding

## Process

### Step 1: Initialize Directory Structure

Invoke the `init-ai-docs` skill to ensure the directory structure exists:

```text
/init-ai-docs
```

This is idempotent and safe to run even if structure already exists.

**Fallback if skill unavailable:**

```bash
mkdir -p ai_docs/plans ai_docs/research ai_docs/logs
```

### Step 2: Gather Context

Ask the user for:

1. **Feature name**: Brief, descriptive name (will become filename)
2. **Overview**: What does this plan achieve?
3. **Constraints**: Technical or business constraints
4. **Alternatives**: What options were considered?

### Step 3: Research Phase

**Before writing the plan, gather context systematically:**

1. **Read all referenced files completely** - Don't skim, read in full
2. **Find 3 similar patterns** - Use parallel sub-agents to locate existing implementations that mirror what you're building
3. **Identify conventions** - Note testing patterns, file organization, naming conventions

**Research approach:**

Use Task tool with `subagent_type: Explore` to search in parallel (preferred) or sequential Glob/Grep if Task unavailable:

| Search Goal | Parallel (Task tool) | Sequential (fallback) |
|-------------|---------------------|----------------------|
| Similar features | `Task(Explore): "Find implementations of [feature type]"` | `Grep` for key terms, then `Read` matches |
| Test templates | `Task(Explore): "Find tests for [similar feature]"` | `Glob` for `**/test*` patterns |
| Helper utilities | `Task(Explore): "Find utility functions for [domain]"` | `Grep` for common function names |

**No open questions rule:** Research or ask the user before writing. The plan document must be complete - questions are allowed during context gathering (Step 2), but not left unresolved in the final document.

### Step 4: Generate Filename

```bash
DATE=$(date +%Y-%m-%d)
FILENAME="ai_docs/plans/${DATE}-<feature-name>.md"
```

**Kebab-case conversion rules** (apply manually - no external tools needed):

1. Convert to lowercase
2. Replace spaces with hyphens
3. Remove special characters except hyphens
4. Collapse multiple hyphens to single hyphen

| Input | Output |
|-------|--------|
| "OAuth2 Implementation" | `oauth2-implementation` |
| "Add User Auth" | `add-user-auth` |
| "Fix Bug #123" | `fix-bug-123` |

Example: `ai_docs/plans/2026-02-02-oauth2-implementation.md`

### Step 5: Write the Plan Document

Use this template:

````markdown
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

## Desired End State

[Describe what success looks like. What will exist when this is done? How will users/developers interact with it?]

## Overview

[1-2 paragraph summary of what this plan achieves]

## What We're NOT Doing

- [Explicitly list out-of-scope items to prevent scope creep]
- [Things that might seem related but are excluded]
- [Future enhancements deferred to later]

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

Each task is ONE action (2-5 minutes):

- [ ] **Step 1:** Write failing test for [specific behavior]
  - File: `tests/path/to/test.py`
  - Run: `pytest tests/path/test.py::test_name -v`
  - Expected: FAIL with "[specific error]"

- [ ] **Step 2:** Verify test fails correctly
  - Run the test command above
  - Confirm failure message matches expected

- [ ] **Step 3:** Write minimal implementation
  - File: `src/path/to/file.py:45-67`
  - Add: [specific code or description]

- [ ] **Step 4:** Verify test passes
  - Run: `pytest tests/path/test.py::test_name -v`
  - Expected: PASS

- [ ] **Step 5:** Commit
  - `git add <files> && git commit -m "feat: add specific feature"`

#### Success Criteria

**Automated Verification:**

- [ ] Tests pass: `pytest tests/path/ -v`
- [ ] Lint passes: `make lint` or project equivalent

**Manual Verification:**

- [ ] [Description of manual check]
- [ ] [Another manual verification step]

### Phase 2: [Name]

**Goal:** [What this phase achieves]

**Tasks:**

- [ ] **Step 1:** [action with file:line reference]
- [ ] **Step 2:** [action]
- [ ] ...

#### Success Criteria

**Automated Verification:**

- [ ] [command to run]

**Manual Verification:**

- [ ] [manual check description]

## Critical Files

- `path/to/file.ext:line-range` - Description of relevance
- `tests/path/to/test.ext` - Test file to mirror
- `path/to/similar/impl.ext:50-75` - Similar pattern to follow
````

### Step 6: Quality Checklist

Before finalizing the plan, verify:

- [ ] **No open questions** - All ambiguities resolved through research or asking
- [ ] **Desired end state** is clearly described
- [ ] **Out-of-scope items** are explicitly listed
- [ ] **Assumptions** are explicitly listed
- [ ] **Alternatives** were considered with pros/cons
- [ ] **Each task is one action** (2-5 minutes, single verb)
- [ ] **File:line references** included for all code changes
- [ ] **Success criteria split** into automated vs manual
- [ ] **TDD cycle explicit** in task steps (test → verify fail → impl → verify pass → commit)
- [ ] **No secrets** or sensitive data included
- [ ] **3 similar patterns** identified and referenced in Critical Files

### Step 7: Remind About Review and Offer Execution

After creating the plan, remind the user:

```text
Plan created at: ai_docs/plans/YYYY-MM-DD-feature-name.md

IMPORTANT: Commit this plan so it merges with your branch:
git add ai_docs/plans/YYYY-MM-DD-feature-name.md && git commit -m "docs: add plan for feature-name"

IMPORTANT: The `reviewed_by` field is required before execution.
A human reviewer must attest that the plan reflects the team's intent.

## Execution Options

Once reviewed, choose an implementation approach:

**1. Subagent-Driven (this session)** - requires Task tool
- Dispatch fresh subagent per task
- Review between tasks
- Fast iteration with code review checkpoints

**2. Parallel Session (separate)** - requires `executing-plans` skill
- Open new session with executing-plans skill
- Batch execution with checkpoints
- Good for longer implementations

**3. Manual Execution (always available)**
- Work through phases sequentially in current session
- Follow TDD cycle for each task
- Commit after each phase passes verification

Which approach would you prefer?
```

## Cross-Referencing

Reference other ai_docs using `@ai_docs/` prefix:

```markdown
Based on constraints in @ai_docs/research/2026-01-10-auth-options.md
```

This syntax is grep-able and parseable by AI agents.

## Task Granularity Guide

**Each step is ONE action (2-5 minutes):**

| Good (one action) | Bad (multiple actions) |
|-------------------|------------------------|
| Write the failing test | Write tests and implement |
| Run test to verify it fails | Test and fix |
| Write minimal implementation | Implement feature |
| Run test to verify it passes | Make it work |
| Commit | Finish phase |

**TDD cycle in tasks:**

```text
Step 1: Write failing test
Step 2: Run test to verify it fails
Step 3: Write minimal implementation
Step 4: Run test to verify it passes
Step 5: Commit
```

Repeat for each behavior/feature within the phase.
