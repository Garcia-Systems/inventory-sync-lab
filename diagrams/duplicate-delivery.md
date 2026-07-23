# Duplicate Delivery

```text
Business Event (once)
          │
          ▼
Synchronization Request 42
          │
     ┌────┴────┐
     ▼         ▼
Delivery 1  Delivery 2
     └────┬────┘
          ▼
Projection Updated Twice
```

The authoritative business event occurs once and creates one immutable request.
The delivery mechanism presents that same request twice, so the projection is
updated twice. Chapter 18 deliberately performs both deliveries: it contains no
duplicate suppression or idempotency policy.
