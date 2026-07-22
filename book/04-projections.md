# Inventory Projections

Chapter 3 made the ledger the record of what happened and derived current
inventory by replaying it. This chapter asks how other systems can use that
current answer without becoming authorities themselves.

## 1. The problem: why other systems need inventory data

A seller's warehouse needs inventory data to organize its work. A website needs
it to show what can be offered. A marketplace needs it for the same basic
reason. Giving each system a useful view does **not** designate every system as
the source of truth. Copies are useful because systems need information where
they perform their responsibilities; they are not inherently a design mistake.

## 2. A simple real-world example

Our fictional seller records this authoritative history:

```text
Receive 10
Reserve 3
```

Replay produces 10 on hand, 3 reserved, and 7 available. Warehouse and website
copies contain those values. The marketplace still contains 10 on hand, 0
reserved, and 10 available. Its copy has not yet been refreshed, so it is stale.
This chapter deliberately does not invent a reason for or a transport mechanism
behind that fact.

## 3. The engineering concept: what is a projection?

A **projection** is a derived or copied view of authoritative information,
prepared for another use. A projection can match the authority, become stale,
and be refreshed. Even when correct, it does not redefine the authoritative
record.

Keep the three layers distinct:

```text
Authoritative ledger
    Records what happened.

Authoritative current state
    Derived from the ledger.

Projection
    A copied view used by another system.
```

Or, as a flow:

```text
Ledger
  | replay
  v
Authoritative current state
  | copied manually
  v
Projection
```

Replay answers the ledger's current state. A manual copy creates a view for
another system. Neither comparison nor copying writes to the ledger.

## 4. Diagram and the fictional systems

[The Chapter 4 diagram](../diagrams/inventory-projections.md) shows the complete
boundary of this lesson: derive, compare, and manually refresh.

The **warehouse projection** supports warehouse responsibilities, the
**website projection** supports the seller's site, and the **marketplace
projection** supports a separate selling surface. Later designs might prepare
different shapes for different uses, but here every projection deliberately
uses the same `on_hand`, `reserved`, and calculated `available` quantities.

## 5. A stale marketplace projection

Authority, warehouse, and website report 7 available. Marketplace reports 10
because its copied `reserved` value is still 0 rather than 3. The authority is
not ambiguous: its value comes from ledger replay. The marketplace copy simply
has not been manually refreshed.

## 6. Measuring disagreement

Chapter 2 established the comparison direction, which Chapter 4 reuses:

```text
Difference = Projection value - Authoritative value
```

A positive difference means the projection reports more than authority, a
negative difference means less, and zero means agreement for that quantity.
Marketplace available inventory is `10 - 7 = +3`. Comparisons expose on-hand,
reserved, and available differences plus an overall match; they only measure
and never repair.

## 7. Manual refresh

Chapter 4's operation is explicit:

```text
Replace the projection's copied state with the current authoritative state.
```

The example calls that method directly. It skips transport and timing questions:
there is no polling, automatic propagation, or scheduled work. Those belong to
later chapters. Refreshing marketplace also does not refresh warehouse or
website.

## 8. Why refresh returns a new object

The projection is immutable, so refresh returns a new value. The old stale
state remains inspectable, the refreshed value is clearly separate, and the
operation cannot silently rewrite the earlier observation. A test can compare
before and after directly. The immutable authoritative `InventoryState` is
shared safely and is not modified.

## 9. Code introduced

The model in `src/inventory_sim/projections.py` is intentionally small:

```python
@dataclass(frozen=True)
class InventoryProjection:
    system: str
    state: InventoryState

    def compare_to(self, authoritative_state: InventoryState) -> InventoryComparison:
        authority = AuthoritativeInventoryRecord(
            f"{self.system} (authority)", authoritative_state
        )
        return compare_inventory(authority, InventoryCopy(self.system, self.state))

    def refresh_from(self, authoritative_state: InventoryState) -> "InventoryProjection":
        return InventoryProjection(self.system, authoritative_state)
```

Construction uses Chapter 2's `InventoryCopy` validation, so names are strings,
trimmed consistently, and cannot be blank. `state` must be an `InventoryState`.
`compare_to` adapts the projection to the existing Chapter 2 comparison rather
than introducing a second formula. `refresh_from` preserves `system` and creates
a new projection around the authority's immutable state.

The CLI needs no manager or repository: an ordinary tuple holds the three
projections so readers can inspect each value.

## 10. Running the example

```bash
docker compose run --rm lab inventory-sim projections
```

The output first prints the two-entry ledger and its replayed authoritative
state. “Projections before manual refresh” shows warehouse and website as
`MATCH`, and marketplace as `STALE` with an available difference of `+3`. The
manual refresh section explicitly copies the state. The final marketplace is a
`MATCH` with difference `+0`, while the original stale object remains unchanged.
No optional arguments are needed: this command preserves one deterministic
teaching scenario.

## 11. Unit tests as part of the lesson

`tests/test_projections.py` checks stale detection, positive and negative
differences, all compared quantities, refresh behavior, immutability, preserved
system identity, validation, and non-mutation of the authority. It also guards
Chapter 2 comparison behavior. CLI tests check the three names, before/after
statuses, explicit manual wording, module invocation, and the absence of any
claim that refresh was automatic.

These tests describe promises visible to a reader, not private implementation
details.

## 12. Manual exercises

1. Before running the command, predict which projections match.
2. Calculate marketplace's on-hand, reserved, and available differences.
3. Change a projection on paper to 8 on hand and 3 reserved. Predict every
   difference and its status.
4. Predict the old and new marketplace values after manual refresh.
5. Explain why neither ledger nor authoritative state changes.
6. Explain why manually refreshing marketplace does not refresh website.

Use paper, a Python shell, or a small test; no experiment framework is needed.

## 13. Questions for the reader

- Why is a projection useful?
- Can a projection be correct without being authoritative?
- What makes a projection stale?
- Why should a stale copy not overwrite the authority?
- What information is missing if we cannot say when a copy became stale?
- What mechanism could eventually automate refreshes?

## 14. Summary

Authoritative current state comes from ledger replay. Projections are useful
copied views and can agree or disagree with that state. Difference is always
projection minus authority. Manual refresh returns a new projection containing
the authoritative state; it changes neither ledger nor authority. Nothing in
this chapter automates synchronization.

## 15. What comes next

Chapter 5 introduces **time and events**. It begins answering when something
happened, how actions can be ordered, and how repeatable simulated timelines can
be created. Chapter 4 stops before clocks, scheduled actions, or a simulation
engine and implements none of those concepts.
