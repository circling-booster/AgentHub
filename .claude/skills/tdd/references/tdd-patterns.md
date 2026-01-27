# TDD Patterns Reference

## Table of Contents

1. [BDD Patterns](#bdd-patterns)
2. [Test Fixtures](#test-fixtures)
3. [Mocking Patterns](#mocking-patterns)
4. [Async Testing](#async-testing)
5. [Parametrized Tests](#parametrized-tests)
6. [Integration Test Patterns](#integration-test-patterns)

---

## BDD Patterns

### Given-When-Then Structure

```python
def test_feature_description():
    """
    Given [precondition/context]
    When [action/trigger]
    Then [expected outcome]
    """
    # Given - Setup
    context = setup_context()

    # When - Action
    result = perform_action(context)

    # Then - Assertion
    assert result == expected_value
```

### pytest-bdd Integration

```python
# features/login.feature
Feature: User Login
    Scenario: Successful login
        Given a registered user with email "test@example.com"
        When the user logs in with correct password
        Then an access token is returned

# tests/test_login.py
from pytest_bdd import scenario, given, when, then

@scenario('features/login.feature', 'Successful login')
def test_successful_login():
    pass

@given('a registered user with email "test@example.com"')
def registered_user():
    return create_user(email="test@example.com")

@when('the user logs in with correct password')
def login_user(registered_user):
    return login(registered_user.email, "password")

@then('an access token is returned')
def verify_token(login_user):
    assert login_user.token is not None
```

---

## Test Fixtures

### Basic Fixture

```python
import pytest

@pytest.fixture
def sample_user():
    """Create a test user."""
    return {"id": 1, "name": "Test User", "email": "test@example.com"}

def test_user_email(sample_user):
    assert "@" in sample_user["email"]
```

### Fixture with Cleanup

```python
@pytest.fixture
def database_connection():
    """Setup and teardown database connection."""
    conn = create_connection()
    yield conn
    conn.close()  # Cleanup after test
```

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def app_config():
    """Session-scoped config loaded once."""
    return load_config("test")

@pytest.fixture
def api_client(app_config):
    """Create API client for each test."""
    return APIClient(app_config)
```

---

## Mocking Patterns

### Basic Mock

```python
from unittest.mock import Mock, patch

def test_with_mock():
    mock_service = Mock()
    mock_service.get_data.return_value = {"status": "ok"}

    result = process_data(mock_service)

    mock_service.get_data.assert_called_once()
    assert result["status"] == "ok"
```

### Patch Decorator

```python
@patch('module.external_api.fetch')
def test_with_patch(mock_fetch):
    mock_fetch.return_value = {"data": [1, 2, 3]}

    result = get_processed_data()

    assert len(result) == 3
```

### Context Manager Patch

```python
def test_with_context_patch():
    with patch('module.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2024, 1, 1)
        result = get_current_date()
        assert result.year == 2024
```

---

## Async Testing

### pytest-asyncio

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await fetch_data_async()
    assert result is not None

@pytest.fixture
async def async_client():
    client = await create_async_client()
    yield client
    await client.close()

@pytest.mark.asyncio
async def test_with_async_fixture(async_client):
    response = await async_client.get("/api/data")
    assert response.status == 200
```

---

## Parametrized Tests

### Basic Parametrize

```python
import pytest

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
])
def test_double(input, expected):
    assert double(input) == expected
```

### Multiple Parameters

```python
@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, 200, 300),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

### Parametrize with IDs

```python
@pytest.mark.parametrize("user_role,can_delete", [
    pytest.param("admin", True, id="admin-can-delete"),
    pytest.param("user", False, id="user-cannot-delete"),
    pytest.param("guest", False, id="guest-cannot-delete"),
])
def test_delete_permission(user_role, can_delete):
    user = create_user(role=user_role)
    assert user.can_delete() == can_delete
```

---

## Integration Test Patterns

### Database Integration

```python
import pytest

@pytest.fixture(scope="function")
def db_session():
    """Create isolated database session for each test."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()

def test_create_user(db_session):
    user = User(name="Test", email="test@example.com")
    db_session.add(user)
    db_session.commit()

    saved = db_session.query(User).filter_by(email="test@example.com").first()
    assert saved is not None
    assert saved.name == "Test"
```

### API Integration

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_api_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_post(client):
    response = client.post("/api/users", json={
        "name": "Test User",
        "email": "test@example.com"
    })
    assert response.status_code == 201
    assert "id" in response.json()
```

### External Service Integration

```python
@pytest.fixture
def mock_external_service():
    """Mock external service for integration tests."""
    with patch('services.external.client') as mock:
        mock.fetch.return_value = {"status": "success"}
        yield mock

def test_workflow_with_external(mock_external_service, db_session):
    # Test full workflow with mocked external dependency
    result = process_workflow(db_session)
    assert result.status == "completed"
    mock_external_service.fetch.assert_called()
```
