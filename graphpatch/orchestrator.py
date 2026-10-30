"""Closed-loop repair orchestration engine with pre-flight dry-run validation."""

import difflib
import subprocess
import sys
from pathlib import Path

try:
    from .runner import run_tests
    from .ast_extractor import extract_context
    from .grounding import ground_error
    from .router import diagnose_bug, generate_patch
    from .config import MAX_RETRIES, TIMEOUT_SECONDS
except (ImportError, ValueError):
    from runner import run_tests
    from ast_extractor import extract_context
    from grounding import ground_error
    from router import diagnose_bug, generate_patch
    MAX_RETRIES = 2
    TIMEOUT_SECONDS = 30


def check_patch(patch_str: str, target_dir: str | Path = ".") -> bool:
    """Pre-flight dry-run validation using git apply --check."""
    res = subprocess.run(
        ["git", "apply", "--check", "--whitespace=fix", "-"],
        input=patch_str,
        text=True,
        cwd=str(target_dir),
        capture_output=True,
    )
    return res.returncode == 0


def apply_patch(patch_str: str, target_dir: str | Path = ".") -> bool:
    """Apply a unified diff patch with pre-flight dry-run check."""
    cwd = str(target_dir)

    # 0. Pre-flight check
    _ = check_patch(patch_str, cwd)

    # 1. Primary: git apply --whitespace=fix -
    res = subprocess.run(
        ["git", "apply", "--whitespace=fix", "-"],
        input=patch_str,
        text=True,
        cwd=cwd,
        capture_output=True,
    )
    if res.returncode == 0:
        return True

    # 2. Permissive git apply with --unsafe-paths
    res = subprocess.run(
        ["git", "apply", "--whitespace=fix", "--unsafe-paths", "-"],
        input=patch_str,
        text=True,
        cwd=cwd,
        capture_output=True,
    )
    if res.returncode == 0:
        return True

    # 3. Fallback: patch -p1
    try:
        res = subprocess.run(
            ["patch", "-p1"],
            input=patch_str,
            text=True,
            cwd=cwd,
            capture_output=True,
        )
        if res.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # 4. Built-in resilient Python fallback
    return _apply_unified_diff_fallback(patch_str, cwd)


def _apply_unified_diff_fallback(patch_str: str, target_dir: str | Path = ".") -> bool:
    """Fallback pure-Python unified diff applier for environments without patch CLI."""
    try:
        lines = patch_str.splitlines()
        target_path = None
        hunks = []
        current_hunk = None

        for line in lines:
            if line.startswith("+++ "):
                part = line[4:].strip()
                if part.startswith("b/"):
                    part = part[2:]
                target_path = Path(target_dir) / part
            elif line.startswith("@@ "):
                current_hunk = []
                hunks.append(current_hunk)
            elif current_hunk is not None:
                current_hunk.append(line)

        if not target_path or not target_path.exists() or not hunks:
            return False

        orig_lines = target_path.read_text(encoding="utf-8").splitlines()
        new_lines = []
        orig_idx = 0

        for hunk in hunks:
            context_before = [
                l[1:] for l in hunk if l.startswith(" ") or l.startswith("-")
            ]
            replaced_with = [
                l[1:] for l in hunk if l.startswith(" ") or l.startswith("+")
            ]
            matched = False
            for i in range(orig_idx, len(orig_lines) - len(context_before) + 1):
                if orig_lines[i : i + len(context_before)] == context_before:
                    new_lines.extend(orig_lines[orig_idx:i])
                    new_lines.extend(replaced_with)
                    orig_idx = i + len(context_before)
                    matched = True
                    break
            if not matched:
                return False

        new_lines.extend(orig_lines[orig_idx:])
        target_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        return True
    except Exception:
        return False


def format_side_by_side_diff(
    before: str, after: str, file_path: str = "", width: int = 40
) -> str:
    """Generate a side-by-side comparison of before and after code using difflib."""
    b_lines = before.splitlines()
    a_lines = after.splitlines()
    matcher = difflib.SequenceMatcher(None, b_lines, a_lines)

    title_b = f"ORIGINAL ({file_path})" if file_path else "ORIGINAL"
    title_a = f"MODIFIED ({file_path})" if file_path else "MODIFIED"
    header = f"{title_b[:width]:<{width}} | {title_a[:width]:<{width}}"
    sep = "-" * len(header)
    lines = [sep, header, sep]

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        b_chunk = b_lines[i1:i2]
        a_chunk = a_lines[j1:j2]
        max_chunk = max(len(b_chunk), len(a_chunk))
        for k in range(max_chunk):
            b = b_chunk[k] if k < len(b_chunk) else ""
            a = a_chunk[k] if k < len(a_chunk) else ""
            mark_b = (
                f"- {b}"
                if tag in ("delete", "replace") and b
                else (b if tag == "equal" else "")
            )
            mark_a = (
                f"+ {a}"
                if tag in ("insert", "replace") and a
                else (a if tag == "equal" else "")
            )
            lines.append(f"{mark_b[:width]:<{width}} | {mark_a[:width]:<{width}}")

    lines.append(sep)
    return "\n".join(lines)


