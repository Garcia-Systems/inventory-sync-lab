# Diagram Style Guide

Diagrams in this repository explain behavior; they are not decoration. A
diagram should remain readable in GitHub's Markdown view and should make the
same deterministic claims as the surrounding lesson.

## Mermaid conventions

- Do not put HTML in Mermaid node or edge labels. In particular, do not use
  `<br>`, `<br/>`, `<br />`, or styling tags. Use a short single-line label such
  as `"Title — subtitle"` instead. If a line break is essential, use Mermaid's
  supported `"Title\nSubtitle"` syntax and verify it in GitHub.
- Prefer `flowchart TD` for a sequence and `flowchart LR` for a compact
  relationship or calculation. Do not change direction within one diagram.
- Keep labels short and use one concept per diagram. Put qualifications and
  detailed explanation in the paragraph after the diagram.
- Avoid crossing arrows. Reorder nodes or simplify the relationship rather than
  adding decorative routing.
- Use deterministic layouts: declare nodes and edges in a stable reading order,
  choose an explicit direction, and avoid layout-dependent ornamentation.
- For a calculation or dependency, show the relationship between inputs and
  output rather than formatting a node as a decorative summary card.

## Validation and review

Run the repository scanner before committing:

```bash
python scripts/validate-mermaid.py
```

The scanner discovers Mermaid fences in Markdown and standalone `.mmd` files,
rejects HTML tags, and exports every diagram for syntax rendering. CI renders
those exported sources with Mermaid CLI, so malformed syntax fails the build.

Automated validation is necessary but not sufficient. Preview every changed
diagram in GitHub before merging, checking label wrapping, arrow crossings, and
reading order against the surrounding prose.
