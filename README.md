# Claude Skills

[![CI](https://github.com/stephen-tatari/claude-skills/workflows/CI/badge.svg)](https://github.com/stephen-tatari/claude-skills/actions)

A curated collection of reusable Skills for Claude Code and other AI coding agents.

## What Are Skills?

Skills are modular capabilities that extend AI agent functionality with specialized, reusable features. Each Skill is:

- **Model-invoked**: The agent autonomously decides when to use it based on context
- **Focused**: Handles one specific capability well
- **Portable**: Easy to share via git for team collaboration

## Quick Start

### Install Globally (All Projects)

```bash
# Clone the repository
git clone https://github.com/stephen-tatari/claude-skills.git

# Copy desired skills to your global skills directory
cp -r claude-skills/skill-name ~/.claude/skills/
```

### Install for Specific Project

```bash
# In your project root
mkdir -p .claude/skills

# Copy desired skills
cp -r /path/to/claude-skills/skill-name .claude/skills/

# Commit to version control for team sharing
git add .claude/skills
git commit -m "Add skill-name skill"
```

## Available Skills

- **[tatari-turbolift](tatari-turbolift/)**: Automates Git branch workflows for feature development, releases, and hotfixes using structured naming conventions

## Creating Your Own Skills

Each Skill is a directory containing a `SKILL.md` file with YAML frontmatter. For comprehensive documentation on creating Skills, see [AGENTS.md](AGENTS.md).

Quick example:

```yaml
---
name: your-skill-name
description: Clear explanation of what it does and when to use it
---

# Detailed Instructions

Provide comprehensive instructions here for the AI agent to follow.
```

## Contributing

Contributions are welcome! Please:

1. Follow the structure outlined in [AGENTS.md](AGENTS.md)
2. Ensure your Skill passes CI validation
3. Test the Skill with various prompts
4. Submit a pull request

## Documentation

- [Complete Documentation](AGENTS.md) - Comprehensive guide to creating and using Skills
- [Claude Code Skills Docs](https://docs.claude.com/en/docs/claude-code/skills.md) - Official documentation

## License

MIT License - See [LICENSE](LICENSE) for details.
