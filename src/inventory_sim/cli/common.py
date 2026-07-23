"""Shared declarative command registration for the laboratory CLI."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass

Command = Callable[..., int]


@dataclass(frozen=True)
class CommandSpec:
    """A command name, its stable help text, and its implementation."""

    name: str
    help: str
    handler: Command


def register_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    commands: tuple[CommandSpec, ...],
) -> None:
    """Register commands that do not define additional arguments."""
    for command in commands:
        parser = subparsers.add_parser(command.name, help=command.help)
        parser.set_defaults(handler=command.handler)
