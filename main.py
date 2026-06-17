import argparse
import os
import sys
from typing import List

from models import SyncDirection, ConflictStrategy, ConflictType, SyncTask
from file_filter import FileFilter
from dir_comparator import DirectoryComparator
from syncer import Syncer


def print_filter_info(filter_obj: FileFilter, dirs: List[str]):
    if not filter_obj.is_enabled():
        print("No file extension filter applied. All file types will be processed.")
        return

    print(f"\n=== File Extension Filter ===")
    print(f"Filtering by extensions: {', '.join(filter_obj.extensions)}")

    from dir_comparator import DirectoryScanner
    scanner = DirectoryScanner(filter_obj)

    all_exts = set()
    for d in dirs:
        if os.path.isdir(d):
            exts = scanner.get_matched_extensions(d)
            if exts:
                all_exts.update(exts)
                print(f"  {os.path.basename(d)}: found {len(exts)} matching type(s): {', '.join(exts)}")

    if not all_exts:
        print("  WARNING: No matching files found with the specified extensions!")
    else:
        print(f"\nTotal file types to process: {', '.join(sorted(all_exts))}")
    print()


def print_unidirectional_diff(diff, source_label: str, target_label: str):
    print(f"\n=== Synchronization Plan ===")
    print(f"Direction: {source_label} → {target_label}")
    print(f"Total changes: {diff.total_changes}")

    if diff.is_empty():
        print("No differences found. Directories are in sync.")
        return

    if diff.added:
        print(f"\n[+] Added ({len(diff.added)}) - will be copied to target:")
        for path in diff.added:
            print(f"    + {path}")

    if diff.modified:
        print(f"\n[*] Modified ({len(diff.modified)}) - will overwrite target:")
        for path in diff.modified:
            print(f"    * {path}")

    if diff.deleted:
        print(f"\n[-] Deleted ({len(diff.deleted)}) - will be removed from target:")
        for path in diff.deleted:
            print(f"    - {path}")

    print()


def print_bidirectional_diff(diff, dir_a_label: str, dir_b_label: str):
    print(f"\n=== Synchronization Plan ===")
    print(f"Direction: {dir_a_label} ↔ {dir_b_label}")
    print(f"Total changes: {diff.total_changes}")

    if diff.is_empty():
        print("No differences found. Directories are in sync.")
        return

    if diff.added:
        print(f"\n[+] New files ({len(diff.added)}) - will be copied to the other side:")
        for path in diff.added:
            print(f"    + {path}  [{dir_a_label} → {dir_b_label}]")

    if diff.deleted:
        print(f"\n[←] New files ({len(diff.deleted)}) - will be copied to the other side:")
        for path in diff.deleted:
            print(f"    + {path}  [{dir_b_label} → {dir_a_label}]")

    if diff.modified:
        print(f"\n[=] Time-only changes ({len(diff.modified)}) - content identical, timestamps differ:")
        for path in diff.modified:
            print(f"    = {path}")

    if diff.conflicts:
        print(f"\n[!] Content Conflicts ({len(diff.conflicts)}) - both sides modified, content differs:")
        for path, ctype in diff.conflicts:
            if ctype == ConflictType.NEWER_A:
                marker = f"[newer in {dir_a_label}]"
            elif ctype == ConflictType.NEWER_B:
                marker = f"[newer in {dir_b_label}]"
            else:
                marker = "[content differs]"
            print(f"    ! {path}  {marker}")

    print()


def select_conflict_strategy(has_conflicts: bool) -> ConflictStrategy:
    if not has_conflicts:
        return ConflictStrategy.KEEP_NEWER

    print("\n=== Conflict Resolution Strategy ===")
    print("Detected content conflicts. Choose a resolution strategy:")
    print("  1) Keep newer file  (default)")
    print("  2) Keep version from source/dir_a")
    print("  3) Keep version from target/dir_b")
    print("  4) Keep both (rename to *.a.ext and *.b.ext)")
    print("  5) Skip all conflicts")

    try:
        choice = input("\nEnter choice [1-5, default=1]: ").strip()
    except EOFError:
        choice = "1"

    if choice == "2":
        return ConflictStrategy.KEEP_A
    elif choice == "3":
        return ConflictStrategy.KEEP_B
    elif choice == "4":
        return ConflictStrategy.KEEP_BOTH
    elif choice == "5":
        return ConflictStrategy.SKIP
    else:
        return ConflictStrategy.KEEP_NEWER


