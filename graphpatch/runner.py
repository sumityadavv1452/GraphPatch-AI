"""Test runner and pytest traceback parser for isolating failure frames."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestFailure:
    __test__ = False
    file_path: str
    line_no: int
    error_type: str
    message: str
    raw_trace: str


def _parse_error(e_lines: list[str]) -> tuple[str, str]:
    
    for line in e_lines:
        if line.startswith("assert"):
            return "AssertionError", line
        if m := re.match(r"^([A-Za-z_][\w.]*):\s*(.*)$", line):
            return m.group(1), m.group(2).strip()
        if re.match(r"^[A-Za-z_][\w.]*(?:Error|Exception)$", line):
            return line, ""
    return (e_lines[0], "") if e_lines else ("Error", "")


def parse_failures(output: str) -> list[TestFailure]:
    failures = []
    blocks = re.split(r"^_{2,}\s+.*?\s+_{2,}\r?$", output, flags=re.MULTILINE)
    for block in blocks[1:]:
        raw_trace = re.split(r"\n={3,}", block)[0].strip()
        frames = re.findall(
            r"^((?:[A-Za-z]:)?[^:\r\n]+?):(\d+):(?:\s+in\s+.*)?$", raw_trace, re.M
        )
        file_path, line_no = (frames[-1][0], int(frames[-1][1])) if frames else ("", 0)
        if m := re.search(r'File "([^"]+)", line (\d+)', raw_trace):
            file_path, line_no = m.group(1), int(m.group(2))
        e_lines = [l[4:].strip() for l in raw_trace.splitlines() if l.startswith("E   ")]
        err_type, msg = _parse_error(e_lines)
        failures.append(TestFailure(file_path, line_no, err_type, msg, raw_trace))
    return failures


def run_tests(target_dir: str | Path = ".") -> list[TestFailure]:
    proc = subprocess.run(
        ["pytest", "-q", "--tb=short", str(target_dir)], capture_output=True, text=True
    )
    return parse_failures(proc.stdout or proc.stderr) if proc.returncode != 0 else []


run_pytest = run_tests
