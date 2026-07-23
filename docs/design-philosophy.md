# Design Philosophy: Determinism Before Infrastructure

The Inventory Synchronization Laboratory is an executable textbook, not a
miniature production platform. Its job is to make one cause and one consequence
visible at a time. Deterministic simulations make that possible: identical
inputs produce identical event order, output, and assertions on every run.

## Intentional omissions

Volume I avoids the following technologies on purpose:

- **Networking** introduces latency, partial connectivity, protocols, ports, and
  environment setup before a reader can examine the synchronization rule.
- **Databases** add schema, transactions, persistence, and vendor behavior. The
  in-memory immutable ledger is enough to teach history and authority.
- **Kafka and RabbitMQ** are valuable production tools, but broker installation,
  configuration, acknowledgements, and client APIs would hide the abstract queue
  and delivery properties under product-specific detail.
- **`asyncio` and threads** allow operating-system and runtime scheduling to
  influence observations. A virtual clock, event scheduler, and deterministic
  worker pool show concurrency and capacity without nondeterministic execution.
- **Randomness** makes an example sometimes demonstrate the lesson and sometimes
  not. Failures, duplicates, delays, and reorderings here are explicit scripted
  inputs, so readers can reproduce and test every claim.

These are boundaries of the teaching model, not claims that production systems
should omit infrastructure or concurrency. Real deployments must address I/O,
persistence, security, operations, and failure modes outside Volume I.

## Why deterministic simulation works

A virtual clock advances only when the scenario says it should. Events at the
same time use stable insertion order. Queues are explicit, worker capacity and
service time are fixed, and failures are named in advance. Consequently:

- a diagram and its CLI trace describe the same causal sequence;
- a reader can change one input and attribute the changed outcome;
- tests are fast and do not sleep, race, or depend on external services;
- incorrect state can be reproduced rather than chased intermittently; and
- later policies can be compared against the same earlier failure case.

Determinism is therefore both a learning aid and a testing strategy. It removes
incidental complexity while preserving the logical problems—staleness,
duplication, ordering, bounded retries—that the chapter is meant to expose.

## Rules for interpreting the models

Treat a simulation as a precise explanation of one property, not as deployable
system design. Keep assumptions visible. Prefer explicit event sequences over
realistic-looking machinery. Add infrastructure only when a future volume first
teaches the new concept; do not retrofit it into Volume I examples.

Next, follow the [learning path](learning-path.md), or see how these constraints
shape the complete [architecture](architecture.md). Contributors should also
read the [extension checklist](../CONTRIBUTING.md#adding-a-future-chapter).
