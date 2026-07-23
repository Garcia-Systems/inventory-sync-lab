# Chapter 16: Fan-Out Synchronization

## Educational question

> How does one inventory change reach many downstream projections?

## One change, many work items

Chapter 15 established that Storefront, Warehouse, and Reporting are independent
projections of one authoritative inventory. Independence means that updating one
projection does not update the others. We therefore need one synchronization
request for every projection that should receive a revision.

Fan-out is the small deterministic step that performs that multiplication. It
accepts one revisioned authority snapshot, visits the registered projections in
registry order, and returns one immutable `SynchronizationRequest` per system.
Every request refers to the same immutable inventory snapshot. The authority is
neither changed nor replayed by this operation.

This adds work, not new business logic: three projections require three work
items and three projection updates.

## Chapter diagram

```text
                 Inventory Revision 8
                          │
                          ▼
                  Fan-Out Generator
                   ┌──────┼──────┐
                   ▼      ▼      ▼
               Storefront Warehouse Reporting
                 Request   Request   Request
```

See the standalone [fan-out diagram](../diagrams/fan-out-synchronization.md).

## Walkthrough

1. The inventory ledger advances once, producing authoritative Revision 8.
2. Storefront, Warehouse, and Reporting are already registered in that order.
3. The fan-out generator reads the registry and creates Requests 1, 2, and 3.
4. The fixed worker pool processes each request as an independent work item.
5. Each immutable projection is replaced only when its own work completes.
6. All three projections finish at Revision 8 with the Revision 8 snapshot.

The simulator uses a virtual clock and event scheduler, so repeated runs produce
the same request ordering and result. There is no transport between generator
and workers and no operating-system concurrency.

## Run the scenario

Docker is the default laboratory environment:

```bash
docker compose build
docker compose run --rm lab inventory-sim fanout
```

## Expected output

```text
Fan-Out Synchronization

Authority advanced to Revision 8

Generating synchronization requests...

Storefront   -> Request 1
Warehouse    -> Request 2
Reporting    -> Request 3

Worker processing...

Storefront updated to Revision 8
Warehouse updated to Revision 8
Reporting updated to Revision 8

Summary
Authoritative revision: 8
Generated requests: 3
Projections updated: 3
```

## Relationship to Chapter 15

Chapter 15 focused on the existence and isolation of multiple projections. This
chapter supplies the missing distribution mechanism: instead of manually
creating work for each projection, one generator deterministically derives all
three requests from one authoritative revision. The existing synchronization
engine still processes each request in the same way.

## Why this matters

Many production systems distribute one business event to multiple downstream
consumers: a sale might update a storefront, warehouse view, and reporting
model. That multiplication increases workload even when the inventory rules do
not change.

This chapter models only the logical fan-out. It deliberately does not model a
network, broker, retries, duplicate delivery, failures, threads, or asynchronous
messaging. Future chapters can explore what happens when delivery becomes
unreliable; those reliability concerns remain separate from this lesson.
