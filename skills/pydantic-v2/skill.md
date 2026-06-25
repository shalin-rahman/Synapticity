# Skill: Pydantic v2 — Official Patterns
# Source: docs.pydantic.dev/latest/

## Model Definition
```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    email: str
    score: Annotated[float, Field(ge=0.0, le=1.0)] = 0.0
```

## Validators
```python
@field_validator("email")
@classmethod
def email_must_have_at(cls, v: str) -> str:
    if "@" not in v:
        raise ValueError("Invalid email")
    return v.lower()

@model_validator(mode="after")
def check_consistency(self) -> "User":
    if self.score > 0 and not self.email:
        raise ValueError("Active users need email")
    return self
```

## Settings (pydantic-settings)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    api_key: str
    debug: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()  # reads from env/.env automatically
```

## Serialisation
```python
user.model_dump()                         # dict
user.model_dump(exclude_none=True)        # skip None fields
user.model_dump_json()                    # JSON string
User.model_validate({"id": 1, ...})       # parse from dict (v2 API)
User.model_validate_json('{"id":1,...}')  # parse from JSON string
```

## Key v1 → v2 Changes
| v1 | v2 |
|---|---|
| `validator` | `field_validator` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `parse_obj()` | `model_validate()` |
| `Config` class | `model_config = SettingsConfigDict(...)` |
| `__fields__` | `model_fields` |
