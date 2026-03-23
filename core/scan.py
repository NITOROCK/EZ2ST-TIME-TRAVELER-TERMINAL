import time
import mss
import numpy as np
import cv2
from core import capture, ocr
from score import db, songs_db
from collections import Counter
from ui import overlay

def preprocess_key_img(img):
    """BASIC用に前処理する"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

def start_scan():
    """OCRスキャンして overlay に渡すだけのバージョン"""
    result = {
        "success": False,
        "title": None,
        "score": None,
        "rate": None,
        "combo": None,
        "rank": None,
        "key": None,
        "mode": None,
        "difficulty": None,
        "song_id": None
    }

    key_results = []
    mode_results = []

    title_result = ""
    score_result = ""
    rate_result = ""
    combo_result = ""
    difficulty_result = ""

    with mss.mss() as sct:
        for _ in range(5):
            screenshot = sct.grab(sct.monitors[1])
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2BGR)
            areas = capture.crop_areas(img)

            # OCR取得
            score = ocr.ocr_number(areas["score"])
            rate = ocr.ocr_number(areas["rate"])
            combo = ocr.ocr_number(areas["combo"])
            title = ocr.ocr_title_auto(areas["title"])
            mode_raw = ocr.ocr_title_auto(areas["mode"])
            difficulty = capture.detect_difficulty(areas)

            # モード判定
            if mode_raw != "UNKNOWN":
                mode_upper = mode_raw.upper()
                if "BASIC" in mode_upper or "C" in mode_upper or "B" in mode_upper or "I" in mode_upper:
                    mode = "BASIC"
                elif "STANDARD" in mode_upper:
                    mode = "STANDARD"
                else:
                    mode = "UNKNOWN"
            else:
                mode = "UNKNOWN"

            if mode != "UNKNOWN":
                mode_results.append(mode)

            key_standard = ocr.ocr_key(areas["key"])
            key_basic = ocr.ocr_key(preprocess_key_img(areas["key_basic"]))

            if mode == "STANDARD":
                key = key_standard
            elif mode == "BASIC":
                key = key_standard if key_standard != "UNKNOWN" else key_basic
            else:
                keys_to_consider = [key_standard, key_basic]
                key_counts = Counter(k for k in keys_to_consider if k != "UNKNOWN")
                key = key_counts.most_common(1)[0][0] if key_counts else "UNKNOWN"

            if key != "UNKNOWN":
                key_results.append(key)

            if title_result == "" and title != "":
                title_result = title.strip()
                score_result = score.strip()
                rate_result = rate.strip()
                combo_result = combo.strip()
                difficulty_result = difficulty

            time.sleep(0.15)

    # 最終決定（多数決）
    key_final = Counter(key_results).most_common(1)[0][0] if key_results else "UNKNOWN"
    mode_final = Counter(mode_results).most_common(1)[0][0] if mode_results else "UNKNOWN"

    if key_final != "UNKNOWN" and mode_final != "UNKNOWN" and title_result != "":
        song_id = songs_db.get_song_id(title_result)
        if song_id is None or score_result == "":
            return result

        # ⭐ overlay に OCRデータを渡す
        overlay.show_rank_in(
            rank_position=0,  # ランクイン演出用（仮）
            player_name="",
            score=0,
            ocr_data={
                "song_id": song_id,
                "key": key_final,
                "mode": mode_final,
                "difficulty": difficulty_result,
                "score": int(score_result),
                "rate": float(rate_result.replace("%", "")),
                "combo": int(combo_result)
            }
        )

        # ⭐ 保存後にランキング表示
        ranking = db.get_ranking(song_id, key_final, mode_final, difficulty_result)
        for i, r in enumerate(ranking[:5], start=1):
            score_val = r[0]
            player_name = r[2] if len(r) > 2 else "NONAME"
            overlay.show_rank_in(
                rank_position=i,
                player_name=player_name,
                score=score_val
            )

        # ランク計算
        rank = 1
        for r in ranking:
            if int(score_result) < r[0]:
                rank += 1

        result.update({
            "success": True,
            "title": title_result,
            "score": score_result,
            "rate": rate_result,
            "combo": combo_result,
            "rank": rank,
            "key": key_final,
            "mode": mode_final,
            "difficulty": difficulty_result,
            "song_id": song_id
        })

    return result