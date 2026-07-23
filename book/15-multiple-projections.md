# Chapter 15: Multiple Projections

## Educational question

> Why would one authoritative inventory need more than one projection?

Different consumers need the same business fact for different purposes. A
storefront needs an availability view for shoppers, a warehouse needs it for
fulfilment, and reporting needs it for analysis. They share one authority but
do not share a mutable projection.

## One source, independent views

The inventory ledger remains the source of truth. Replaying its six events
produces authoritative Revision 6 with 18 units available. `ProjectionRegistry`
holds three named, immutable `InventoryProjection` values: **Storefront**,
**Warehouse**, and **Reporting**. A synchronization request names exactly one
of those projections and carries a snapshot of authority.

Independence is important: accepting a Warehouse request replaces only the
Warehouse value in the registry. It neither updates nor blocks Reporting or
Storefront. Given the same request sequence, virtual time, and fixed worker
rules, every run has the same outcome.

## Walkthrough

1. The ledger establishes Revision 3 and all three projections synchronize to it.
2. Authority advances deterministically to Revision 6.
3. Storefront receives stale Revision 3, while Warehouse and Reporting receive
   current Revision 6.
4. The Chapter 14 policy rejects only Storefront's stale request. The two
   current requests succeed normally.
5. A current Storefront request then succeeds, so all three independent views
   finish at Revision 6 with 18 available.

This is deliberately not a retry: the final Storefront request is a separately
scheduled, current request in the fixed scenario. There is no fan-out queue,
event bus, networking, duplicate delivery, or thread.

## Chapter diagram

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

The standalone diagram is in
[`diagrams/multiple-projections.md`](../diagrams/multiple-projections.md).

## Run the scenario

Docker remains the primary interface:

```bash
docker compose run --rm lab inventory-sim multiple-projections
```

Expected summary:

```text
Authority
Revision: 6
Available: 18

Storefront
Revision: 6
Available: 18

Warehouse
Revision: 6
Available: 18

Reporting
Revision: 6
Available: 18
```

The command also explains the isolated stale rejection before printing this
final state.

## Relationship to earlier chapters

Chapter 4 introduced projections, Chapters 6–9 built the synchronization
pipeline, Chapters 10–13 made snapshot age and revision ordering visible, and
Chapter 14 supplied the rejection policy. This chapter reuses those pieces
without redesigning the engine. Its one new idea is that one authority can feed
several separately named projections.

## Why this matters

Modern distributed systems frequently maintain multiple read models derived
from one authoritative source. Each model can serve its own workload and update
on its own schedule while deterministic revision checks prevent stale work for
that projection. Independence contains an outdated or rejected update instead
of allowing it to disturb every downstream view.
