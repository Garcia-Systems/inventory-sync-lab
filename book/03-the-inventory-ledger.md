# Chapter 3: The Inventory Ledger

## 1. The problem

An inventory state answers an important question: *what is true now?* If it says
eight units are on hand and one is reserved, however, it cannot explain how that
happened. Replacing yesterday's quantity with today's quantity erases the path
between them.

Inventory is therefore more than a quantity. It is the current result of recorded
business events.

## 2. Why a single quantity loses history

Suppose on-hand inventory changes from zero to eight. The final number alone
cannot tell us whether eight arrived, ten arrived and two shipped, or a count
found eight additional units. Those stories can have different meanings even
though they end with the same number.

The Chapter 1 `InventoryState` remains useful. It represents the answer, not the
explanation. Chapter 3 preserves the explanation as well.

## 3. Recording what happened

We record small facts in the order they occurred:

```text
Receive 10 ─┐
Reserve 3  ─┼──▶ [ ordered inventory ledger ]
Ship 2     ─┘
```

Each `InventoryEvent` contains only a valid event type and a positive integer
quantity. There are no identifiers, clocks, locations, products, or descriptive
metadata yet. The five event types are receive, reserve, release reservation,
ship, and adjustment. In this chapter an adjustment is positive only and adds to
on-hand inventory.

## 4. Ledger replay

Replay begins with zero on hand and zero reserved, then applies every event in
order. The rules are deliberately direct:

| Event | Effect |
| --- | --- |
| Receive | add quantity to on hand |
| Reserve | add quantity to reserved |
| Release reservation | subtract quantity from reserved |
| Ship | subtract quantity from both reserved and on hand |
| Adjustment | add quantity to on hand |

Order matters. Reserving before inventory has arrived is not made valid by a
later receive. While replaying, the ledger rejects a reserve larger than what is
available, a release larger than what is reserved, and a shipment larger than
what is reserved. This catches an impossible history at the exact event that
makes it impossible.

## 5. Inventory derivation

Our canonical history produces the following transitions:

```text
start        on hand  0   reserved 0
Receive 10   on hand 10   reserved 0
Reserve 3    on hand 10   reserved 3
Ship 2       on hand  8   reserved 1
                         available = 8 - 1 = 7
```

Shipping two removes two physical units and also consumes their reservations.
That is why the result is on hand 8, reserved 1, and available 7.

```text
[ Receive 10, Reserve 3, Ship 2 ]
                  │ replay
                  ▼
     InventoryState(8, 1) ──▶ available 7
```

The ledger does not store any of those three result quantities. Replaying the
history constructs the existing Chapter 1 `InventoryState`, which continues to
derive `available` as `on_hand - reserved`.

## 6. Python implementation

The public interface stays small:

```python
from inventory_sim import InventoryLedger, Receive, Reserve, Ship

ledger = InventoryLedger([
    Receive(10),
    Reserve(3),
    Ship(2),
])

state = ledger.current_state()
assert state.on_hand == 8
assert state.reserved == 1
assert state.available == 7
```

Both events and the ledger are frozen dataclasses. The ledger copies its input
into a tuple, so changing the caller's original list cannot change history.
`current_state()` walks that tuple and returns `InventoryState`; it does not keep
a second mutable answer that could disagree with the events.

## 7. Unit tests

Readable tests demonstrate each rule separately. They cover receiving,
reserving, releasing, shipping, adjustment, complete replay, derived available
inventory, invalid values, impossible histories, input copying, and immutability.
The CLI test checks the whole canonical lesson exactly as a reader sees it.

Run them with coverage:

```bash
pytest --cov=inventory_sim --cov-branch --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

## 8. Manual CLI exercise

Run:

```bash
inventory-sim ledger
```

Read the three events first. Before looking below them, replay each change on
paper. Confirm that the displayed current inventory is on hand 8, reserved 1,
available 7. The command intentionally accepts no custom events, keeping the
exercise focused on one shared example.

## 9. Questions

1. What information disappears when a program overwrites one quantity?
2. Why does `Reserve 3` not reduce on-hand inventory?
3. Why does `Ship 2` reduce both on hand and reserved?
4. Why must replay validate each event rather than only the final totals?
5. How does an immutable event list make an explanation easier to trust?
6. What answer does the ledger store, and what answer does it derive?

## 10. Summary

A current quantity tells us where inventory ended. An ordered ledger also tells
us what happened. Replaying valid events derives the current `InventoryState`,
while impossible events are rejected when encountered. Preserving this simple
history gives later chapters a dependable foundation without adding machinery
that this lesson does not need.

## 11. Preview of Chapter 4

Chapter 4 introduces **Inventory Projections**: additional useful views derived
from the same recorded history. Chapter 3 stops at the ledger and its current
inventory state.
