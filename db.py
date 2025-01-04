import os
import aiosqlite
from mjson import json
import time


class Snowflake:
    def __init__(self):
        self.sequence = 0
        self.last_timestamp = -1
        self.last_check_time = 0  # 新增变量，记录上一次检查的时间戳

        # 41位时间戳
        self.twepoch = 1718869600

    def _timestamp(self):
        return int(time.time())

    def _til_next_millis(self):
        timestamp = self._timestamp()
        while timestamp <= self.last_timestamp:
            if (timestamp - self.last_check_time) > 5:  # 避免过于频繁的循环
                self.last_check_time = timestamp
                break
            timestamp = self._timestamp()
        self.last_timestamp = timestamp
        return timestamp

    def get_id(self):
        timestamp = self._timestamp()
        if self.last_timestamp == timestamp:
            self.sequence = (self.sequence + 1) & 4095
            if self.sequence == 0:
                timestamp = self._til_next_millis()
        else:
            self.sequence = 0

        self.last_timestamp = timestamp

        return ((timestamp - self.twepoch) << 12) | self.sequence


class AsyncBase:
    def __init__(self, name):
        os.makedirs("db", exist_ok=True)
        self.db_name = f"db/{name}.db"
        self.name = name
        self.snow = Snowflake()
        
    async def init_db(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f"CREATE TABLE IF NOT EXISTS {self.name} (id TEXT PRIMARY KEY, tags TEXT, fn TEXT)")
            await db.commit()

class Images(AsyncBase):
    async def len(self):
        query = f"SELECT COUNT(*) FROM {self.name}"
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(query)
            result = await cursor.fetchone()
            return result[0]  # 返回总数
            
    def raw2dict(self, data):
        return {
            'id':data[0],
            'tags':json.loads(data[1]),
            'fn':data[2]
        }
        
    async def add(self, fn, tag):
        idx = str(self.snow.get_id())
        tag = json.dumps(tag)
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f"INSERT INTO {self.name} (id, tags, fn) VALUES (?, ?, ?)", (idx, tag, fn))
            await db.commit()
        return await self.get(idx)
        
    async def delete(self, ids):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(f"DELETE FROM {self.name} WHERE id = ?", (ids,))
            await db.commit()

    async def get(self, idx):
        query = f"SELECT * FROM {self.name} WHERE id = ?"
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(query, (idx,))
            data = await cursor.fetchone()
            return self.raw2dict(data)

    async def all(self):
        query = f"SELECT * FROM {self.name}"
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(query)
            data = await cursor.fetchall()
            l = []    
            for i in data:
                l.append(self.raw2dict(i))
            return l

    async def get_by_tag(self, tag):
        query = f"SELECT * FROM {self.name} WHERE tags LIKE ?"
        data = await self.search(query, ('%' + tag + ',%',))
        l = []
        for i in data:
            l.append(self.raw2dict(i))
        return l

    async def modify(self, idx, tags):
        query = f"UPDATE {self.name} SET tags = ? WHERE id = ?"
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(query, (tags, idx))
            await db.commit()

    async def search(self, query, params):
        async with aiosqlite.connect(self.db_name) as db:
            cursor = await db.execute(query, params)
            return await cursor.fetchall()

# 创建 Images 类的实例
db = Images("images")
