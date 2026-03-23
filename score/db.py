# score/db.py
import sqlite3
from datetime import datetime
import os

DB_PATH = "ez2score.db"  # スコア管理用DB

def find_same_score(song_id, key, mode, difficulty, score, rate, combo):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT 1 FROM scores
        WHERE song_id=? AND key=? AND mode=? AND difficulty=?
        AND score=? AND rate=? AND combo=?
        LIMIT 1
    """, (song_id, key, mode, difficulty, score, rate, combo))

    result = cur.fetchone()
    conn.close()
    return result is not None

#print("DB_PATH:", os.path.abspath(DB_PATH))
# ===== スコア登録 =====
def register_score(song_id, key, mode, difficulty, score, rate, combo, entry_name=""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # scoresテーブルを安全に作成
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER NOT NULL,
            key TEXT NOT NULL,
            mode TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            rate REAL NOT NULL,
            combo INTEGER NOT NULL,
            play_time TEXT NOT NULL,
            entry_name TEXT DEFAULT ''
        )
    """)

    # 必須項目チェック
    if None in (song_id, key, mode, difficulty, score, rate, combo):
        conn.close()
        return False

    # 重複チェック（同条件・同スコア・同rate・同combo）
    cur.execute("""
        SELECT id FROM scores
        WHERE song_id=? AND key=? AND mode=? AND difficulty=? AND score=? AND rate=? AND combo=?
    """, (song_id, key, mode, difficulty, score, rate, combo))
    if cur.fetchone():
        conn.close()
        return False  # 重複あり

    # 同条件でスコアより低いものは削除
    cur.execute("""
        DELETE FROM scores
        WHERE song_id=? AND key=? AND mode=? AND difficulty=? AND score < ?
    """, (song_id, key, mode, difficulty, score))

    # 登録
    play_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO scores (song_id, key, mode, difficulty, score, rate, combo, play_time, entry_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (song_id, key, mode, difficulty, score, rate, combo, play_time, entry_name))

    # 上位10件整理
    cur.execute("""
        DELETE FROM scores
        WHERE id NOT IN (
            SELECT id FROM scores
            WHERE song_id=? AND key=? AND mode=? AND difficulty=?
            ORDER BY score DESC, rate DESC, combo DESC, play_time ASC
            LIMIT 10
        )
        AND song_id=? AND key=? AND mode=? AND difficulty=?
    """, (song_id, key, mode, difficulty, song_id, key, mode, difficulty))

    conn.commit()
    conn.close()
    return True

# ===== ランキング取得 =====
def get_ranking(song_id, key, mode, difficulty):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT score, rate, combo, entry_name FROM scores
        WHERE song_id = ? AND key = ? AND mode = ? AND difficulty = ?
        ORDER BY score DESC, rate DESC, combo DESC 
    """, (song_id, key, mode, difficulty))

    ranking = cur.fetchall()
    conn.close()
    return ranking