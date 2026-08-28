#!/usr/bin/env python3
"""Query bundled NanoCortex command specifications without model dependencies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FILES = {
    "dorado": ("dorado_subcommand_info.json", "dorado_subcommand_parameter.json"),
    "modkit": ("modkit_subcommand_info.json", "modkit_subcommand_parameter.json"),
    "rnafm": ("rnafm_subcommand_info.json", "rnafm_subcommand_parameter.json"),
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List subcommands or print a subcommand specification."
    )
    parser.add_argument("tool", choices=sorted(FILES))
    parser.add_argument("subcommand", nargs="?")
    parser.add_argument("--list", action="store_true", dest="list_subcommands")
    args = parser.parse_args()

    if not args.list_subcommands and not args.subcommand:
        parser.error("provide a subcommand or use --list")

    data_dir = Path(__file__).resolve().parent / "data"
    info_name, params_name = FILES[args.tool]
    info = load_json(data_dir / info_name)

    if args.list_subcommands:
        for name, definition in info.items():
            description = definition.get("description", "")
            print(f"{name}\t{description}")
        return 0

    params = load_json(data_dir / params_name)
    if args.subcommand not in info and args.subcommand not in params:
        available = ", ".join(sorted(set(info) | set(params)))
        parser.error(f"unknown subcommand {args.subcommand!r}; available: {available}")

    result = {
        "tool": args.tool,
        "subcommand": args.subcommand,
        "info": info.get(args.subcommand, {}),
        "parameters": params.get(args.subcommand, {}),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
