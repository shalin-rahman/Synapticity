# Skill: Pytest Modern Standards (QA Professional)
# Usage: Use for unit, integration, and E2E testing in Python.

## Core Directives:
- **Fixtures:** Use `pytest.fixture` for setup/teardown. Avoid globals. Use `scope="session"` for database connections.
- **Parametrization:** Use `@pytest.mark.parametrize` to test multiple inputs against the same logic.
- **Mocks:** Use `unittest.mock` or `pytest-mock` (mocker) to isolate external dependencies.
- **Async:** Use `pytest-asyncio` and mark tests with `@pytest.mark.asyncio`.
- **Assertions:** Use standard `assert` with clear failure messages.

## Pattern: Clean Mocking
```python
@pytest.mark.asyncio
async def test_create_user(mocker, async_session):
    # Mock the external service
    mock_notify = mocker.patch("app.services.email.send_welcome")
    
    # Run logic
    user = await create_user(async_session, "test@example.com")
    
    assert user.id is not None
    mock_notify.assert_called_once_with("test@example.com")
```

## Maintenance:
- Keep `tests/` directory synchronized with `app/` structure.
- Use `conftest.py` for shared fixtures.
- Run with `--cov` to maintain visibility on test coverage.
