# Testing Setup for Meta Padel Rating System

## Overview

This document describes the testing infrastructure set up for the Meta Padel Rating System.

## Test Structure

```
tests/
├── __init__.py           # Tests package marker
├── conftest.py           # Test configuration and fixtures
├── test_basic.py         # Basic application setup tests
├── test_run_simple.py    # Simple model and route tests
├── pytest.ini            # Pytest configuration
├── requirements-test.txt # Testing dependencies
└── run_tests.py          # Test runner script
```

## Configuration

### TestingConfig (config.py)
The testing configuration has been enhanced with:
- In-memory SQLite database (`sqlite:///:memory:`)
- CSRF protection disabled for testing
- Temporary upload directories
- Test-specific secret key
- Sentry disabled for testing

### Test Dependencies (requirements-test.txt)
- `pytest==7.4.4` - Testing framework
- `pytest-flask==1.3.0` - Flask testing utilities
- `pytest-cov==4.1.0` - Coverage reporting
- `coverage==7.4.1` - Coverage measurement

## Running Tests

### Quick Start
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests with coverage
python run_tests.py
```

### Manual Testing
```bash
# Set testing environment
export FLASK_ENV=testing

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_basic.py -v

# Run with coverage report
python -m pytest tests/ --cov=app --cov-report=html
```

## Current Test Coverage

The test suite currently includes:

### Basic Application Tests (`test_basic.py`)
- ✅ Application creation with TestingConfig
- ✅ Database connection and table creation
- ✅ Test client functionality
- ✅ Configuration validation

### Model Tests (`test_run_simple.py`)
- ✅ User model creation with required fields
- ✅ Role model creation
- ✅ User password hashing and verification
- ✅ Basic route accessibility

### Coverage Report
Current coverage: **49%** (440/862 lines covered)

Key areas covered:
- Application initialization (93%)
- User forms (78%)
- Services (69%)
- Models (49% - basic functionality)
- User routes (35% - authentication flows)

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
- Form validation tests
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
3. **Configuration**: Verify FLASK_ENV=testing is set
4. **Dependencies**: Install test requirements with `pip install -r requirements-test.txt`

### Debug Mode
```bash
# Run tests with more verbose output
python -m pytest tests/ -v -s

# Run specific test with debugging
python -m pytest tests/test_basic.py::TestBasicSetup::test_app_creation -v -s
```

## Integration with CI/CD

The test suite is ready for integration with CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: pip install -r requirements-test.txt

- name: Run tests
  run: python run_tests.py
  env:
    FLASK_ENV: testing
```
