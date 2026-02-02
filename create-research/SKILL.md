---
name: create-research
description: Create research notes or Architecture Decision Records (ADRs) in ai_docs/research/. Generates YYYY-MM-DD-<topic>.md with findings, alternatives, decision, and consequences. Use when evaluating options or documenting decisions.
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

# Create Research Document

**Announce at start:** "I'm using the create-research skill to document [topic]."

## Mandate

**Documentation only.** You must:

- Describe what exists
- Explain how code works
- Document patterns and connections
- Cite sources with file:line references

You must NOT:

- Critique implementation choices
- Suggest improvements or refactoring
- Evaluate code quality
- Recommend changes (unless explicitly asked)

---

Create research notes or Architecture Decision Records (ADRs) in `ai_docs/research/` following the [Decision Records with AI Assistance](https://github.com/stephen-tatari/coding-agent-documentation) schema.

## When to Use

- Evaluating technical options before making a decision
- Documenting architectural decisions (ADR)
- Recording investigation findings
- Capturing constraints and trade-offs

## Process

### Step 1: Initialize Directory Structure

First, invoke the `init-ai-docs` skill to ensure the directory structure exists:

```text
/init-ai-docs
```

This is idempotent and safe to run even if structure already exists.

### Step 2: Determine Document Type

Ask the user:

> Is this exploratory research or a decision record (ADR)?
>
> - **Exploratory**: Gathering information, no decision yet
> - **Decision Record (ADR)**: Documenting a specific architectural decision

This affects which sections to emphasize.

### Step 3: Research Phase

**Before writing the document, investigate systematically:**

#### 3a: Read Mentioned Files First

Read ALL files the user mentioned completely. Do not use limit/offset parameters. This happens in YOUR context, not delegated.

#### 3b: Spawn Parallel Sub-Agents

Launch these Task agents **in parallel** (single message, multiple tool calls):

**codebase-locator** (subagent_type: Explore)

````text
Find all files and components related to: [research topic]
Report file paths, their purposes, and how they connect.
Do not evaluate or critique - document only.
````

**codebase-analyzer** (subagent_type: Explore)

````text
Analyze how [specific component/feature] works.
Trace the code path and explain the implementation.
Include file:line references for key locations.
Do not suggest improvements - document only.
````

**pattern-finder** (subagent_type: Explore)

````text
Find 3+ existing examples of [relevant pattern] in the codebase.
Document each with file:line references.
Note any variations in how the pattern is applied.
````

#### 3c: Synthesize Findings

Wait for all agents to complete before proceeding. Compile:

- File paths and line numbers for all relevant code
- Code flow traces
- Pattern documentation with 3+ examples
- Connections between components

### Step 4: Gather Context

For **exploratory research**, ask:

- Topic/question being investigated
- What prompted this research?
- Data sensitivity level (public/internal/restricted)

For **decision records (ADR)**, ask:

- What decision needs to be made?
- What options are being considered?
- What constraints apply?
- Data sensitivity level

### Step 5: Generate Filename

```bash
DATE=$(date +%Y-%m-%d)
# Convert topic to kebab-case
FILENAME="ai_docs/research/${DATE}-<topic>.md"
```

Example: `ai_docs/research/2026-02-02-auth-library-selection.md`

### Step 6: Gather Git Metadata

```bash
GIT_COMMIT=$(git rev-parse --short HEAD)
GIT_BRANCH=$(git branch --show-current)
GIT_REPO=$(basename $(git rev-parse --show-toplevel))
```

Use these values in the frontmatter.

### Step 7: Write the Document

**For Exploratory Research:**

````markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: research
status: draft
topic: "[Topic] Research"

# Accountability
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true

# Linking
related_pr:
related_issue:

# Git Context
git_commit: [short-sha from git rev-parse --short HEAD]
branch: [from git branch --show-current]
repository: [from basename $(git rev-parse --show-toplevel)]

# Classification
tags: [relevant, tags]
data_sensitivity: [public|internal|restricted]
---

# Research: [Topic]

## Context

[What prompted this research? What question are we trying to answer?]

## Findings

### [Finding 1]

[Details with links to sources]

### [Finding 2]

[Details with links to sources]

## Code References

| File | Lines | Purpose |
|------|-------|---------|
| path/to/file.ext | 10-50 | Description of relevance |

## Key Takeaways

- [Takeaway 1]
- [Takeaway 2]

## Open Questions

- [Question 1]
- [Question 2]

## Sources

- [Link to source 1]
- [Link to source 2]
````

**For Decision Records (ADR):**

````markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: research
status: draft
topic: "[Decision Topic] ADR"

# Accountability
author: [git-user]              # Human owner (run: git config user.name)
ai_assisted: true

# Linking
related_pr:
related_issue:

# Git Context
git_commit: [short-sha from git rev-parse --short HEAD]
branch: [from git branch --show-current]
repository: [from basename $(git rev-parse --show-toplevel)]

# Classification
tags: [adr, relevant, tags]
data_sensitivity: [public|internal|restricted]
---

# ADR: [Decision Topic]

## Status

[Proposed | Accepted | Deprecated | Superseded]

## Context

[What is the issue that we're seeing that is motivating this decision?]

## Alternatives Considered

### Option A: [Name]

[Description]

**Pros:**

- [Benefit 1]
- [Benefit 2]

**Cons:**

- [Drawback 1]
- [Drawback 2]

### Option B: [Name]

[Description]

**Pros:**

- [Benefit 1]
- [Benefit 2]

**Cons:**

- [Drawback 1]
- [Drawback 2]

## Decision

We will use [Option X] because [rationale].

## Code References

| File | Lines | Purpose |
|------|-------|---------|
| path/to/file.ext | 10-50 | Description of relevance |

## Consequences

### Positive

- [Consequence 1]
- [Consequence 2]

### Negative

- [Consequence 1]
- [Consequence 2]

### Neutral

- [Consequence 1]

## Sources

- [Link to source 1]
- [Link to source 2]
````

### Step 8: Quality Checklist

Before finalizing, verify:

- [ ] **Research phase complete** - Parallel agents spawned and findings synthesized
- [ ] **3+ patterns found** - pattern-finder agent returned examples with file:line refs
- [ ] **File:line references** - Every finding has specific code references
- [ ] **Code References table** - Populated with key files
- [ ] Claims are linked to sources
- [ ] Assumptions are explicitly stated
- [ ] For ADRs: Alternatives have clear pros/cons
- [ ] Data sensitivity is appropriate (no secrets if public)
- [ ] No credentials or sensitive internal URLs
- [ ] Git metadata is populated (commit, branch, repository)

### Step 9: Remind About Review Requirement

After creating the document, remind the user:

```text
Research document created at: ai_docs/research/YYYY-MM-DD-topic.md

IMPORTANT: Commit this document so it merges with your branch:
git add ai_docs/research/YYYY-MM-DD-topic.md && git commit -m "docs: add research on topic"

NOTE: Human accountability is provided through PR review. Ensure the document
is reviewed as part of the normal PR process before merging.

For ADRs: Update status from "Proposed" to "Accepted" after team review.
```

### Step 10: Offer Convergent Review (Complex Research)

For complex or high-stakes research, offer multi-pass review:

```text
Research document created at: ai_docs/research/YYYY-MM-DD-topic.md

For complex research, consider convergent review (4-5 passes until findings stabilize):
- Pass 1: Completeness - Are all aspects of the question addressed?
- Pass 2: Accuracy - Are file:line references correct and current?
- Pass 3: Alternatives - Did we miss any relevant patterns or approaches?
- Pass 4: Integration - How do findings connect to broader codebase?

Would you like me to run convergent review on this research?
```

## Status Transitions

For ADRs:

```text
Proposed → Accepted → [Deprecated | Superseded]
```

- **Proposed**: Under discussion
- **Accepted**: Team has agreed
- **Deprecated**: No longer applies
- **Superseded**: Replaced by newer decision (link via `superseded_by`)

## Cross-Referencing

Reference other ai_docs using `@ai_docs/` prefix:

```markdown
This decision builds on @ai_docs/research/2026-01-10-initial-investigation.md
```
