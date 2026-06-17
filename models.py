from dataclasses import dataclass, field
from enum import Enum
from typing import List


class ChangeType(Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"


class SyncDirection(Enum):
    UNIDIRECTIONAL = "unidirectional"
    BIDIRECTIONAL = "bidirectional"


class SyncAction(Enum):
    COPY = "copy"
    DELETE = "delete"


@dataclass
class FileInfo:
    relative_path: str
    size: int
    mtime: float

    def __eq__(self, other):
        if not isinstance(other, FileInfo):
            return False
        return (self.relative_path == other.relative_path
                and self.size == other.size
                and abs(self.mtime - other.mtime) < 0.001)


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.deleted) + len(self.modified)

    def is_empty(self) -> bool:
        return self.total_changes == 0


@dataclass
class SyncTask:
    action: SyncAction
    source_path: str
    dest_path: str
    relative_path: str
    size: int = 0

    def __str__(self):
        if self.action == SyncAction.COPY:
            return f"[COPY] {self.relative_path}"
        return f"[DELETE] {self.relative_path}"
