# Chapter 2: The Authoritative Source of Truth

Chapter 1 represented a valid current inventory state. This chapter asks a new
question: when several systems contain such states, which record does the
business use as its official reference? We identify that record and compare
copies with it. We do not yet synchronize or repair anything.

> The authoritative inventory record describes the state the business currently
> accepts as correct. Other systems may hold copies of that state, but those
> copies are not independently authoritative.

## 1. When systems disagree

A small seller uses an inventory authority, a website, and a marketplace. They
currently report:

```text
Authoritative available quantity: 7
Website copy:                    7
Marketplace copy:              10
```

The authority's complete state is ten on hand, three reserved, and seven
available. The website agrees. The marketplace copy is stale and says ten are
available. Disagreement is normal whenever systems maintain copies. Its presence
does not, by itself, prove which value is wrong.

## 2. What “authoritative” means

Authority is a business and system-design decision. The authoritative record is
the official current state that the organization accepts for decision-making. It
is the reference point because responsibility was explicitly assigned—not
because software can prove that it is objectively correct.

Authoritative therefore does not mean infallible. Data entry, counting, and
software errors can still occur. If the organization discovers an error, its
correction must ultimately be reflected in the authoritative record. Copies must
not independently redefine the official state while leaving the authority
unchanged, or the organization again has competing answers.

## 3. Copies are not authorities

The website and marketplace need inventory information, but their values are
copies of the official current state. A copy can match the authority, report too
much, or report too little. A customer-facing system does not become authoritative
merely because customers can see it. Presentation and data ownership are
different responsibilities.

## 4. Why voting does not work

Consider the original values:

```text
Authority:    7
Website:      7
Marketplace: 10
```

A majority happens to select seven, but that coincidence is not a sound ownership
rule. Change both copies without changing the official record:

```text
Authority:    7
Website:     10
Marketplace: 10
```

Two incorrect copies do not overrule the designated authority. The number of
copies is unrelated to which system owns the business decision.

## 5. Why averaging does not work

Averaging also ignores ownership. The values 7, 10, and 10 average to 9. No
system observed or accepted nine, and the business has no justification for
offering it. Arithmetic cannot manufacture an official inventory state.

## 6. Comparing copies

Every difference uses one consistent formula:

```text
Difference = Copy value - Authoritative value

Marketplace available: 10
Authority available:     7
Difference:              +3
```

A positive difference means the copy reports more than the authority; a negative
difference means it reports less; zero means that quantity is equal. The code
applies this formula separately to on-hand, reserved, and available quantities.
A full match requires the copied `InventoryState` to equal the authoritative
state.

## 7. Detecting is not repairing

Chapter 2 detects disagreement only. Comparison does not update the website,
update the marketplace, modify the authority, send a message, or retry anything.
It neither votes nor selects a winner. A future synchronization mechanism will
spread authoritative changes, but no such mechanism exists here.

The neutral relationships in [the authority diagram](../diagrams/authoritative-inventory.md)
mean “compared with”; they are deliberately not message-flow arrows.

## 8. The Python model

The implementation in `src/inventory_sim/authority.py` gives authority and copies
different types, making their roles structural rather than Boolean flags:

```python
authority = AuthoritativeInventoryRecord(
    system="inventory-authority",
    state=InventoryState(on_hand=10, reserved=3),
)
marketplace = InventoryCopy(
    system="marketplace",
    state=InventoryState(on_hand=10, reserved=0),
)
comparison = compare_inventory(authority, marketplace)

assert comparison.matches is False
assert comparison.available_difference == 3
```

`AuthoritativeInventoryRecord`, `InventoryCopy`, and `InventoryComparison` are
frozen dataclasses. Names are trimmed and must be nonblank strings. States must be
existing `InventoryState` objects, so Chapter 1 remains the single home of
quantity validation. Direct comparison requires the authority type and copy type,
and rejects the same normalized system name on both sides. The result retains the
two immutable inputs and reports match status plus all three differences.

The public imports are:

```python
from inventory_sim.authority import (
    AuthoritativeInventoryRecord,
    InventoryComparison,
    InventoryCopy,
    compare_inventory,
)
```

They are also exported from `inventory_sim` for convenience.

## 9. Running the example

Run the default scenario:

```bash
docker compose run --rm lab inventory-sim authority
```

It identifies `inventory-authority`, reports the website as `MATCH`, and reports
the marketplace as `DIFFERS` with an available difference of `+3`. It explicitly
states that no synchronization or repair occurred.

All six quantities can be changed without files or configuration:

```bash
docker compose run --rm lab inventory-sim authority \
  --authority-on-hand 12 --authority-reserved 4 \
  --website-on-hand 12 --website-reserved 4 \
  --marketplace-on-hand 12 --marketplace-reserved 4
```

Both copies match with a `+0` difference. To see a copy report less:

```bash
docker compose run --rm lab inventory-sim authority \
  --authority-on-hand 10 --authority-reserved 2 \
  --website-on-hand 8 --website-reserved 2 \
  --marketplace-on-hand 10 --marketplace-reserved 2
```

The website has six available against the authority's eight, so its difference
is `6 - 8 = -2`.

## 10. Tests as part of the lesson

Tests verify equal states and zero differences, positive and negative differences,
invalid names and types, immutability, and the fact that comparison does not
mutate either input. CLI tests cover defaults, custom values, friendly validation
errors, and `python -m inventory_sim authority`. These checks turn the direction
of the formula and the role boundary into executable promises.

Run them with statement and branch coverage:

```bash
docker compose run --rm lab pytest \
  --cov=inventory_sim \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

## 11. Manual exercise

Predict the two signs and statuses before running anything:

```text
Authority available:    8
Website available:      6
Marketplace available:  9
```

One equivalent valid input is authority `(10, 2)`, website `(8, 2)`, and
marketplace `(10, 1)`. Run the CLI with those six values, compare its output with
your prediction, and explain why neither copy changes. This is a manual exercise,
not an experiment framework.

## 12. Questions for the reader

1. Why must authority be explicitly assigned?
2. Can a customer-facing system be non-authoritative?
3. Does a matching copy prove that it will remain correct?
4. Why should values not be averaged?
5. What should happen when the authority itself is discovered to be wrong?
6. Why do two agreeing copies not outvote an authority?
7. What process is still missing from the laboratory?

## 13. Chapter summary

One designated system holds the official current record; other systems hold
copies. Copies may agree, report more, or report less. Disagreement is measured
as `copy - authority`, never by voting, averaging, or selecting the largest
value. Authority is an organizational decision, not a guarantee of infallibility.
Most importantly, detecting a difference does not repair it.

## 14. What comes next

Chapter 3 introduces the inventory ledger and begins recording what happened to
inventory over time. We stop before that boundary: Chapter 2 contains no history,
ledger, synchronization, messages, workers, persistence, or simulation engine.
