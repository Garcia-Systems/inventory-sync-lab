# End-to-End Operations Laboratory

```mermaid
flowchart TD
    L[Inventory Ledger] --> A[Authoritative Inventory]
    A --> F[Fan-Out]
    F --> Q[Synchronization Queue]
    Q --> W[Worker Pool]
    W --> R{Retry Policy}
    R -->|retry| Q
    R -->|delivery| D{Duplicate Delivery / Idempotency}
    D --> O{Ordering Guarantees}
    O --> P[Projection Registry]
    R -->|attempt limit exceeded| X[Dead Letter Queue]
```

The solid downward path is successful work. A retry returns the same immutable
request to the queue. Idempotency removes the effect of repeated delivery, while
revision ordering stops an older request from moving a projection backward.
Only work that exhausts its retry allowance enters the dead letter queue.
