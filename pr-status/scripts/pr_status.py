#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""PR Status Analyzer — diagnose why a PR can't merge."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# gh CLI wrapper
# ---------------------------------------------------------------------------

def run_gh(*args: str, timeout: int = 30, repo: str | None = None) -> dict | list | str:
    """Run a gh CLI command, return parsed JSON or raw text.

    Raises RuntimeError on non-zero exit or timeout.
    """
    cmd: list[str] = ["gh"]
    if repo:
        cmd.extend(["-R", repo])
    cmd.extend(args)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"gh command timed out after {timeout}s: {' '.join(cmd)}") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"gh failed (exit {result.returncode}): {stderr}")

    text = result.stdout.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def run_gh_api(endpoint: str, *, repo: str | None = None, timeout: int = 30) -> dict | list | str:
    """Call gh api with proper error propagation."""
    cmd = ["gh", "api"]
    if repo:
        cmd.extend(["-H", "Accept: application/vnd.github+json"])
    cmd.append(endpoint)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"gh api timed out after {timeout}s: {endpoint}") from exc

    text = result.stdout.strip()
    parsed = None
    if text:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None

    if result.returncode != 0:
        status_code = None
        if parsed and isinstance(parsed, dict):
            msg = parsed.get("message", "")
            # Try to extract HTTP status from stderr
            m = re.search(r"HTTP (\d{3})", result.stderr)
            if m:
                status_code = int(m.group(1))
            raise RuntimeError(f"gh api failed ({status_code or result.returncode}): {msg}")
        raise RuntimeError(f"gh api failed (exit {result.returncode}): {result.stderr.strip()}")

    return parsed if parsed is not None else text


# ---------------------------------------------------------------------------
# Pure helpers (no gh calls — testable in isolation)
# ---------------------------------------------------------------------------

