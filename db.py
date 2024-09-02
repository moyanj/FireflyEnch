import os
import mjson as json
import io
from tinydb import TinyDB, Storage, Query
from typing import Dict, Any, Optional
import threading


class FastJSONStorage(Storage):
    def __init__(
        self,
        path: str,
        create_dirs=False,
        encoding=None,
        access_mode="r+",
        write_threshold=1,
        force=False,
        **kwargs
    ):
        super().__init__()
        self._mode = access_mode
        self.kwargs = kwargs
        self.force = force
        self.write_threshold = write_threshold  # 指定写入阈值
        self.write_counter = 0
        self._lock = threading.Lock()  # 添加互斥锁

        if any(
            [character in self._mode for character in ("+", "w", "a")]
        ):  # any of the writing modes
            self.touch(path, create_dirs=create_dirs)
        self._handle = open(path, mode=self._mode, encoding=encoding)

    def close(self) -> None:
        self._handle.close()

    def touch(self, path: str, create_dirs: bool):
        if create_dirs:
            base_dir = os.path.dirname(path)

            if not os.path.exists(base_dir):
                os.makedirs(base_dir)

        with open(path, "a"):
            pass

    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        self._lock.acquire()
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()

        if not size:
            self._lock.release()
            return None
        else:
            self._handle.seek(0)

            ret = json.loads(self._handle.read())
            self._lock.release()
            return ret

    def write(self, data: Dict[str, Dict[str, Any]]):
        with self._lock:  # 加锁
            self.write_counter += 1
            if self.write_counter == self.write_threshold or self.force:
                self._handle.seek(0)

                serialized = json.dumps(data, **self.kwargs)

                try:
                    self._handle.write(serialized)
                except io.UnsupportedOperation:
                    raise IOError(
                        'Cannot write to the database. Access mode is "{0}"'.format(
                            self._mode
                        )
                    )

                self._handle.flush()
                os.fsync(self._handle.fileno())

                self._handle.truncate()
                self.write_counter = 0


class Base:
    def __init__(self, name, write_threshold=2, force=False):
        os.makedirs("db", exist_ok=True)
        self.rootdb = TinyDB(
            "db/DB.pcdb",
            storage=FastJSONStorage,
            write_threshold=write_threshold,
            force=False,
        )
        self.db = self.rootdb.table(name, cache_size=32)
        self.q = Query()

    def search(self, expr):
        return self.db.search(expr)

    def insert(self, data):
        self.db.insert(data)

    def remove(self, query):
        self.db.remove(query)


class Images(Base):

    def add(self, path, tag):
        max_id = str(self.db.__len__() + 1)
        d = {"id": max_id, "path": path, "tags": tag.split(",")}
        self.insert(d)
        return d

    def delete(self, ids):
        self.db.remove(self.q.id == str(ids))

    def get(self, idx):
        return self.search(self.q.id == str(idx))

    def get_by_tag(self, tag):
        return self.search(self.q.tags.any(tag))

    def modify(self, idx, tags):
        self.db.update({"tags": tags}, self.q.id == idx)


# 创建 Images 类的实例
db = Images("images", 1)
