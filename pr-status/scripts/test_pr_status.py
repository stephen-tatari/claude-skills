#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = ["pytest"]
# ///
"""Tests for pr_status pure functions."""

from __future__ import annotations

import pytest

from unittest.mock import patch

from pr_status import (
    build_parser,
    classify_bot,
    cmd_analyze_logs,
    extract_error_annotations,
    extract_run_ids_from_checks,
    extract_test_summary,
    filter_noise_lines,
    find_error_keywords,
    is_stale_approval,
    merge_state_message,
    parse_pr_identifier,
    truncate_log_lines,
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

    def test_url_with_files_suffix(self):
        pr, repo = parse_pr_identifier(
            "https://github.com/o/r/pull/123/files",
        )
        assert pr == "123"
        assert repo == "o/r"

    def test_url_with_query_string(self):
        pr, repo = parse_pr_identifier(
            "https://github.com/o/r/pull/123?diff=unified",
        )
        assert pr == "123"
        assert repo == "o/r"

    def test_url_with_trailing_slash(self):
        pr, repo = parse_pr_identifier(
            "https://github.com/o/r/pull/123/",
        )
        assert pr == "123"
        assert repo == "o/r"

    def test_issue_url_exits(self):
        """Issue URLs are not PR URLs — should reject."""
        with pytest.raises(SystemExit) as exc_info:
            parse_pr_identifier("https://github.com/o/r/issues/123")
        assert exc_info.value.code == 2

    def test_whitespace_padded_number_exits(self):
        """Leading/trailing whitespace on a number is not a valid identifier."""
        with pytest.raises(SystemExit) as exc_info:
            parse_pr_identifier(" 42 ")
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

    def test_numeric_sort_not_lexicographic(self):
        """Run IDs sort numerically: 2 before 10, not "10" before "2"."""
        checks = [
            {"bucket": "fail", "link": "https://github.com/o/r/actions/runs/10"},
            {"bucket": "fail", "link": "https://github.com/o/r/actions/runs/2"},
        ]
        assert extract_run_ids_from_checks(checks) == ["2", "10"]

    def test_ignores_pending_bucket_with_actions_link(self):
        """Only 'fail' bucket checks are extracted, even if link is valid."""
        checks = [
            {"bucket": "pending", "link": "https://github.com/o/r/actions/runs/999"},
        ]
        assert extract_run_ids_from_checks(checks) == []


# ---------------------------------------------------------------------------
# merge_state_message
# ---------------------------------------------------------------------------

class TestMergeStateMessage:
    def test_dirty(self):
        assert merge_state_message("DIRTY") == "Branch has merge conflicts that need resolution"

    def test_behind(self):
        assert merge_state_message("BEHIND") == "Branch is behind base and needs to be updated"

    def test_blocked(self):
        assert merge_state_message("BLOCKED") == "Merge is blocked by branch protection rules"

    def test_unstable(self):
        assert merge_state_message("UNSTABLE") == "Some required checks are failing"

    def test_unknown(self):
        assert merge_state_message("UNKNOWN") == "GitHub is still computing merge status — try again shortly"

    def test_unmapped_state_includes_state_name(self):
        msg = merge_state_message("SOMETHING_NEW")
        assert "SOMETHING_NEW" in msg

    def test_clean_not_in_map(self):
        """CLEAN is not an error state, so it falls through to default."""
        msg = merge_state_message("CLEAN")
        assert "CLEAN" in msg

    def test_has_hooks_not_in_map(self):
        msg = merge_state_message("HAS_HOOKS")
        assert "HAS_HOOKS" in msg


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
        assert "conflict" in find_error_keywords("Merge conflict detected")

    def test_finds_conflicts_plural(self):
        assert "conflict" in find_error_keywords("Merge conflicts detected")

    def test_no_keywords(self):
        assert find_error_keywords("All good, no problems here") == []

    def test_empty_body(self):
        assert find_error_keywords("") == []

    def test_case_insensitive(self):
        assert "warning" in find_error_keywords("WARNING: something")

    def test_multiple_keywords_in_defined_order(self):
        """When multiple keywords match, they appear in definition order."""
        kw = find_error_keywords("Error: build failed with conflict and warning")
        assert kw == ["error", "failure", "warning", "conflict"]

    def test_no_duplicates_on_repeated_matches(self):
        """Each keyword appears at most once even if the word appears multiple times."""
        kw = find_error_keywords("error error error")
        assert kw.count("error") == 1

    def test_word_boundary_no_false_positive_terror(self):
        """'terror' should not trigger 'error' due to word boundary."""
        assert find_error_keywords("reign of terror") == []

    def test_word_boundary_no_false_positive_warning_substring(self):
        """'forewarning' should not trigger 'warning' due to word boundary."""
        assert find_error_keywords("a forewarning sign") == []

    def test_deprecated_singular_and_trailing_d(self):
        assert "deprecated" in find_error_keywords("This API is deprecated")
        assert "deprecated" in find_error_keywords("deprecate this function")


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
        assert is_stale_approval("2025-01-01T10:00:00Z", None) is False
        assert is_stale_approval(None, None) is False

    def test_timezone_offsets_equivalent_not_stale(self):
        """Same instant expressed in different timezones should not be stale."""
        assert is_stale_approval(
            "2025-01-02T12:00:00+02:00",
            "2025-01-02T10:00:00Z",
        ) is False

    def test_timezone_offsets_stale(self):
        """Earlier instant in positive offset is still stale."""
        assert is_stale_approval(
            "2025-01-01T10:00:00+02:00",
            "2025-01-02T10:00:00Z",
        ) is True

    def test_fractional_seconds(self):
        assert is_stale_approval(
            "2025-01-01T10:00:00.123Z",
            "2025-01-02T10:00:00.456Z",
        ) is True


# ---------------------------------------------------------------------------
# build_parser
# ---------------------------------------------------------------------------

class TestBuildParser:
    def test_requires_subcommand(self):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args([])
        assert exc_info.value.code == 2

    def test_analyze_logs_requires_run_id(self):
        parser = build_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["analyze-logs"])
        assert exc_info.value.code == 2

    def test_diagnose_accepts_optional_pr(self):
        parser = build_parser()
        args = parser.parse_args(["diagnose"])
        assert args.command == "diagnose"
        assert args.pr is None

    def test_diagnose_accepts_pr_number(self):
        parser = build_parser()
        args = parser.parse_args(["diagnose", "123"])
        assert args.pr == "123"

    def test_global_repo_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--repo", "org/repo", "status", "42"])
        assert args.repo == "org/repo"
        assert args.command == "status"

    def test_subcommand_format_flag(self):
        parser = build_parser()
        args = parser.parse_args(["checks", "--format", "json"])
        assert args.format == "json"

    def test_format_flag_with_pr_url(self):
        parser = build_parser()
        args = parser.parse_args(["diagnose", "--format", "json", "https://github.com/o/r/pull/1"])
        assert args.format == "json"
        assert args.pr == "https://github.com/o/r/pull/1"

    def test_format_default_is_text(self):
        parser = build_parser()
        args = parser.parse_args(["diagnose"])
        assert args.format == "text"

    def test_analyze_logs_accepts_optional_pr(self):
        parser = build_parser()
        args = parser.parse_args(["analyze-logs", "12345", "https://github.com/org/repo/pull/99"])
        assert args.run_id == "12345"
        assert args.pr == "https://github.com/org/repo/pull/99"

    def test_analyze_logs_run_id_only(self):
        parser = build_parser()
        args = parser.parse_args(["analyze-logs", "12345"])
        assert args.run_id == "12345"
        assert args.pr is None


