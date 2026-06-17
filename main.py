import argparse
import os
import sys

from models import SyncDirection
from file_filter import FileFilter
from dir_comparator import DirectoryComparator
from syncer import Syncer


def print_diff(diff, source_label: str = "Source", target_label: str = "Target"):
    print(f"\n=== Directory Comparison: {source_label} vs {target_label} ===")
    print(f"Total changes: {diff.total_changes}")

    if diff.is_empty():
        print("No differences found. Directories are in sync.")
        return

    if diff.added:
        print(f"\n[+] Added files ({len(diff.added)}):")
        for path in diff.added:
            print(f"    + {path}")

    if diff.deleted:
        print(f"\n[-] Deleted files ({len(diff.deleted)}):")
        for path in diff.deleted:
            print(f"    - {path}")

    if diff.modified:
        print(f"\n[*] Modified files ({len(diff.modified)}):")
        for path in diff.modified:
            print(f"    * {path}")

    print()


def confirm_action(prompt: str = "Proceed with sync?") -> bool:
    try:
        response = input(f"{prompt} [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    except EOFError:
        return False


def run_unidirectional(source_dir: str, target_dir: str,
                       file_filter: FileFilter, apply: bool = False):
    comparator = DirectoryComparator(file_filter)
    diff = comparator.compare(source_dir, target_dir)
    print_diff(diff, source_dir, target_dir)

    if diff.is_empty():
        return

    if not apply:
        if not confirm_action("Apply changes (source -> target)?"):
            print("Sync cancelled.")
            return

    syncer = Syncer(file_filter, show_progress=True)
    syncer.sync_unidirectional(source_dir, target_dir, diff)
    print(f"\nSync completed: {source_dir} -> {target_dir}")


def run_bidirectional(dir_a: str, dir_b: str,
                      file_filter: FileFilter, apply: bool = False):
    comparator = DirectoryComparator(file_filter)
    diff_ab = comparator.compare(dir_a, dir_b)
    diff_ba = comparator.compare(dir_b, dir_a)

    print(f"\n=== Bidirectional Comparison: {dir_a} <-> {dir_b} ===")

    all_added = set(diff_ab.added) | set(diff_ba.deleted)
    all_deleted = set(diff_ab.deleted) | set(diff_ba.added)
    all_modified = set(diff_ab.modified)

    total = len(all_added) + len(all_deleted) + len(all_modified)
    print(f"Total files to sync: {total}")

    if total == 0:
        print("Directories are in sync.")
        return

    syncer = Syncer(file_filter, show_progress=False)
    tasks = syncer.planner.plan_bidirectional(dir_a, dir_b)

    if tasks:
        print(f"\nSync plan:")
        for task in tasks:
            direction = "->" if task.source_path.startswith(os.path.abspath(dir_a)) else "<-"
            print(f"  {task.action.value.upper():6s} {task.relative_path} ({direction})")
        print()

    if not apply:
        if not confirm_action("Proceed with bidirectional sync?"):
            print("Sync cancelled.")
            return

    syncer.show_progress = True
    syncer._execute_tasks(tasks)
    print(f"\nBidirectional sync completed: {dir_a} <-> {dir_b}")


def main():
    parser = argparse.ArgumentParser(
        description="Directory Sync Tool - Compare and synchronize directories"
    )

    parser.add_argument("source", help="Source directory path")
    parser.add_argument("target", help="Target directory path")

    parser.add_argument(
        "-d", "--direction",
        choices=["uni", "bi"],
        default="uni",
        help="Sync direction: 'uni' for unidirectional (source->target), 'bi' for bidirectional (default: uni)"
    )

    parser.add_argument(
        "-e", "--extensions",
        nargs="*",
        default=None,
        help="Filter by file extensions (e.g., .txt .py or txt py)"
    )

    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Automatically confirm sync without prompting"
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar display"
    )

    args = parser.parse_args()

    source_dir = os.path.abspath(args.source)
    target_dir = os.path.abspath(args.target)

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory does not exist: {source_dir}", file=sys.stderr)
        sys.exit(1)

    if args.direction == "uni" and not os.path.isdir(target_dir):
        print(f"Note: Target directory does not exist, will be created during sync.")

    file_filter = FileFilter(args.extensions)

    if file_filter.is_enabled():
        print(f"Filtering by extensions: {', '.join(file_filter.extensions)}")

    direction = SyncDirection.UNIDIRECTIONAL if args.direction == "uni" else SyncDirection.BIDIRECTIONAL

    if direction == SyncDirection.UNIDIRECTIONAL:
        run_unidirectional(source_dir, target_dir, file_filter, apply=args.yes)
    else:
        run_bidirectional(source_dir, target_dir, file_filter, apply=args.yes)


if __name__ == "__main__":
    main()
