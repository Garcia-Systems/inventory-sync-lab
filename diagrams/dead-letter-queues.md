# Dead Letter Queues

```text
Synchronization Request

        │

Retry Policy

        │

 ┌──────┴────────┐

 ▼               ▼

Success      Retry Limit

                 │

                 ▼

      Dead Letter Queue
```

The terminal branch isolates permanently failing work for inspection. It does
not stop successful requests or keep the failed request in the active queue.
