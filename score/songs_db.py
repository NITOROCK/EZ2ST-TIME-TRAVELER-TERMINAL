# songs_db.py
import sqlite3

DB_PATH = "db/songs.db"

def get_song_id(title):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
    "SELECT id FROM songs WHERE song LIKE ?",
    (f"%{title}%",)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None