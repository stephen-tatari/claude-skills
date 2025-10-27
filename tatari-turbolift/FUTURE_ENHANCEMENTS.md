# Future Enhancement Plan for tatari-turbolift Skill

This document outlines optional supporting files that could be added to enhance the skill.

## Proposed Supporting Files

### 1. templates/transformation-script-template.py

**Purpose:** Reusable template for creating transformation scripts

**Contents:**

- Standard script structure with shebang
- Common imports (Path, sys, re, yaml)
- validate_prerequisites() skeleton
- make_changes() skeleton
- Proper error handling
- Test harness structure
- Usage documentation

**Benefit:** Speeds up script creation, ensures consistency

### 2. templates/test-transformation-template.py

**Purpose:** pytest template for testing transformation scripts

**Contents:**

- Test fixtures for sample files
- Tests for validation logic
- Tests for transformation logic
- Tests for edge cases (missing files, already transformed, etc.)
- Mock file system usage examples

**Benefit:** Encourages TDD, improves script reliability

### 3. templates/EXECUTION_PLAN.md

**Purpose:** Template for campaign planning documents

**Contents:**

- Overview section
- Scope and objectives
- Changes to be made
- Safety checks
- Phase breakdown
- Command sequences for each phase
- Troubleshooting section
- Files generated tracking

**Benefit:** Standardizes planning, ensures nothing forgotten

### 4. templates/PROGRESS.md

**Purpose:** Template for progress tracking

**Contents:**

- Current status section
- Completed phases breakdown
- Remaining work
- Issues encountered and resolutions
- Next steps
- Lessons learned section

**Benefit:** Consistent progress reporting

### 5. templates/README.md

**Purpose:** Template for turbolift campaign README

**Contents:**

- Campaign description
- Changes made
- Safety verification
- Reviewer checklist
- How the change was made
- Attribution footer

**Benefit:** Standard PR description and documentation

### 6. reference/workflow-examples.md

**Purpose:** Detailed walkthrough of SRE-3447 and SRE-3449

**Contents:**

- Complete command sequences used
- Decision points and rationale
- Problems encountered and solutions
- Screenshots or output examples
- Timing and metrics
- Post-mortems and learnings

**Benefit:** Concrete examples to reference

### 7. reference/common-patterns.md

**Purpose:** Library of common transformation patterns

**Contents:**

- YAML file modifications (workflows, configs)
- pyproject.toml updates
- package.json modifications
- Regex patterns for common replacements
- Text-based vs YAML-parsing approaches
- Code snippets with explanations

**Benefit:** Quick reference for implementing transformations

### 8. scripts/verify-changes.sh

**Purpose:** Generic verification script template

**Contents:**

- Loop through repos from repos.txt
- Check specific conditions per repo
- Report successes and failures
- Summary statistics

**Benefit:** Standardize post-merge verification

### 9. scripts/tag-repos.sh

**Purpose:** Automated tagging script for manual-version repos

**Contents:**

- Loop through repos needing tags
- Version validation logic
- Tag creation and pushing
- Workflow monitoring
- Error handling

**Benefit:** Automate Phase 5 tagging tasks

## Implementation Priority

If implementing these files:

1. **High Priority** (most useful immediately):

   - templates/transformation-script-template.py
   - templates/EXECUTION_PLAN.md
   - reference/common-patterns.md

2. **Medium Priority** (useful for best practices):

   - templates/test-transformation-template.py
   - templates/README.md
   - templates/PROGRESS.md

3. **Low Priority** (nice to have):

   - reference/workflow-examples.md
   - scripts/verify-changes.sh
   - scripts/tag-repos.sh

## Usage Recommendation

When the Skill is invoked, the agent should:

1. **Always** use SKILL.md as the primary reference
2. **Reference templates** when user starts a new campaign
3. **Reference examples** when user needs concrete patterns
4. **Reference scripts** when automation opportunities exist

Templates should be copied to campaign directories and customized, not used directly.

## Alternative: Inline in SKILL.md

Instead of separate files, these could be included as sections within SKILL.md:

**Pros:**

- Single file to read
- All context immediately available
- Simpler skill structure

**Cons:**

- Very long SKILL.md (could hit token limits)
- Harder to navigate
- Templates harder to copy/customize

**Recommendation:** Keep current structure (separate files for templates/reference) to maintain clarity and usability.
