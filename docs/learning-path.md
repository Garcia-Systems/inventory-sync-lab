# Volume I Learning Path

Read Volume I in order. Each chapter preserves the previous model and introduces
one new question; skipping ahead can make a policy look arbitrary because the
failure that motivates it appeared earlier. Run the listed command after reading
each chapter (`docker compose run --rm lab` is the common prefix).

## Foundations — Chapters 0–9

Foundations establish the vocabulary and mechanics needed by every later lesson.
Inventory first becomes an immutable history and an authoritative derived state.
Copied projections then create a synchronization problem. Only after those ideas
are clear do virtual time, scheduling, queues, and worker capacity appear. This
order separates domain truth from transport mechanics.

| Chapter | Lesson | CLI command |
| ---: | --- | --- |
| 0 | [Setting Up Your Laboratory](../book/00-setting-up-your-laboratory.md) | `inventory-sim doctor` and `inventory-sim demo` |
| 1 | [What Is Inventory?](../book/01-what-is-inventory.md) | `inventory-sim inventory --on-hand 10 --reserved 3` |
| 2 | [Authoritative Source of Truth](../book/02-authoritative-source-of-truth.md) | `inventory-sim authority` |
| 3 | [The Inventory Ledger](../book/03-the-inventory-ledger.md) | `inventory-sim ledger` |
| 4 | [Inventory Projections](../book/04-projections.md) | `inventory-sim projections` |
| 5 | [Time and Events](../book/05-time-and-events.md) | `inventory-sim timeline` |
| 6 | [Direct Synchronization](../book/06-direct-synchronization.md) | `inventory-sim sync-direct` |
| 7 | [Queues](../book/07-queues.md) | `inventory-sim sync-queue` |
| 8 | [Workers and Capacity](../book/08-workers-and-capacity.md) | `inventory-sim worker-capacity` |
| 9 | [Multiple Workers](../book/09-multiple-workers.md) | `inventory-sim multiple-workers` |

## Correctness — Chapters 10–15

Once work can wait and overlap, a successful delivery can still carry an old
snapshot. These chapters first observe and measure that problem, then introduce
monotonic revisions to identify it and explicit policies to detect or reject it.
Multiple projections come last so readers apply the same correctness reasoning
to independent consumers rather than confusing multiplicity with correctness.

| Chapter | Lesson | CLI command |
| ---: | --- | --- |
| 10 | [Stale Snapshots](../book/10-stale-snapshots.md) | `inventory-sim stale-snapshots` |
| 11 | [Measuring Freshness](../book/11-measuring-freshness.md) | `inventory-sim freshness` |
| 12 | [Inventory Revisions](../book/12-inventory-revisions.md) | `inventory-sim revisions` |
| 13 | [Detecting Stale Synchronizations](../book/13-detecting-stale-synchronizations.md) | `inventory-sim detect-stale` |
| 14 | [Rejecting Stale Synchronizations](../book/14-rejecting-stale-synchronizations.md) | `inventory-sim reject-stale` |
| 15 | [Multiple Projections](../book/15-multiple-projections.md) | `inventory-sim multiple-projections` |

## Reliable Distribution — Chapters 16–22

With independent projections in place, one authority change must fan out into
multiple deliveries. Distribution creates retry, duplicate-delivery, and
reordering hazards. The book exposes each hazard before adding its corresponding
policy: retries, idempotency, monotonic ordering, and finally bounded failure
isolation in a dead-letter queue.

| Chapter | Lesson | CLI command |
| ---: | --- | --- |
| 16 | [Fan-Out Synchronization](../book/16-fan-out-synchronization.md) | `inventory-sim fanout` |
| 17 | [Retry Policies](../book/17-retry-policies.md) | `inventory-sim retries` |
| 18 | [Duplicate Delivery](../book/18-duplicate-delivery.md) | `inventory-sim duplicate-delivery` |
| 19 | [Idempotent Synchronization](../book/19-idempotent-synchronization.md) | `inventory-sim idempotency` |
| 20 | [Out-of-Order Delivery](../book/20-out-of-order-delivery.md) | `inventory-sim out-of-order` |
| 21 | [Ordering Guarantees](../book/21-ordering-guarantees.md) | `inventory-sim ordering` |
| 22 | [Dead Letter Queues](../book/22-dead-letter-queues.md) | `inventory-sim dead-letter` |

## Integration — Chapter 23

Integration adds no new mechanism. It composes the ledger, authority, fan-out,
queue, worker pool, retries, idempotency, ordering, and dead-letter handling into
one deterministic operational trace. Reading it last makes every line of the
capstone an application of an already-tested concept.

| Chapter | Lesson | CLI command |
| ---: | --- | --- |
| 23 | [End-to-End Operations Laboratory](../book/23-end-to-end-operations-laboratory.md) | `inventory-sim laboratory` |

## How to use each stop

1. Read the chapter's educational question and walkthrough.
2. Inspect its linked diagram rather than treating the diagram as a separate
   specification.
3. Run the CLI command with the Docker prefix.
4. Locate the corresponding model under [`src/inventory_sim/`](../src/inventory_sim/__init__.py)
   and behavioral checks under [`tests/`](../tests/test_package.py).
5. Move on only after you can explain the observed transition and the model's
   stated limits.

For a concept-to-code map, continue to the [architecture overview](architecture.md).
For why the laboratory excludes production infrastructure, read the
[design philosophy](design-philosophy.md).
