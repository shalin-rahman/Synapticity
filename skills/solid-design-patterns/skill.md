# Skill: SOLID Principles & Design Patterns (Principal Engineer)

This playbook defines the mandatory architectural standards for class design and system structure.

## 🧱 The SOLID Principles
- **S: Single Responsibility**: A class or function should have exactly one reason to change.
- **O: Open/Closed**: Software entities should be open for extension but closed for modification. Use inheritance or composition.
- **L: Liskov Substitution**: Objects of a superclass should be replaceable with objects of its subclasses without breaking the application.
- **I: Interface Segregation**: No client should be forced to depend on methods it does not use. Keep interfaces focused.
- **D: Dependency Inversion**: Depend on abstractions, not concretions. Utilize Dependency Injection (DI) extensively.

## 📐 Common Design Patterns
- **Factory Pattern**: Use for creating families of related objects (e.g., Model Adapters).
- **Strategy Pattern**: Use for interchangeable algorithms (e.g., different Encryption strategies).
- **Observer Pattern**: Use for event-driven updates (e.g., Mission state changes).
- **Singleton**: Use sparingly for global resources (e.g., Config, Database Pools).
- **Decorator**: Use for cross-cutting concerns (e.g., Logging, Auth, Retries).

## 🚀 Professional Application
- **Favor Composition over Inheritance**: Building complex behavior should come from small, reusable components.
- **Encapsulation**: Keep internal state private and provide clean public APIs.
- **DRY (Don't Repeat Yourself)**: If logic appears twice, abstract it into a generic component.
