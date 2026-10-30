import argparse
import sys
from pathlib import Path
try:
    from graphpatch.orchestrator import repair_loop
except ImportError:
    from orchestrator import repair_loop


def main():
    parser = argparse.ArgumentParser(
        description="GraphPatch-AI: Autonomous AST-Grounded Program Repair Engine"
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=".",
        help="Path to target repository or test directory to repair (default: .)",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=2,
        help="Maximum number of retry attempts for failed patches (default: 2)",
    )
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not repo_path.exists():
        print(f"[!] Error: Target directory '{repo_path}' does not exist.")
        sys.exit(1)

    print(f"=== GraphPatch-AI Starting Repair Cycle ===")
    print(f"Target Repository : {repo_path}")
    print(f"Max Retries       : {args.max_retries}")
    print("=" * 43 + "\n")

    success = repair_loop(target_dir=repo_path, max_retries=args.max_retries)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