# ---------------------------------------------------------------------------
# truncate_log_lines
# ---------------------------------------------------------------------------

class TestTruncateLogLines:
    def test_short_logs_returned_unchanged(self):
        lines = [f"line {i}" for i in range(50)]
        result = truncate_log_lines(lines)
        assert result == lines

    def test_long_logs_keep_head_and_tail(self):
        lines = [f"line {i}" for i in range(1000)]
        result = truncate_log_lines(lines)
        # First 100 lines preserved
        assert result[0] == "line 0"
        assert result[99] == "line 99"
        # Separator with count
        assert result[100] == "--- 500 lines truncated ---"
        # Last 400 lines preserved
        assert result[-1] == "line 999"
        assert result[-400] == "line 600"

    def test_exactly_500_lines_no_truncation(self):
        lines = [f"line {i}" for i in range(500)]
        result = truncate_log_lines(lines)
        assert result == lines

    def test_501_lines_triggers_truncation(self):
        lines = [f"line {i}" for i in range(501)]
        result = truncate_log_lines(lines)
        assert len(result) == 501  # 100 + 1 separator + 400

    def test_empty_input(self):
        assert truncate_log_lines([]) == []

    def test_tail_zero_returns_head_only(self):
        lines = [f"line {i}" for i in range(200)]
        result = truncate_log_lines(lines, head=50, tail=0)
        assert len(result) == 51  # 50 head + 1 separator
        assert result[0] == "line 0"
        assert result[49] == "line 49"
        assert "150 lines truncated" in result[50]

    def test_head_zero_returns_tail_only(self):
        lines = [f"line {i}" for i in range(200)]
        result = truncate_log_lines(lines, head=0, tail=50)
        assert len(result) == 51  # 1 separator + 50 tail
        assert "150 lines truncated" in result[0]
        assert result[-1] == "line 199"


