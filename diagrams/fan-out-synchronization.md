# Fan-Out Synchronization

```text
                 Inventory Revision 8
                          │
                          ▼
                  Fan-Out Generator
                   ┌──────┼──────┐
                   ▼      ▼      ▼
               Storefront Warehouse Reporting
                 Request   Request   Request
                    1         2         3
```

The single authoritative event is not copied or changed. The generator walks
the projection registry in its stable order and creates one independent,
immutable synchronization request for each projection.
