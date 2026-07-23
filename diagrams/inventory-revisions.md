# Inventory Revisions

```mermaid
flowchart TD
    A[Ledger] --> B[Revision 1<br/>Available 10]
    B --> C[Revision 2<br/>Available 7]
    C --> D[Revision 3<br/>Available 10]
    D --> E[Quantity repeats<br/>Revision increases]
```

The downward path is ledger chronology. Available quantity returns to 10, while
the monotonically increasing revision distinguishes the later observation. The
diagram expresses ordering only, not synchronization policy or correctness.
