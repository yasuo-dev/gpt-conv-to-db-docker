#!/usr/bin/env python3
"""
ChatGPT Export (*.json) → SQLite 取り込みスクリプト
  ├ conversations         (1 ファイル = 1 レコード)
  ├ conversation_nodes    (ツリー構造)
  ├ messages              (メッセージ本体 + メタ)
  └ message_parts         (content.parts を縦持ち)

使い方:
  $ docker-compose run --rm jsonimport python import_json_files.py
"""

import glob
import sqlite3
from pathlib import Path
from typing import Any, Iterable, List, Dict

import orjson

DATA_DIR = Path("./data")
DB_FILE = Path("db/conversations.sqlite3")

# ───────────────────────────────────────── DDL
DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS conversations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name    TEXT UNIQUE,
    title        TEXT,
    create_time  REAL,
    update_time  REAL
);

CREATE TABLE IF NOT EXISTS conversation_nodes (
    node_id      TEXT PRIMARY KEY,
    conv_id      INTEGER NOT NULL,
    parent_id    TEXT,
    FOREIGN KEY(conv_id)  REFERENCES conversations(id),
    FOREIGN KEY(parent_id)REFERENCES conversation_nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_node_conv   ON conversation_nodes(conv_id);
CREATE INDEX IF NOT EXISTS idx_node_parent ON conversation_nodes(parent_id);

CREATE TABLE IF NOT EXISTS messages (
    msg_id        TEXT PRIMARY KEY,     -- = node_id
    role          TEXT,
    name          TEXT,
    content_type  TEXT,
    metadata_json TEXT,
    status        TEXT,
    end_turn      BOOLEAN,
    weight        REAL,
    create_time   REAL,
    update_time   REAL,
    FOREIGN KEY(msg_id) REFERENCES conversation_nodes(node_id)
);

CREATE INDEX IF NOT EXISTS idx_msg_role ON messages(role);

CREATE TABLE IF NOT EXISTS message_parts (
    msg_id      TEXT,
    part_index  INTEGER,
    part_text   TEXT,
    PRIMARY KEY (msg_id, part_index),
    FOREIGN KEY(msg_id) REFERENCES messages(msg_id)
);

CREATE INDEX IF NOT EXISTS idx_parts_msg ON message_parts(msg_id);
"""

# ───────────────────────────────────────── UTIL
def norm(v: Any) -> Any:
    """dict / list → JSON str, 他はそのまま"""
    if v is None:
        return None
    if isinstance(v, (dict, list)):
        return orjson.dumps(v).decode()
    return v


def iter_json_files(dir_path: Path) -> Iterable[Path]:
    yield from (Path(p) for p in glob.glob(str(dir_path / "*.json")))


# ───────────────────────────────────────── CORE
class Importer:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(DDL)

    # ---------- conversations ----------
    def _ensure_conversation(
        self, file_name: str, hdr: Dict[str, Any]
    ) -> int:
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO conversations(file_name,title,create_time,update_time)"
            " VALUES(?,?,?,?)",
            (
                file_name,
                hdr.get("title"),
                hdr.get("create_time"),
                hdr.get("update_time"),
            ),
        )
        # 既にあれば SELECT
        if cur.rowcount == 0:
            conv_id = self.conn.execute(
                "SELECT id FROM conversations WHERE file_name=?",
                (file_name,),
            ).fetchone()[0]
        else:
            conv_id = cur.lastrowid
        return conv_id

    # ---------- insert helpers ----------
    def _insert_node(self, node_id: str, conv_id: int, parent_id: str | None):
        self.conn.execute(
            "INSERT OR IGNORE INTO conversation_nodes(node_id,conv_id,parent_id)"
            " VALUES(?,?,?)",
            (node_id, conv_id, parent_id),
        )

    def _insert_message(self, msg: Dict[str, Any]):
        self.conn.execute(
            """INSERT OR IGNORE INTO messages
               (msg_id, role, name, content_type, metadata_json,
                status, end_turn, weight, create_time, update_time)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (
                norm(msg["id"]),
                norm(msg["author"].get("role")),
                norm(msg["author"].get("name")),
                norm(msg["content"].get("content_type")),
                norm(msg.get("metadata")),
                norm(msg.get("status")),
                msg.get("end_turn"),
                msg.get("weight"),
                msg.get("create_time"),
                msg.get("update_time"),
            ),
        )

    def _insert_parts(self, msg_id: str, parts: List[str]):
        self.conn.executemany(
            "INSERT OR IGNORE INTO message_parts(msg_id,part_index,part_text)"
            " VALUES(?,?,?)",
            [(msg_id, idx, part) for idx, part in enumerate(parts)],
        )

    # ---------- per-file importer ----------
    def import_file(self, path: Path):
        obj = orjson.loads(path.read_bytes())
        conv_id = self._ensure_conversation(path.name, obj)

        mapping = obj["mapping"]
        for node_id, node in mapping.items():
            parent_id = node.get("parent")
            self._insert_node(node_id, conv_id, parent_id)

            if node.get("message") is None:  # system root など
                continue

            msg = node["message"]
            self._insert_message(msg)
            parts = msg["content"].get("parts") or []
            self._insert_parts(msg["id"], parts)

    # ---------- run ----------
    def run(self, files: Iterable[Path]):
        for f in files:
            try:
                self.conn.execute("BEGIN")
                self.import_file(f)
                self.conn.commit()
                print(f"✅ {f.name}")
            except Exception as e:
                self.conn.rollback()
                print(f"❌ {f.name}: {e}")

        self.conn.close()


# ───────────────────────────────────────── entry
def main():
    importer = Importer(DB_FILE)
    importer.run(iter_json_files(DATA_DIR))


if __name__ == "__main__":
    main()