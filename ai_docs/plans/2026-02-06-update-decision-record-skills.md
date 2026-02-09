---
schema_version: "1.1"
date: "2026-02-06"
type: plan
status: approved
topic: Update Decision Record Skills to Match README
author: sprice
ai_assisted: true
related_prs: []
related_issue:
tags: [skills, decision-records, schema]
data_sensitivity: none
---

# Plan: Update Decision Record Skills to Match README

## Context

The `coding-agent-documentation` README.md has shifted to a hybrid architecture with new schema fields. The 5 decision record skills need to match. Key design decision: **the project's AGENTS.md/CLAUDE.md determines whether plans/research go to a central repo or stay local** — skills read that config at runtime.

## Desired End State

All 5 skills produce documents matching the README's current schema and support both central-repo and local-only modes. Handoffs are always local, gitignored by default, with opt-in commit.

## What We're NOT Doing

- Updating the user's global CLAUDE.md (out of scope)
- Updating any project AGENTS.md files (those are per-project)
- Adding CI/tooling to the skills repo
- Changing skill names or descriptions beyond what's needed

## Assumptions

- The README is the source of truth for schema and conventions
- Skills should support both modes (central and local) rather than hardcoding one
- Legacy `thoughts/shared/` path support can be removed (migration period over)

---

## Phase 1: Schema Updates Across All Skills

Update frontmatter templates in all 5 skills to match the README schema.

### Task 1.1: `related_pr` → `related_prs` in init-ai-docs

**File:** `init-ai-docs/SKILL.md`

Replace in plan template (line 117-118) and research template (line 204-205):

```yaml
# Old
related_pr:
related_issue:

# New
related_prs: []
related_issue:
```

### Task 1.2: `related_pr` → `related_prs` in create-plan

**File:** `create-plan/SKILL.md` (line 115-116)

Same replacement as 1.1.

### Task 1.3: `related_pr` → `related_prs` in create-research

**File:** `create-research/SKILL.md` — exploratory template (line 168-169) and ADR template (line 233-234)

Same replacement as 1.1.

### Task 1.4: Add `project`/`repo` fields to plan and research templates

Add after Linking section in each plan/research template:

```yaml
# Project association (recommended for plans/research)
project:                                 # Logical project/service name
repo:                                    # GitHub org/repo
# repos: []                             # Uncomment for cross-repo docs
```

**Files:**
- `init-ai-docs/SKILL.md` — plan template (~line 119), research template (~line 206)
- `create-plan/SKILL.md` — template (~line 117)
- `create-research/SKILL.md` — both templates (~lines 170, 235)

### Task 1.5: Add `ai_model` field to accountability sections

Add after `ai_assisted: true` in every frontmatter template:

```yaml
ai_assisted: true
ai_model:                                # optional: which model
```

**Files:** All 5 skills, every template with an accountability section.

### Task 1.6: Fix `ai_docs/logs` typo in create-plan

**File:** `create-plan/SKILL.md` line 44

```bash
# Old
mkdir -p ai_docs/plans ai_docs/research ai_docs/logs

# New
mkdir -p ai_docs/plans ai_docs/research ai_docs/handoffs
```

#### Phase 1 Success Criteria

- `rg "related_pr:" claude-skills/*/SKILL.md` returns zero matches (only `related_prs:`)
- `rg "project:" claude-skills/{init-ai-docs,create-plan,create-research}/SKILL.md` finds the new field in all plan/research templates
- `rg "ai_model:" claude-skills/*/SKILL.md` finds it in all 5 skills
- `rg "ai_docs/logs" claude-skills/` returns zero matches

---

## Phase 2: Output Location Detection (create-plan, create-research)

Add a step to create-plan and create-research that reads the project's AGENTS.md/CLAUDE.md to determine where to create documents.

### Task 2.1: Add "Detect Output Location" step to create-plan

**File:** `create-plan/SKILL.md`

Insert new step between current Step 1 (init-ai-docs) and Step 2 (Gather Context):

```markdown
### Step 2: Detect Output Location

Read the project's AGENTS.md (or CLAUDE.md) to determine where plans are stored:

1. Read `$REPO_ROOT/AGENTS.md` (or `CLAUDE.md`)
2. Find the "Decision Records" section
3. If it references a central repo path (e.g., `../<ai-docs-repo>/plans/`):
   - Set `PLANS_DIR` to that path
   - Verify the directory exists; if not, warn the user
4. If it references local `ai_docs/plans/` or no Decision Records section exists:
   - Set `PLANS_DIR` to `ai_docs/plans/`
   - Run `/init-ai-docs` if needed
```

Renumber subsequent steps.

### Task 2.2: Add "Detect Output Location" step to create-research

**File:** `create-research/SKILL.md`

Same pattern as 2.1, but for `RESEARCH_DIR` / `research/`.

### Task 2.3: Update filename generation steps

In both skills, replace hardcoded `ai_docs/plans/` and `ai_docs/research/` paths with the detected `$PLANS_DIR` / `$RESEARCH_DIR`.

### Task 2.4: Update naming convention

In both skills, add note about optional project prefix in filenames:

```markdown
**Naming convention:**
- `YYYY-MM-DD-<topic>.md` (default)
- `YYYY-MM-DD-<project>-<topic>.md` (recommended when project-specific in a central repo)
```

#### Phase 2 Success Criteria

- Both create-plan and create-research have a "Detect Output Location" step
- No hardcoded `ai_docs/plans/` or `ai_docs/research/` paths remain in the document creation flow (paths come from detection)
- Naming convention documented in both skills

---

## Phase 3: Handoff Lifecycle Changes (create-handoff, resume-handoff)

