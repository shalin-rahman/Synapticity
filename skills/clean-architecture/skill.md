# Skill: Clean Architecture & Hexagonal Architecture (Ports and Adapters)
# Usage: Use when designing application structure to ensure separation of concerns and testability.

## 🏛️ Core Principles
- **Dependency Rule**: Source code dependencies must only point INWARD, toward higher-level policies (the domain).
- **Independence**: The architecture must be independent of frameworks, databases, and external interfaces.
- **Testability**: The business rules can be tested without the UI, Database, Web Server, or any other external element.

## 🍰 Architectural Layers (Inside-Out)
1. **Entities / Domain Model**: Enterprise-wide business rules. Plain objects without external dependencies.
2. **Use Cases / Application Services**: Application-specific business rules. Orchestrates the flow of data to and from entities.
3. **Interface Adapters (Controllers, Gateways, Presenters)**: Converts data from the format most convenient for use cases to the format most convenient for external agencies (e.g., Web, DB).
4. **Frameworks & Drivers**: The outermost layer. Contains details like the Database, Web Framework, or UI. Keep this layer thin.

## 🔌 Hexagonal Concepts (Ports and Adapters)
- **Ports**: Interfaces/Contracts defined in the Application core.
  - *Driving Ports* (Inbound): How external systems interact with the core (e.g., an API endpoint calling a use case).
  - *Driven Ports* (Outbound): How the core interacts with external systems (e.g., a repository interface for DB access).
- **Adapters**: Implementations of the Ports, living in the outer layer.
  - *Driving Adapters*: Controllers handling HTTP requests and invoking driving ports.
  - *Driven Adapters*: SQL repositories implementing the driven port interfaces.

## 🚫 Anti-Patterns
- Leaking database details (e.g., ORM models) into the Use Case or Domain layers.
- Depending on a web framework (like FastAPI or Express) inside the core business logic.
- Mocking the database framework directly in tests instead of mocking the repository interface.
