#!/usr/bin/env python3
"""
Test runner script for Factory ERP System.

Provides convenient commands for running different types of tests.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list[str]) -> int:
    """
    Run shell command and return exit code.
    
    Args:
        cmd: Command list to execute
        
    Returns:
        int: Exit code
    """
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_all_tests() -> int:
    """Run all tests."""
    return run_command(["python", "-m", "pytest", "tests/", "-v"])


def run_unit_tests() -> int:
    """Run unit tests only."""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_models/", 
        "tests/test_services/",
        "-v", "-m", "not integration"
    ])


def run_integration_tests() -> int:
    """Run integration tests only."""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_api/",
        "-v"
    ])


def run_specific_test(test_path: str) -> int:
    """
    Run specific test file or test function.
    
    Args:
        test_path: Path to test file or test function
        
    Returns:
        int: Exit code
    """
    return run_command(["python", "-m", "pytest", test_path, "-v"])


def run_coverage() -> int:
    """Run tests with coverage report."""
    cmd = [
        "python", "-m", "pytest", 
        "tests/",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v"
    ]
    return run_command(cmd)


def run_fast_tests() -> int:
    """Run fast tests only (excluding slow tests)."""
    return run_command([
        "python", "-m", "pytest", 
        "tests/",
        "-m", "not slow",
        "-v"
    ])


def run_auth_tests() -> int:
    """Run authentication tests only."""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_api/test_auth.py",
        "-v"
    ])


def run_excel_tests() -> int:
    """Run Excel functionality tests only."""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_services/test_excel_service.py",
        "-v"
    ])


def run_model_tests() -> int:
    """Run model tests only."""
    return run_command([
        "python", "-m", "pytest", 
        "tests/test_models/",
        "-v"
    ])


def lint_code() -> int:
    """Run code linting."""
    print("Running flake8...")
    flake8_result = run_command(["python", "-m", "flake8", "app/", "tests/"])
    
    print("Running black check...")
    black_result = run_command(["python", "-m", "black", "--check", "app/", "tests/"])
    
    print("Running isort check...")
    isort_result = run_command(["python", "-m", "isort", "--check-only", "app/", "tests/"])
    
    return max(flake8_result, black_result, isort_result)


def format_code() -> int:
    """Format code using black and isort."""
    print("Formatting with black...")
    black_result = run_command(["python", "-m", "black", "app/", "tests/"])
    
    print("Sorting imports with isort...")
    isort_result = run_command(["python", "-m", "isort", "app/", "tests/"])
    
    return max(black_result, isort_result)


def check_dependencies() -> bool:
    """Check if required testing dependencies are installed."""
    required_packages = [
        "pytest",
        "pytest-asyncio", 
        "httpx",
        "coverage",
        "pytest-cov"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Factory ERP Test Runner")
    parser.add_argument(
        "command",
        choices=[
            "all", "unit", "integration", "coverage", "fast",
            "auth", "excel", "models", "lint", "format", "specific"
        ],
        help="Test command to run"
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Specific test path (for 'specific' command)"
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check if testing dependencies are installed"
    )
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("All testing dependencies are installed.")
            return 0
        else:
            return 1
    
    # Check dependencies before running tests
    if not check_dependencies():
        return 1
    
    # Map commands to functions
    command_map = {
        "all": run_all_tests,
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "coverage": run_coverage,
        "fast": run_fast_tests,
        "auth": run_auth_tests,
        "excel": run_excel_tests,
        "models": run_model_tests,
        "lint": lint_code,
        "format": format_code,
    }
    
    if args.command == "specific":
        if not args.path:
            print("Error: --path is required for 'specific' command")
            return 1
        return run_specific_test(args.path)
    
    if args.command in command_map:
        return command_map[args.command]()
    
    print(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)