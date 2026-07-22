# What Is Inventory?

Chapter 0 built a trustworthy laboratory. This chapter adds its first inventory
concept: a small representation of the **current state**. It does not record how
the state changed and does not synchronize anything.

## 1. Why one inventory number is not enough

Imagine a small online seller has ten notebooks on a shelf. Customers have already
claimed three, but those notebooks have not left the shelf. A physical count still
finds ten. Only seven can honestly be offered to another buyer. Reporting all ten
as sellable would promise units that are already committed.

This gives us three useful quantities:

```text
On hand:   10
Reserved:   3
Available:  7
```

Physical stock and sellable stock answer different questions, so inventory is not
always represented well by one number.

## 2. On-hand quantity

**On hand** means physical units currently held. In the example, all ten notebooks
remain on the shelf, including the three that someone has claimed. On hand is
therefore not automatically the same as available.

## 3. Reserved quantity

**Reserved** means units set aside for accepted demand but not yet removed from
physical stock. Reserved units are both physically present and already committed.
That definition is enough for this chapter; no order or fulfillment workflow is
needed to understand the current state.

## 4. Available quantity

**Available** means units that can still be offered for sale:

```text
Available = On hand - Reserved
```

For ten on hand and three reserved, `10 - 3 = 7`. The model derives available;
callers enter only on hand and reserved.

## 5. Why derived values matter

Suppose all three values were entered independently:

```text
On hand: 10
Reserved: 3
Available: 9
```

That record contradicts the formula, leaving readers to guess which number is
correct. Deriving available from the other two prevents this particular
inconsistency: one state has only one possible available value.

## 6. Inventory invariants

An **invariant** is a rule that must remain true for every valid instance. This
chapter enforces three rules:

```text
On hand cannot be negative.
Reserved cannot be negative.
Reserved cannot exceed on hand.
```

These rules prevent impossible states and make mistakes fail close to their
source. They describe this intentionally small model, not every future inventory
system.

## 7. Zero is valid

An empty shelf is ordinary, not malformed:

```text
on hand = 0
reserved = 0
available = 0
```

The state satisfies every invariant and truthfully says that nothing can be sold.

## 8. Fully reserved inventory

All physical units may already be committed:

```text
on hand = 5
reserved = 5
available = 0
```

This is also valid. It demonstrates especially clearly why positive on-hand stock
does not guarantee positive sellable stock.

## 9. The Python model

The complete model in `src/inventory_sim/inventory.py` is deliberately small:

```python
@dataclass(frozen=True)
class InventoryState:
    on_hand: int
    reserved: int

    def __post_init__(self) -> None:
        for field_name, quantity in (
            ("on_hand", self.on_hand),
            ("reserved", self.reserved),
        ):
            if type(quantity) is not int:
                raise ValueError(
                    f"{field_name} must be an integer "
                    "(Boolean values are not allowed)"
                )

        if self.on_hand < 0:
            raise ValueError("on_hand cannot be negative")
        if self.reserved < 0:
            raise ValueError("reserved cannot be negative")
        if self.reserved > self.on_hand:
            raise ValueError("reserved cannot exceed on_hand")

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved
```

`frozen=True` makes the value immutable: code cannot construct a valid state and
then silently assign an invalid quantity. Validation names the offending field.
The exact `int` check deliberately rejects strings, floats, `None`, numeric-like
objects, and Boolean values (Python otherwise treats `bool` as a subclass of
`int`). Whole units keep the lesson unambiguous; this model has no fractional
stock. The public interface is direct:

```python
from inventory_sim import InventoryState

state = InventoryState(on_hand=10, reserved=3)
assert state.available == 7
```

The relationship is illustrated in [the inventory-state diagram](../diagrams/inventory-state.md).

## 10. Running the example

Defaults reproduce the chapter's example:

```bash
docker compose run --rm lab inventory-sim inventory
```

Custom values use the two input options:

```bash
docker compose run --rm lab inventory-sim inventory \
  --on-hand 10 \
  --reserved 3
```

Both print:

```text
Inventory State

On hand:   10
Reserved:  3
Available: 7
```

Try an invalid state:

```bash
docker compose run --rm lab inventory-sim inventory \
  --on-hand 5 \
  --reserved 6
```

It exits unsuccessfully with `Error: invalid inventory state: reserved cannot
exceed on_hand`, rather than showing a Python traceback.

## 11. Tests as part of the lesson

Readable tests prove the formula, zero and fully reserved boundaries, every
invariant, integer-only inputs, and immutability. CLI tests prove defaults, custom
inputs, module execution, friendly errors, and the older commands. Testing each
invariant makes the prose an executable promise.

Run the suite with branch coverage in Docker:

```bash
docker compose run --rm lab pytest \
  --cov=inventory_sim \
  --cov-branch \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml
```

Coverage shows which implementation paths ran; as Chapter 0 explained, it does
not replace meaningful assertions.

## 12. Manual exercises

1. Calculate available for `(on hand=12, reserved=4)` and `(3, 3)`.
2. Decide whether `(0, 0)`, `(4, -1)`, and `(2, 5)` are valid, and name the rule.
3. Run the CLI with several valid quantities. Predict its output first.
4. Run an invalid example and inspect its exit status with `echo $?` on a shell
   that supports that syntax.
5. Write down why entering available separately would permit a contradiction.

These are manual observations, not an experiment framework.

## 13. Questions for the reader

1. Can on-hand quantity be positive while available quantity is zero?
2. Why should reserved quantity not exceed on-hand quantity?
3. What could go wrong if available were stored separately?
4. Is zero inventory an invalid state? Why or why not?
5. Why does this model reject `True` even though Python can treat it like `1`?
6. What information about changes over time is still missing from this model?

## 14. Chapter summary

Inventory is not always one number. On hand describes physical units, while
available describes sellable units after reserved commitments are accounted for.
Available is derived as `on hand - reserved`, preventing it from contradicting
its inputs. Simple invariants reject negative or over-reserved states, while zero
and fully reserved states remain valid.

## 15. What comes next

Chapter 2 will examine the idea of an authoritative source of truth. We stop here:
this chapter represents only a current inventory state and does not yet record,
project, or synchronize changes.
