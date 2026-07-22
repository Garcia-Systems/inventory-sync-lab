# Direct synchronization

```text
Authoritative state: available 7
             |
             | scheduled direct refresh at time 6
             | direct copy
             v
Website projection
Before time 6: available 10
After time 6:  available 7

0          4            6             8
|----------|------------|-------------|
           Inspect      Direct sync   Inspect
           STALE                      MATCH
```

The scheduled action performs the direct copy. The model has no intermediate
transport.
