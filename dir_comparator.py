import os
from typing import Dict, List, Tuple

from models import FileInfo, DiffResult, ConflictType
from file_filter import FileFilter
from file_hasher import FileHasher


class DirectoryScanner:
    def __init__(self, file_filter: FileFilter = None):
        self.file_filter = file_filter or FileFilter()

    def scan(self, directory: str) -> Dict[str, FileInfo]:
        directory = os.path.abspath(directory)
        files = {}
        if not os.path.isdir(directory):
            return files

        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if not self.file_filter.accept(filename):
                    continue
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, directory)
                relative_path = relative_path.replace(os.sep, '/')
                try:
                    stat = os.stat(full_path)
                    files[relative_path] = FileInfo(
                        relative_path=relative_path,
                        size=stat.st_size,
                        mtime=stat.st_mtime
                    )
                except OSError:
                    continue
        return files

    def get_matched_extensions(self, directory: str) -> List[str]:
        directory = os.path.abspath(directory)
        exts = set()
        if not os.path.isdir(directory):
            return sorted(exts)

        for root, _, filenames in os.walk(directory):
            for filename in filenames:
                if not self.file_filter.accept(filename):
                    continue
                _, ext = os.path.splitext(filename)
                if ext:
                    exts.add(ext.lower())
        return sorted(exts)


class DirectoryComparator:
    def __init__(self, file_filter: FileFilter = None, use_hash: bool = True):
        self.scanner = DirectoryScanner(file_filter)
        self.hasher = FileHasher() if use_hash else None
        self._source_root = ""
        self._target_root = ""

    def compare(self, source_dir: str, target_dir: str) -> DiffResult:
        self._source_root = os.path.abspath(source_dir)
        self._target_root = os.path.abspath(target_dir)
        source_files = self.scanner.scan(source_dir)
        target_files = self.scanner.scan(target_dir)

        result = DiffResult()

        all_paths = set(source_files.keys()) | set(target_files.keys())

        for path in all_paths:
            in_source = path in source_files
            in_target = path in target_files

            if in_source and not in_target:
                result.added.append(path)
            elif not in_source and in_target:
                result.deleted.append(path)
            else:
                if self._is_modified(source_files[path], target_files[path]):
                    result.modified.append(path)

        result.added.sort()
        result.deleted.sort()
        result.modified.sort()

        return result

    def compare_bidirectional(self, dir_a: str, dir_b: str) -> DiffResult:
        dir_a = os.path.abspath(dir_a)
        dir_b = os.path.abspath(dir_b)
        self._source_root = dir_a
        self._target_root = dir_b

        files_a = self.scanner.scan(dir_a)
        files_b = self.scanner.scan(dir_b)

        result = DiffResult()

        all_paths = set(files_a.keys()) | set(files_b.keys())

        for path in all_paths:
            in_a = path in files_a
            in_b = path in files_b

            if in_a and not in_b:
                result.added.append(path)
            elif not in_a and in_b:
                result.deleted.append(path)
            else:
                info_a = files_a[path]
                info_b = files_b[path]
                if self._is_modified(info_a, info_b):
                    if self.hasher is not None:
                        full_a = os.path.join(dir_a, path.replace('/', os.sep))
                        full_b = os.path.join(dir_b, path.replace('/', os.sep))
                        if not self.hasher.files_equal(full_a, full_b):
                            if info_a.mtime > info_b.mtime:
                                result.conflicts.append((path, ConflictType.NEWER_A))
                            else:
                                result.conflicts.append((path, ConflictType.NEWER_B))
                        else:
                            result.modified.append(path)
                    else:
                        if info_a.mtime > info_b.mtime:
                            result.conflicts.append((path, ConflictType.NEWER_A))
                        else:
                            result.conflicts.append((path, ConflictType.NEWER_B))

        result.added.sort()
        result.deleted.sort()
        result.modified.sort()
        result.conflicts.sort(key=lambda x: x[0])

        return result

    def _is_modified(self, src_info: FileInfo, tgt_info: FileInfo) -> bool:
        if src_info.size != tgt_info.size:
            return True
        if abs(src_info.mtime - tgt_info.mtime) <= 0.001:
            return False
        if self.hasher is None:
            return True
        src_full = os.path.join(self._source_root, src_info.relative_path.replace('/', os.sep))
        tgt_full = os.path.join(self._target_root, tgt_info.relative_path.replace('/', os.sep))
        return not self.hasher.files_equal(src_full, tgt_full)
