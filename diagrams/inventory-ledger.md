# Inventory ledger

```text
Receive 10 ─┐
Reserve 3  ─┼──▶ [ ordered inventory ledger ] ── replay ──▶ InventoryState
Ship 2     ─┘                                      on hand 8, reserved 1
```

The ledger retains what happened and its order. The state is an answer produced
from that history, rather than another quantity stored beside it.
