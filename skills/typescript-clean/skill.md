# Skill: TypeScript Clean Code (Staff Engineer)
# Usage: Use for any TypeScript-based project to ensure enterprise-grade type safety and readability.

## Core Rules:
- **Strict Typing:** Never use `any`. Use `unknown` with type guards if the type is truly uncertain.
- **Interfaces vs Types:** Use `interface` for public APIs (extendability) and `type` for unions, intersections, and primitives.
- **Functional Patterns:** Prioritize immutability. Use `readonly` for arrays and objects where possible.
- **Error Handling:** Use custom `Error` classes or the `Result` pattern (e.g., `{ success: true, data: T } | { success: false, error: E }`) for predictable logic.
- **Naming:** Use `PascalCase` for classes/interfaces, `camelCase` for variables/functions, and `UPPER_SNAKE_CASE` for constants.

## Pattern: Discriminated Union
```typescript
type ApiResponse<T> = 
  | { status: 'success'; data: T }
  | { status: 'error'; message: string; code: number };

function handle(res: ApiResponse<User>) {
  if (res.status === 'success') {
    return res.data.name; // Type is narrowed
  }
}
```

## Maintenance:
- Keep functions small and single-purpose (SOLID principles).
- Use Template Literal Types for complex string configurations.
- Prefer `Record<K, V>` over index signatures.
