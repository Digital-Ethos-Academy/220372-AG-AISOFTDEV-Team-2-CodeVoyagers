```markdown
# ADR-XXX: [Short descriptive title of the decision]

- **Status**: Proposed | Accepted | Deprecated | Superseded by [ADR-XXX](ADR-XXX.md)
- **Date**: YYYY-MM-DD
- **Decision Makers**: [List of names or roles]

---

## 1. Context

This section describes the problem, the context, and the forces at play that necessitated this decision. It should be a clear and concise summary of the issue being addressed.

- **Problem Statement**: What is the specific problem or challenge that needs a decision? What is the scope of this decision?
- **Driving Forces**: What are the key architectural drivers, constraints, requirements, or quality attributes influencing this decision? (e.g., performance, security, cost, maintainability, team skills, time-to-market).
- **Alternatives Considered**: Briefly list other options that were evaluated before arriving at this decision.

---

## 2. Decision

This section clearly and concisely describes our solution to the problem. It is the "what" of the decision.

We will: [State the chosen solution, approach, or technology. Be specific and unambiguous. For example, "We will adopt a microservices architecture for the new payment module using Kafka for asynchronous communication."]

- **Justification**: Why was this option chosen over the alternatives? Connect the decision back to the driving forces and context mentioned above.
- **Details/Implementation**: Provide enough detail for someone to understand the decision and its implementation. This can include diagrams, code snippets, or references to other documents if necessary.

---

## 3. Consequences

This section describes the resulting context after applying the decision. All consequences, both positive and negative, should be listed here to ensure a balanced understanding of the trade-offs.

### Positive Consequences

- [List the benefits and positive outcomes of this decision.]
- [e.g., Improved scalability and independent deployment of the payment service.]
- [e.g., Aligns with the team's existing expertise in technology X.]
- [e.g., Reduces long-term maintenance costs by using a managed service.]

### Negative Consequences

- [List the trade-offs, risks, or liabilities introduced by this decision.]
- [e.g., Increased operational complexity due to managing multiple services.]
- [e.g., Requires investment in new monitoring and deployment tooling.]
- [e.g., Introduces a new technology that the team needs to learn.]

```