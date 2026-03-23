import time
import mss
import numpy as np
import cv2
import pytesseract
from PIL import Image
import keyboard

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================
# 座標設定
# =========================

areas_key = {
    "4": {"top":116,"left":69,"width":33,"height":26},
    "5": {"top":118,"left":114,"width":33,"height":24},
    "6": {"top":118,"left":160,"width":33,"height":24},
    "8": {"top":119,"left":207,"width":32,"height":23},
}

basic_area = {"top":53,"left":532,"width":51,"height":19}
std_area   = {"top":51,"left":513,"width":90,"height":24}

capture_areas = {
    "TITLE": {"top": 532, "left": 833, "width": 646, "height": 37},
    "EZ": {"top": 536, "left": 1497, "width": 39, "height": 32},
    "NM": {"top": 538, "left": 1562, "width": 37, "height": 30},
    "HD": {"top": 535, "left": 1622, "width": 39, "height": 34},
    "SHD": {"top": 536, "left": 1682, "width": 47, "height": 32},
}

difficulty_order = ["EZ","NM","HD","SHD"]

# =========================
# KEY判定（白量最小）
# =========================
def detect_key(sct):
    scores = {}
    for k, area in areas_key.items():
        img = np.array(sct.grab(area))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        white = np.sum(gray > 220)
        scores[k] = white

    key = min(scores, key=scores.get)
    return key

# =========================
# MODE判定（二点OCR）
# =========================
def detect_mode(sct):

    def read(area):
        img = np.array(sct.grab(area))
        img = cv2.resize(img, None, fx=4, fy=4)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

        txt = pytesseract.image_to_string(th, config="--psm 7")
        return txt.upper()

    tb = read(basic_area)
    ts = read(std_area)

    score_b = sum(tb.count(c) for c in "BASIC")
    score_s = sum(ts.count(c) for c in "STANDR")

    if score_s > score_b:
        return "STANDARD"
    else:
        return "BASIC"

# =========================
# 難易度判定（白量最大）
# =========================
def detect_difficulty(sct):
    scores = {}
    for diff in difficulty_order:
        img = np.array(sct.grab(capture_areas[diff]))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        scores[diff] = np.sum(th) / 255

    return max(scores, key=scores.get)

# =========================
# 曲名OCR
# =========================
def detect_title(sct):
    img = sct.grab(capture_areas["TITLE"])
    img_pil = Image.frombytes("RGB", img.size, img.rgb)
    txt = pytesseract.image_to_string(img_pil, config="--psm 7 -l jpn+eng")
    return txt.strip()

# =========================
# 統合スキャン
# =========================
def scan_select(sct):

    key = detect_key(sct)
    mode = detect_mode(sct)
    diff = detect_difficulty(sct)
    title = detect_title(sct)

    return {
        "song": title,
        "difficulty": diff,
        "key": key,
        "mode": mode
    }

# =========================
# テストループ
# =========================
if __name__ == "__main__":
    with mss.mss() as sct:
        #print("ALTで選曲解析")

        while True:
            if keyboard.is_pressed("end"):
                time.sleep(0.25)

                result = scan_select(sct)

                #print(result)
            

                time.sleep(0.7)
            else:
                time.sleep(0.1)