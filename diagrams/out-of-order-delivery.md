# Out-of-Order Delivery

```text
             Creation order

              Revision 13
                  ↓
              Revision 14

        ───────────────────────

             Delivery order

              Revision 14
                  ↓
              Revision 13
                  ↓
     Projection finishes on Revision 13
```

Revisions preserve the authority's chronology. Delivery order determines the
updates in this intentionally uncorrected scenario, so successful exactly-once
processing leaves the projection older than authority.
