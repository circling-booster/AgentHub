---
name: tdd
description: Test-Driven Development workflow skill that enforces the Red-Green-Refactor cycle. Use when (1) implementing new features - automatically suggest TDD approach, (2) user explicitly calls /tdd command, (3) fixing bugs - write failing test first, (4) refactoring code - ensure tests exist before changes. Supports pytest with coverage tracking, optional BDD patterns (Given-When-Then), and integrates with the project's test structure.
---

# TDD Workflow

## Overview

Enforce Test-Driven Development practices by following the Red-Green-Refactor cycle. Write tests before implementation, ensure minimal code to pass tests, then refactor with confidence.

## Workflow

### Phase 1: Red (Write Failing Test)

1. **Understand the requirement** - Clarify what needs to be implemented
2. **Write test first** - Create a test that defines expected behavior
3. **Run test** - Confirm it fails for the right reason

```python
# Example: Testing a new function
def test_calculate_total_with_discount():
    # Given
    items = [{"price": 100}, {"price": 200}]
    discount = 0.1

    # When
    result = calculate_total(items, discount)

    # Then
    assert result == 270  # (100 + 200) * 0.9
```

### Phase 2: Green (Minimal Implementation)

1. **Write minimum code** to make the test pass
2. **No extra features** - Only what's needed for the test
3. **Run test** - Confirm it passes

```python
# Minimal implementation
def calculate_total(items: list, discount: float = 0) -> float:
    total = sum(item["price"] for item in items)
    return total * (1 - discount)
```

### Phase 3: Refactor

1. **Improve code quality** while keeping tests green
2. **Remove duplication**, improve naming, simplify logic
3. **Run tests after each change** - Ensure nothing breaks

## Test Structure

Follow pytest conventions:

```
project/
├── src/
│   └── module.py
└── tests/
    ├── __init__.py
    ├── conftest.py      # Shared fixtures
    ├── test_module.py   # Unit tests
    └── integration/     # Integration tests (optional)
```

## Commands

### Run Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

### Run Specific Test
```bash
pytest tests/test_module.py::test_function_name -v
```

## Coverage Guidelines

- **Target:** 80%+ line coverage for new code
- **Critical paths:** 100% coverage for business logic
- **Check coverage:** Run `pytest --cov` before completing implementation

## BDD Pattern (Optional)

For behavior-focused tests, use Given-When-Then structure. See [references/tdd-patterns.md](references/tdd-patterns.md) for detailed patterns.

```python
def test_user_login_with_valid_credentials():
    """
    Given a registered user
    When they login with correct credentials
    Then they should receive an access token
    """
    # Given
    user = create_test_user(email="test@example.com", password="secret")

    # When
    result = login(email="test@example.com", password="secret")

    # Then
    assert result.access_token is not None
    assert result.user_id == user.id
```

## TDD Checklist

Before implementation:
- [ ] Requirement is clear
- [ ] Test file exists or created
- [ ] Test is written and fails

During implementation:
- [ ] Minimal code written
- [ ] Test passes
- [ ] No hardcoded values (except constants)

After implementation:
- [ ] Code refactored if needed
- [ ] All tests still pass
- [ ] Coverage meets target (80%+)

## Auto-Detection Triggers

This skill is automatically suggested when:
- User requests "implement", "add feature", "create function"
- User mentions "bug fix" or "fix"
- User asks for "refactor" without existing tests

## Manual Invocation

Use `/tdd` command to explicitly enter TDD mode for any task.
