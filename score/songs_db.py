# songs_db.py
import sqlite3
import sys
from pathlib import Path

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(".")

BASE_PATH = get_base_path()

# ★ DBの正しいパスを作る
SONGS_DB_PATH = BASE_PATH / "db" / "songs.db"

# ★ 存在チェック
if not SONGS_DB_PATH.exists():
    raise FileNotFoundError(f"songs.db が見つかりません: {SONGS_DB_PATH}")

def get_song_id(title):
    conn = sqlite3.connect(SONGS_DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM songs WHERE song LIKE ?",
        (f"%{title}%",)
    )

    row = cur.fetchone()
    conn.close()

    return row[0] if row else None