import os
import shutil
from typing import List, Callable, Optional

from models import SyncTask, SyncAction, SyncDirection, DiffResult, FileInfo, ConflictStrategy
from dir_comparator import DirectoryScanner
from file_filter import FileFilter
from file_hasher import FileHasher
from progress_bar import ProgressBar


class SyncPlanner:
    def __init__(self, file_filter: FileFilter = None, use_hash: bool = True):
        self.scanner = DirectoryScanner(file_filter)
        self.file_filter = file_filter or FileFilter()
        self.hasher = FileHasher() if use_hash else None

    def plan_unidirectional(self, source_dir: str, target_dir: str,
                            diff: DiffResult) -> List[SyncTask]:
        tasks = []
        source_dir = os.path.abspath(source_dir)
        target_dir = os.path.abspath(target_dir)

        source_files = self.scanner.scan(source_dir)

        for path in diff.added:
            src = os.path.join(source_dir, path.replace('/', os.sep))
            dst = os.path.join(target_dir, path.replace('/', os.sep))
            size = source_files.get(path, FileInfo(path, 0, 0)).size
            tasks.append(SyncTask(
                action=SyncAction.COPY,
                source_path=src,
                dest_path=dst,
                relative_path=path,
                size=size
            ))

        for path in diff.modified:
            src = os.path.join(source_dir, path.replace('/', os.sep))
            dst = os.path.join(target_dir, path.replace('/', os.sep))
            size = source_files.get(path, FileInfo(path, 0, 0)).size
            tasks.append(SyncTask(
                action=SyncAction.COPY,
                source_path=src,
                dest_path=dst,
                relative_path=path,
                size=size
            ))

        for path in diff.deleted:
            dst = os.path.join(target_dir, path.replace('/', os.sep))
            tasks.append(SyncTask(
                action=SyncAction.DELETE,
                source_path='',
                dest_path=dst,
                relative_path=path,
                size=0
            ))

        return tasks

    def plan_bidirectional(self, dir_a: str, dir_b: str,
                           diff: DiffResult,
                           strategy: ConflictStrategy = ConflictStrategy.KEEP_NEWER) -> List[SyncTask]:
        dir_a = os.path.abspath(dir_a)
        dir_b = os.path.abspath(dir_b)

        files_a = self.scanner.scan(dir_a)
        files_b = self.scanner.scan(dir_b)

        conflict_paths = set(p for p, _ in diff.conflicts)

        tasks = []
        all_paths = set(files_a.keys()) | set(files_b.keys())

        for path in all_paths:
            in_a = path in files_a
            in_b = path in files_b
            is_conflict = path in conflict_paths

            if in_a and not in_b:
                src = os.path.join(dir_a, path.replace('/', os.sep))
                dst = os.path.join(dir_b, path.replace('/', os.sep))
                tasks.append(SyncTask(
                    action=SyncAction.COPY,
                    source_path=src,
                    dest_path=dst,
                    relative_path=path,
                    size=files_a[path].size,
                    is_conflict=is_conflict
                ))
            elif not in_a and in_b:
                src = os.path.join(dir_b, path.replace('/', os.sep))
                dst = os.path.join(dir_a, path.replace('/', os.sep))
                tasks.append(SyncTask(
                    action=SyncAction.COPY,
                    source_path=src,
                    dest_path=dst,
                    relative_path=path,
                    size=files_b[path].size,
                    is_conflict=is_conflict
                ))
            else:
                info_a = files_a[path]
                info_b = files_b[path]
                if self._needs_bidir_copy(info_a, info_b, path, dir_a, dir_b):
                    tasks.extend(self._resolve_conflict(info_a, info_b, path, dir_a, dir_b, strategy, is_conflict))

        return tasks

    def _resolve_conflict(self, info_a: FileInfo, info_b: FileInfo,
                          relative_path: str, dir_a: str, dir_b: str,
                          strategy: ConflictStrategy, is_conflict: bool) -> List[SyncTask]:
        tasks = []
        full_a = os.path.join(dir_a, relative_path.replace('/', os.sep))
        full_b = os.path.join(dir_b, relative_path.replace('/', os.sep))

        if strategy == ConflictStrategy.SKIP:
            return tasks

        if strategy == ConflictStrategy.KEEP_BOTH:
            base, ext = os.path.splitext(relative_path)
            dir_name = os.path.dirname(relative_path)
            name = os.path.basename(base)
            if dir_name:
                new_a = f"{dir_name}/{name}.a{ext}"
                new_b = f"{dir_name}/{name}.b{ext}"
            else:
                new_a = f"{name}.a{ext}"
                new_b = f"{name}.b{ext}"
            tasks.append(SyncTask(
                action=SyncAction.COPY,
                source_path=full_a,
                dest_path=os.path.join(dir_b, new_a.replace('/', os.sep)),
                relative_path=new_a,
                size=info_a.size,
                is_conflict=is_conflict
            ))
            tasks.append(SyncTask(
                action=SyncAction.COPY,
                source_path=full_b,
                dest_path=os.path.join(dir_a, new_b.replace('/', os.sep)),
                relative_path=new_b,
                size=info_b.size,
                is_conflict=is_conflict
            ))
            return tasks

        a_is_newer = info_a.mtime > info_b.mtime + 0.001
        b_is_newer = info_b.mtime > info_a.mtime + 0.001

        if strategy == ConflictStrategy.KEEP_A:
            tasks.append(SyncTask(
                action=SyncAction.COPY,
                source_path=full_a,
                dest_path=full_b,
                relative_path=relative_path,
                size=info_a.size,
                is_conflict=is_conflict
            ))
        elif strategy == ConflictStrategy.KEEP_B:
            tasks.append(SyncTask(
                action=SyncAction.COPY,
                source_path=full_b,
                dest_path=full_a,
                relative_path=relative_path,
                size=info_b.size,
                is_conflict=is_conflict
            ))
        elif strategy == ConflictStrategy.KEEP_NEWER:
            if a_is_newer:
                tasks.append(SyncTask(
                    action=SyncAction.COPY,
                    source_path=full_a,
                    dest_path=full_b,
                    relative_path=relative_path,
                    size=info_a.size,
                    is_conflict=is_conflict
                ))
            elif b_is_newer:
                tasks.append(SyncTask(
                    action=SyncAction.COPY,
                    source_path=full_b,
                    dest_path=full_a,
                    relative_path=relative_path,
                    size=info_b.size,
                    is_conflict=is_conflict
                ))

        return tasks

    def _needs_bidir_copy(self, info_a: FileInfo, info_b: FileInfo,
                          relative_path: str, dir_a: str, dir_b: str) -> bool:
        if info_a.size != info_b.size:
            return True
        if abs(info_a.mtime - info_b.mtime) <= 0.001:
            return False
        if self.hasher is None:
            return True
        full_a = os.path.join(dir_a, relative_path.replace('/', os.sep))
        full_b = os.path.join(dir_b, relative_path.replace('/', os.sep))
        return not self.hasher.files_equal(full_a, full_b)


