import os
from typing import Dict

from models import FileInfo, DiffResult
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
