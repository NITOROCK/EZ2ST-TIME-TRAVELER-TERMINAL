import mss
import numpy as np
import cv2
import pytesseract
import keyboard
import time
import winsound
import sqlite3
from datetime import datetime

# 音ファイルパス（ニトロが用意する想定）
SUCCESS_SOUND = r"C:\Users\user\Desktop\頂ーITADAKIー\EZ2ST\success.wav"
FAIL_SOUND    = r"C:\Users\user\Desktop\頂ーITADAKIー\EZ2ST\fail.wav"

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def save_score(song_id, key, mode, difficulty, score, rate, combo):

    conn = sqlite3.connect("ez2score.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO scores (
            song_id,
            key,
            mode,
            difficulty,
            score,
            rate,
            combo,
            play_time
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        song_id,
        key,
        mode,
        difficulty,
        int(score) if score != "" else 0,
        float(rate.replace("%","")) if rate != "" else 0,
        int(combo) if combo != "" else 0,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()
    
# =========================
# 座標（EZ2SCREEN流用）
# =========================

def crop_areas(img):

    areas = {}

    areas["score"] = img[637:694 , 1441:1650]
    areas["rate"] = img[616:650 , 1131:1259]
    areas["combo"] = img[652:688 , 1132:1260]

    areas["title"] = img[179:221 , 843:1503]
    areas["key"] = img[139:190, 52:128]
    areas["mode"] = img[239:462 , 83:126]

    areas["EZ"]  = img[181:219, 1502:1550]
    areas["NM"]  = img[181:219, 1570:1610]
    areas["HD"]  = img[181:219, 1630:1675]
    areas["SHD"] = img[181:219, 1695:1735]

    return areas

# =========================
# OCR関数群（そのまま移植）
# =========================

def ocr_text(area):
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray, config="--psm 7")
    return text.strip()

def ocr_number(area):
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray,150,255,cv2.THRESH_BINARY)[1]
    text = pytesseract.image_to_string(
        thresh,
        config="--psm 7 -c tessedit_char_whitelist=0123456789.%"
    )
    return text.strip()

def ocr_vertical(area):
    rotated = cv2.rotate(area, cv2.ROTATE_90_COUNTERCLOCKWISE)
    gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray,130,255,cv2.THRESH_BINARY)[1]
    text = pytesseract.image_to_string(thresh, config="--psm 7")
    return text.strip()

def ocr_key(area):

    rotated = cv2.rotate(area, cv2.ROTATE_90_COUNTERCLOCKWISE)
    hsv = cv2.cvtColor(rotated, cv2.COLOR_BGR2HSV)

    lower = (20,120,120)
    upper = (40,255,255)

    mask = cv2.inRange(hsv, lower, upper)

    # ⭐ここ追加
    mask = cv2.GaussianBlur(mask, (5,5), 0)
    _, mask = cv2.threshold(mask, 180, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(
        mask,
        config="--psm 10 -c tessedit_char_whitelist=4568"
    ).strip()

    if text in ["4","5","6","8"]:
        return text + "K"

    return "UNKNOWN"

def ocr_difficulty(area):
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray,200,255,cv2.THRESH_BINARY)
    text = pytesseract.image_to_string(
        thresh,
        config="--psm 7 -c tessedit_char_whitelist=0123456789"
    )
    return text.strip()

def fix_mode(text):

    t = text.upper().replace(" ", "")

    if "BAS" in t:
        return "BASIC"

    if "ST" in t or len(t) >= 6:
        return "STANDARD"

    return "UNKNOWN"

def detect_difficulty(areas):

    diff_areas = {
        "EZ": areas["EZ"],
        "NM": areas["NM"],
        "HD": areas["HD"],
        "SHD": areas["SHD"]
    }

    for name, area in diff_areas.items():

        gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)

        bright = cv2.countNonZero(
            cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1]
        )

        if bright > 40:
            return name

    return "UNKNOWN"

