#!/usr/bin/env python3
"""
Test runner for Meta Padel Rating System
"""
import os
import sys
import subprocess


def run_tests():
    """Run the test suite."""
    # Set testing environment
    os.environ['FLASK_ENV'] = 'testing'
    
    # Run pytest with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--cov=app',
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov'
    ]
    
    print("Running Meta Padel Rating System tests...")
    print("=" * 50)
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/")
    else:
        print("\n" + "=" * 50)
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    run_tests()