class SyncExecutor:
    def _copy_file(self, task: SyncTask) -> bool:
        try:
            dest_dir = os.path.dirname(task.dest_path)
            if dest_dir and not os.path.exists(dest_dir):
                os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(task.source_path, task.dest_path)
            return True
        except OSError:
            return False

    def _delete_file(self, task: SyncTask) -> bool:
        try:
            if os.path.isfile(task.dest_path):
                os.remove(task.dest_path)
            return True
        except OSError:
            return False

    def execute(self, task: SyncTask) -> bool:
        if task.action == SyncAction.COPY:
            return self._copy_file(task)
        elif task.action == SyncAction.DELETE:
            return self._delete_file(task)
        return False


class Syncer:
    def __init__(self, file_filter: FileFilter = None, show_progress: bool = True, use_hash: bool = True):
        self.planner = SyncPlanner(file_filter, use_hash=use_hash)
        self.executor = SyncExecutor()
        self.show_progress = show_progress

    def sync_unidirectional(self, source_dir: str, target_dir: str,
                            diff: DiffResult,
                            progress_callback: Optional[Callable[[int, int, str], None]] = None) -> int:
        tasks = self.planner.plan_unidirectional(source_dir, target_dir, diff)
        return self._execute_tasks(tasks, progress_callback)

    def sync_bidirectional(self, dir_a: str, dir_b: str,
                           diff: DiffResult,
                           strategy: ConflictStrategy = ConflictStrategy.KEEP_NEWER,
                           progress_callback: Optional[Callable[[int, int, str], None]] = None) -> int:
        tasks = self.planner.plan_bidirectional(dir_a, dir_b, diff, strategy)
        return self._execute_tasks(tasks, progress_callback)

    def _execute_tasks(self, tasks: List[SyncTask],
                       progress_callback: Optional[Callable[[int, int, str], None]] = None) -> int:
        total = len(tasks)
        success_count = 0

        progress = None
        if self.show_progress and total > 0:
            progress = ProgressBar(total=total, prefix="Syncing")

        for i, task in enumerate(tasks):
            if progress_callback:
                progress_callback(i, total, task.relative_path)

            if self.executor.execute(task):
                success_count += 1

            if progress:
                short_name = task.relative_path
                if len(short_name) > 30:
                    short_name = '...' + short_name[-27:]
                progress.update(current=i + 1, message=short_name)

        if progress:
            progress.finish(message=f"Complete ({success_count}/{total})")

        return success_count
