# Stale Snapshots

```text
Simulated time     0              1              2           3 to 6       6
                   |--------------|--------------|--------------|---------|

Authority          Available 7                   Receive 5       Available 12
                         |                            |
                         v                            v
Snapshot captured                 Available 7        Authority changes
                                       |
                                       v
Queue waiting                     [website] -----> Worker processes
                                                         |
                                                         v
Worker finishes                                           success
                                                         |
                                                         v
Projection updated                                  Available 7
                                                         |
                                                         v
Projection already stale                      7 differs from current 12
```

The worker copies exactly what the request carries. The queue and worker
succeed; the authoritative world simply changes before that copy arrives.
