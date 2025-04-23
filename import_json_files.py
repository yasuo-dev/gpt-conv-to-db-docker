# import_json_files.py
import os
import json
import sqlite3

DATA_DIR = "data"
DB_PATH = "from_json_files.db"

# SQLite DB作成とテーブル定義
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        title TEXT,
        create_time REAL,
        update_time REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        parent_id TEXT,
        role TEXT,
        content TEXT,
        create_time REAL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    )
    """)

    conn.commit()
    conn.close()

# 分割された各item_*.jsonを処理
def import_json_files():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for fname in sorted(os.listdir(DATA_DIR)):
        if not fname.endswith(".json"):
            continue

        fpath = os.path.join(DATA_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                conv_id = data.get("id")
                title = data.get("title")
                create_time = data.get("create_time")
                update_time = data.get("update_time")

                # insert conversation
                cur.execute("""
                    INSERT OR IGNORE INTO conversations (id, title, create_time, update_time)
                    VALUES (?, ?, ?, ?)
                """, (conv_id, title, create_time, update_time))

                # insert messages from mapping
                mapping = data.get("mapping", {})
                for msg_id, msg in mapping.items():
                    msg_data = msg.get("message")
                    if not msg_data:
                        continue

                    role = msg_data.get("author", {}).get("role")
                    content = msg_data.get("content", {}).get("parts", [""])[0]
                    parent_id = msg.get("parent")
                    create_time = msg_data.get("create_time")

                    cur.execute("""
                        INSERT OR IGNORE INTO messages (id, conversation_id, parent_id, role, content, create_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (msg_id, conv_id, parent_id, role, content, create_time))

                print(f"✔ Imported {fname}")

            except Exception as e:
                print(f"❌ Failed to import {fname}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    import_json_files()

