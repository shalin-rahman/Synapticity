# Skill: FastAPI Expert
# Usage: Use when building or refactoring RESTful backend services.

## Best Practices:
- **Dependency Injection:** Always use `Annotated` for dependencies to improve type checking and readability.
- **Pydantic v2:** Use `BaseModel` for all request/response schemas. Ensure proper `response_model` definitions in routes.
- **Background Tasks:** Use `BackgroundTasks` for non-blocking operations like sending emails or heavy processing.
- **Security:** Implement `OAuth2PasswordBearer` for authentication. Use `PassLib` with `bcrypt` for hashing.
- **Async:** Utilize `async def` for all path operations that perform I/O.

## Snippet: Annotated Dependency
```python
from typing import Annotated
from fastapi import Depends, FastAPI

def get_db(): ...

@app.get("/items/")
async def read_items(db: Annotated[Session, Depends(get_db)]):
    return db.query(Item).all()
```
