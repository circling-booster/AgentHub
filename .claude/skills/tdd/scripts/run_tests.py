#!/usr/bin/env python3
"""
TDD Test Runner Script

Runs pytest with configurable options for coverage, verbosity, and test selection.

Usage:
    python run_tests.py                     # Run all tests
    python run_tests.py --cov               # Run with coverage
    python run_tests.py --path tests/unit   # Run specific directory
    python run_tests.py --match "test_user" # Run matching tests
    python run_tests.py --failed            # Run only failed tests
"""

import argparse
import subprocess
import sys
from pathlib import Path


def find_project_root() -> Path:
    """Find project root by looking for common markers."""
    current = Path.cwd()
    markers = ["pyproject.toml", "setup.py", "setup.cfg", ".git"]

    for parent in [current] + list(current.parents):
        if any((parent / marker).exists() for marker in markers):
            return parent
    return current


def build_pytest_command(args: argparse.Namespace) -> list[str]:
    """Build pytest command based on arguments."""
    cmd = ["pytest"]

    # Test path
    test_path = args.path or "tests/"
    cmd.append(test_path)

    # Verbosity
    if args.verbose:
        cmd.append("-v")

    # Coverage
    if args.cov:
        src_dir = args.cov_source or "src"
        cmd.extend([
            f"--cov={src_dir}",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
        ])
        if args.cov_fail_under:
            cmd.append(f"--cov-fail-under={args.cov_fail_under}")

    # Pattern matching
    if args.match:
        cmd.extend(["-k", args.match])

    # Only failed tests
    if args.failed:
        cmd.append("--lf")

    # Stop on first failure
    if args.exitfirst:
        cmd.append("-x")

    # Show local variables in tracebacks
    if args.locals:
        cmd.append("-l")

    # Markers
    if args.markers:
        for marker in args.markers:
            cmd.extend(["-m", marker])

    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TDD Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--path", "-p",
        help="Path to test directory or file (default: tests/)",
    )
    parser.add_argument(
        "--cov", "-c",
        action="store_true",
        help="Enable coverage reporting",
    )
    parser.add_argument(
        "--cov-source",
        help="Source directory for coverage (default: src)",
    )
    parser.add_argument(
        "--cov-fail-under",
        type=int,
        help="Fail if coverage is below this percentage",
    )
    parser.add_argument(
        "--match", "-k",
        help="Only run tests matching this expression",
    )
    parser.add_argument(
        "--failed", "-f",
        action="store_true",
        help="Only run tests that failed last time",
    )
    parser.add_argument(
        "--exitfirst", "-x",
        action="store_true",
        help="Stop on first failure",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--locals", "-l",
        action="store_true",
        help="Show local variables in tracebacks",
    )
    parser.add_argument(
        "--markers", "-m",
        nargs="+",
        help="Only run tests with these markers",
    )

    args = parser.parse_args()

    # Change to project root
    project_root = find_project_root()

    # Build and run command
    cmd = build_pytest_command(args)

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")
    print("-" * 50)

    result = subprocess.run(cmd, cwd=project_root)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
