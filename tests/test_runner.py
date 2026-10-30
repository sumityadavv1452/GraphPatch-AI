import subprocess
from pathlib import Path
from runner import TestFailure, parse_failures, run_tests, run_pytest


def test_parse_failures_synthetic():
    sample_output = """
FFF                                                                      [100%]
================================== FAILURES ===================================
_________________________________ test_assert _________________________________
tests/test_math.py:12: in test_assert
    assert 1 == 2
E   assert 1 == 2
_____________________________ test_custom_assert ______________________________
tests/test_math.py:18: in test_custom_assert
    raise AssertionError("expected greater")
E   AssertionError: expected greater
_________________________________ test_divide _________________________________
tests/test_math.py:25: in test_divide
    divide(10, 0)
src/calculator.py:7: in divide
    return a / b
E   ZeroDivisionError: division by zero
=========================== short test summary info ===========================
FAILED tests/test_math.py::test_assert - assert 1 == 2
FAILED tests/test_math.py::test_custom_assert - AssertionError: expected greater
FAILED tests/test_math.py::test_divide - ZeroDivisionError: division by zero
3 failed in 0.05s
"""
    failures = parse_failures(sample_output)
    assert len(failures) == 3

    assert failures[0].file_path == "tests/test_math.py"
    assert failures[0].line_no == 12
    assert failures[0].error_type == "AssertionError"
    assert failures[0].message == "assert 1 == 2"
    assert "assert 1 == 2" in failures[0].raw_trace

    assert failures[1].file_path == "tests/test_math.py"
    assert failures[1].line_no == 18
    assert failures[1].error_type == "AssertionError"
    assert failures[1].message == "expected greater"

    # Nested stack frame: must pinpoint where exception occurred (calculator.py:7)
    assert failures[2].file_path == "src/calculator.py"
    assert failures[2].line_no == 7
    assert failures[2].error_type == "ZeroDivisionError"
    assert failures[2].message == "division by zero"


def test_parse_failures_empty():
    assert parse_failures("") == []
    assert parse_failures("1 passed in 0.01s") == []


def test_run_tests_integration(tmp_path):
    # Create passing test
    test_file = tmp_path / "test_ok.py"
    test_file.write_text("def test_success():\n    assert True\n")
    results = run_tests(str(tmp_path))
    assert results == []

    # Create failing test
    fail_file = tmp_path / "test_broken.py"
    fail_file.write_text("def test_fail():\n    1 / 0\n")
    results = run_tests(str(tmp_path))
    assert len(results) == 1
    fail = results[0]
    assert fail.line_no == 2
    assert fail.error_type == "ZeroDivisionError"
    assert fail.message == "division by zero"
    assert str(fail_file.name) in fail.file_path
