# ADR-001: Use SQLite for the Internal Hiring Platform Prototype Database

- **Status**: Accepted
- **Date**: 2025-11-06
- **Decision Makers**: Staff Engineer, Lead Engineer

---

## 1. Context

This section describes the problem, the context, and the forces at play that necessitated this decision. It should be a clear and concise summary of the issue being addressed.

- **Problem Statement**: The AI-powered internal hiring platform requires a database for its initial one-day prototype. The chosen solution must support rapid development, require zero configuration, and enable easy local demonstration without imposing any operational or infrastructure overhead. The scope of this decision is strictly limited to the proof-of-concept (PoC) phase.

- **Driving Forces**:
    - **Time-to-Market**: The primary constraint is the one-day development timeline. Any solution that requires significant setup, configuration, or a learning curve is unacceptable.
    - **Developer Velocity**: The team must be able to focus entirely on building application features, not on managing infrastructure. Eliminating setup friction is paramount.
    - **Simplicity & Portability**: The prototype must be self-contained and easily run on any developer's machine for development and demonstration purposes without external dependencies like a database server or cloud service.
    - **Cost**: The solution for this PoC phase should have zero financial cost.
    - **Sufficient Functionality**: The database must be capable of handling relational data for employee profiles, skills metrics, and conversation histories for the PoC.

- **Alternatives Considered**:
    - **Dockerized PostgreSQL/MySQL**: A robust, production-grade option. However, it introduces overhead (Docker setup, container management, connection configuration) that conflicts with the one-day timeline and simplicity requirement.
    - **Cloud-hosted Database (e.g., AWS RDS, Google Cloud SQL)**: Powerful and scalable, but requires network access, account setup, and configuration, making it unsuitable for a fast, local-first PoC.
    - **In-Memory Database (e.g., H2)**: Extremely fast, but data is typically volatile. This would complicate the development-test-demo cycle, as the application state would be lost on every restart.

---

## 2. Decision

This section clearly and concisely describes our solution to the problem. It is the "what" of the decision.

We will: **Use SQLite as the database technology for the internal hiring platform prototype.** The database will be managed as a single file (`prototype.db`) within the project's local file system.

- **Justification**: This decision directly addresses our primary driving force: speed of development.
    - **Zero-Configuration Setup**: SQLite is a serverless, self-contained library. It requires no installation, no server process to manage, and no user configuration. This completely eliminates database setup time, allowing the team to begin feature development immediately.
    - **Rapid Prototyping**: The simplicity of a file-based database is ideal for a one-day PoC. The entire application stack can be run with a single command.
    - **Excellent for Local Development & Demos**: Because the database is just a file, the entire prototype can be cloned from a repository and run instantly on any machine. This makes it trivial to develop, test, and demonstrate the PoC without any external dependencies.
    - **Sufficient for PoC Scope**: SQLite provides a full-featured SQL implementation, including transactions and relational constraints, which is more than sufficient to model the data for employee profiles and dashboards for a single-user demonstration.
    - **Low-Risk Migration Path**: By using a standard ORM (Object-Relational Mapper) or a data access layer, our application code will be largely database-agnostic. Migrating to a production-grade system like PostgreSQL in a future phase is a well-understood process and is a planned, accepted cost if the prototype is successful.

- **Details/Implementation**:
    - The application will connect to a local database file (e.g., `data/prototype.db`).
    - This database file will be added to `.gitignore` to prevent test data from being committed to version control.
    - A simple schema initialization script (e.g., `schema.sql`) or a lightweight migration tool will be used to create the necessary tables on application startup, ensuring a consistent environment for all developers.

---

## 3. Consequences

This section describes the resulting context after applying the decision. All consequences, both positive and negative, should be listed here to ensure a balanced understanding of the trade-offs.

### Positive Consequences

- **Maximized Development Time**: The team will spend 100% of the allotted day on building the application's features, not on infrastructure.
- **Ultimate Portability**: The entire prototype is self-contained. It can be shared via a Git repository and run without any setup, which is perfect for demos.
- **No Operational Overhead**: No servers to manage, secure, or pay for. This aligns perfectly with the ephemeral nature of a PoC.
- **Simplified Testing**: Automated tests can create their own ephemeral, file-based, or in-memory SQLite databases in milliseconds, leading to a fast and reliable testing process.

### Negative Consequences

- **Not Suitable for Production**: SQLite does not handle high levels of write concurrency well and lacks the robustness and management features of a client-server RDBMS. This choice is explicitly not for production use.
- **Future Migration is Required**: If the prototype is approved to move forward, a dedicated task to migrate the database to a production-grade system (e.g., PostgreSQL) will be necessary. This work is a known and accepted trade-off.
- **Limited Real-Time Capabilities**: The prompt mentions "real-time collaboration." SQLite has no native pub/sub or real-time push capabilities. For the PoC, this feature will be simulated via front-end polling. A production implementation would require a different architecture (e.g., WebSockets, a message queue). This limitation is acceptable for the proof-of-concept.