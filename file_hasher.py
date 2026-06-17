import hashlib
import os
from typing import Optional


class FileHasher:
    CHUNK_SIZE = 65536

    def __init__(self, algorithm: str = "md5"):
        self.algorithm = algorithm

    def _new_hasher(self):
        if self.algorithm.lower() == "md5":
            return hashlib.md5()
        elif self.algorithm.lower() in ("sha1", "sha-1"):
            return hashlib.sha1()
        elif self.algorithm.lower() in ("sha256", "sha-256"):
            return hashlib.sha256()
        else:
            return hashlib.md5()

    def hash_file(self, file_path: str) -> Optional[str]:
        file_path = os.path.abspath(file_path)
        if not os.path.isfile(file_path):
            return None

        hasher = self._new_hasher()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError):
            return None

    def files_equal(self, path_a: str, path_b: str) -> bool:
        hash_a = self.hash_file(path_a)
        hash_b = self.hash_file(path_b)
        if hash_a is None or hash_b is None:
            return False
        return hash_a == hash_b
