"""Command Line Interface for win-cache-sweep."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from wincachesweep.scanner import DiskScanner, FileItem, purge_items


def format_bytes(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def print_report_text(report, safe_only: bool = False):
    print("=" * 60)
    print(" Windows Cache & Temp File Audit ")
    print("=" * 60)
    print(f"Total Files Analyzed: {report.scanned_files_count}")
    print(f"Total Potential Space: {format_bytes(report.total_scanned_bytes)}\n")

    print("Category Breakdown:")
    print("-" * 40)
    for category, size in report.category_totals.items():
        print(f"  {category:<20}: {format_bytes(size)}")
    print("-" * 40)

    filtered_items = report.items
    if safe_only:
        filtered_items = [i for i in report.items if i.safety_level == "SAFE"]

    safe_bytes = sum(i.size_bytes for i in filtered_items if i.safety_level == "SAFE")
    caution_bytes = sum(i.size_bytes for i in filtered_items if i.safety_level == "CAUTION")

    print(f"\nReclaimable Space (SAFE to clean): {format_bytes(safe_bytes)}")
    print(f"Reclaimable Space (CAUTION required): {format_bytes(caution_bytes)}\n")

    if filtered_items:
        print("Top Reclaimable Items:")
        sorted_items = sorted(filtered_items, key=lambda x: x.size_bytes, reverse=True)[:10]
        for item in sorted_items:
            print(f" [{item.safety_level:<7}] {format_bytes(item.size_bytes):>9} | {item.path}")


def export_report_json(report) -> str:
    data = {
        "summary": {
            "scanned_files": report.scanned_files_count,
            "total_bytes": report.total_scanned_bytes,
            "formatted_total": format_bytes(report.total_scanned_bytes),
            "category_totals": {
                k: {"bytes": v, "formatted": format_bytes(v)}
                for k, v in report.category_totals.items()
            },
        },
        "items": [
            {
                "path": str(item.path),
                "size_bytes": item.size_bytes,
                "formatted_size": format_bytes(item.size_bytes),
                "modified_time": item.modified_time.isoformat(),
                "category": item.category,
                "safety_level": item.safety_level,
                "reason": item.reason,
            }
            for item in report.items
        ],
    }
    return json.dumps(data, indent=2)


def main(argv: List[str] = None):
    parser = argparse.ArgumentParser(
        prog="win-cache-sweep",
        description="Audit and safely clean Windows temporary directories and crash dumps.",
    )
    parser.add_argument(
        "--stale-days",
        type=int,
        default=14,
        help="Number of days since modification to consider files stale (default: 14).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output result in JSON format.",
    )
    parser.add_argument(
        "--safe-only",
        action="store_true",
        help="Limit output/action to items rated strictly SAFE.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Perform actual cleanup of safe target files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate cleanup without deleting any files.",
    )

    args = parser.parse_args(argv)

    scanner = DiskScanner(stale_days=args.stale_days)
    report = scanner.scan_all()

    if args.json:
        print(export_report_json(report))
        return 0

    print_report_text(report, safe_only=args.safe_only)

    if args.clean or args.dry_run:
        target_items = [
            item for item in report.items
            if item.safety_level == "SAFE" or (not args.safe_only and item.safety_level == "CAUTION")
        ]
        is_dry = args.dry_run or not args.clean
        mode_str = "DRY RUN" if is_dry else "EXECUTION"
        print(f"\n[{mode_str}] Purging selected cache files...")
        reclaimed, count = purge_items(target_items, dry_run=is_dry)
        print(f"[{mode_str}] Reclaimed {format_bytes(reclaimed)} across {count} file(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
