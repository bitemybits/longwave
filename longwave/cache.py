from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path


class JsonCache:
    def __init__(self, path: str, ttl_seconds: int):
        self.path = Path(path)
        self.ttl = ttl_seconds

    def read(self):
        try:
            st = self.path.stat()
            if time.time() - st.st_mtime > self.ttl:
                return None
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return None

    def write(self, value) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=self.path.name, dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, separators=(",", ":"))
            os.replace(tmp, self.path)
        finally:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass
