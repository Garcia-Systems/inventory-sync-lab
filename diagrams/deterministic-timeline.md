# Deterministic Timeline

```text
0          2             5                 8
|----------|-------------|-----------------|
           Inspect       Refresh website   Inspect again
                         Refresh marketplace

Time 5 insertion order:
1. Refresh website projection
2. Refresh marketplace projection
```

The clock jumps between event times. Both actions at tick 5 run without moving
the clock, and their explicit insertion order breaks the tie.
