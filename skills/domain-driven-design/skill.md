# Skill: Domain-Driven Design (DDD)
# Usage: Use when modeling complex business domains to ensure code reflects the real-world business vocabulary and rules.

## 🧠 Core Philosophy
- Focus on the core domain and domain logic.
- Base complex designs on a model of the domain.
- Collaborate constantly with domain experts to improve the application model and resolve any emerging domain issues.

## 🗣️ Ubiquitous Language
- The source code must speak the same language as the business experts. 
- Avoid technical jargon in domain classes. If the business calls it a "Subscriber", do not name the class `UserAccount`.

## 📦 Strategic Design (Macro)
- **Bounded Contexts**: Explicit boundaries within which a domain model is defined and applicable. A `Product` in the Sales context is different from a `Product` in the Shipping context.
- **Context Mapping**: Defining how different Bounded Contexts integrate (e.g., Anti-Corruption Layer, Shared Kernel).

## 🧩 Tactical Design (Micro)
- **Entities**: Objects with a distinct identity that persists over time (e.g., a specific Order).
- **Value Objects**: Immutable objects that describe characteristics but have no conceptual identity. Equality is based on state, not identity (e.g., Money, Address). Favor Value Objects over Primitives.
- **Aggregates**: A cluster of domain objects that can be treated as a single unit. 
- **Aggregate Root**: The only entity in the Aggregate that outside objects are allowed to hold references to. It ensures the consistency of the entire Aggregate.
- **Repositories**: Mechanisms to retrieve and store Aggregates. Only Aggregate Roots have Repositories.
- **Domain Events**: A record of something of business significance that happened in the past. Used to communicate between aggregates or contexts.

## 🚫 Anti-Patterns
- **Anemic Domain Model**: Classes that have state but no behavior (just getters and setters), while business logic sits in procedural service classes.
- Allowing Aggregates to reference other Aggregates' internal entities directly. Always reference by ID.