# ---------------------------------------------------------------------------
# cmd_analyze_logs — repo resolution
# ---------------------------------------------------------------------------

class TestCmdAnalyzeLogsRepoResolution:
    """Verify that cmd_analyze_logs passes the correct repo to run_gh."""

    def _make_args(self, run_id: str, pr: str | None = None, repo: str | None = None):
        parser = build_parser()
        argv = []
        if repo:
            argv.extend(["--repo", repo])
        argv.extend(["analyze-logs", run_id])
        if pr:
            argv.append(pr)
        return parser.parse_args(argv)

    @patch("pr_status.run_gh", return_value="some log output")
    @patch("pr_status._detect_local_repo", return_value="local/repo")
    def test_pr_url_extracts_cross_repo(self, mock_local, mock_gh):
        """PR URL from a different repo should override local repo."""
        args = self._make_args("789", pr="https://github.com/org/other/pull/42")
        cmd_analyze_logs(args)
        mock_gh.assert_called_once_with(
            "run", "view", "789", "--log-failed", repo="org/other", timeout=60,
        )

    @patch("pr_status.run_gh", return_value="some log output")
    @patch("pr_status._detect_local_repo", return_value="local/repo")
    def test_repo_flag_takes_priority(self, mock_local, mock_gh):
        """--repo flag should take priority over PR URL extraction."""
        args = self._make_args("789", pr="https://github.com/org/other/pull/42", repo="flag/repo")
        cmd_analyze_logs(args)
        mock_gh.assert_called_once_with(
            "run", "view", "789", "--log-failed", repo="flag/repo", timeout=60,
        )

    @patch("pr_status.run_gh", return_value="some log output")
    @patch("pr_status._detect_local_repo", return_value="local/repo")
    def test_no_pr_no_flag_falls_back_to_local(self, mock_local, mock_gh):
        """No --repo, no PR URL should fall back to local repo detection."""
        args = self._make_args("789")
        cmd_analyze_logs(args)
        mock_gh.assert_called_once_with(
            "run", "view", "789", "--log-failed", repo="local/repo", timeout=60,
        )

    @patch("pr_status.run_gh", return_value="some log output")
    @patch("pr_status._detect_local_repo", return_value=None)
    def test_no_pr_no_flag_no_local_passes_none(self, mock_local, mock_gh):
        """No repo context at all should pass None (gh uses CWD)."""
        args = self._make_args("789")
        cmd_analyze_logs(args)
        mock_gh.assert_called_once_with(
            "run", "view", "789", "--log-failed", repo=None, timeout=60,
        )


# ---------------------------------------------------------------------------
# filter_noise_lines
# ---------------------------------------------------------------------------

