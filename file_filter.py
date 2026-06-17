import os
from typing import List, Optional


class FileFilter:
    def __init__(self, extensions: Optional[List[str]] = None):
        self.extensions = self._normalize_extensions(extensions)

    def _normalize_extensions(self, extensions: Optional[List[str]]) -> List[str]:
        if not extensions:
            return []
        normalized = []
        for ext in extensions:
            ext = ext.strip().lower()
            if not ext:
                continue
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized.append(ext)
        return normalized

    def is_enabled(self) -> bool:
        return len(self.extensions) > 0

    def accept(self, filename: str) -> bool:
        if not self.is_enabled():
            return True
        _, ext = os.path.splitext(filename)
        return ext.lower() in self.extensions

    def accept_path(self, relative_path: str) -> bool:
        return self.accept(os.path.basename(relative_path))
