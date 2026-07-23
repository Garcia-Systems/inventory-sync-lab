# Idempotent Synchronization

```text
Synchronization Request 57

           │

    ┌──────┼──────┐

    ▼      ▼      ▼

Delivery Delivery Delivery
   1        2        3

   │        │        │

   ▼        ▼        ▼

 Update   Ignore   Ignore

     Projection changed once
```

All three work items carry the identical immutable request. The receiving and
processing count is three, but the effective projection-state change count is
one.
