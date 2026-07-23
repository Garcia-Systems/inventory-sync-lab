# Detecting a stale synchronization

```text
Authoritative inventory — Revision 5
                 │
                 ▼
Worker begins request — Revision 3
                 │
                 ▼
Compare revisions — 3 < 5
                 │
                 ▼
Request identified as stale (observation only)
                 │
                 ▼
Synchronization still proceeds
```

The comparison reports what the worker is carrying. It does not decide whether the worker may update the projection.
