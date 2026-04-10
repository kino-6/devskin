from __future__ import annotations

import argparse
import sys

from devskin.patch_starship import (
    DEFAULT_CONFIG_PATH,
    DevskinError,
    apply_preset,
    available_presets,
    preview_diff,
    rollback,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="devskin", description="Apply subtle modern-retro Starship presets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List available presets")

    preview_parser = subparsers.add_parser("preview", help="Preview a preset diff without modifying files")
    preview_parser.add_argument("preset")

    apply_parser = subparsers.add_parser("apply", help="Apply a preset to Starship config")
    apply_parser.add_argument("preset")

    subparsers.add_parser("rollback", help="Restore the last backup created by devskin apply")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            for name in available_presets():
                print(name)
            return 0

        if args.command == "preview":
            diff = preview_diff(DEFAULT_CONFIG_PATH, args.preset)
            if diff:
                print(diff, end="")
            else:
                print("No changes would be made.")
            return 0

        if args.command == "apply":
            config_path, backup_path = apply_preset(DEFAULT_CONFIG_PATH, args.preset)
            print(f"Applied preset: {args.preset}")
            print(f"Config path: {config_path}")
            print(f"Backup path: {backup_path}")
            print("Next step: open a new shell (or run 'exec $SHELL') to see the updated prompt.")
            return 0

        if args.command == "rollback":
            restored_path = rollback(DEFAULT_CONFIG_PATH)
            print(f"Restored config from backup: {restored_path}")
            return 0

        parser.error("Unknown command")
        return 2

    except DevskinError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
