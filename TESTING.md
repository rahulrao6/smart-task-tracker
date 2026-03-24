# Testing Guide

## Test Structure

The test suite is organized into the following test modules:

### Unit Tests

- **test_jwt_auth.py** - JWT token generation and validation
- **test_rate_limit.py** - Rate limiting logic and exceptions
- **test_config.py** - Configuration and settings validation
- **test_auth.py** - Password hashing and user authentication
- **test_models.py** - Database models and relationships
- **test_services.py** - Business logic services

### Integration Tests

- **test_auth_endpoints.py** - Authentication REST endpoints (register, login, refresh, me)
- **test_api_integration.py** - API documentation, health checks, CORS, error handling
- **test_api_projects.py** - Project CRUD operations
- **test_api_tasks.py** - Task CRUD operations
- **test_logging_utils.py** - Logging utilities

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_auth_endpoints.py -v
```

### Run specific test class
```bash
pytest tests/test_auth_endpoints.py::TestAuthEndpoints -v
```

### Run specific test function
```bash
pytest tests/test_auth_endpoints.py::TestAuthEndpoints::test_register_user -v
```

### Run with coverage report
```bash
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

### Run with markers (e.g., slow tests)
```bash
pytest -m asyncio tests/ -v
```

## Test Coverage

Target: **>85% coverage** across all modules.

To view detailed coverage:
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Testing Best Practices

### Authentication Tests
- Test successful login with valid credentials
- Test failed login with invalid credentials
- Test token refresh and expiration
- Test unauthorized access without token
- Test token validation and verification

### API Tests
- Test successful operations (200, 201 status codes)
- Test client errors (400, 401, 403, 404)
- Test rate limiting (429 status code)
- Test CORS headers
- Test error response format

### Integration Tests
- Use fixtures for database setup/teardown
- Override dependencies for isolated testing
- Test complete workflows (e.g., register → login → access protected resource)
- Test error conditions and edge cases

### Performance Tests
- Test rate limiting effectiveness
- Test pagination with large datasets
- Monitor query performance

## Continuous Integration

Tests run automatically on:
- Push to main/develop branches
- Pull requests
- Scheduled weekly security checks

See `.github/workflows/tests.yml` for CI configuration.

## Test Fixtures

Common fixtures available in `tests/conftest.py`:

- **client** - AsyncClient for testing API
- **db_engine** - Test database engine
- **db_session** - Test database session
- **sample_project** - Sample project model
- **sample_task** - Sample task model
- **sample_tag** - Sample tag model
- **multiple_tasks** - Multiple task objects

## Authentication Testing

### User Registration
```python
response = await client.post(
    "/api/auth/register",
    json={"username": "user", "password": "secure123"},
)
```

### User Login
```python
response = await client.post(
    "/api/auth/login",
    json={"username": "user", "password": "secure123"},
)
```

### Protected Endpoint Access
```python
headers = {"Authorization": f"Bearer {access_token}"}
response = await client.get("/api/auth/me", headers=headers)
```

## Rate Limiting Testing

Rate limiting is tested in `test_rate_limit.py`:
- Per-IP limiting via middleware
- Per-user limiting on specific endpoints
- Reset timing and headers
- Exception handling

## Security Testing

Security tests run in CI pipeline:
- Bandit for code security analysis
- Safety for dependency vulnerabilities
- Docker image scanning with Trivy
- Linting with flake8
- Type checking with mypy

Run locally:
```bash
bandit -r src/
safety check
pip-audit
```

## Known Test Limitations

- Tests use in-memory SQLite database for speed
- Async tests require pytest-asyncio plugin
- Some integration tests may be slow due to database operations
- Rate limiting tests use mock time

## Troubleshooting

### AsyncIO errors
Ensure `pytest-asyncio` is installed and configured:
```bash
pip install pytest-asyncio
```

### Import errors
Make sure to run tests from project root:
```bash
cd /path/to/smart-task-tracker
pytest tests/
```

### Database errors
Ensure database is properly initialized and fixtures are used correctly.

## Adding New Tests

When adding new features:

1. Write test first (TDD approach)
2. Test the happy path
3. Test error cases
4. Test edge cases
5. Add integration tests for API endpoints
6. Update coverage report

Template for new test module:
```python
"""Tests for new feature."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestNewFeature:
    """Test new feature."""

    async def test_basic_functionality(self, client: AsyncClient):
        """Test basic functionality."""
        response = await client.get("/api/new-endpoint")
        assert response.status_code == 200
```
