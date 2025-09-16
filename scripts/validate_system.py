#!/usr/bin/env python3
"""
KOL Management System Validation Script

Comprehensive validation of the system architecture, configuration,
and implementation to identify potential issues and ensure production readiness.
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SystemValidator:
    """Main system validation class."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "categories": {},
            "issues": [],
            "recommendations": []
        }

    def validate_file_structure(self) -> Tuple[bool, List[str]]:
        """Validate project file structure and required files."""
        logger.info("Validating file structure...")

        issues = []
        required_files = [
            "app/__init__.py",
            "app/main.py",
            "app/core/config.py",
            "app/core/database.py",
            "app/core/auth.py",
            "app/models/__init__.py",
            "app/schemas/__init__.py",
            "app/api/__init__.py",
            "requirements.txt",
            "requirements-prod.txt",
            "requirements-dev.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".env.example",
            "alembic.ini",
            "pytest.ini",
        ]

        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                issues.append(f"Missing required file: {file_path}")

        # Check for important directories
        required_dirs = [
            "app/api/endpoints",
            "app/services",
            "app/tasks",
            "app/models",
            "app/schemas",
            "tests",
            "docker",
            "scripts"
        ]

        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                issues.append(f"Missing required directory: {dir_path}")

        return len(issues) == 0, issues

    def validate_dependencies(self) -> Tuple[bool, List[str]]:
        """Validate dependency files and versions."""
        logger.info("Validating dependencies...")

        issues = []

        # Check requirements files
        req_files = ["requirements.txt", "requirements-prod.txt", "requirements-dev.txt"]
        for req_file in req_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text()
                    if len(content.strip()) == 0:
                        issues.append(f"Empty requirements file: {req_file}")

                    # Check for critical dependencies
                    critical_deps = ["fastapi", "sqlalchemy", "pydantic", "celery", "redis"]
                    missing_deps = []
                    for dep in critical_deps:
                        if dep not in content.lower():
                            missing_deps.append(dep)

                    if missing_deps:
                        issues.append(f"Missing critical dependencies in {req_file}: {missing_deps}")

                except Exception as e:
                    issues.append(f"Error reading {req_file}: {str(e)}")

        return len(issues) == 0, issues

    def validate_configuration(self) -> Tuple[bool, List[str]]:
        """Validate configuration files."""
        logger.info("Validating configuration...")

        issues = []

        # Check .env.example
        env_example = self.project_root / ".env.example"
        if env_example.exists():
            try:
                content = env_example.read_text()

                # Check for critical configuration keys
                critical_keys = [
                    "DATABASE_URL", "REDIS_URL", "JWT_SECRET_KEY",
                    "CELERY_BROKER_URL", "SECRET_KEY"
                ]

                for key in critical_keys:
                    if key not in content:
                        issues.append(f"Missing critical configuration key in .env.example: {key}")

            except Exception as e:
                issues.append(f"Error reading .env.example: {str(e)}")

        # Check Docker configuration
        docker_compose = self.project_root / "docker-compose.yml"
        if docker_compose.exists():
            try:
                content = docker_compose.read_text()

                # Check for required services
                required_services = ["postgres", "redis", "web", "worker"]
                for service in required_services:
                    if service not in content:
                        issues.append(f"Missing required service in docker-compose.yml: {service}")

            except Exception as e:
                issues.append(f"Error reading docker-compose.yml: {str(e)}")

        # Check Alembic configuration
        alembic_ini = self.project_root / "alembic.ini"
        if alembic_ini.exists():
            try:
                content = alembic_ini.read_text()
                if "sqlalchemy.url" not in content:
                    issues.append("Missing sqlalchemy.url in alembic.ini")
            except Exception as e:
                issues.append(f"Error reading alembic.ini: {str(e)}")

        return len(issues) == 0, issues

    def validate_code_structure(self) -> Tuple[bool, List[str]]:
        """Validate code structure and imports."""
        logger.info("Validating code structure...")

        issues = []

        # Check main application files
        main_py = self.project_root / "app" / "main.py"
        if main_py.exists():
            try:
                content = main_py.read_text()

                # Check for FastAPI app creation
                if "FastAPI(" not in content:
                    issues.append("FastAPI app not found in app/main.py")

                # Check for router inclusion
                if "include_router" not in content:
                    issues.append("No routers included in app/main.py")

            except Exception as e:
                issues.append(f"Error reading app/main.py: {str(e)}")

        # Check database configuration
        db_py = self.project_root / "app" / "core" / "database.py"
        if db_py.exists():
            try:
                content = db_py.read_text()

                # Check for async database setup
                if "AsyncSession" not in content:
                    issues.append("Async database session not configured")

                if "create_async_engine" not in content:
                    issues.append("Async database engine not configured")

            except Exception as e:
                issues.append(f"Error reading app/core/database.py: {str(e)}")

        # Check authentication setup
        auth_py = self.project_root / "app" / "core" / "auth.py"
        if auth_py.exists():
            try:
                content = auth_py.read_text()

                # Check for JWT and password handling
                if "jwt" not in content.lower():
                    issues.append("JWT authentication not implemented")

                if "bcrypt" not in content.lower() and "passlib" not in content.lower():
                    issues.append("Password hashing not implemented")

            except Exception as e:
                issues.append(f"Error reading app/core/auth.py: {str(e)}")

        return len(issues) == 0, issues

    def validate_docker_setup(self) -> Tuple[bool, List[str]]:
        """Validate Docker setup and configuration."""
        logger.info("Validating Docker setup...")

        issues = []

        # Check Dockerfile
        dockerfile = self.project_root / "Dockerfile"
        if dockerfile.exists():
            try:
                content = dockerfile.read_text()

                # Check for multi-stage build
                if "FROM python:" not in content:
                    issues.append("Dockerfile not using Python base image")

                # Check for security practices
                if "USER" not in content:
                    issues.append("Dockerfile not using non-root user")

                # Check for health check
                if "HEALTHCHECK" not in content:
                    issues.append("Dockerfile missing health check")

            except Exception as e:
                issues.append(f"Error reading Dockerfile: {str(e)}")

        # Check .dockerignore
        dockerignore = self.project_root / ".dockerignore"
        if not dockerignore.exists():
            issues.append("Missing .dockerignore file")

        # Check entrypoint scripts
        entrypoint = self.project_root / "docker" / "entrypoint.sh"
        if entrypoint.exists():
            try:
                content = entrypoint.read_text()

                # Check for database wait logic
                if "wait_for_db" not in content:
                    issues.append("Entrypoint script missing database wait logic")

            except Exception as e:
                issues.append(f"Error reading entrypoint script: {str(e)}")

        return len(issues) == 0, issues

    def validate_testing_setup(self) -> Tuple[bool, List[str]]:
        """Validate testing configuration and structure."""
        logger.info("Validating testing setup...")

        issues = []

        # Check pytest configuration
        pytest_ini = self.project_root / "pytest.ini"
        if pytest_ini.exists():
            try:
                content = pytest_ini.read_text()

                # Check for async testing support
                if "asyncio" not in content:
                    issues.append("pytest.ini missing asyncio configuration")

                # Check for coverage configuration
                if "cov" not in content:
                    issues.append("pytest.ini missing coverage configuration")

            except Exception as e:
                issues.append(f"Error reading pytest.ini: {str(e)}")

        # Check test structure
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.rglob("test_*.py"))
            if len(test_files) == 0:
                issues.append("No test files found in tests directory")

            # Check for conftest.py
            conftest = tests_dir / "conftest.py"
            if not conftest.exists():
                issues.append("Missing tests/conftest.py for test configuration")

        return len(issues) == 0, issues

    def validate_security_implementation(self) -> Tuple[bool, List[str]]:
        """Validate security implementation."""
        logger.info("Validating security implementation...")

        issues = []

        # Check authentication models
        auth_models = self.project_root / "app" / "models" / "auth.py"
        if auth_models.exists():
            try:
                content = auth_models.read_text()

                # Check for essential security models
                security_models = ["User", "Role", "Permission", "UserSession", "SecurityAuditLog"]
                for model in security_models:
                    if f"class {model}" not in content:
                        issues.append(f"Missing security model: {model}")

            except Exception as e:
                issues.append(f"Error reading auth models: {str(e)}")

        # Check authentication schemas
        auth_schemas = self.project_root / "app" / "schemas" / "auth.py"
        if auth_schemas.exists():
            try:
                content = auth_schemas.read_text()

                # Check for password validation
                if "password" not in content.lower():
                    issues.append("Missing password validation in auth schemas")

            except Exception as e:
                issues.append(f"Error reading auth schemas: {str(e)}")

        return len(issues) == 0, issues

    def validate_api_structure(self) -> Tuple[bool, List[str]]:
        """Validate API structure and endpoints."""
        logger.info("Validating API structure...")

        issues = []

        endpoints_dir = self.project_root / "app" / "api" / "endpoints"
        if endpoints_dir.exists():
            # Check for core endpoint files
            core_endpoints = ["auth.py", "kols.py", "campaigns.py"]
            for endpoint in core_endpoints:
                endpoint_path = endpoints_dir / endpoint
                if not endpoint_path.exists():
                    issues.append(f"Missing core API endpoint: {endpoint}")

        return len(issues) == 0, issues

    def validate_monitoring_setup(self) -> Tuple[bool, List[str]]:
        """Validate monitoring and observability setup."""
        logger.info("Validating monitoring setup...")

        issues = []

        # Check for monitoring configuration
        prometheus_config = self.project_root / "docker" / "prometheus.yml"
        if not prometheus_config.exists():
            issues.append("Missing Prometheus configuration")

        grafana_dir = self.project_root / "docker" / "grafana"
        if not grafana_dir.exists():
            issues.append("Missing Grafana configuration directory")

        return len(issues) == 0, issues

    def generate_recommendations(self, all_issues: List[str]) -> List[str]:
        """Generate recommendations based on found issues."""
        recommendations = []

        # Security recommendations
        if any("security" in issue.lower() for issue in all_issues):
            recommendations.append("Review and strengthen security implementations")
            recommendations.append("Ensure all authentication endpoints are properly secured")
            recommendations.append("Implement rate limiting and request validation")

        # Configuration recommendations
        if any("configuration" in issue.lower() or "missing" in issue.lower() for issue in all_issues):
            recommendations.append("Complete missing configuration files")
            recommendations.append("Validate all environment variables are properly set")
            recommendations.append("Ensure production secrets are not hardcoded")

        # Docker recommendations
        if any("docker" in issue.lower() for issue in all_issues):
            recommendations.append("Complete Docker configuration for production deployment")
            recommendations.append("Test Docker build and startup process")
            recommendations.append("Implement proper health checks for all services")

        # Testing recommendations
        if any("test" in issue.lower() for issue in all_issues):
            recommendations.append("Implement comprehensive test coverage")
            recommendations.append("Set up continuous integration testing")
            recommendations.append("Add integration tests for critical workflows")

        # Monitoring recommendations
        if any("monitoring" in issue.lower() or "prometheus" in issue.lower() for issue in all_issues):
            recommendations.append("Complete monitoring and observability setup")
            recommendations.append("Configure alerting for critical system metrics")
            recommendations.append("Set up log aggregation and analysis")

        # General recommendations
        recommendations.extend([
            "Perform load testing before production deployment",
            "Set up automated backup and recovery procedures",
            "Document deployment and operational procedures",
            "Implement proper logging and error tracking",
            "Review and update security policies regularly"
        ])

        return recommendations

    def run_validation(self) -> Dict[str, Any]:
        """Run complete system validation."""
        logger.info("Starting comprehensive system validation...")

        validation_categories = [
            ("file_structure", self.validate_file_structure),
            ("dependencies", self.validate_dependencies),
            ("configuration", self.validate_configuration),
            ("code_structure", self.validate_code_structure),
            ("docker_setup", self.validate_docker_setup),
            ("testing_setup", self.validate_testing_setup),
            ("security_implementation", self.validate_security_implementation),
            ("api_structure", self.validate_api_structure),
            ("monitoring_setup", self.validate_monitoring_setup),
        ]

        all_issues = []

        for category_name, validation_func in validation_categories:
            try:
                is_valid, issues = validation_func()
                self.validation_results["categories"][category_name] = {
                    "status": "PASS" if is_valid else "FAIL",
                    "issues": issues
                }
                all_issues.extend(issues)

                if is_valid:
                    logger.info(f"✅ {category_name}: PASS")
                else:
                    logger.warning(f"❌ {category_name}: FAIL ({len(issues)} issues)")

            except Exception as e:
                logger.error(f"Error validating {category_name}: {str(e)}")
                self.validation_results["categories"][category_name] = {
                    "status": "ERROR",
                    "issues": [f"Validation error: {str(e)}"]
                }
                all_issues.append(f"Validation error in {category_name}: {str(e)}")

        # Set overall status
        total_categories = len(validation_categories)
        passed_categories = sum(1 for cat in self.validation_results["categories"].values()
                               if cat["status"] == "PASS")

        if passed_categories == total_categories:
            self.validation_results["overall_status"] = "PASS"
        elif passed_categories >= total_categories * 0.8:
            self.validation_results["overall_status"] = "WARNING"
        else:
            self.validation_results["overall_status"] = "FAIL"

        # Store all issues and generate recommendations
        self.validation_results["issues"] = all_issues
        self.validation_results["recommendations"] = self.generate_recommendations(all_issues)

        return self.validation_results

    def print_report(self):
        """Print a formatted validation report."""
        results = self.validation_results

        print("\n" + "="*80)
        print("KOL MANAGEMENT SYSTEM - VALIDATION REPORT")
        print("="*80)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Overall Status: {results['overall_status']}")
        print("="*80)

        # Print category results
        print("\nCATEGORY RESULTS:")
        print("-" * 50)
        for category, result in results["categories"].items():
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} {category.replace('_', ' ').title()}: {result['status']}")

            if result["issues"]:
                for issue in result["issues"]:
                    print(f"    • {issue}")

        # Print summary
        total_issues = len(results["issues"])
        if total_issues > 0:
            print(f"\nISSUES SUMMARY ({total_issues} total):")
            print("-" * 50)
            for i, issue in enumerate(results["issues"], 1):
                print(f"{i}. {issue}")

        # Print recommendations
        if results["recommendations"]:
            print(f"\nRECOMMENDATIONS:")
            print("-" * 50)
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"{i}. {rec}")

        # Print conclusion
        print("\n" + "="*80)
        if results["overall_status"] == "PASS":
            print("🎉 VALIDATION PASSED: System appears ready for deployment!")
        elif results["overall_status"] == "WARNING":
            print("⚠️ VALIDATION WARNING: System has some issues but may be deployable.")
            print("   Address the issues above before production deployment.")
        else:
            print("❌ VALIDATION FAILED: System has critical issues that must be resolved.")
            print("   Please address all issues before attempting deployment.")
        print("="*80)

    def save_report(self, output_file: str = "validation_report.json"):
        """Save validation report to JSON file."""
        output_path = self.project_root / output_file
        try:
            with open(output_path, 'w') as f:
                json.dump(self.validation_results, f, indent=2)
            logger.info(f"Validation report saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")


def main():
    """Main entry point for the validation script."""
    try:
        validator = SystemValidator()

        # Run validation
        results = validator.run_validation()

        # Print report
        validator.print_report()

        # Save report
        validator.save_report()

        # Exit with appropriate code
        if results["overall_status"] == "PASS":
            sys.exit(0)
        elif results["overall_status"] == "WARNING":
            sys.exit(1)  # Warning level
        else:
            sys.exit(2)  # Critical issues

    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        sys.exit(3)


if __name__ == "__main__":
    main()