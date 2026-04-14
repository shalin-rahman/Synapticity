```python
"""
Vault API - A Secure Data Management System

This FastAPI application provides a secure vault for storing sensitive data.
It includes user authentication, data encryption at rest, and access control mechanisms.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
import os
import time

# Configuration
DATABASE_URL = "postgresql+psycopg2://user:password@localhost/dbname"
SECRET_KEY = os.urandom(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app initialization
app = FastAPI()

# OAuth2 password bearer scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database setup
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Encryption key management
fernet = Fernet(SECRET_KEY)

# User model
class User(BaseModel):
    id: int
    email: EmailStr
    hashed_password: str

# Data model
class DataItem(BaseModel):
    user_id: int
    data: str
    encrypted_data: bytes

# Dependency to get database session
async def get_db():
    async with async_session() as db:
        yield db

# Dummy user store for demonstration purposes
users = {
    "user@example.com": User(id=1, email="user@example.com", hashed_password="hashed_password")
}

# Dummy data store for demonstration purposes
data_store = {}

# Authentication endpoint
@app.post("/token", response_model=User)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users.get(form_data.username)
    if not user or form_data.password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES
    return User(id=user.id, email=user.email)

# Data storage endpoint
@app.post("/data", response_model=DataItem)
async def store_data(data_item: DataItem, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = users.get(token)
    if not user or data_item.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    encrypted_data = fernet.encrypt(data_item.data.encode())
    data_store[data_item.id] = DataItem(user_id=data_item.user_id, data=data_item.data, encrypted_data=encrypted_data)
    return data_store[data_item.id]

# Data retrieval endpoint
@app.get("/data/{data_id}", response_model=DataItem)
async def retrieve_data(data_id: int, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    user = users.get(token)
    if not user or data_store[data_id].user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    decrypted_data = fernet.decrypt(data_store[data_id].encrypted_data).decode()
    return DataItem(user_id=data_store[data_id].user_id, data=decrypted_data, encrypted_data=data_store[data_id].encrypted_data)

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```