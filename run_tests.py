#!/usr/bin/env python3
"""
Test Runner Script for KOL Management System

Provides convenient commands for running different types of tests with various configurations.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description=""):
    """
    Run a shell command and handle errors.

    Args:
        cmd: Command to run
        description: Description of what the command does

    Returns:
        bool: True if command succeeded, False otherwise
    """
    if description:
        print(f"\n{description}")
        print("-" * 50)

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return False


def run_all_tests():
    """Run all tests with coverage."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "-v"
    ]
    return run_command(cmd, "Running all tests with coverage")


def run_unit_tests():
    """Run only unit tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-m", "unit or not (integration or slow)",
        "-v"
    ]
    return run_command(cmd, "Running unit tests only")


def run_integration_tests():
    """Run only integration tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-m", "integration",
        "-v"
    ]
    return run_command(cmd, "Running integration tests only")


def run_auth_tests():
    """Run authentication-related tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_models/test_auth.py",
        "tests/test_api/test_auth.py",
        "tests/test_core/test_auth.py",
        "tests/test_tasks/test_auth.py",
        "-v"
    ]
    return run_command(cmd, "Running authentication tests")


def run_api_tests():
    """Run API endpoint tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_api/",
        "-v"
    ]
    return run_command(cmd, "Running API tests")


def run_service_tests():
    """Run service layer tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_services/",
        "-v"
    ]
    return run_command(cmd, "Running service tests")


def run_task_tests():
    """Run background task tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_tasks/",
        "-v"
    ]
    return run_command(cmd, "Running background task tests")


def run_fast_tests():
    """Run fast tests only (exclude slow tests)."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-m", "not slow",
        "-v"
    ]
    return run_command(cmd, "Running fast tests (excluding slow tests)")


def run_specific_test(test_path):
    """
    Run a specific test file or test function.

    Args:
        test_path: Path to test file or test function
    """
    cmd = [
        "python", "-m", "pytest",
        test_path,
        "-v"
    ]
    return run_command(cmd, f"Running specific test: {test_path}")


def run_parallel_tests():
    """Run tests in parallel (requires pytest-xdist)."""
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-n", "auto",
        "-v"
    ]
    return run_command(cmd, "Running tests in parallel")


def run_coverage_report():
    """Generate and open coverage report."""
    # Run tests with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing"
    ]

    if run_command(cmd, "Generating coverage report"):
        # Try to open the HTML report
        html_report = Path("htmlcov/index.html")
        if html_report.exists():
            import webbrowser
            try:
                webbrowser.open(f"file://{html_report.absolute()}")
                print(f"\nCoverage report opened in browser: {html_report}")
            except Exception:
                print(f"\nCoverage report generated: {html_report}")
        return True
    return False


def run_linting():
    """Run code linting checks."""
    success = True

    # Run flake8
    cmd = ["python", "-m", "flake8", "app", "tests"]
    if not run_command(cmd, "Running flake8 linting"):
        success = False

    # Run mypy
    cmd = ["python", "-m", "mypy", "app"]
    if not run_command(cmd, "Running mypy type checking"):
        success = False

    # Run black check
    cmd = ["python", "-m", "black", "--check", "app", "tests"]
    if not run_command(cmd, "Running black format checking"):
        success = False

    return success


def run_format_code():
    """Format code with black and isort."""
    success = True

    # Run black
    cmd = ["python", "-m", "black", "app", "tests"]
    if not run_command(cmd, "Formatting code with black"):
        success = False

    # Run isort
    cmd = ["python", "-m", "isort", "app", "tests"]
    if not run_command(cmd, "Sorting imports with isort"):
        success = False

    return success


def run_security_checks():
    """Run security checks with bandit."""
    cmd = ["python", "-m", "bandit", "-r", "app", "-f", "json"]
    return run_command(cmd, "Running security checks with bandit")


def run_full_check():
    """Run full test suite with linting and security checks."""
    print("Running full check suite...")
    print("=" * 70)

    success = True

    # Format code first
    if not run_format_code():
        success = False

    # Run linting
    if not run_linting():
        success = False

    # Run security checks
    if not run_security_checks():
        success = False

    # Run all tests
    if not run_all_tests():
        success = False

    print("\n" + "=" * 70)
    if success:
        print("✅ Full check completed successfully!")
    else:
        print("❌ Full check completed with errors!")

    return success


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="Test runner for KOL Management System")
    parser.add_argument("command", nargs="?", default="all", help="Test command to run")
    parser.add_argument("--test", help="Specific test file or function to run")

    args = parser.parse_args()

    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Command mapping
    commands = {
        "all": run_all_tests,
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "auth": run_auth_tests,
        "api": run_api_tests,
        "services": run_service_tests,
        "tasks": run_task_tests,
        "fast": run_fast_tests,
        "parallel": run_parallel_tests,
        "coverage": run_coverage_report,
        "lint": run_linting,
        "format": run_format_code,
        "security": run_security_checks,
        "full": run_full_check,
    }

    # Handle specific test
    if args.test:
        success = run_specific_test(args.test)
    elif args.command in commands:
        success = commands[args.command]()
    else:
        print(f"Unknown command: {args.command}")
        print(f"Available commands: {', '.join(commands.keys())}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)