def confirm_action(prompt: str = "Proceed with sync?") -> bool:
    try:
        response = input(f"{prompt} [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    except EOFError:
        return False


def print_task_preview(tasks: List[SyncTask]):
    if not tasks:
        return

    copy_tasks = [t for t in tasks if t.action.value == "copy"]
    del_tasks = [t for t in tasks if t.action.value == "delete"]
    conflict_tasks = [t for t in tasks if t.is_conflict]

    print(f"\n=== Task Summary ===")
    print(f"Total operations: {len(tasks)}")
    print(f"  Copy:   {len(copy_tasks)}")
    if del_tasks:
        print(f"  Delete: {len(del_tasks)}")
    if conflict_tasks:
        print(f"  Conflict resolutions: {len(conflict_tasks)}")


def run_unidirectional(source_dir: str, target_dir: str,
                       file_filter: FileFilter, apply: bool = False):
    comparator = DirectoryComparator(file_filter)
    diff = comparator.compare(source_dir, target_dir)

    print_filter_info(file_filter, [source_dir, target_dir])
    print_unidirectional_diff(diff, source_dir, target_dir)

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
                      file_filter: FileFilter, apply: bool = False,
                      pre_selected_strategy: ConflictStrategy = None):
    comparator = DirectoryComparator(file_filter)
    diff = comparator.compare_bidirectional(dir_a, dir_b)

    print_filter_info(file_filter, [dir_a, dir_b])
    print_bidirectional_diff(diff, dir_a, dir_b)

    if diff.is_empty():
        return

    has_conflicts = len(diff.conflicts) > 0
    if pre_selected_strategy:
        strategy = pre_selected_strategy
        print(f"\nConflict strategy: {strategy.value}")
    else:
        strategy = select_conflict_strategy(has_conflicts)

    syncer = Syncer(file_filter, show_progress=False)
    tasks = syncer.planner.plan_bidirectional(dir_a, dir_b, diff, strategy)

    if tasks:
        print(f"\nSync plan:")
        for task in tasks:
            direction = "→" if task.source_path.startswith(os.path.abspath(dir_a)) else "←"
            conflict_tag = " [CONFLICT]" if task.is_conflict else ""
            print(f"  {task.action.value.upper():6s} {task.relative_path}  ({direction}){conflict_tag}")
        print()
        print_task_preview(tasks)

    if not apply:
        if not confirm_action("Proceed with bidirectional sync?"):
            print("Sync cancelled.")
            return

    syncer.show_progress = True
    syncer._execute_tasks(tasks)
    print(f"\nBidirectional sync completed: {dir_a} ↔ {dir_b}")


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

    parser.add_argument(
        "--strategy",
        choices=["keep_newer", "keep_a", "keep_b", "keep_both", "skip"],
        default=None,
        help="Conflict resolution strategy for bidirectional sync (default: ask user)"
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

    strategy = None
    if args.strategy:
        strategy_map = {
            "keep_newer": ConflictStrategy.KEEP_NEWER,
            "keep_a": ConflictStrategy.KEEP_A,
            "keep_b": ConflictStrategy.KEEP_B,
            "keep_both": ConflictStrategy.KEEP_BOTH,
            "skip": ConflictStrategy.SKIP,
        }
        strategy = strategy_map[args.strategy]

    direction = SyncDirection.UNIDIRECTIONAL if args.direction == "uni" else SyncDirection.BIDIRECTIONAL

    if direction == SyncDirection.UNIDIRECTIONAL:
        run_unidirectional(source_dir, target_dir, file_filter, apply=args.yes)
    else:
        run_bidirectional(source_dir, target_dir, file_filter, apply=args.yes,
                          pre_selected_strategy=strategy)


if __name__ == "__main__":
    main()
