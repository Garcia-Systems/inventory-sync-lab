# Multiple Workers

```text
Time       1            4            7            8
           |------------|------------|------------|

worker-1   website      storefront    idle
           [1 to 4]     [4 to 7]

worker-2   marketplace  partner       idle
           [1 to 4]     [4 to 7]

Time 1 after assignment: queue []
Time 2:                  queue [storefront]
Time 3:                  queue [storefront, partner]
Time 4 after assignment: queue []
Time 7:                  queue []

Idle workers:     worker-1, worker-2
Waiting requests: storefront, partner
Assignments:      storefront -> worker-1
                  partner    -> worker-2
```

Each lane holds at most one request. Queue depth excludes the two requests in
progress. These are deterministic simulated intervals, not operating-system
threads or claims of physically simultaneous execution.
