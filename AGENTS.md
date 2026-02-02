# Claude Code Skills Repository

This repository contains a collection of reusable Skills for AI coding agents, specifically designed for use with Claude Code.

## Repository Structure

Each subdirectory in this repository represents a single Skill:

```text
claude-skills/
├── skill-name-1/
│   ├── SKILL.md          # Required: Skill definition and instructions
│   ├── reference.md      # Optional: Additional reference material
│   └── scripts/          # Optional: Supporting scripts and templates
├── skill-name-2/
│   └── SKILL.md
└── ...
```

## What Are Skills?

Skills are modular capabilities that extend AI coding agent functionality with specialized, reusable features tailored to specific workflows. They are:

- **Model-invoked**: The agent autonomously decides when to use them based on the user's request and the Skill's description
- **Focused**: Each Skill should handle one specific capability
- **Portable**: Can be shared via git for team collaboration

## Creating a New Skill

### 1. Create a Directory

```bash
mkdir your-skill-name
cd your-skill-name
```

**Naming conventions:**

- Use lowercase letters, numbers, and hyphens only
- Maximum 64 characters
- Be descriptive but concise

### 2. Create SKILL.md

Every Skill requires a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: your-skill-name
description: Clear explanation of what it does and when to use it (max 1024 chars)
---

# Detailed Instructions

Provide comprehensive instructions here for the AI agent to follow when
this Skill is invoked.

## When to Use

Describe the specific scenarios or trigger phrases that should activate
this Skill.

## Implementation Steps

Detail the steps the agent should follow, referencing any supporting
files with relative paths.
```

**Critical Requirements:**

- `name`: Must match directory name, lowercase with hyphens only
- `description`: This is crucial - agents use it to decide when to invoke the Skill
- Use valid YAML syntax (no tabs, proper indentation)
- Write specific, concrete trigger terms in the description

### 3. Add Supporting Files (Optional)

Organize additional resources alongside SKILL.md:

```text
your-skill-name/
├── SKILL.md
├── reference.md           # Reference documentation
├── templates/             # Template files
│   └── config.template
└── scripts/               # Helper scripts
    └── process.py
```

Reference these from SKILL.md using relative paths. Agents load them progressively to manage context efficiently.

### 4. Restrict Tools (Optional)

Limit which tools the agent can use within the Skill by adding `allowed-tools` to frontmatter:

```yaml
---
name: read-only-analyzer
description: Analyzes code without making modifications
allowed-tools: Read, Grep, Glob
---
```

Common tool sets:

- Read-only: `Read, Grep, Glob, Bash`
- File operations: `Read, Write, Edit`
- Full access: Omit `allowed-tools` field

## Best Practices

### Writing Effective Descriptions

The description field is the most important part of your Skill. It determines when agents will use it.

**Good description:**
> "Analyze GitHub Actions workflow files for performance issues, security vulnerabilities, and best practices. Use when troubleshooting CI/CD failures or optimizing build times."

**Poor description:**
> "Helps with GitHub stuff"

### Keep Skills Focused

Each Skill should do one thing well:

- ✅ Good: "Format Python code with black and check with ruff"
- ❌ Too broad: "Handle all Python development tasks"

### Test Your Skills

Test by asking questions that match your description:

- Verify the agent invokes the Skill at appropriate times
- Ensure the instructions are clear and actionable
- Check that supporting files are properly referenced

### Document Thoroughly

Include in SKILL.md:

- Clear purpose and use cases
- Step-by-step instructions
- Examples of expected input/output
- References to supporting files
- Any prerequisites or dependencies

## Using This Repository

### As Project Skills

To use these Skills in a specific project:

1. Copy the `.claude/skills/` structure:

   ```bash
   mkdir -p .claude/skills
   ```

2. Copy desired Skill directories:

   ```bash
   cp -r /path/to/claude-skills/skill-name .claude/skills/
   ```

3. Commit to version control for team sharing

### As Personal Skills

To install Skills globally for all your projects:

```bash
cp -r skill-name ~/.claude/skills/
```

## Decision Record Skills

This repository includes skills for creating decision documentation following the [Decision Records with AI Assistance](https://github.com/stephen-tatari/coding-agent-documentation) convention.

### Workflow

1. **Start a feature**: Run `/create-plan` to document approach before coding
2. **Technical decisions**: Run `/create-research` to capture ADRs
3. **Session breaks**: Run `/create-handoff` to preserve context
4. **Resume work**: Run `/resume-handoff` to continue from where you left off

### Schema

Documents follow a structured schema:

- **Required**: `schema_version`, `date`, `type`, `status`, `topic`
- **Accountability**: `author`, `reviewed_by` (required for plans/research), `ai_assisted`
- **Linking**: `related_pr`, `related_issue`, `superseded_by`
- **Classification**: `tags`, `data_sensitivity`

### Quality Bar

Before committing decision documents:

- Claims linked to sources
- Assumptions explicitly listed
- Alternatives considered (for plans/research)
- Human reviewer attests via `reviewed_by` field
- No secrets or sensitive data

## Reference

For comprehensive documentation on Skills, see:

- [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills.md)
- [Sub-agents Documentation](https://docs.claude.com/en/docs/claude-code/sub-agents.md)

## Contributing

When adding new Skills to this repository:

1. Create a descriptive directory name
2. Include a complete SKILL.md with proper frontmatter
3. Add supporting files if needed
4. Test the Skill with various prompts
5. Document any dependencies or requirements
6. Commit with clear commit messages

## License

This repository is licensed under the MIT License. See LICENSE file for details.
