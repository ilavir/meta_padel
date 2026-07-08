# Testing Setup for Meta Padel Rating System

## Overview

This document describes the testing infrastructure set up for the Meta Padel Rating System.

## Test Structure

```
tests/
├── conftest.py           # Test configuration and fixtures
├── test_forms.py         # Form validation tests
└── test_scheduler.py     # Scheduler job and lock-recovery tests
```

## Configuration

### TestingConfig (config.py)
The testing configuration has been enhanced with:
- In-memory SQLite database (`sqlite:///:memory:`)
- CSRF protection disabled for testing
- Temporary upload directories
- Test-specific secret key
- Sentry disabled for testing

### Tooling and Test Dependencies
Dependencies are managed with [`uv`](https://docs.astral.sh/uv/), with
`pyproject.toml` as the single source of truth. Runtime dependencies live
under `[project.dependencies]`; test-only dependencies live in the
`test` dependency group (PEP 735) under `[dependency-groups]`:
- `pytest==7.4.4` - Testing framework
- `pytest-flask==1.3.0` - Flask testing utilities
- `pytest-cov==4.1.0` - Coverage reporting
- `coverage==7.4.1` - Coverage measurement
- `aiosmtpd==1.4.6`, `atpublic==6.0.1` - Local SMTP support used by email tests

The `test` group is a default group (see `[tool.uv]` in `pyproject.toml`),
so `uv run` includes it automatically.

Production's Docker image is unaffected: it still installs from
`requirements.txt`, which is regenerated from `uv.lock` via
`uv export --no-default-groups --no-annotate --no-hashes -o requirements.txt`
whenever dependencies change.

## Running Tests

### Quick Start
```bash
# Run all tests with coverage (uv manages the isolated .venv automatically)
uv run pytest
```

### Manual Testing
```bash
# Run all tests
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_scheduler.py -v

# Run a subset by keyword
uv run pytest tests/test_scheduler.py -k "liveness or acquire" -v
```

Coverage (`--cov=app --cov-report=term-missing`) and pytest options are
configured in `pyproject.toml` under `[tool.pytest.ini_options]`, so no
extra flags are needed. Coverage is reported to the terminal only - no
HTML report (`htmlcov/`) is generated.

There is no MariaDB dependency for tests: the suite uses an in-memory
SQLite database, a mocked `BackgroundScheduler`, and `tempfile`/`tmp_path`
for filesystem interactions, so `uv run pytest` works standalone.

## Current Test Coverage

The test suite currently includes:

### Scheduler Tests (`test_scheduler.py`)
- ✅ `update_rankings_job` execution, error handling, and app-context creation
- ✅ `init_scheduler` enable/disable and lock acquisition behavior
- ✅ Lock-file liveness helpers (`_read_lock_pid`, `_is_process_alive`)
- ✅ Atomic lock acquisition and stale-lock reclaim (`_acquire_scheduler_lock`)
- ✅ End-to-end recovery: a lock left behind by a hard-killed worker (dead
  PID) is reclaimed and the scheduler starts; a lock held by a live
  process blocks a second worker from starting its own scheduler

### Form Tests (`test_forms.py`)
- ✅ Avatar file size validation
- ✅ Avatar-related configuration checks

## Scheduler Lock Recovery

`app/scheduler.py` uses a PID-based lock file (`/tmp/scheduler_lock`) so
only one Gunicorn worker runs the ranking-update job. If a worker is
killed hard (e.g. a `WORKER TIMEOUT` → `SIGKILL`, often from OOM), its
`atexit` cleanup never runs and the lock file can be left behind holding
a dead PID. On the next `init_scheduler` call, the stored PID's liveness
is checked (`os.kill(pid, 0)`); a dead or invalid PID causes the stale
lock to be removed and atomically reclaimed, so the scheduler self-heals
without requiring a container restart. A guarded `SIGTERM` handler also
runs the same cleanup on graceful shutdown, chaining to any
previously-installed handler (e.g. Gunicorn's own) so existing shutdown
behavior is preserved.

## Test Fixtures

The `conftest.py` provides several fixtures:

- `app` - Flask application with testing config
- `client` - Test client for HTTP requests
- `runner` - CLI test runner
- `db_session` - Database session with transaction rollback
- `temp_upload_dir` - Temporary directory for file uploads
- `sample_user` - Pre-created user for testing
- `admin_user` - Pre-created admin user
- `authenticated_client` - Client with logged-in user session

## Best Practices

1. **Isolation**: Each test is isolated with fresh database state
2. **Cleanup**: Tests clean up after themselves
3. **Realistic Data**: Tests use realistic user data with required fields
4. **Environment**: Tests run in dedicated testing environment
5. **Coverage**: Coverage reports help identify untested code

## Future Enhancements

Areas for additional test coverage:
- Rating system functionality
- File upload handling
- User authentication flows
- Admin functionality
- API endpoints
- Error handling

## Troubleshooting

### Common Issues

1. **Database Constraints**: Ensure test data includes all required fields
2. **Import Errors**: Check that imported modules exist and are accessible
3. **Dependencies**: Run `uv sync` to make sure the `.venv` is up to date
   with `pyproject.toml` / `uv.lock`

### Debug Mode
```bash
# Run tests with more verbose output
uv run pytest tests/ -v -s

# Run a specific test with debugging
uv run pytest tests/test_scheduler.py::TestAcquireSchedulerLock::test_fresh_lock_is_acquired -v -s
```

## Integration with CI/CD

The test suite is ready for integration with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install uv
  uses: astral-sh/setup-uv@v3

- name: Run tests
  run: uv run pytest
```
