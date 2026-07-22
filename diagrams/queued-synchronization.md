# Queued synchronization

```text
Synchronization request
          |
          v
      FIFO Queue
    [website]
    [marketplace]
          |
          v
     Single Worker
          |
          v
  Projection Registry

Time 2: [website]                    depth 1
Time 3: [website, marketplace]       depth 2
Time 5: [marketplace]                depth 1
Time 7: []                           depth 0
```

The worker removes no more than one request during each scheduled worker action.
The queue is an in-memory simulation structure, not a network service.
