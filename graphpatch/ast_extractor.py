"""AST scope extraction engine for isolating target functions and module imports."""

import ast
from pathlib import Path


def _find_enclosing_node(tree: ast.AST, line_no: int):
    candidates = []

    def visit(node: ast.AST, depth: int = 0) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            end = getattr(node, "end_lineno", node.lineno)
            if start <= line_no <= end:
                candidates.append((end - start, -depth, node, start, end))
        for child in ast.iter_child_nodes(node):
            visit(child, depth + 1)

    visit(tree)
    if not candidates:
        return None
    candidates.sort(key=lambda c: (c[0], c[1]))
    return candidates[0]


def _extract_imports(tree: ast.AST, lines: list[str]) -> str:
    import_chunks = []
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            import_chunks.append("\n".join(lines[start:end]))
    return "\n".join(import_chunks)


def _extract_surrounding_lines(
    lines: list[str], target_line: int, window: int = 20
) -> str:
    total = len(lines)
    if total <= window:
        return "\n".join(lines)
    half = window // 2
    start = max(0, target_line - half - 1)
    end = min(total, start + window)
    if end - start < window:
        start = max(0, end - window)
    return "\n".join(lines[start:end])


def extract_context(file_path: str | Path, line_no: int) -> str:
    path = Path(file_path)
    source = path.read_text(encoding="utf-8") if path.is_file() else str(file_path)
    lines = source.splitlines()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return _extract_surrounding_lines(lines, line_no)

    imports_code = _extract_imports(tree, lines)
    enclosing = _find_enclosing_node(tree, line_no)

    if enclosing:
        _, _, _, start, end = enclosing
        target_code = "\n".join(lines[start - 1 : end])
        parts = [p for p in (imports_code, target_code) if p]
    else:
        surrounding = _extract_surrounding_lines(lines, line_no)
        # Check if surrounding lines already capture the top of the file
        first_surrounding_line = max(0, line_no - 11)
        if first_surrounding_line > 0 and imports_code:
            parts = [imports_code, surrounding]
        else:
            parts = [surrounding]

    return "\n\n".join(parts)


isolate_code = extract_context
extract_code = extract_context
extract = extract_context
