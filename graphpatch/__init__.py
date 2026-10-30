"""GraphPatch-AI: AST-Guided Autonomous Program Repair Package."""

from graphpatch.runner import run_tests, parse_failures, TestFailure
from graphpatch.ast_extractor import extract_context
from graphpatch.grounding import ground_error, is_external_error
from graphpatch.router import diagnose_bug, generate_patch, get_usage, reset_usage
from graphpatch.orchestrator import repair_loop, evaluate_repair, apply_patch

__version__ = "0.1.0"

__all__ = [
    "run_tests",
    "parse_failures",
    "TestFailure",
    "extract_context",
    "ground_error",
    "is_external_error",
    "diagnose_bug",
    "generate_patch",
    "get_usage",
    "reset_usage",
    "repair_loop",
    "evaluate_repair",
    "apply_patch",
]
