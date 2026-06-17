import os
from typing import Dict

from models import FileInfo, DiffResult
from file_filter import FileFilter


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
    def __init__(self, file_filter: FileFilter = None):
        self.scanner = DirectoryScanner(file_filter)

    def compare(self, source_dir: str, target_dir: str) -> DiffResult:
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
                src_info = source_files[path]
                tgt_info = target_files[path]
                if src_info.size != tgt_info.size or abs(src_info.mtime - tgt_info.mtime) > 0.001:
                    result.modified.append(path)

        result.added.sort()
        result.deleted.sort()
        result.modified.sort()

        return result
