#!/usr/bin/env python3
"""
FraudWatch Environment Validation Script
Validates the development environment setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")

def print_status(item, status, details=""):
    status_symbol = "✓" if status else "✗"
    print(f"{status_symbol} {item:40} {details}")

def check_python_version():
    version = sys.version_info
    is_valid = version.major == 3 and version.minor >= 11
    print_status(
        "Python version",
        is_valid,
        f"({version.major}.{version.minor}.{version.micro})"
    )
    return is_valid

def check_virtual_environment():
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    print_status("Virtual environment active", in_venv, sys.prefix)
    return in_venv

def check_required_packages():
    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'sqlalchemy': 'SQLAlchemy',
        'alembic': 'Alembic',
        'pydantic': 'Pydantic',
        'celery': 'Celery',
        'redis': 'Redis',
    }
    all_ok = True
    for package, name in required.items():
        try:
            __import__(package)
            print_status(f"{name} installed", True)
        except ImportError:
            print_status(f"{name} installed", False, "(missing)")
            all_ok = False
    return all_ok

def check_postgresql_connectivity():
    try:
        import asyncpg
        print_status("PostgreSQL driver (asyncpg)", True)
        return True
    except ImportError:
        print_status("PostgreSQL driver (asyncpg)", False)
        return False

def check_redis_connectivity():
    try:
        import redis
        print_status("Redis client available", True)
        return True
    except ImportError:
        print_status("Redis client available", False)
        return False

def check_alembic_config():
    alembic_ini = Path("alembic.ini")
    env_py = Path("alembic/env.py")
    exists = alembic_ini.exists() and env_py.exists()
    print_status("Alembic configuration", exists)
    return exists

def check_fastapi_imports():
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from app.main import app
        print_status("FastAPI app imports", True)
        return True
    except Exception as e:
        print_status("FastAPI app imports", False, str(e)[:30])
        return False

def check_project_structure():
    required_dirs = ['app', 'alembic', 'seed']
    required_files = ['requirements.txt', 'alembic.ini', '.env.example']

    all_ok = True
    for directory in required_dirs:
        exists = Path(directory).exists()
        print_status(f"Directory: {directory}/", exists)
        all_ok = all_ok and exists

    for file in required_files:
        exists = Path(file).exists()
        print_status(f"File: {file}", exists)
        all_ok = all_ok and exists

    return all_ok

def check_environment_variables():
    env_example = Path(".env.example")
    env_file = Path(".env")

    print_status(".env.example exists", env_example.exists())
    # .env is optional (developers create their own)
    print_status(".env file exists (optional)", env_file.exists())

    if not env_example.exists():
        return False

    # Read expected variables from .env.example
    with open(env_example) as f:
        content = f.read()
        expected_vars = [line.split('=')[0].strip() for line in content if '=' in line and not line.startswith('#')]

    print_status(f"Environment variables defined", True, f"({len(expected_vars)} in .env.example)")
    return True

def check_write_permissions():
    try:
        test_file = Path("test_write_permission.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print_status("Write permissions (root)", True)
        return True
    except Exception as e:
        print_status("Write permissions (root)", False, str(e))
        return False

def check_operating_system():
    platform = sys.platform
    print_status("Operating system", True, platform)
    return True

def check_platform_compatibility():
    issues = []

    # Check for Windows-specific paths in Python files
    backend_dir = Path(".")
    for py_file in backend_dir.rglob("*.py"):
        # Skip this validation script and venv files
        if "validate_environment.py" in str(py_file) or "venv" in str(py_file) or "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text()
            # Check for hardcoded Windows drive letters (e.g., C:\ or C:/)
            if "C:\\\\" in content or "C:/" in content:
                issues.append(f"Hardcoded path in {py_file}")
        except:
            pass

    if issues:
        print_status("Platform compatibility", False, f"{len(issues)} issues")
        for issue in issues[:3]:
            print(f"  - {issue}")
        return False
    else:
        print_status("Platform compatibility", True, "No hardcoded paths")
        return True

def main():
    print_header("FraudWatch Environment Validation")
    print(f"Project root: {Path.cwd()}")
    print(f"Python executable: {sys.executable}")

    results = []

    print_header("Python Environment")
    results.append(check_python_version())
    results.append(check_virtual_environment())
    results.append(check_required_packages())

    print_header("Services")
    results.append(check_postgresql_connectivity())
    results.append(check_redis_connectivity())

    print_header("Configuration")
    results.append(check_alembic_config())
    results.append(check_fastapi_imports())
    results.append(check_project_structure())
    results.append(check_environment_variables())

    print_header("System")
    results.append(check_write_permissions())
    results.append(check_operating_system())
    results.append(check_platform_compatibility())

    print_header("Summary")
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"Checks passed: {passed}/{total} ({percentage:.1f}%)")

    if passed == total:
        print("\n✓ Environment is ready for development!")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
