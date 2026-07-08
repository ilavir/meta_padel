#!/usr/bin/env python3
"""
Test runner for Meta Padel Rating System

Delegates to `uv run pytest`, which manages the isolated virtual
environment and test dependencies declared in pyproject.toml.
"""
import os
import sys
import subprocess


def run_tests():
    """Run the test suite via uv."""
    # Set testing environment
    os.environ['FLASK_ENV'] = 'testing'

    cmd = ['uv', 'run', 'pytest'] + sys.argv[1:]

    print("Running Meta Padel Rating System tests...")
    print("=" * 50)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
    else:
        print("\n" + "=" * 50)
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    run_tests()