def print_side_by_side_diff(
    before: str, after: str, file_path: str = "", width: int = 40
) -> None:
    """Print the side-by-side diff to terminal."""
    print(format_side_by_side_diff(before, after, file_path, width))


from dataclasses import dataclass


@dataclass
class RepairReport:
    success: bool
    retries: int
    status: str
    failure_reason: str = ""


def evaluate_repair(
    target_dir: str | Path = ".", max_retries: int = 2
) -> RepairReport:
    """Closed-loop repair cycle returning detailed RepairReport."""
    print(f"[*] Running tests in: {target_dir}")
    failures = run_tests(target_dir)

    # 1. If passing, exit early with success
    if not failures:
        print("[+] All tests passed! No repair needed.")
        return RepairReport(
            success=True, retries=0, status="Pass@0", failure_reason=""
        )

    print(
        f"[!] Initial test run detected {len(failures)} failure(s). Starting repair cycle..."
    )

    retries = 0
    current_failures = failures
    last_diagnosis = None

    # Strict maximum limit of 2 retry attempts (initial attempt + up to 2 retries)
    while retries <= max_retries:
        failure = current_failures[0]
        file_path = failure.file_path
        target_file = (
            Path(target_dir) / file_path
            if not Path(file_path).is_absolute()
            else Path(file_path)
        )

        print(
            f"\n[Attempt {retries + 1}/{max_retries + 1}] Repairing failure at "
            f"{file_path}:{failure.line_no} ({failure.error_type}: {failure.message})"
        )

        before_content = (
            target_file.read_text(encoding="utf-8") if target_file.exists() else ""
        )

        # 2. Extract blast-radius context via ast_extractor
        isolated_code = extract_context(target_file, failure.line_no)

        # 3. Check Tavily conditionally via grounding
        snippets = ground_error(failure)
        search_context = "\n".join(snippets) if snippets else None
        if search_context:
            print("[*] Tavily external search context retrieved.")

        # 4. Diagnose bug and generate patch from router
        if retries == 0 or not last_diagnosis:
            diagnosis = diagnose_bug(
                isolated_code=isolated_code,
                error_info=f"{failure.error_type}: {failure.message}\n{failure.raw_trace}",
                search_context=search_context,
            )
        else:
            # 7. Feed the new stack trace back into generate_patch for retry
            diagnosis = (
                f"Previous patch failed. New error trace: {failure.error_type}: {failure.message}\n"
                f"New traceback:\n{failure.raw_trace}\n"
                f"Previous diagnosis was: {last_diagnosis}"
            )
        last_diagnosis = diagnosis
        print(f"[*] Diagnosis: {diagnosis}")

        patch = generate_patch(
            isolated_code=isolated_code,
            file_path=file_path,
            diagnosis=diagnosis,
        )

        # 5. Apply diff using git apply
        applied = apply_patch(patch, target_dir=target_dir)
        if not applied:
            print(f"[-] Warning: Failed to apply patch cleanly:\n{patch}")
        else:
            print("[+] Patch successfully applied.")
            # 9. Print side-by-side terminal diff of what changed
            after_content = (
                target_file.read_text(encoding="utf-8") if target_file.exists() else ""
            )
            print_side_by_side_diff(before_content, after_content, file_path=file_path)

        # 6. Re-run tests
        current_failures = run_tests(target_dir)
        if not current_failures:
            status = (
                "Fixed on 1st Attempt"
                if retries == 0
                else f"Fixed within 3 Attempts (Attempt {retries + 1})"
            )
            print(
                f"[+] All tests passed after {retries} retry attempt(s)! Status: {status}"
            )
            return RepairReport(
                success=True, retries=retries, status=status, failure_reason=""
            )

        retries += 1
        if retries <= max_retries:
            print(
                f"[!] Tests still failing ({len(current_failures)} failure(s)). Retrying ({retries}/{max_retries})..."
            )

    # 8. Strict maximum limit reached
    last_err = current_failures[0]
    reason = f"{last_err.error_type}: {last_err.message}"
    print(f"[-] Repair failed: exceeded maximum limit of {max_retries} retry attempts.")
    return RepairReport(
        success=False, retries=max_retries, status="Failed", failure_reason=reason
    )


def repair_loop(target_dir: str | Path = ".", max_retries: int = 2) -> bool:
    """Run closed-loop repair cycle returning boolean success."""
    return evaluate_repair(target_dir, max_retries=max_retries).success


run_repair_loop = repair_loop
orchestrate = repair_loop

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    ok = repair_loop(target)
    sys.exit(0 if ok else 1)
