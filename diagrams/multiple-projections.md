# Multiple projections

```text
Inventory Ledger
        │
        ▼
Authoritative Inventory
        │
 ┌──────┼────────┐
 ▼      ▼        ▼
Storefront   Warehouse   Reporting
Projection  Projection  Projection
```

Each arrow represents a deterministic synchronization request. The three
projections are named, independent copies; changing or rejecting one copy does
not change either of the others.
