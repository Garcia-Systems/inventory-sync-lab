# Ordering Guarantees

```text
Revision 14
    ↓
Projection Revision 14
    ↓
Revision 13 arrives
    ↓
Revision comparison
    ↓
Update skipped
    ↓
Projection remains Revision 14
```

The projection revision progresses monotonically. A request may arrive later,
but it can update the projection only when its revision is newer.
