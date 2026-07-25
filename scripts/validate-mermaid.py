#!/usr/bin/env python3
"""Discover and validate the repository's Mermaid diagram sources."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

MERMAID_FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*mermaid\s*$", re.IGNORECASE)
HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "node_modules",
}


@dataclass(frozen=True)
class Diagram:
    path: Path
    line: int
    source: str


def markdown_diagrams(
    path: Path, display_path: Path
) -> tuple[list[Diagram], list[str]]:
    diagrams: list[Diagram] = []
    errors: list[str] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        match = MERMAID_FENCE.match(lines[index])
        if not match:
            index += 1
            continue
        start = index + 2
        fence = match.group(1)
        index += 1
        body: list[str] = []
        while index < len(lines) and not re.match(
            rf"^\s*{re.escape(fence[0])}{{{len(fence)},}}\s*$", lines[index]
        ):
            body.append(lines[index])
            index += 1
        if index == len(lines):
            errors.append(f"{display_path}:{start - 1}: unclosed Mermaid fence")
            break
        diagrams.append(Diagram(display_path, start, "\n".join(body) + "\n"))
        index += 1
    return diagrams, errors


def discover(root: Path) -> tuple[list[Diagram], list[str]]:
    diagrams: list[Diagram] = []
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(
            part in EXCLUDED_DIRECTORIES for part in path.parts
        ):
            continue
        if path.suffix.lower() == ".mmd":
            diagrams.append(
                Diagram(path.relative_to(root), 1, path.read_text(encoding="utf-8"))
            )
        elif path.suffix.lower() in {".md", ".markdown"}:
            found, found_errors = markdown_diagrams(path, path.relative_to(root))
            diagrams.extend(found)
            errors.extend(found_errors)
    return diagrams, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output", type=Path, help="directory for extracted .mmd files"
    )
    args = parser.parse_args()
    root = args.root.resolve()
    diagrams, errors = discover(root)

    for diagram in diagrams:
        for offset, line in enumerate(diagram.source.splitlines()):
            if HTML_TAG.search(line):
                errors.append(
                    f"{diagram.path}:{diagram.line + offset}: "
                    f"HTML is not allowed in Mermaid: {line.strip()}"
                )

    if not diagrams:
        errors.append("no Mermaid diagrams found")

    if args.output:
        shutil.rmtree(args.output, ignore_errors=True)
        args.output.mkdir(parents=True)
        for number, diagram in enumerate(diagrams, start=1):
            safe_name = re.sub(r"[^A-Za-z0-9_.-]", "-", str(diagram.path))
            (args.output / f"{number:03d}-{safe_name}.mmd").write_text(
                diagram.source, encoding="utf-8"
            )

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Validated {len(diagrams)} Mermaid diagram(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
