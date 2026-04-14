# Skill: Microservices & Distributed Systems
# Usage: Use when designing or interacting with scalable, independent service boundaries.

## 🕸️ Core Philosophy
- **Independent Deployability**: A single microservice can be changed and deployed independently of the rest of the system.
- **Loose Coupling**: Services should know as little about each other as possible.
- **High Cohesion**: Related behavior should be grouped together.

## 📡 Communication Patterns
- **Synchronous (REST/gRPC)**: Use when an immediate response is required. Be wary of tight coupling and cascading failures.
- **Asynchronous (Pub/Sub, Event Streaming)**: Prefer async communication using message brokers (RabbitMQ, Kafka, Azure Service Bus) for high availability and decoupling.
- **Event-Driven Architecture**: Services react to events emitted by other services rather than direct calls.

## 🗄️ Data Management
- **Database per Service**: Each microservice must have its own private database to ensure loose coupling. Never share a DB.
- **Saga Pattern**: Manage distributed transactions across multiple services using a sequence of local transactions, coordinated by a central orchestrator or choreography.
- **CQRS (Command Query Responsibility Segregation)**: Separate the models used for updating data (Commands) from the models used for reading data (Queries).
- **Event Sourcing**: Store the state of a domain entity as a sequence of state-changing events.

## 🛡️ Resilience & Fault Tolerance
- **Circuit Breaker Pattern**: Prevent failures in a downstream service from cascading upstream by quickly failing calls to an unhealthy service.
- **Retry with Exponential Backoff**: Handle transient networking issues gracefully.
- **Bulkheads**: Isolate resources (like connection pools) for different services to prevent one failing service from exhausting all resources.
- **Timeouts**: Always set timeouts on network calls.

## 🚫 Anti-Patterns
- **Distributed Monolith**: Services are deployed separately but are tightly coupled (e.g., sharing a database, synchronous chatty communication).
- Building microservices without robust automated deployment and monitoring in place.