def parse_pr_identifier(value: str | None, local_repo: str | None = None) -> tuple[str | None, str | None]:
    """Parse a PR identifier into (pr_number_or_empty, repo_override).

    Returns (None, None) to signal "detect from current branch".
    """
    if not value:
        return None, None

    # URL form
    m = re.match(r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", value)
    if m:
        repo_from_url = m.group(1)
        pr_number = m.group(2)
        repo_override = repo_from_url if repo_from_url != local_repo else None
        return pr_number, repo_override

    # Numeric
    if value.isdigit():
        return value, None

    print(f"Error: Cannot parse PR identifier: {value}", file=sys.stderr)
    sys.exit(2)


def classify_bot(login: str) -> bool:
    """Return True if login looks like a bot account.

    Catches GitHub App bots (renovate[bot], dependabot[bot], etc.)
    but not service-account bots using regular user accounts
    (e.g. codecov-commenter). Intentional: suffix check avoids
    maintaining a hardcoded bot list.
    """
    return login.endswith("[bot]")


def extract_run_ids_from_checks(checks: list[dict]) -> list[str]:
    """Extract unique GitHub Actions run IDs from failed check links."""
    run_ids: set[str] = set()
    for check in checks:
        if check.get("bucket") != "fail":
            continue
        link = check.get("link") or ""
        m = re.search(r"/actions/runs/(\d+)", link)
        if m:
            run_ids.add(m.group(1))
    return sorted(run_ids)


def merge_state_message(state: str) -> str:
    """Return an actionable message for a merge state."""
    messages = {
        "DIRTY": "Branch has merge conflicts that need resolution",
        "BEHIND": "Branch is behind base and needs to be updated",
        "BLOCKED": "Merge is blocked by branch protection rules",
        "UNSTABLE": "Some required checks are failing",
        "UNKNOWN": "GitHub is still computing merge status — try again shortly",
    }
    return messages.get(state, f"Merge state: {state}")


def find_error_keywords(body: str) -> list[str]:
    """Return error-related keywords found in a comment body."""
    keyword_patterns: list[tuple[str, str]] = [
        ("error", r"(?i)\berror\b"),
        ("failure", r"(?i)\bfail(?:ed|ure|ing)?\b"),
        ("warning", r"(?i)\bwarn(?:ing)?\b"),
        ("conflict", r"(?i)\bconflict\b"),
        ("deprecated", r"(?i)\bdeprecated?\b"),
        ("vulnerability", r"(?i)\bvulnerabilit(?:y|ies)\b"),
        ("breaking", r"(?i)\bbreaking\b"),
    ]
    found = []
    for label, pat in keyword_patterns:
        if re.search(pat, body):
            found.append(label)
    return found


def is_stale_approval(approval_time_str: str | None, head_commit_time_str: str | None) -> bool:
    """Return True if approval predates the head commit."""
    if not approval_time_str or not head_commit_time_str:
        return False
    try:
        approved = datetime.fromisoformat(approval_time_str.replace("Z", "+00:00"))
        committed = datetime.fromisoformat(head_commit_time_str.replace("Z", "+00:00"))
        return approved < committed
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_detect_repo(_args: argparse.Namespace) -> int:
    """Detect GitHub repo from git remote."""
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or no origin remote", file=sys.stderr)
        return 2

    if "github.com" not in url:
        print(f"Error: Not a GitHub repository (remote: {url})", file=sys.stderr)
        return 2

    m = re.search(r"github\.com[:/]([^/]+)/([^.\s]+?)(?:\.git)?$", url)
    if not m:
        print(f"Error: Cannot parse GitHub URL: {url}", file=sys.stderr)
        return 2

    repo = f"{m.group(1)}/{m.group(2)}"
    print(repo)
    return 0


def _detect_local_repo() -> str | None:
    """Detect local repo silently, return owner/repo or None."""
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None
    m = re.search(r"github\.com[:/]([^/]+)/([^.\s]+?)(?:\.git)?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def _resolve_pr(args: argparse.Namespace) -> tuple[str, str | None]:
    """Resolve PR number and repo from args. Exits on failure."""
    local_repo = _detect_local_repo()
    pr_input = getattr(args, "pr", None)
    pr_number, repo_override = parse_pr_identifier(pr_input, local_repo)
    repo = args.repo or repo_override

    if pr_number is None:
        # Detect from current branch
        try:
            data = run_gh("pr", "view", "--json", "number", repo=repo)
            pr_number = str(data["number"])
        except RuntimeError as exc:
            print(f"Error detecting PR from current branch: {exc}", file=sys.stderr)
            sys.exit(2)

    return pr_number, repo


def cmd_check_cli(_args: argparse.Namespace) -> int:
    """Verify gh auth and repo access."""
    # Check gh exists
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: gh CLI is not installed — https://cli.github.com/", file=sys.stderr)
        return 2

    # Check auth
    try:
        run_gh("auth", "status")
    except RuntimeError:
        print("Error: gh is not authenticated — run: gh auth login", file=sys.stderr)
        return 2

    # Check repo access
    local_repo = _detect_local_repo()
    if local_repo:
        try:
            run_gh("api", f"repos/{local_repo}")
            print(f"Authenticated with access to {local_repo}")
        except RuntimeError:
            login = _get_current_login()
            _handle_access_failure(login, local_repo)
            return 2
    else:
        print("Authenticated (not in a GitHub repository)")

    return 0


def _get_current_login() -> str:
    """Get current gh login."""
    try:
        return run_gh("api", "user", "--jq", ".login")
    except RuntimeError:
        return "unknown"


def _handle_access_failure(login: str, repo: str) -> None:
    """Handle repo access failure with interactive/non-interactive detection."""
    is_interactive = os.isatty(0) and os.isatty(1)
    if is_interactive:
        print(f"Current account '{login}' cannot access '{repo}'", file=sys.stderr)
        print("", file=sys.stderr)
        print("To fix:", file=sys.stderr)
        print("  1. Check accounts: gh auth status", file=sys.stderr)
        print("  2. Switch accounts: gh auth switch", file=sys.stderr)
        print("  3. Or login: gh auth login", file=sys.stderr)
    else:
        print(f"Error: Account '{login}' cannot access '{repo}'", file=sys.stderr)
        print("Run: gh auth switch  or  gh auth login", file=sys.stderr)


def cmd_status(args: argparse.Namespace) -> int:
    """PR metadata: merge state, reviews, draft, checks summary."""
    pr, repo = _resolve_pr(args)
    data = run_gh(
        "pr", "view", pr, "--json",
        "number,title,state,isDraft,mergeable,mergeStateStatus,"
        "reviewDecision,reviewRequests,latestReviews,"
        "headRefName,baseRefName,statusCheckRollup",
        repo=repo,
    )
    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        _print_status_text(data)
    return 0


def _print_status_text(data: dict) -> None:
    """Print human-readable PR status."""
    print(f"PR #{data['number']}: {data['title']}")
    print(f"Branch: {data['headRefName']} -> {data['baseRefName']}")
    print(f"State: {data['state']}", end="")
    if data.get("isDraft"):
        print(" (DRAFT)", end="")
    print()
    print(f"Merge state: {data.get('mergeStateStatus', 'N/A')}")
    print(f"Review decision: {data.get('reviewDecision') or 'NONE'}")

    rollup = data.get("statusCheckRollup") or []
    if rollup:
        states = {}
        for c in rollup:
            s = (c.get("conclusion") or c.get("status") or "PENDING").upper()
            bucket = "pass" if s == "SUCCESS" else "fail" if s == "FAILURE" else "pending"
            states[bucket] = states.get(bucket, 0) + 1
        print(f"Checks: {states.get('pass', 0)} passed, {states.get('fail', 0)} failed, {states.get('pending', 0)} pending")


def cmd_checks(args: argparse.Namespace) -> int:
    """Detailed check results."""
    pr, repo = _resolve_pr(args)
    try:
        checks = run_gh("pr", "checks", pr, "--json", "bucket,name,state,description,link,workflow", repo=repo)
    except RuntimeError:
        checks = []

    if args.format == "json":
        print(json.dumps(checks, indent=2))
        return 0

    if not checks:
        print("No checks found.")
        return 0

    for c in checks:
        bucket = c.get("bucket", "?")
        icon = {"pass": "+", "fail": "X", "pending": "~"}.get(bucket, "?")
        print(f"  [{icon}] {c.get('name', '?')}: {c.get('state', '?')}")
    return 0


def cmd_comments(args: argparse.Namespace) -> int:
    """All PR comments and reviews."""
    pr, repo = _resolve_pr(args)
    data = run_gh(
        "pr", "view", pr, "--json",
        "comments,reviews",
        repo=repo,
    )

    comments = (data.get("comments") or [])[-100:]  # limit to last 100
    reviews = data.get("reviews") or []

    if args.format == "json":
        print(json.dumps({"comments": comments, "reviews": reviews}, indent=2))
        return 0

    if reviews:
        print("=== Reviews ===")
        for r in reviews:
            author = r.get("author", {}).get("login", "?")
            state = r.get("state", "?")
            body = (r.get("body") or "").strip()
            ts = r.get("submittedAt", "")
            print(f"  {author} ({state}) [{ts}]")
            if body:
                for line in body.split("\n")[:5]:
                    print(f"    {line}")
        print()

    if comments:
        print("=== Comments ===")
        for c in comments:
            author = c.get("author", {}).get("login", "?")
            body = (c.get("body") or "").strip()
            ts = c.get("createdAt", "")
            print(f"  {author} [{ts}]")
            if body:
                for line in body.split("\n")[:5]:
                    print(f"    {line}")
    elif not reviews:
        print("No comments or reviews.")
    return 0


def cmd_bot_comments(args: argparse.Namespace) -> int:
    """Filter for bot authors + error keywords."""
    pr, repo = _resolve_pr(args)
    data = run_gh("pr", "view", pr, "--json", "comments", repo=repo)
    comments = (data.get("comments") or [])[-100:]

    bot_comments = []
    for c in comments:
        author = c.get("author", {}).get("login", "")
        if not classify_bot(author):
            continue
        body = (c.get("body") or "").strip()
        keywords = find_error_keywords(body)
        bot_comments.append({
            "author": author,
            "createdAt": c.get("createdAt", ""),
            "error_keywords": keywords,
            "body_preview": body[:300],
        })

    if args.format == "json":
        print(json.dumps(bot_comments, indent=2))
        return 0

    if not bot_comments:
        print("No bot comments found.")
        return 0

    print(f"Found {len(bot_comments)} bot comment(s):")
    for bc in bot_comments:
        kw = ", ".join(bc["error_keywords"]) if bc["error_keywords"] else "none"
        print(f"  {bc['author']} [{bc['createdAt']}] error keywords: {kw}")
        if bc["error_keywords"]:
            preview = bc["body_preview"].replace("\n", " ")[:120]
            print(f"    {preview}...")
    return 0


def cmd_failed_runs(args: argparse.Namespace) -> int:
    """Extract run IDs from failed checks."""
    pr, repo = _resolve_pr(args)
    try:
        checks = run_gh("pr", "checks", pr, "--json", "bucket,link", repo=repo)
    except RuntimeError:
        checks = []

    run_ids = extract_run_ids_from_checks(checks)
    if args.format == "json":
        print(json.dumps(run_ids))
    else:
        if run_ids:
            print(" ".join(run_ids))
        else:
            print("No failed runs found.")
    return 0


def cmd_analyze_logs(args: argparse.Namespace) -> int:
    """Download and pattern-match failed CI logs."""
    run_id = args.run_id
    repo = args.repo

    try:
        logs = run_gh("run", "view", run_id, "--log-failed", repo=repo, timeout=60)
    except RuntimeError as exc:
        print(f"Error fetching logs: {exc}", file=sys.stderr)
        return 2

    if not logs:
        print("No failed logs found (run may have succeeded or be in progress).")
        return 0

    # Truncate to 500 lines per conceptual block
    lines = str(logs).split("\n")[:500]
    log_text = "\n".join(lines)
    print(log_text)

    # Pattern matching
    patterns = {
        "Permission denied": r"(?i)permission denied",
        "Command not found": r"(?i)command not found",
        "Missing file/directory": r"(?i)no such file or directory",
        "Test failures": r"(?i)(test.*fail|fail.*test|assertion.*error)",
        "Syntax/parse error": r"(?i)(syntax.*error|parse.*error)",
        "Timeout": r"(?i)(timeout|timed out)",
        "Out of memory": r"(?i)(out of memory|oom)",
        "Network error": r"(?i)(connection.*refused|connection.*timeout|network.*error)",
    }
    print("\n=== Error Patterns ===")
    found_any = False
    for label, pat in patterns.items():
        if re.search(pat, log_text):
            print(f"  Found: {label}")
            found_any = True
    if not found_any:
        print("  No common patterns matched — review logs above.")
    return 0


def cmd_required_checks(args: argparse.Namespace) -> int:
    """Fetch branch protection required status checks."""
    pr, repo = _resolve_pr(args)

    # Get base branch
    pr_data = run_gh("pr", "view", pr, "--json", "baseRefName", repo=repo)
    base_branch = pr_data["baseRefName"]
    effective_repo = repo or _detect_local_repo()
    if not effective_repo:
        print("Error: Cannot determine repository", file=sys.stderr)
        return 2

    required = _fetch_required_checks(effective_repo, base_branch)
    if required is None:
        return 0  # already printed info message

    if args.format == "json":
        print(json.dumps(required, indent=2))
    else:
        if required:
            print(f"Required checks for {base_branch}:")
            for name in required:
                print(f"  - {name}")
        else:
            print(f"No required status checks configured for {base_branch}.")
    return 0


def _fetch_required_checks(repo: str, branch: str) -> list[str] | None:
    """Fetch required status check names. Returns None if no protection."""
    encoded_branch = branch.replace("/", "%2F")
    owner, repo_name = repo.split("/")

    # Try legacy branch protection API
    try:
        data = run_gh_api(
            f"repos/{owner}/{repo_name}/branches/{encoded_branch}/protection/required_status_checks",
        )
        if isinstance(data, dict):
            contexts = data.get("contexts") or []
            checks = data.get("checks") or []
            names = list(set(contexts + [c.get("context", "") for c in checks]))
            return [n for n in names if n]
    except RuntimeError as exc:
        err_str = str(exc)
        if "404" in err_str:
            # Try rulesets API as fallback
            return _fetch_required_checks_rulesets(owner, repo_name, branch)
        if "403" in err_str:
            print(
                "Warning: Insufficient permissions to read branch protection. "
                "Fix with: gh auth refresh -s repo",
                file=sys.stderr,
            )
            return None
        raise

    return []


def _fetch_required_checks_rulesets(owner: str, repo_name: str, branch: str) -> list[str] | None:
    """Try repository rulesets API for required checks."""
    try:
        rulesets = run_gh_api(f"repos/{owner}/{repo_name}/rulesets")
    except RuntimeError:
        # No branch protection at all
        print(f"Info: No branch protection configured for {branch}.")
        return None

    if not isinstance(rulesets, list):
        print(f"Info: No branch protection configured for {branch}.")
        return None

    required_names: set[str] = set()
    for ruleset in rulesets:
        rs_id = ruleset.get("id")
        if not rs_id:
            continue
        try:
            detail = run_gh_api(f"repos/{owner}/{repo_name}/rulesets/{rs_id}")
        except RuntimeError:
            continue
        rules = detail.get("rules") or []
        for rule in rules:
            if rule.get("type") == "required_status_checks":
                params = rule.get("parameters") or {}
                for check in params.get("required_status_checks") or []:
                    name = check.get("context") or ""
                    if name:
                        required_names.add(name)

    if not required_names:
        print(f"Info: No required status checks found in rulesets for {branch}.")
        return None

    return sorted(required_names)


def cmd_missing_checks(args: argparse.Namespace) -> int:
    """Compare required vs actual checks, report absent ones."""
    pr, repo = _resolve_pr(args)

    # Get base branch + actual checks
    pr_data = run_gh("pr", "view", pr, "--json", "baseRefName", repo=repo)
    base_branch = pr_data["baseRefName"]
    effective_repo = repo or _detect_local_repo()
    if not effective_repo:
        print("Error: Cannot determine repository", file=sys.stderr)
        return 2

    required = _fetch_required_checks(effective_repo, base_branch)
    if required is None:
        return 0

    if not required:
        print("No required status checks configured.")
        return 0

    try:
        checks = run_gh("pr", "checks", pr, "--json", "name", repo=repo)
    except RuntimeError:
        checks = []

    actual_names = {c.get("name", "") for c in checks}
    missing = [r for r in required if r not in actual_names]

    if args.format == "json":
        print(json.dumps({"required": required, "actual": sorted(actual_names), "missing": missing}, indent=2))
    else:
        if missing:
            print(f"Missing required checks ({len(missing)}):")
            for name in missing:
                print(f"  ! {name}")
        else:
            print(f"All {len(required)} required checks are present.")
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    """Full blocker report — the primary command."""
    pr, repo = _resolve_pr(args)
    blockers: list[dict] = []

    # --- Fetch PR data ---
    pr_data = run_gh(
        "pr", "view", pr, "--json",
        "number,title,state,isDraft,mergeable,mergeStateStatus,"
        "reviewDecision,reviewRequests,latestReviews,"
        "headRefName,baseRefName,statusCheckRollup,reviewThreads",
        repo=repo,
    )

    title = pr_data.get("title", "")
    head_ref = pr_data.get("headRefName", "")
    base_ref = pr_data.get("baseRefName", "")
    state = pr_data.get("state", "")

    if args.format != "json":
        print(f"=== PR #{pr}: {title} ===")
        print(f"Branch: {head_ref} -> {base_ref}")
        print(f"State: {state}")
        print()

    # 1. Draft status
    if pr_data.get("isDraft"):
        blockers.append({
            "type": "draft",
            "message": "PR is in draft mode",
            "fix": "Mark as ready for review",
        })

    # 2. Merge state
    merge_state = pr_data.get("mergeStateStatus", "UNKNOWN")
    if merge_state not in ("CLEAN", "HAS_HOOKS"):
        blockers.append({
            "type": "merge_state",
            "state": merge_state,
            "message": merge_state_message(merge_state),
            "fix": {
                "DIRTY": "Resolve merge conflicts",
                "BEHIND": f"Rebase or merge {base_ref} into {head_ref}",
                "BLOCKED": "Satisfy branch protection requirements",
                "UNSTABLE": "Fix failing required checks",
                "UNKNOWN": "Wait for GitHub to recompute — try again shortly",
            }.get(merge_state, "Investigate merge state"),
        })

    # 3. Review decision
    review_decision = pr_data.get("reviewDecision") or ""
    if review_decision == "CHANGES_REQUESTED":
        reviewers = [
            r.get("author", {}).get("login", "?")
            for r in (pr_data.get("latestReviews") or [])
            if r.get("state") == "CHANGES_REQUESTED"
        ]
        blockers.append({
            "type": "review",
            "decision": review_decision,
            "reviewers": reviewers,
            "message": f"Changes requested by: {', '.join(reviewers)}",
            "fix": "Address review feedback and re-request review",
        })
    elif review_decision == "REVIEW_REQUIRED":
        pending = [
            r.get("login") or r.get("name") or r.get("slug") or "?"
            for r in (pr_data.get("reviewRequests") or [])
        ]
        blockers.append({
            "type": "review",
            "decision": review_decision,
            "pending_reviewers": pending,
            "message": f"Review required — pending: {', '.join(pending) or 'unassigned'}",
            "fix": "Request review or wait for pending reviewers",
        })

    # 4. Unresolved review threads
    threads = pr_data.get("reviewThreads") or []
    unresolved = [t for t in threads if not t.get("isResolved", True)]
    if unresolved:
        blockers.append({
            "type": "unresolved_threads",
            "count": len(unresolved),
            "message": f"{len(unresolved)} unresolved review thread(s)",
            "fix": "Resolve all review conversations",
        })

    # 5. Stale approvals
    approvals = [
        r for r in (pr_data.get("latestReviews") or [])
        if r.get("state") == "APPROVED"
    ]
    if approvals:
        # Get head commit date
        try:
            commit_data = run_gh(
                "pr", "view", pr, "--json", "commits", repo=repo,
            )
            commits = commit_data.get("commits") or []
            if commits:
                head_commit_date = commits[-1].get("committedDate") or ""
                stale = [
                    a.get("author", {}).get("login", "?")
                    for a in approvals
                    if is_stale_approval(a.get("submittedAt", ""), head_commit_date)
                ]
                if stale:
                    blockers.append({
                        "type": "stale_approvals",
                        "reviewers": stale,
                        "message": f"Stale approval(s) from: {', '.join(stale)} (pre-date latest push)",
                        "fix": "Re-request review from stale approvers",
                    })
        except RuntimeError:
            pass  # non-critical

    # 6. CI checks
    try:
        checks = run_gh("pr", "checks", pr, "--json", "bucket,name,state,link,workflow", repo=repo)
    except RuntimeError:
        checks = []

    if checks:
        counts = {"pass": 0, "fail": 0, "pending": 0}
        failing_names = []
        pending_names = []
        for c in checks:
            bucket = c.get("bucket", "pending")
            counts[bucket] = counts.get(bucket, 0) + 1
            if bucket == "fail":
                failing_names.append(c.get("name", "?"))
            elif bucket == "pending":
                pending_names.append(c.get("name", "?"))

        if counts["fail"] > 0:
            blockers.append({
                "type": "ci_failure",
                "pass": counts["pass"],
                "fail": counts["fail"],
                "pending": counts["pending"],
                "failing_checks": failing_names,
                "message": f"{counts['fail']} check(s) failing: {', '.join(failing_names)}",
                "fix": "Investigate failing checks — use: failed-runs / analyze-logs",
            })
        elif counts["pending"] > 0:
            blockers.append({
                "type": "ci_pending",
                "pass": counts["pass"],
                "pending": counts["pending"],
                "pending_checks": pending_names,
                "message": f"{counts['pending']} check(s) still pending: {', '.join(pending_names)}",
                "fix": "Wait for pending checks to complete",
            })

    # 7. Missing required checks
    effective_repo = repo or _detect_local_repo()
    if effective_repo:
        required = _fetch_required_checks(effective_repo, base_ref)
        if required:
            actual_names = {c.get("name", "") for c in checks}
            missing = [r for r in required if r not in actual_names]
            if missing:
                blockers.append({
                    "type": "missing_checks",
                    "missing": missing,
                    "message": f"Missing required check(s): {', '.join(missing)}",
                    "fix": "Ensure CI workflows are triggered for this PR",
                })

    # 8. Bot comments with errors
    try:
        comment_data = run_gh("pr", "view", pr, "--json", "comments", repo=repo)
        comments = (comment_data.get("comments") or [])[-100:]
        bot_errors = []
        for c in comments:
            author = c.get("author", {}).get("login", "")
            if not classify_bot(author):
                continue
            body = (c.get("body") or "").strip()
            keywords = find_error_keywords(body)
            if keywords:
                bot_errors.append({"author": author, "keywords": keywords})
        if bot_errors:
            summary = "; ".join(f"{b['author']}: {','.join(b['keywords'])}" for b in bot_errors[:5])
            blockers.append({
                "type": "bot_errors",
                "count": len(bot_errors),
                "details": bot_errors[:5],
                "message": f"{len(bot_errors)} bot comment(s) with errors: {summary}",
                "fix": "Review bot error comments — use: bot-comments",
            })
    except RuntimeError:
        pass  # non-critical

    # --- Output ---
    if args.format == "json":
        result = {
            "pr": int(pr),
            "title": title,
            "state": state,
            "head": head_ref,
            "base": base_ref,
            "blockers": blockers,
            "ready_to_merge": len(blockers) == 0,
        }
        print(json.dumps(result, indent=2))
    else:
        if not blockers:
            print("No blockers found — PR appears ready to merge.")
        else:
            print(f"Found {len(blockers)} blocker(s):\n")
            for i, b in enumerate(blockers, 1):
                print(f"  {i}. [{b['type'].upper()}] {b['message']}")
                print(f"     Fix: {b['fix']}")
            print()
            print("---")
            print("Use subcommands for deeper investigation:")
            print("  failed-runs, analyze-logs, comments, bot-comments, missing-checks")

    return 0 if not blockers else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pr_status",
        description="PR Status Analyzer — diagnose why a PR can't merge",
    )
    parser.add_argument("--repo", help="Repository in owner/repo format")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")

    sub = parser.add_subparsers(dest="command", required=True)

    # diagnose
    p = sub.add_parser("diagnose", help="Full blocker report (primary command)")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # status
    p = sub.add_parser("status", help="PR metadata")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # checks
    p = sub.add_parser("checks", help="Detailed check results")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # comments
    p = sub.add_parser("comments", help="All PR comments and reviews")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # bot-comments
    p = sub.add_parser("bot-comments", help="Bot comments with error keywords")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # failed-runs
    p = sub.add_parser("failed-runs", help="Extract run IDs from failed checks")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # analyze-logs
    p = sub.add_parser("analyze-logs", help="Download and analyze failed CI logs")
    p.add_argument("run_id", help="GitHub Actions run ID")

    # required-checks
    p = sub.add_parser("required-checks", help="Branch protection required checks")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # missing-checks
    p = sub.add_parser("missing-checks", help="Compare required vs actual checks")
    p.add_argument("pr", nargs="?", help="PR number or URL")

    # check-cli
    sub.add_parser("check-cli", help="Verify gh auth and repo access")

    # detect-repo
    sub.add_parser("detect-repo", help="Detect GitHub repo from git remote")

    return parser


COMMANDS = {
    "diagnose": cmd_diagnose,
    "status": cmd_status,
    "checks": cmd_checks,
    "comments": cmd_comments,
    "bot-comments": cmd_bot_comments,
    "failed-runs": cmd_failed_runs,
    "analyze-logs": cmd_analyze_logs,
    "required-checks": cmd_required_checks,
    "missing-checks": cmd_missing_checks,
    "check-cli": cmd_check_cli,
    "detect-repo": cmd_detect_repo,
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    handler = COMMANDS.get(args.command)
    if not handler:
        parser.print_help()
        return 2
    try:
        return handler(args)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
