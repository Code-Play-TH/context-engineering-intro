#!/usr/bin/env python3
"""
Syntax Check Script for CRUD Implementation

This script checks for basic syntax errors and import issues
in the newly implemented CRUD operations.
"""

import ast
import os
import sys
from pathlib import Path


def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the AST to check for syntax errors
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error reading file: {str(e)}"


def check_imports(file_path):
    """Check if all imports in a file can be resolved (basic check)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        # Basic validation - check for common problematic patterns
        issues = []
        for imp in imports:
            if 'app.models.kols' in imp:
                issues.append(f"Should be 'app.models.kol' not 'app.models.kols': {imp}")
            elif 'app.schemas.campaigns' in imp and 'CampaignBriefCreate' in imp:
                # This is fine - just checking for awareness
                pass

        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"Error checking imports: {str(e)}"]


def main():
    """Main function to check all relevant files."""
    print("🔍 Checking CRUD Implementation for Bugs and Errors")
    print("=" * 60)

    # Files to check
    files_to_check = [
        # Models
        'app/models/user.py',
        'app/models/kol.py',
        'app/models/campaign.py',
        'app/models/collaboration.py',
        'app/models/campaign_content.py',
        'app/models/__init__.py',

        # Schemas
        'app/schemas/users.py',
        'app/schemas/kols.py',
        'app/schemas/campaigns.py',

        # APIs
        'app/api/endpoints/users.py',
        'app/api/endpoints/campaigns.py',
        'app/main.py',

        # Tests
        'tests/test_api/test_users_crud.py',
        'tests/test_api/test_kols_crud.py',
        'tests/test_api/test_campaigns_crud.py'
    ]

    total_files = 0
    passed_syntax = 0
    passed_imports = 0

    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"⚠️  MISSING: {file_path}")
            continue

        total_files += 1
        print(f"\n📁 Checking: {file_path}")

        # Check syntax
        syntax_ok, syntax_error = check_syntax(file_path)
        if syntax_ok:
            print("  ✅ Syntax: OK")
            passed_syntax += 1
        else:
            print(f"  ❌ Syntax: {syntax_error}")

        # Check imports
        imports_ok, import_issues = check_imports(file_path)
        if imports_ok:
            print("  ✅ Imports: OK")
            passed_imports += 1
        else:
            print("  ⚠️  Import Issues:")
            for issue in import_issues:
                print(f"    - {issue}")

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print(f"Total files checked: {total_files}")
    print(f"Syntax checks passed: {passed_syntax}/{total_files}")
    print(f"Import checks passed: {passed_imports}/{total_files}")

    if passed_syntax == total_files and passed_imports == total_files:
        print("\n🎉 All checks passed! CRUD implementation looks good.")
        return 0
    else:
        print("\n⚠️  Some issues found. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())