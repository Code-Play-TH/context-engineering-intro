#!/usr/bin/env python3
"""
Comprehensive Test Runner

Runs all tests with comprehensive coverage, performance metrics, and reporting.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
import argparse


def run_command(command: List[str], description: str, capture_output: bool = True) -> Dict[str, Any]:
    """
    Run a command and return results.

    Args:
        command: Command to run
        description: Description of the command
        capture_output: Whether to capture output

    Returns:
        Dict containing results
    """
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")

    start_time = time.time()

    try:
        if capture_output:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )
        else:
            result = subprocess.run(
                command,
                check=False
            )

        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ {description} completed successfully in {duration:.2f}s")
            if capture_output and result.stdout:
                print(f"Output:\n{result.stdout}")
        else:
            print(f"❌ {description} failed with code {result.returncode}")
            if capture_output and result.stderr:
                print(f"Error:\n{result.stderr}")

        return {
            "command": " ".join(command),
            "description": description,
            "success": result.returncode == 0,
            "duration": duration,
            "stdout": result.stdout if capture_output else "",
            "stderr": result.stderr if capture_output else "",
            "return_code": result.returncode
        }

    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ {description} failed with exception: {str(e)}")

        return {
            "command": " ".join(command),
            "description": description,
            "success": False,
            "duration": duration,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1
        }


def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")

    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-xdist",
        "httpx",
        "fastapi",
        "sqlalchemy",
        "asyncpg"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            subprocess.run(
                [sys.executable, "-c", f"import {package.replace('-', '_')}"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    print("✅ All dependencies are installed")
    return True


def run_unit_tests(args: argparse.Namespace) -> Dict[str, Any]:
    """Run unit tests with coverage."""
    command = [
        sys.executable, "-m", "pytest",
        "tests/test_services/",
        "tests/test_models/",
        "tests/test_core/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-fail-under=80"
    ]

    if args.parallel:
        command.extend(["-n", "auto"])

    if args.markers:
        command.extend(["-m", args.markers])

    return run_command(command, "Running Unit Tests")


def run_integration_tests(args: argparse.Namespace) -> Dict[str, Any]:
    """Run integration tests."""
    command = [
        sys.executable, "-m", "pytest",
        "tests/test_integration/",
        "-v",
        "--tb=short",
        "-m", "integration"
    ]

    if args.parallel:
        command.extend(["-n", "auto"])

    return run_command(command, "Running Integration Tests")


def run_api_tests(args: argparse.Namespace) -> Dict[str, Any]:
    """Run API tests."""
    command = [
        sys.executable, "-m", "pytest",
        "tests/test_api/",
        "-v",
        "--tb=short"
    ]

    if args.parallel:
        command.extend(["-n", "auto"])

    return run_command(command, "Running API Tests")


def run_performance_tests(args: argparse.Namespace) -> Dict[str, Any]:
    """Run performance tests."""
    if not args.include_performance:
        print("⏭️  Skipping performance tests (use --include-performance to run)")
        return {"success": True, "description": "Performance tests skipped"}

    command = [
        sys.executable, "-m", "pytest",
        "tests/test_performance/",
        "-v",
        "--tb=short",
        "-m", "performance",
        "--durations=10"
    ]

    return run_command(command, "Running Performance Tests")


def run_linting() -> Dict[str, Any]:
    """Run code linting with ruff."""
    command = [sys.executable, "-m", "ruff", "check", "app/", "tests/"]
    return run_command(command, "Running Code Linting (Ruff)")


def run_type_checking() -> Dict[str, Any]:
    """Run type checking with mypy."""
    command = [sys.executable, "-m", "mypy", "app/", "--ignore-missing-imports"]
    return run_command(command, "Running Type Checking (MyPy)")


def run_security_scan() -> Dict[str, Any]:
    """Run security scanning with bandit."""
    try:
        command = [sys.executable, "-m", "bandit", "-r", "app/", "-f", "json"]
        return run_command(command, "Running Security Scan (Bandit)")
    except FileNotFoundError:
        print("⚠️  Bandit not installed, skipping security scan")
        return {"success": True, "description": "Security scan skipped (bandit not installed)"}


def generate_test_report(results: List[Dict[str, Any]]) -> None:
    """Generate comprehensive test report."""
    print(f"\n{'='*60}")
    print("📊 COMPREHENSIVE TEST REPORT")
    print(f"{'='*60}")

    total_duration = sum(result.get("duration", 0) for result in results)
    successful_tests = sum(1 for result in results if result.get("success", False))
    total_tests = len(results)

    print(f"\n📈 Summary:")
    print(f"  Total test suites: {total_tests}")
    print(f"  Successful: {successful_tests}")
    print(f"  Failed: {total_tests - successful_tests}")
    print(f"  Total duration: {total_duration:.2f}s")
    print(f"  Success rate: {(successful_tests/total_tests)*100:.1f}%")

    print(f"\n📝 Detailed Results:")
    for result in results:
        status = "✅" if result.get("success", False) else "❌"
        duration = result.get("duration", 0)
        description = result.get("description", "Unknown")

        print(f"  {status} {description:<30} ({duration:.2f}s)")

        if not result.get("success", False) and result.get("stderr"):
            # Show first few lines of error
            error_lines = result.get("stderr", "").split('\n')[:3]
            for line in error_lines:
                if line.strip():
                    print(f"    ⚠️  {line.strip()}")

    # Coverage information
    if any("Unit Tests" in r.get("description", "") for r in results):
        print(f"\n📊 Code Coverage:")
        print(f"  Coverage report generated in: htmlcov/index.html")
        print(f"  Open with: python -m http.server 8000 --directory htmlcov")

    # Performance recommendations
    long_running = [r for r in results if r.get("duration", 0) > 30]
    if long_running:
        print(f"\n⚡ Performance Notes:")
        for result in long_running:
            print(f"  - {result['description']} took {result['duration']:.2f}s (consider optimization)")

    print(f"\n{'='*60}")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner")
    parser.add_argument(
        "--include-performance",
        action="store_true",
        help="Include performance tests (slower)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel where possible"
    )
    parser.add_argument(
        "--skip-linting",
        action="store_true",
        help="Skip linting and type checking"
    )
    parser.add_argument(
        "--markers",
        type=str,
        help="Pytest markers to filter tests (e.g., 'not slow')"
    )
    parser.add_argument(
        "--test-types",
        nargs="+",
        choices=["unit", "integration", "api", "performance", "lint", "security"],
        help="Specific test types to run"
    )

    args = parser.parse_args()

    print("🚀 Starting Comprehensive Test Suite")
    print(f"Working directory: {os.getcwd()}")

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    # Determine which tests to run
    if args.test_types:
        test_types = args.test_types
    else:
        test_types = ["unit", "integration", "api", "lint"]
        if args.include_performance:
            test_types.append("performance")
        if not args.skip_linting:
            test_types.extend(["security"])

    results = []

    # Run selected test types
    if "lint" in test_types and not args.skip_linting:
        results.append(run_linting())
        results.append(run_type_checking())

    if "security" in test_types:
        results.append(run_security_scan())

    if "unit" in test_types:
        results.append(run_unit_tests(args))

    if "api" in test_types:
        results.append(run_api_tests(args))

    if "integration" in test_types:
        results.append(run_integration_tests(args))

    if "performance" in test_types:
        results.append(run_performance_tests(args))

    # Generate comprehensive report
    generate_test_report(results)

    # Exit with error code if any tests failed
    if any(not result.get("success", False) for result in results):
        print("\n❌ Some tests failed!")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()