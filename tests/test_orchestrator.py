from unittest.mock import MagicMock, patch
from pathlib import Path
from runner import TestFailure
from orchestrator import (
    repair_loop,
    format_side_by_side_diff,
    apply_patch,
)


def test_format_side_by_side_diff():
    before = "line 1\nline 2\nline 3"
    after = "line 1\nline 2 modified\nline 3\nline 4"
    diff_output = format_side_by_side_diff(before, after, "sample.py", width=30)

    assert "ORIGINAL (sample.py)" in diff_output
    assert "MODIFIED (sample.py)" in diff_output
    assert "line 1" in diff_output
    assert "line 2 modified" in diff_output
    assert "|" in diff_output


def test_early_exit_on_passing_tests():
    with patch("orchestrator.run_tests", return_value=[]) as mock_run:
        success = repair_loop("dummy_dir")
        assert success is True
        mock_run.assert_called_once_with("dummy_dir")


def test_successful_repair_cycle(tmp_path: Path):
    target_file = tmp_path / "test_calc.py"
    target_file.write_text("def test_div():\n    1 / 0\n", encoding="utf-8")

    fail = TestFailure(
        file_path="test_calc.py",
        line_no=2,
        error_type="ZeroDivisionError",
        message="division by zero",
        raw_trace="Traceback...",
    )

    # First run fails, second run (after patch) passes
    with patch("orchestrator.run_tests", side_effect=[[fail], []]) as mock_run, \
         patch("orchestrator.extract_context", return_value="def test_div():\n    1 / 0") as mock_extract, \
         patch("orchestrator.ground_error", return_value=None) as mock_ground, \
         patch("orchestrator.diagnose_bug", return_value="Zero division. Change denominator.") as mock_diag, \
         patch("orchestrator.generate_patch", return_value="--- a/test_calc.py\n+++ b/test_calc.py\n@@ -2 +2 @@\n- 1 / 0\n+ 1 / 1") as mock_patch, \
         patch("orchestrator.apply_patch", return_value=True) as mock_apply:

        success = repair_loop(str(tmp_path), max_retries=2)
        assert success is True

        assert mock_run.call_count == 2
        mock_extract.assert_called_once()
        mock_ground.assert_called_once_with(fail)
        mock_diag.assert_called_once()
        mock_patch.assert_called_once()
        mock_apply.assert_called_once()


def test_retry_limit_enforced(tmp_path: Path):
    target_file = tmp_path / "test_fail.py"
    target_file.write_text("def test_fail():\n    assert False\n", encoding="utf-8")

    fail = TestFailure(
        file_path="test_fail.py",
        line_no=2,
        error_type="AssertionError",
        message="assert False",
        raw_trace="Traceback...",
    )

    # Always failing: Initial run + 3 checks after patches (initial attempt + 2 retries = 3 patch attempts)
    with patch("orchestrator.run_tests", return_value=[fail]) as mock_run, \
         patch("orchestrator.extract_context", return_value="def test_fail():\n    assert False"), \
         patch("orchestrator.ground_error", return_value=None), \
         patch("orchestrator.diagnose_bug", return_value="Diagnosis"), \
         patch("orchestrator.generate_patch", return_value="--- patch"), \
         patch("orchestrator.apply_patch", return_value=True):

        success = repair_loop(str(tmp_path), max_retries=2)
        assert success is False

        # 1 initial test run + 3 post-patch test runs = 4 total runs
        assert mock_run.call_count == 4
