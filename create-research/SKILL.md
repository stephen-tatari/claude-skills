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
---

# Create Research Document

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

### Step 3: Gather Context

For **exploratory research**, ask:

- Topic/question being investigated
- What prompted this research?
- Data sensitivity level (public/internal/restricted)

For **decision records (ADR)**, ask:

- What decision needs to be made?
- What options are being considered?
- What constraints apply?
- Data sensitivity level

### Step 4: Generate Filename

```bash
DATE=$(date +%Y-%m-%d)
# Convert topic to kebab-case
FILENAME="ai_docs/research/${DATE}-<topic>.md"
```

Example: `ai_docs/research/2026-02-02-auth-library-selection.md`

### Step 5: Write the Document

**For Exploratory Research:**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: research
status: draft
topic: "[Topic] Research"

# Accountability
author: ai-assisted
reviewed_by:                    # Required before merging
ai_assisted: true

# Linking
related_pr:
related_issue:

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

## Key Takeaways

- [Takeaway 1]
- [Takeaway 2]

## Open Questions

- [Question 1]
- [Question 2]

## Sources

- [Link to source 1]
- [Link to source 2]
```

**For Decision Records (ADR):**

```markdown
---
schema_version: 1
date: [YYYY-MM-DD]
type: research
status: draft
topic: "[Decision Topic] ADR"

# Accountability
author: ai-assisted
reviewed_by:                    # Required before merging
ai_assisted: true

# Linking
related_pr:
related_issue:

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
```

### Step 6: Remind About Review Requirement

After creating the document, remind the user:

```text
Research document created at: ai_docs/research/YYYY-MM-DD-topic.md

IMPORTANT: The `reviewed_by` field is required before merging.
A human reviewer must attest that the content reflects the team's understanding.

For ADRs: Update status from "Proposed" to "Accepted" after team review.
```

## Quality Checklist

Before finalizing, verify:

- [ ] Claims are linked to sources
- [ ] Assumptions are explicitly stated
- [ ] For ADRs: Alternatives have clear pros/cons
- [ ] Data sensitivity is appropriate (no secrets if public)
- [ ] No credentials or sensitive internal URLs

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