### Task 3.1: Update create-handoff — gitignored by default

**File:** `create-handoff/SKILL.md`

Changes:
- Line 42: Remove "Commit the handoff so it merges with your branch"
- Lines 129-139 (Response section): Replace commit-as-default messaging with:

  ```text
  Handoff created at: <full-path>/ai_docs/handoffs/<filename>.md

  Handoffs are gitignored by default. To preserve beyond this session:
  git add -f ai_docs/handoffs/<filename>.md && git commit -m "docs: add handoff for <description>"

  Resume in a new session with:
  /resume-handoff <full-path>/ai_docs/handoffs/<filename>.md
  ```

- Line 146: Change "Commit handoffs in worktrees" → "Handoffs are gitignored by default; commit when context is worth preserving"
- Lines 161-166: Remove "Migrating from Personal Skills" section (legacy)

### Task 3.2: Update resume-handoff — delete consumed handoff

**File:** `resume-handoff/SKILL.md`

Add to Phase 3 (Implementation), after step 1:

```markdown
4. **Clean up consumed handoff** — After confirming work has resumed successfully:
   - For gitignored handoffs: delete the file
   - For committed handoffs: leave in place (part of git history)
   - Ask user before deleting if uncertain
```

### Task 3.3: Remove legacy path support from resume-handoff

**File:** `resume-handoff/SKILL.md`

Remove `thoughts/shared/handoffs` references from Path Detection (lines 38-40, 48-51) and "Migrating from Personal Skills" section (lines 189-195).

#### Phase 3 Success Criteria

- `rg "Commit.*handoff.*merges" claude-skills/create-handoff/SKILL.md` returns zero matches
- create-handoff Response section shows gitignored-by-default messaging
- resume-handoff has a "Clean up consumed handoff" step
- `rg "thoughts/shared" claude-skills/*/SKILL.md` returns zero matches

---

## Phase 4: init-ai-docs Updates

### Task 4.1: Add mode-aware directory creation

**File:** `init-ai-docs/SKILL.md`

Update Step 2 to be mode-aware:
- **If local mode:** Create full `ai_docs/{plans,research,handoffs,templates}/` (current behavior)
- **If central repo mode:** Only create `ai_docs/handoffs/` locally

Add detection logic similar to Phase 2 but simpler — if AGENTS.md already points to a central repo, only create the handoffs directory locally.

### Task 4.2: Add .gitignore suggestion

**File:** `init-ai-docs/SKILL.md`

After directory creation, suggest adding to `.gitignore`:

```gitignore
# AI session handoffs — ephemeral by default
ai_docs/handoffs/
```

### Task 4.3: Update AGENTS.md template to offer two options

**File:** `init-ai-docs/SKILL.md` (Step 5, lines 313-327)

Replace single template with two options:

**Option A — Central repo (when plans/research are centralized):**

```markdown
## Decision Records

Plans and research for this project are centralized at:
**Repository:** ../<ai-docs-repo>/

Find this project's docs:
rg -l "repo: org/<this-repo>" ../<ai-docs-repo>/plans/

### Handoffs (Local)
Session handoffs live in `ai_docs/handoffs/` (gitignored by default).
```

**Option B — Local (when plans/research are in this repo):**

```markdown
## Decision Records

Before implementing significant changes, check `ai_docs/` for existing context:
- **Plans** (`ai_docs/plans/`): Active implementation plans
- **Research** (`ai_docs/research/`): Technical investigations and ADRs
- **Handoffs** (`ai_docs/handoffs/`): Session continuity notes (gitignored by default)

Start at `ai_docs/index.md` for project overview.
```

### Task 4.4: Update schema in init-ai-docs templates

Apply all schema changes from Phase 1 to the templates in init-ai-docs (plan.md, research.md, handoff.md templates).

#### Phase 4 Success Criteria

- init-ai-docs offers two AGENTS.md templates (central and local)
- .gitignore suggestion for `ai_docs/handoffs/` is present
- Templates match updated schema

---

## Phase 5: Cross-Referencing and Review Messaging

### Task 5.1: Update cross-referencing sections

**Files:** `create-plan/SKILL.md`, `create-research/SKILL.md`, `create-handoff/SKILL.md`

Add mode-aware cross-referencing guidance:
- **Central mode:** Use relative sibling paths (`../<ai-docs-repo>/research/2026-01-10-topic.md`)
- **Local mode:** Use `@ai_docs/` prefix (`@ai_docs/research/2026-01-10-topic.md`)

### Task 5.2: Update review/commit messaging in create-plan

**File:** `create-plan/SKILL.md` (Step 7, lines 249-281)

- Central mode: "Commit directly to the docs repo — no PR required for documentation. Reference this plan from the implementing code PR."
- Local mode: Keep current messaging but add "Update `related_prs` when implementing PR is created."

### Task 5.3: Update review/commit messaging in create-research

**File:** `create-research/SKILL.md` (Step 9, lines 336-348)

Same pattern as 5.2.

#### Phase 5 Success Criteria

- Cross-referencing sections handle both modes
- Review messaging is mode-aware
- `related_prs` mentioned in review reminders

---

## Critical Files

- `init-ai-docs/SKILL.md` — bootstrapping, templates, AGENTS.md integration
- `create-plan/SKILL.md` — plan creation workflow and templates
- `create-research/SKILL.md` — research/ADR creation workflow and templates
- `create-handoff/SKILL.md` — handoff creation and commit messaging
- `resume-handoff/SKILL.md` — handoff consumption and cleanup
- `../coding-agent-documentation/README.md` — source of truth for schema and conventions
