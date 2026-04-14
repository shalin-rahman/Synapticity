## Architecture

The system is built using FastAPI, a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints. The architecture includes the following components:

1. **FastAPI Application:** The core of the application that handles incoming requests and routes them to the appropriate endpoints.
2. **OAuth2 Authentication:** For user authentication, using OAuth2 password flow.
3. **Pydantic Models:** Data validation and settings management using Pydantic models.
4. **SQLAlchemy ORM:** Asynchronous ORM for database operations.
5. **PostgreSQL Database:** The relational database used to store user data and encrypted data.
6. **Cryptography Library:** For encrypting and decrypting data at rest.

## Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 12+

### Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/vault-api.git
   cd vault-api
   ```

2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies:**
   ```bash
   pip install fastapi[all] pydantic sqlalchemy psycopg2-binary cryptography uvicorn
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the project root and add the following:
   ```
   DATABASE_URL=postgresql+psycopg2://user:password@localhost/dbname
   SECRET_KEY=$(openssl rand -hex 32)
   ```

5. **Initialize Database:**
   ```bash
   uvicorn main:app --reload
   ```
   This will create the necessary tables in your PostgreSQL database.

6. **Run the Application:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## API Reference

### User Authentication

#### Register a New User
**Endpoint:** `/token`
**Method:** `POST`
**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "password"
}
```
**Response:**
- **Success:** Returns the user details.
- **Failure:** HTTP 401 Unauthorized if credentials are incorrect.

#### Login and Get Access Token
**Endpoint:** `/token`
**Method:** `POST`
**Request Body:**
```json
{
  "username": "user@example.com",
  "password": "password"
}
```
**Response:**
- **Success:** Returns the access token.
- **Failure:** HTTP 401 Unauthorized if credentials are incorrect.

### Data Management

#### Store Data
**Endpoint:** `/data`
**Method:** `POST`
**Request Body:**
```json
{
  "user_id": 1,
  "data": "sensitive_data"
}
```
**Response:**
- **Success:** Returns the stored data with encrypted data.
- **Failure:** HTTP 403 Forbidden if access is denied.

#### Retrieve Data
**Endpoint:** `/data/{data_id}`
**Method:** `GET`
**Response:**
- **Success:** Returns the decrypted data.
- **Failure:** HTTP 403 Forbidden if access is denied.

## Security Summary

### Password Hashing
User passwords are hashed using a strong hashing algorithm (HS256) before being stored in the database. This ensures that even if the database is compromised, the actual passwords remain secure.

### CSRF Protection
CSRF tokens are used to protect against cross-site request forgery attacks. These tokens must be included in all requests that modify user data.

### Data Encryption at Rest
All sensitive data stored in the database is encrypted using AES-256-GCM. This ensures that even if an attacker gains access to the database, they cannot read the encrypted data without the encryption key.

### Database Connections
Database connections are secured using SSL/TLS to prevent man-in-the-middle attacks and ensure secure communication between the application and the database.

## Usage Examples

### Register a New User
```python
import requests

response = requests.post("http://localhost:8000/token", json={"username": "user@example.com", "password": "password"})
print(response.json())
```

### Login and Get Access Token
```python
import requests

response = requests.post("http://localhost:8000/token", json={"username": "user@example.com", "password": "password"})
access_token = response.json().get("id")
print(access_token)
```

### Store Data
```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}
data = {
    "user_id": 1,
    "data": "sensitive_data"
}
response = requests.post("http://localhost:8000/data", json=data, headers=headers)
print(response.json())
```

### Retrieve Data
```python
import requests

headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("http://localhost:8000/data/1", headers=headers)
print(response.json())
```

This documentation provides a comprehensive guide to setting up and using the secure FastAPI encrypted vault. It covers all the necessary aspects, from architecture and installation to API reference and usage examples.