class TestFilterNoiseLines:
    def test_removes_group_markers(self):
        lines = [
            "##[group]Run actions/checkout@v4",
            "actual content",
            "##[endgroup]",
        ]
        result = filter_noise_lines(lines)
        assert result == ["actual content"]

    def test_removes_debug_lines(self):
        lines = ["##[debug]Some debug info", "real output"]
        result = filter_noise_lines(lines)
        assert result == ["real output"]

    def test_removes_action_downloads(self):
        lines = [
            "Download action repository 'actions/checkout@v4' (SHA:abc123)",
            "real output",
        ]
        result = filter_noise_lines(lines)
        assert result == ["real output"]

    def test_removes_cache_restored(self):
        lines = ["Cache restored from key: linux-pip-abc123", "test output"]
        result = filter_noise_lines(lines)
        assert result == ["test output"]

    def test_removes_progress_indicators(self):
        lines = [
            "Receiving objects:  45% (100/222)",
            "Resolving deltas:  100% (50/50)",
            "actual output",
        ]
        result = filter_noise_lines(lines)
        assert result == ["actual output"]

    def test_removes_runner_version(self):
        lines = [
            "Runner version 2.321.0",
            "Operating System",
            "actual content",
        ]
        result = filter_noise_lines(lines)
        assert result == ["actual content"]

    def test_preserves_error_lines(self):
        lines = [
            "##[group]Run tests",
            "##[error]Process completed with exit code 1",
            "##[endgroup]",
            "FAILED tests/test_foo.py::test_bar",
        ]
        result = filter_noise_lines(lines)
        assert "##[error]Process completed with exit code 1" in result
        assert "FAILED tests/test_foo.py::test_bar" in result

    def test_empty_input(self):
        assert filter_noise_lines([]) == []

    def test_all_noise_returns_empty(self):
        lines = [
            "##[group]Setup",
            "##[endgroup]",
            "##[debug]foo",
        ]
        assert filter_noise_lines(lines) == []


# ---------------------------------------------------------------------------
# extract_error_annotations
# ---------------------------------------------------------------------------

class TestExtractErrorAnnotations:
    def test_extracts_error_with_context(self):
        lines = [
            "line 0",
            "line 1",
            "line 2",
            "##[error]Something failed",
            "line 4",
            "line 5",
            "line 6",
        ]
        result = extract_error_annotations(lines)
        assert "##[error]Something failed" in result
        # Context lines before
        assert "line 1" in result
        assert "line 2" in result
        # Context lines after
        assert "line 4" in result
        assert "line 5" in result

    def test_no_errors_returns_empty(self):
        lines = ["all good", "no problems"]
        assert extract_error_annotations(lines) == []

    def test_multiple_errors_merged_context(self):
        lines = [f"line {i}" for i in range(10)]
        lines[3] = "##[error]first error"
        lines[5] = "##[error]second error"
        result = extract_error_annotations(lines)
        assert "##[error]first error" in result
        assert "##[error]second error" in result

    def test_error_at_start(self):
        lines = ["##[error]fail", "line 1", "line 2"]
        result = extract_error_annotations(lines)
        assert "##[error]fail" in result

    def test_error_at_end(self):
        lines = ["line 0", "line 1", "##[error]fail"]
        result = extract_error_annotations(lines)
        assert "##[error]fail" in result

    def test_empty_input(self):
        assert extract_error_annotations([]) == []


# ---------------------------------------------------------------------------
# extract_test_summary
# ---------------------------------------------------------------------------

class TestExtractTestSummary:
    def test_extracts_pytest_failures_section(self):
        lines = [
            "collecting ...",
            "=== FAILURES ===",
            "FAILED test_foo.py::test_bar - AssertionError",
            "=== short test summary info ===",
            "FAILED test_foo.py::test_bar",
            "=== 1 failed, 5 passed ===",
            "more stuff",
        ]
        result = extract_test_summary(lines)
        assert "FAILED test_foo.py::test_bar" in result

    def test_extracts_failed_lines(self):
        lines = [
            "some output",
            "FAILED tests/test_a.py::test_one",
            "FAILED tests/test_b.py::test_two",
            "more output",
        ]
        result = extract_test_summary(lines)
        assert "FAILED tests/test_a.py::test_one" in result
        assert "FAILED tests/test_b.py::test_two" in result

    def test_extracts_assertion_errors(self):
        lines = [
            "normal line",
            "AssertionError: expected 1 got 2",
            "normal line",
        ]
        result = extract_test_summary(lines)
        assert any("AssertionError" in l for l in result)

    def test_no_test_output(self):
        lines = ["all good", "nothing failed"]
        assert extract_test_summary(lines) == []

    def test_empty_input(self):
        assert extract_test_summary([]) == []

    def test_extracts_generic_error_fail_lines(self):
        lines = [
            "normal output",
            "ERROR tests/test_foo.py::test_bar",
            "normal output",
        ]
        result = extract_test_summary(lines)
        assert any("ERROR" in l for l in result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
