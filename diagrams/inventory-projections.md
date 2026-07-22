# Inventory projections

```text
                         replay
Inventory Ledger ----------------------> Authoritative Inventory State
                                                   |
                                              manual copy
                                                   |
                         +-------------------------+-------------------------+
                         |                         |                         |
                         v                         v                         v
                    Warehouse                  Website                Marketplace
                      MATCH                     MATCH                  STALE: +3
                                                                            |
                                                                      manual refresh
                                                                            v
                                                                    Marketplace
                                                                       MATCH
```

The ledger records what happened. Replay derives the authority. Each projection
is only a copied view; manually refreshing the marketplace replaces that copy.
