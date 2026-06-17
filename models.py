from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple


class ChangeType(Enum):
    ADDED = "added"
    DELETED = "deleted"
    MODIFIED = "modified"


class ConflictType(Enum):
    CONTENT = "content"
    NEWER_A = "newer_a"
    NEWER_B = "newer_b"


class ConflictStrategy(Enum):
    KEEP_A = "keep_a"
    KEEP_B = "keep_b"
    KEEP_NEWER = "keep_newer"
    KEEP_BOTH = "keep_both"
    SKIP = "skip"


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
    conflicts: List[Tuple[str, ConflictType]] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.deleted) + len(self.modified) + len(self.conflicts)

    def is_empty(self) -> bool:
        return self.total_changes == 0


@dataclass
class SyncTask:
    action: SyncAction
    source_path: str
    dest_path: str
    relative_path: str
    size: int = 0
    is_conflict: bool = False

    def __str__(self):
        conflict_marker = " [CONFLICT]" if self.is_conflict else ""
        if self.action == SyncAction.COPY:
            return f"[COPY] {self.relative_path}{conflict_marker}"
        return f"[DELETE] {self.relative_path}{conflict_marker}"
