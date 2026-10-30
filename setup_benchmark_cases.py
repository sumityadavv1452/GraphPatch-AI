import os
from pathlib import Path

BENCHMARK_CASES = {
    "case_01_off_by_one": {
        "desc": "Off-by-one slicing error",
        "category": "Off-by-one",
        "solution": '''def get_last_n_items(lst: list, n: int) -> list:
    if n <= 0:
        return []
    return lst[-n + 1 :]
''',
        "test": '''from solution import get_last_n_items

def test_get_last_n():
    items = [1, 2, 3, 4, 5]
    assert get_last_n_items(items, 3) == [3, 4, 5]
    assert get_last_n_items(items, 1) == [5]
''',
        "fixed": '''def get_last_n_items(lst: list, n: int) -> list:
    if n <= 0:
        return []
    return lst[-n:]
''',
    },
    "case_02_type_error": {
        "desc": "Type mismatch in string concatenation",
        "category": "Type Error",
        "solution": '''def format_user_badge(username: str, score: int) -> str:
    return username + "#" + score
''',
        "test": '''from solution import format_user_badge

def test_format_user_badge():
    assert format_user_badge("alice", 100) == "alice#100"
''',
        "fixed": '''def format_user_badge(username: str, score: int) -> str:
    return username + "#" + str(score)
''',
    },
    "case_03_missing_key": {
        "desc": "Unchecked dictionary key access",
        "category": "Missing Key",
        "solution": '''def get_config_timeout(config: dict) -> int:
    return config["timeout"]
''',
        "test": '''from solution import get_config_timeout

def test_config_timeout():
    assert get_config_timeout({"timeout": 30}) == 30
    assert get_config_timeout({}) == 10
''',
        "fixed": '''def get_config_timeout(config: dict) -> int:
    return config.get("timeout", 10)
''',
    },
    "case_04_zero_division": {
        "desc": "Division by zero without guard",
        "category": "Zero Division",
        "solution": '''def calculate_ratio(success_count: int, total_count: int) -> float:
    return success_count / total_count
''',
        "test": '''from solution import calculate_ratio

def test_calculate_ratio():
    assert calculate_ratio(10, 20) == 0.5
    assert calculate_ratio(0, 0) == 0.0
''',
        "fixed": '''def calculate_ratio(success_count: int, total_count: int) -> float:
    return 0.0 if total_count == 0 else success_count / total_count
''',
    },
    "case_05_attribute_error": {
        "desc": "Calling method attribute without invoking",
        "category": "Attribute Error",
        "solution": '''def clean_identifier(text: str) -> str:
    return text.strip.lower()
''',
        "test": '''from solution import clean_identifier

def test_clean_identifier():
    assert clean_identifier("  AdminUser  ") == "adminuser"
''',
        "fixed": '''def clean_identifier(text: str) -> str:
    return text.strip().lower()
''',
    },
    "case_06_index_error": {
        "desc": "Index lookup on empty sequence",
        "category": "Index Error",
        "solution": '''def peek_front(queue: list):
    return queue[0]
''',
        "test": '''from solution import peek_front

def test_peek_front():
    assert peek_front([1, 2]) == 1
    assert peek_front([]) is None
''',
        "fixed": '''def peek_front(queue: list):
    return queue[0] if queue else None
''',
    },
    "case_07_boundary_condition": {
        "desc": "Strict inequality excluding range boundaries",
        "category": "Boundary Condition",
        "solution": '''def is_valid_percentage(val: float) -> bool:
    return 0 < val < 100
''',
        "test": '''from solution import is_valid_percentage

def test_valid_percentage():
    assert is_valid_percentage(50) is True
    assert is_valid_percentage(0) is True
    assert is_valid_percentage(100) is True
    assert is_valid_percentage(105) is False
''',
        "fixed": '''def is_valid_percentage(val: float) -> bool:
    return 0 <= val <= 100
''',
    },
    "case_08_logic_inversion": {
        "desc": "Inverted boolean retry condition",
        "category": "Logic Inversion",
        "solution": '''def should_retry_request(status_code: int) -> bool:
    return status_code == 200
''',
        "test": '''from solution import should_retry_request

def test_should_retry():
    assert should_retry_request(503) is True
    assert should_retry_request(500) is True
    assert should_retry_request(200) is False
''',
        "fixed": '''def should_retry_request(status_code: int) -> bool:
    return status_code >= 500
''',
    },
    "case_09_case_sensitivity": {
        "desc": "Case sensitivity mapping failure",
        "category": "Case Mismatch",
        "solution": '''def normalize_color(color_name: str) -> str:
    mapping = {"red": "#FF0000", "green": "#00FF00", "blue": "#0000FF"}
    return mapping[color_name]
''',
        "test": '''from solution import normalize_color

def test_normalize_color():
    assert normalize_color("RED") == "#FF0000"
    assert normalize_color("green") == "#00FF00"
''',
        "fixed": '''def normalize_color(color_name: str) -> str:
    mapping = {"red": "#FF0000", "green": "#00FF00", "blue": "#0000FF"}
    return mapping[color_name.lower()]
''',
    },
    "case_10_external_import": {
        "desc": "Deprecated import from collections instead of collections.abc",
        "category": "Import Deprecation",
        "solution": '''from collections import Mapping

def is_mapping_type(obj) -> bool:
    return isinstance(obj, Mapping)
''',
        "test": '''from solution import is_mapping_type

def test_is_mapping_type():
    assert is_mapping_type({"a": 1}) is True
    assert is_mapping_type([1, 2]) is False
''',
        "fixed": '''from collections.abc import Mapping

def is_mapping_type(obj) -> bool:
    return isinstance(obj, Mapping)
''',
    },
}


def setup_cases(base_dir: Path = Path("benchmark_cases")) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    for case_name, data in BENCHMARK_CASES.items():
        case_dir = base_dir / case_name
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "solution.py").write_text(data["solution"], encoding="utf-8")
        (case_dir / "test_solution.py").write_text(data["test"], encoding="utf-8")
    print(f"Created {len(BENCHMARK_CASES)} benchmark cases in {base_dir}")


if __name__ == "__main__":
    setup_cases()
