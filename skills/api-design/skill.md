# Skill: RESTful API Design & Best Practices
# Usage: Use when building robust, scalable, and consumer-friendly web APIs.

## 📡 REST Core Principles
- **Statelessness**: Every request from client to server must contain all of the information necessary to understand the request.
- **Resource-Based**: APIs should represent entities (resources) using URLs. Nouns, not verbs.
- **Standard Methods**: Use HTTP verbs correctly:
  - `GET`: Retrieve a resource (Safe, Idempotent).
  - `POST`: Create a new resource.
  - `PUT`: Update a resource entirely (Idempotent).
  - `PATCH`: Partially update a resource.
  - `DELETE`: Remove a resource (Idempotent).

## 🛣️ URL Structure
- Keep URLs clean and hierarchical.
  - Good: `GET /users/123/orders` (Get orders for user 123)
  - Bad: `GET /get_orders_for_user?id=123`
- Use plural nouns for collections: `/users`, `/products`, `/orders`.
- Use sub-resources for relations, but restrict depth to avoid complex routes (max 2 levels deep).

## 📄 Payloads & Responses
- Always consume and produce `application/json`.
- Return standardized success payloads.
- **Pagination**: Use cursor-based or limit/offset pagination for collections. Return metadata (`total`, `next_page_url`).
- **Filtering, Sorting, Field Selection**: Allow clients to shape the response via query parameters:
  - `GET /users?sort=-created_at&fields=id,name`
- **HATEOAS** (Optional but powerful): Include hypermedia links in responses to guide the client through state transitions.

## 🛡️ Error Handling
- Use standard HTTP status codes to indicate success or failure:
  - `200 OK`, `201 Created`, `204 No Content`
  - `400 Bad Request` (Client error/Validation failed)
  - `401 Unauthorized` (Authentication missing/invalid)
  - `403 Forbidden` (Authenticated, but lacks permissions)
  - `404 Not Found` (Resource doesn't exist)
  - `409 Conflict` (State violation, duplicate entry)
  - `500 Internal Server Error` (Server crashed - shouldn't happen)
- Provide a consistent, machine-readable error payload:
  `{"error": {"code": "VALIDATION_FAILED", "message": "Email is required", "details": [...]}}`

## 🔒 Security & Versioning
- Always use HTTPS.
- Use stateless auth mechanisms like JWT.
- Version the API early to prevent breaking changes for clients (e.g., `api.example.com/v1/users`). header-based versioning is also an accepted standard.
