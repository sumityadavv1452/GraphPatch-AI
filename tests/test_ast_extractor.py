import pytest
from pathlib import Path
from ast_extractor import extract_context


def test_extract_function_with_imports(tmp_path: Path):
    source = """import os
from sys import version_info

def ignored_one():
    return 1

def failing_function(a, b):
    # Important comment
    return a / b

def ignored_two():
    return 2
"""
    file_path = tmp_path / "sample.py"
    file_path.write_text(source, encoding="utf-8")

    # Line 8 is `return a / b`
    result = extract_context(file_path, 8)

    assert "import os" in result
    assert "from sys import version_info" in result
    assert "def failing_function(a, b):" in result
    assert "# Important comment" in result
    assert "return a / b" in result
    assert "def ignored_one" not in result
    assert "def ignored_two" not in result


def test_extract_async_function_with_decorator(tmp_path: Path):
    source = """import asyncio

@decorator1
@decorator2(flag=True)
async def async_worker():
    await asyncio.sleep(0)
    raise ValueError("fail")
"""
    file_path = tmp_path / "async_sample.py"
    file_path.write_text(source, encoding="utf-8")

    # Line 7 is `raise ValueError("fail")`
    result = extract_context(file_path, 7)

    assert "import asyncio" in result
    assert "@decorator1" in result
    assert "@decorator2(flag=True)" in result
    assert "async def async_worker():" in result
    assert 'raise ValueError("fail")' in result


def test_extract_method_inside_class(tmp_path: Path):
    source = """from typing import Optional

class Calculator:
    def add(self, x: int, y: int) -> int:
        return x + y

    def divide(self, x: int, y: int) -> float:
        return x / y
"""
    file_path = tmp_path / "calc.py"
    file_path.write_text(source, encoding="utf-8")

    # Line 8 is `return x / y`
    result = extract_context(file_path, 8)

    assert "from typing import Optional" in result
    assert "def divide(self, x: int, y: int) -> float:" in result
    assert "return x / y" in result
    # method add should be excluded
    assert "def add(" not in result


def test_extract_class_level_error(tmp_path: Path):
    source = """import math

class Config:
    DEFAULT_TIMEOUT = 10 / 0
"""
    file_path = tmp_path / "config.py"
    file_path.write_text(source, encoding="utf-8")

    # Line 4 is `DEFAULT_TIMEOUT = 10 / 0`
    result = extract_context(file_path, 4)

    assert "import math" in result
    assert "class Config:" in result
    assert "DEFAULT_TIMEOUT = 10 / 0" in result


def test_extract_module_level_surrounding_window(tmp_path: Path):
    lines = [f"line_{i} = {i}" for i in range(1, 51)]
    lines.insert(0, "import sys")
    # File has 51 lines. Line 30 fails.
    source = "\n".join(lines)
    file_path = tmp_path / "module_level.py"
    file_path.write_text(source, encoding="utf-8")

    result = extract_context(file_path, 30)

    # Line 30 should be present
    assert "line_29 = 29" in result
    assert "import sys" in result
    # Far-away lines should not be in the window
    assert "line_1 = 1" not in result
    assert "line_50 = 50" not in result


def test_extract_syntax_error_fallback(tmp_path: Path):
    source = """import sys
def bad_syntax(
"""
    file_path = tmp_path / "syntax_err.py"
    file_path.write_text(source, encoding="utf-8")

    result = extract_context(file_path, 2)
    assert "def bad_syntax(" in result
