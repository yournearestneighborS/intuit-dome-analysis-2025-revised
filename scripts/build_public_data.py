#!/usr/bin/env python3
"""Build aggregate public data from the private challenge workbook."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.clippers_analysis import build_and_write_public_data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path, help="Path to the private XLSX workbook")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed",
        help="Directory for de-identified aggregate CSV files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tables = build_and_write_public_data(args.workbook, args.output_dir)
    print(f"Wrote {len(tables)} aggregate tables to {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
