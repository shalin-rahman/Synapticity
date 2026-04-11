# Skill: Advanced Testing Strategies (TDD / BDD)
# Usage: Use to enforce high code quality, prevent regressions, and ensure requirements are met implicitly.

## 🧪 The Testing Pyramid
- **Unit Tests (70%)**: Fast, isolated tests for individual functions and classes. Mock all external dependencies.
- **Integration Tests (20%)**: Test the interaction between several units or external systems (e.g., Database, APIs).
- **End-to-End (E2E) Tests (10%)**: Slow, brittle tests that verify the system as a whole from the user's perspective.

## 🔄 Test-Driven Development (TDD) Lifecycle
1. **Red**: Write a failing test that defines a desired improvement or new function.
2. **Green**: Write the minimum amount of code to pass the test.
3. **Refactor**: Clean up the new code, ensuring it meets standards without breaking the test.

## 🗣️ Behavior-Driven Development (BDD)
- Tests should read like human specifications.
- Format using Given-When-Then:
  - **Given** some initial context (the preconditions).
  - **When** an action occurs.
  - **Then** ensure some outcomes.
- Naming convention: Test names should describe the behavior, not the method being tested. (e.g., `test_user_cannot_withdraw_more_than_balance()` vs `test_withdraw()`)

## 🛠️ Best Practices
- **F.I.R.S.T Principles**: Tests must be Fast, Independent, Repeatable, Self-Validating, and Timely.
- **Arrange, Act, Assert (AAA)**: Clearly separate test setup, execution, and verification.
- **Avoid Logic in Tests**: No `if`, `while`, or `switch` statements in test code. A test should be a straight path.
- **Test Only Public APIs**: Do not test private methods. Test them through the public interface they support.
- **Mock Interfaces, Not Concretions**: Ensures the tests are resilient to implementation details.

## 🚫 Anti-Patterns
- Interdependent tests (where test B fails if test A doesn't run first).
- Asserting on implementation details rather than outcomes.
- "Flaky" tests that fail randomly due to race conditions or external state.
