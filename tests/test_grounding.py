from unittest.mock import MagicMock
from runner import TestFailure
from grounding import is_external_error, ground_error


def test_local_logic_failures_return_none():
    mock_client = MagicMock()

    local_failures = [
        TestFailure("test.py", 10, "AssertionError", "assert 1 == 2", ""),
        TestFailure("test.py", 12, "AssertionError", "expected True but got False", ""),
        TestFailure("test.py", 15, "ValueError", "invalid literal for int() with base 10", ""),
        TestFailure("test.py", 18, "ZeroDivisionError", "division by zero", ""),
        TestFailure("test.py", 20, "KeyError", "'item_id'", ""),
        TestFailure("test.py", 22, "IndexError", "list index out of range", ""),
        TestFailure("test.py", 25, "AttributeError", "'User' object has no attribute 'age'", ""),
    ]

    for fail in local_failures:
        assert not is_external_error(fail), f"Failed for {fail.error_type}: {fail.message}"
        res = ground_error(fail, client=mock_client)
        assert res is None

    # Tavily client should never have been invoked
    mock_client.search.assert_not_called()


def test_external_library_failures_trigger_search():
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [
            {"content": "Snippet 1: Pydantic v2 moved BaseModel to pydantic.v1"},
            {"content": "Snippet 2: Upgrade guide for Pydantic migration"},
            {"content": "Snippet 3: Extra result that should be ignored"},
        ]
    }

    external_failures = [
        TestFailure("test.py", 5, "ModuleNotFoundError", "No module named 'pydantic'", ""),
        TestFailure("test.py", 6, "ImportError", "cannot import name 'BaseModel' from 'pydantic'", ""),
        TestFailure("test.py", 7, "AttributeError", "module 'numpy' has no attribute 'int'", ""),
        TestFailure("test.py", 8, "DeprecationWarning", "np.matrix is deprecated and will be removed", ""),
    ]

    for fail in external_failures:
        assert is_external_error(fail)

    # Test execution on one of them
    fail = external_failures[2]  # AttributeError module 'numpy'
    res = ground_error(fail, client=mock_client)

    expected_query = "AttributeError: module 'numpy' has no attribute 'int' python"
    mock_client.search.assert_called_with(query=expected_query, max_results=2)

    assert res == [
        "Snippet 1: Pydantic v2 moved BaseModel to pydantic.v1",
        "Snippet 2: Upgrade guide for Pydantic migration",
    ]
    assert len(res) == 2


def test_ground_error_empty_results():
    mock_client = MagicMock()
    mock_client.search.return_value = {"results": []}

    fail = TestFailure("test.py", 5, "ModuleNotFoundError", "No module named 'foo'", "")
    res = ground_error(fail, client=mock_client)
    assert res == []
