# AGENTS.md

This file provides guidance to Claude Code when working in this repository.
`CLAUDE.md` is a symlink to this file.

## What This Repo Is

A collection of reusable Claude Code skills. Each top-level directory with a `SKILL.md` is a skill.

## Repo Layout

```text
claude-skills/
├── {skill-name}/
│   ├── SKILL.md       # Skill definition (YAML frontmatter + instructions)
│   ├── reference.md   # Optional reference material
│   └── scripts/       # Optional helper scripts
├── scripts/           # CI validation helpers
├── README.md          # User-facing docs and skill catalog
└── AGENTS.md          # This file (CLAUDE.md symlinks here)
```

## Available Skills

| Category | Skills |
|---|---|
| Decision Records | `init-ai-docs`, `init-central-docs`, `create-plan`, `create-research`, `create-handoff`, `resume-handoff` |
| DevOps & CI/CD | `tatari-turbolift`, `argocd-ops`, `pr-status`, `loki-debug` |
| Code Analysis | `codex` |
| Quality & Review | `convergent-review` |
| Project Management | `jira` |

## Adding a New Skill

1. Create `{skill-name}/SKILL.md` with YAML frontmatter (`name`, `description`)
2. `name` must match the directory name (lowercase, hyphens only)
3. Add helper scripts in `{skill-name}/scripts/` if needed
4. Update the "Available Skills" table in `README.md`

See [README.md](./README.md) for the full creation guide and examples.
