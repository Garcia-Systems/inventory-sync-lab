# Retry Policies

```text
Inventory Revision 10
          │
          ▼
Synchronization Request
          │
          ▼
      Attempt 1
          │
          ▼
        Failure
          │
          ▼
         Retry
          │
          ▼
      Attempt 2
          │
          ▼
        Success
```

The retry schedules another attempt of the same immutable request and snapshot.
Its fixed policy contains no randomness, duplicate detection, or idempotency.
