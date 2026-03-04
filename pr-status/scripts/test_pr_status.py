#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["pytest"]
# ///
"""Tests for pr_status pure functions."""

from __future__ import annotations

import pytest

from pr_status import (
    classify_bot,
    extract_run_ids_from_checks,
    find_error_keywords,
    is_stale_approval,
    merge_state_message,
    parse_pr_identifier,
)


# ---------------------------------------------------------------------------
# parse_pr_identifier
# ---------------------------------------------------------------------------

class TestParsePrIdentifier:
    def test_none_returns_none(self):
        pr, repo = parse_pr_identifier(None)
        assert pr is None
        assert repo is None

    def test_empty_string_returns_none(self):
        pr, repo = parse_pr_identifier("")
        assert pr is None
        assert repo is None

    def test_numeric_string(self):
        pr, repo = parse_pr_identifier("42")
        assert pr == "42"
        assert repo is None

    def test_url_same_repo(self):
        pr, repo = parse_pr_identifier(
            "https://github.com/acme/widgets/pull/99",
            local_repo="acme/widgets",
        )
        assert pr == "99"
        assert repo is None  # no override needed

    def test_url_cross_repo(self):
        pr, repo = parse_pr_identifier(
            "https://github.com/acme/widgets/pull/99",
            local_repo="acme/other",
        )
        assert pr == "99"
        assert repo == "acme/widgets"

    def test_url_no_local_repo(self):
        pr, repo = parse_pr_identifier(
            "https://github.com/acme/widgets/pull/7",
            local_repo=None,
        )
        assert pr == "7"
        assert repo == "acme/widgets"

    def test_url_with_http(self):
        pr, repo = parse_pr_identifier(
            "http://github.com/org/repo/pull/1",
        )
        assert pr == "1"
        assert repo == "org/repo"

    def test_invalid_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            parse_pr_identifier("not-a-pr")
        assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# classify_bot
# ---------------------------------------------------------------------------

class TestClassifyBot:
    def test_github_app_bot(self):
        assert classify_bot("renovate[bot]") is True

    def test_dependabot(self):
        assert classify_bot("dependabot[bot]") is True

    def test_github_actions_bot(self):
        assert classify_bot("github-actions[bot]") is True

    def test_regular_user(self):
        assert classify_bot("octocat") is False

    def test_service_account_no_suffix(self):
        assert classify_bot("codecov-commenter") is False

    def test_empty_string(self):
        assert classify_bot("") is False

    def test_partial_match(self):
        assert classify_bot("bot") is False
        assert classify_bot("[bot]extra") is False


# ---------------------------------------------------------------------------
# extract_run_ids_from_checks
# ---------------------------------------------------------------------------

class TestExtractRunIds:
    def test_extracts_from_failed_checks(self):
        checks = [
            {"bucket": "fail", "link": "https://github.com/o/r/actions/runs/12345/jobs/99"},
            {"bucket": "fail", "link": "https://github.com/o/r/actions/runs/67890"},
            {"bucket": "pass", "link": "https://github.com/o/r/actions/runs/11111"},
        ]
        assert extract_run_ids_from_checks(checks) == ["12345", "67890"]

    def test_deduplicates(self):
        checks = [
            {"bucket": "fail", "link": "https://github.com/o/r/actions/runs/12345/jobs/1"},
            {"bucket": "fail", "link": "https://github.com/o/r/actions/runs/12345/jobs/2"},
        ]
        assert extract_run_ids_from_checks(checks) == ["12345"]

    def test_no_link(self):
        checks = [{"bucket": "fail", "link": None}]
        assert extract_run_ids_from_checks(checks) == []

    def test_non_actions_link(self):
        checks = [{"bucket": "fail", "link": "https://app.codecov.io/gh/o/r/pull/1"}]
        assert extract_run_ids_from_checks(checks) == []

    def test_empty_list(self):
        assert extract_run_ids_from_checks([]) == []


# ---------------------------------------------------------------------------
# merge_state_message
# ---------------------------------------------------------------------------

class TestMergeStateMessage:
    def test_known_states(self):
        assert "conflict" in merge_state_message("DIRTY").lower()
        assert "behind" in merge_state_message("BEHIND").lower()
        assert "blocked" in merge_state_message("BLOCKED").lower()
        assert "failing" in merge_state_message("UNSTABLE").lower()
        assert "computing" in merge_state_message("UNKNOWN").lower()

    def test_unknown_state_passthrough(self):
        msg = merge_state_message("SOMETHING_NEW")
        assert "SOMETHING_NEW" in msg


# ---------------------------------------------------------------------------
# find_error_keywords
# ---------------------------------------------------------------------------

class TestFindErrorKeywords:
    def test_finds_error(self):
        assert "error" in find_error_keywords("Something threw an Error here")

    def test_finds_failure(self):
        kw = find_error_keywords("Build failed with 3 errors")
        assert "failure" in kw

    def test_finds_vulnerability(self):
        kw = find_error_keywords("Found 2 vulnerabilities")
        assert "vulnerability" in kw

    def test_finds_conflict(self):
        kw = find_error_keywords("Merge conflict detected")
        assert any("conflict" in k for k in kw)

    def test_no_keywords(self):
        assert find_error_keywords("All good, no problems here") == []

    def test_empty_body(self):
        assert find_error_keywords("") == []

    def test_case_insensitive(self):
        assert len(find_error_keywords("WARNING: something")) > 0


# ---------------------------------------------------------------------------
# is_stale_approval
# ---------------------------------------------------------------------------

class TestIsStaleApproval:
    def test_stale(self):
        assert is_stale_approval(
            "2025-01-01T10:00:00Z",
            "2025-01-02T10:00:00Z",
        ) is True

    def test_not_stale(self):
        assert is_stale_approval(
            "2025-01-03T10:00:00Z",
            "2025-01-02T10:00:00Z",
        ) is False

    def test_same_time(self):
        assert is_stale_approval(
            "2025-01-02T10:00:00Z",
            "2025-01-02T10:00:00Z",
        ) is False

    def test_invalid_dates(self):
        assert is_stale_approval("not-a-date", "2025-01-02T10:00:00Z") is False
        assert is_stale_approval("2025-01-01T10:00:00Z", "") is False

    def test_none_values(self):
        assert is_stale_approval(None, "2025-01-02T10:00:00Z") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
