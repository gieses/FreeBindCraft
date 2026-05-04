#!/usr/bin/env python3
"""Scaffold a BindCraft project directory from bundled presets."""

from __future__ import annotations

import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path
from typing import Any

from loguru import logger

SETTINGS_ADVANCED = files("freebindcraft") / "assets" / "settings_advanced"
SETTINGS_FILTERS = files("freebindcraft") / "assets" / "settings_filters"


def normalize_json_stem(name: str) -> str:
    """Return the basename without ``.json`` for a preset label or filename."""
    name = name.strip()
    if name.endswith(".json"):
        return Path(name).stem
    return name


def list_bundled_json_stems(assets_dir: Any) -> list[str]:
    """Collect sorted stems of all ``*.json`` files under a bundled asset directory."""
    stems: list[str] = []
    for entry in assets_dir.iterdir():
        if entry.is_file() and entry.name.endswith(".json"):
            stems.append(Path(entry.name).stem)
    return sorted(stems)


def format_bundled_presets_help() -> str:
    """Build epilog text listing bundled advanced presets and filter files for ``--help``."""
    advanced = list_bundled_json_stems(SETTINGS_ADVANCED)
    filters = list_bundled_json_stems(SETTINGS_FILTERS)
    adv_lines = "\n".join(f"  - {s}" for s in advanced)
    fil_lines = "\n".join(f"  - {s}" for s in filters)
    return (
        "Available configs — advanced presets (settings argument, maps to --advanced):\n"
        f"{adv_lines}\n\n"
        "Available filters (filter_name argument, maps to --filters):\n"
        f"{fil_lines}\n"
    )


def resolve_bundled_json(stem: str, assets_dir: Any, label: str) -> Any:
    """Resolve ``stem`` to a readable bundled JSON resource; exit if missing."""
    candidate = assets_dir / f"{stem}.json"
    if not candidate.is_file():
        available = ", ".join(list_bundled_json_stems(assets_dir))
        logger.error("Unknown {} {!r}. Expected one of: {}", label, stem, available)
        sys.exit(1)
    return candidate


def validate_project_name(name: str) -> None:
    """Ensure *name* is a safe single-directory project label."""
    if not name or name.strip() != name:
        logger.error("Project name must be non-empty and must not have leading or trailing whitespace.")
        sys.exit(1)
    if name in (".", "..") or "/" in name or "\\" in name:
        logger.error("Project name must be a single path segment (no slashes or '..').")
        sys.exit(1)


def write_target_config_json(out: Path, project_name: str) -> None:
    """Write target settings JSON in the same shape as ``example/settings_target/PDL1.json``."""
    cfg = {
        "design_path": "./designs/",
        "binder_name": project_name,
        "starting_pdb": "./target.pdb",
        "chains": "A",
        "target_hotspot_residues": "",
        "lengths": [20, 40],
        "number_of_final_designs": 5,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def copy_resource_bytes(src: Any, dest: Path) -> None:
    """Copy bytes from a bundled resource (Traversable) to *dest*."""
    dest.write_bytes(src.read_bytes())


def build_argument_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser with description and dynamic preset epilog."""
    return argparse.ArgumentParser(
        description=(
            "Create a project folder with copied advanced settings, filters, and a target config JSON. "
            "The settings argument selects a bundled advanced preset (settings_advanced). "
            "The filter_name argument selects a bundled filter preset (settings_filters). "
            "Edit the generated *_config.json (starting_pdb, hotspots, lengths, etc.)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=format_bundled_presets_help(),
    )


def main() -> None:
    """CLI entry: parse args, validate, copy presets, write target config."""
    parser = build_argument_parser()
    parser.add_argument("project_name", help="Directory to create (also binder_name in the target config).")
    parser.add_argument(
        "settings",
        help="Bundled advanced preset stem or filename (e.g. default_4stage_multimer).",
    )
    parser.add_argument(
        "filter_name",
        help="Bundled filter preset stem or filename (e.g. default_filters).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow a non-empty project directory and overwrite output files.",
    )
    args = parser.parse_args()

    project = args.project_name
    validate_project_name(project)

    settings_stem = normalize_json_stem(args.settings)
    filter_stem = normalize_json_stem(args.filter_name)

    advanced_src = resolve_bundled_json(settings_stem, SETTINGS_ADVANCED, "settings")
    filters_src = resolve_bundled_json(filter_stem, SETTINGS_FILTERS, "filter")

    out_dir = Path(project)
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        logger.error(
            "Directory {} already exists and is not empty. Pass --force to write outputs anyway.",
            out_dir,
        )
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=True)

    dest_filters = out_dir / f"{project}_filters_{filter_stem}.json"
    dest_advanced = out_dir / f"{project}_settings_{settings_stem}.json"
    dest_config = out_dir / f"{project}_config.json"

    for path in (dest_filters, dest_advanced, dest_config):
        if path.exists() and not args.force:
            logger.error("{} already exists. Pass --force to overwrite.", path)
            sys.exit(1)

    copy_resource_bytes(filters_src, dest_filters)
    copy_resource_bytes(advanced_src, dest_advanced)
    write_target_config_json(dest_config, project)

    logger.success("Created {}", out_dir.resolve())
    logger.info("  {}", dest_filters.name)
    logger.info("  {}", dest_advanced.name)
    logger.info("  {}", dest_config.name)
    logger.info(
        "From inside {}, place your target as ./target.pdb (or edit {}), then run e.g.:",
        out_dir.name,
        dest_config.name,
    )
    logger.info(
        "  bindcraft --settings ./{} --filters ./{} --advanced ./{} --no-pyrosetta",
        dest_config.name,
        dest_filters.name,
        dest_advanced.name,
    )


if __name__ == "__main__":
    main()