def get_ranking(song_id, key, mode, difficulty):

    import sqlite3

    conn = sqlite3.connect("ez2score.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT score, rate, combo, play_time
        FROM scores
        WHERE song_id = ?
        AND key = ?
        AND mode = ?
        AND difficulty = ?
        ORDER BY score DESC
        LIMIT 10
    """, (song_id, key, mode, difficulty))

    rows = cur.fetchall()
    conn.close()

    return rows

def get_song_id(title):

    import sqlite3

    conn = sqlite3.connect("songs.db")
    cur = conn.cursor()

    cur.execute("""
        SELECT id, song
        FROM songs
        WHERE song LIKE ?
    """, ("%" + title + "%",))

    row = cur.fetchone()
    conn.close()

    if row:
        return row[0]

    return None

# =========================
# タイトル OCR（背景自動判定付き）
# =========================
def ocr_title_auto(area):
    """
    画面タイトルエリアを見て背景が明るいか暗いか判定し、
    適切な OCR 関数を呼び出す
    """
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)

    if mean_brightness > 180:
        # 明るい（白背景） → adaptiveThreshold 方式
        gray = cv2.equalizeHist(gray)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        text = pytesseract.image_to_string(thresh, config="--psm 7")
    else:
        # 暗い背景 → 従来方式
        text = pytesseract.image_to_string(gray, config="--psm 7")

    return text.strip()

# =========================
# メインループ
# =========================

#print("EZ2ST OCR待機中… HOMEキーを1秒長押しで読取")

with mss.mss() as sct:

    while True:

        if keyboard.is_pressed("home"):

            key_results = []
            mode_results = []
            title_result = ""
            score_result = ""
            rate_result = ""
            combo_result = ""
            difficulty_result = ""
            song_id = None
            success = False

            for i in range(5):

                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                areas = crop_areas(img)

                # OCR
                score = ocr_number(areas["score"])
                rate = ocr_number(areas["rate"])
                combo = ocr_number(areas["combo"])
                title = ocr_title_auto(areas["title"])
                key = ocr_key(areas["key"])
                mode_raw = ocr_vertical(areas["mode"])
                mode = fix_mode(mode_raw)
                difficulty = detect_difficulty(areas)

                # 値を蓄積
                if key not in ["UNKNOWN", ""]:
                    key_results.append(key)
                if mode not in ["UNKNOWN", ""]:
                    mode_results.append(mode)

                if not title_result and title != "":
                    title_result = title
                    score_result = score
                    rate_result = rate
                    combo_result = combo
                    difficulty_result = difficulty

                time.sleep(0.15)

            # 最も多かった結果を確定
            from collections import Counter

            key_final = Counter(key_results).most_common(1)[0][0] if key_results else "UNKNOWN"
            mode_final = Counter(mode_results).most_common(1)[0][0] if mode_results else "UNKNOWN"

            # 判定
            if key_final != "UNKNOWN" and mode_final != "UNKNOWN":
                song_id = get_song_id(title_result)
                if song_id is None:
                    #print("⚠ 曲ID未検出 スキップ")
                    winsound.PlaySound(FAIL_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    ranking = get_ranking(song_id, key_final, mode_final, difficulty_result)
                    rank = 1
                    for r in ranking:
                        if int(score_result) < r[0]:
                            rank += 1

                    #print("✔ 安定スキャン成功")
                    #print("今回順位:", rank)
                    #print("========== RESULT ==========")
                    #print("TITLE      :", title_result)
                    #print("KEY        :", key_final)
                    #print("MODE       :", mode_final)
                    #print("DIFFICULTY :", difficulty_result)
                    #print("SCORE      :", score_result)
                    #print("RATE       :", rate_result)
                    #print("MAX COMBO  :", combo_result)

                    save_score(song_id, key_final, mode_final, difficulty_result,
                               score_result, rate_result, combo_result)
                    #print("▶ DB保存完了")
                    winsound.PlaySound(SUCCESS_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    success = True
            else:
                #print("⚠ 読み取り安定せず")
                winsound.PlaySound(FAIL_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)

            time.sleep(1)

        time.sleep(0.05)