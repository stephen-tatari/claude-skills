#!/usr/bin/env python3
"""Validate Claude skill directory structure and metadata."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

EXCLUDED_DIRS = {"scripts", "docs"}
VALID_TOOL_NAMES = {
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Grep",
    "Glob",
    "WebFetch",
    "WebSearch",
}
MAX_DESCRIPTION_LENGTH = 1024
MAX_NAME_LENGTH = 64


def iter_skill_dirs(root: Path) -> Iterable[Path]:
    """Yield candidate skill directories under the given root."""
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        if path.name in EXCLUDED_DIRS:
            continue
        yield path


def validate_skill(skill_dir: Path, *, errors: list[str], warnings: list[str]) -> None:
    """Validate a single skill directory and collect errors/warnings."""
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    print(f"\n🔍 Checking {skill_name}/")

    if not skill_md.exists():
        errors.append(f"❌ {skill_name}/: Missing required SKILL.md file")
        return

    try:
        content = skill_md.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"❌ {skill_name}/SKILL.md: Error reading file: {exc}")
        return

    if not content.startswith("---"):
        errors.append(f"❌ {skill_name}/SKILL.md: Missing YAML frontmatter (must start with ---)")
        return

    parts = content.split("---", 2)
    if len(parts) < 3:
        errors.append(f"❌ {skill_name}/SKILL.md: Invalid YAML frontmatter (must be enclosed in ---)")
        return

    frontmatter = parts[1].strip()

    try:
        metadata = yaml.safe_load(frontmatter) or {}
    except yaml.YAMLError as exc:
        errors.append(f"❌ {skill_name}/SKILL.md: Invalid YAML syntax: {exc}")
        return

    if "name" not in metadata:
        errors.append(f"❌ {skill_name}/SKILL.md: Missing required 'name' field in frontmatter")
        return

    if "description" not in metadata:
        errors.append(f"❌ {skill_name}/SKILL.md: Missing required 'description' field in frontmatter")
        return

    yaml_name = metadata["name"]
    if yaml_name != skill_name:
        errors.append(
            f"❌ {skill_name}/SKILL.md: Name field '{yaml_name}' doesn't match directory name '{skill_name}'"
        )

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", skill_name):
        errors.append(
            f"❌ {skill_name}/: Invalid directory name (must be lowercase letters, numbers, and hyphens only)"
        )

    if len(skill_name) > MAX_NAME_LENGTH:
        errors.append(f"❌ {skill_name}/: Directory name exceeds {MAX_NAME_LENGTH} characters")

    description = metadata["description"]
    if len(description) > MAX_DESCRIPTION_LENGTH:
        warnings.append(f"⚠️  {skill_name}/: Description exceeds recommended {MAX_DESCRIPTION_LENGTH} characters")

    allowed_tools = metadata.get("allowed-tools")
    if isinstance(allowed_tools, str):
        tools = [tool.strip() for tool in allowed_tools.split(",")]
        for tool in tools:
            if tool and tool not in VALID_TOOL_NAMES:
                warnings.append(f"⚠️  {skill_name}/: Unknown tool '{tool}' in allowed-tools")

    print("  ✅ Valid structure")


def run(root: Path) -> int:
    """Run validations for all skills under the given root."""
    errors: list[str] = []
    warnings: list[str] = []

    skill_dirs = list(iter_skill_dirs(root))
    if not skill_dirs:
        print("No skill directories found")
        return 0

    for skill_dir in skill_dirs:
        validate_skill(skill_dir, errors=errors, warnings=warnings)

    print("\n" + "=" * 60)
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(warning)

    if errors:
        print("\nErrors:")
        for error in errors:
            print(error)
        print(f"\n❌ Validation failed with {len(errors)} error(s)")
        return 1

    print("\n✅ All skills validated successfully!")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Claude skill directories.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Root directory to scan (defaults to current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return run(args.root.resolve())


if __name__ == "__main__":
    sys.exit(main())
