import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# =========================
# 画像読み込み
# =========================

img = cv2.imread("result.png")


# =========================
# 参照エリア
# =========================

# SCORE
score_area = img[637:694 , 1441:1650]

# RATE
rate_area = img[616:650 , 1131:1259]

# MAX COMBO
combo_area = img[652:688 , 1132:1260]

# TITLE
title_area = img[179:221 , 843:1503]

# KEY
key_area = img[139:190, 52:128]

# MODE
mode_area = img[239:462 , 83:126]

# DIFFICULTY
difficulty_area = img[181:219 , 1502:1745]


# =========================
# OCR関数
# =========================

def ocr_text(area):

    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(
        gray,
        config="--psm 7"
    )

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

    # 90度回転
    rotated = cv2.rotate(area, cv2.ROTATE_90_CLOCKWISE)

    gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)

    thresh = cv2.threshold(gray,130,255,cv2.THRESH_BINARY)[1]

    text = pytesseract.image_to_string(
        thresh,
        config="--psm 7"
    )

    return text.strip()

def ocr_key(area):

    # KEYも縦表示なので回転
    rotated = cv2.rotate(area, cv2.ROTATE_90_COUNTERCLOCKWISE)

    hsv = cv2.cvtColor(rotated, cv2.COLOR_BGR2HSV)

    lower = (20, 120, 120)
    upper = (40, 255, 255)

    mask = cv2.inRange(hsv, lower, upper)

    mask = cv2.medianBlur(mask, 3)

    text = pytesseract.image_to_string(
        mask,
        config="--psm 10 -c tessedit_char_whitelist=4568"
    )

    text = text.strip()

    if text in ["4","5","6","8"]:
        return text + "K"

    return "UNKNOWN"

def ocr_difficulty(area):

    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)

    # 明るい部分だけ抽出
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    text = pytesseract.image_to_string(
        thresh,
        config="--psm 7 -c tessedit_char_whitelist=0123456789"
    )

    return text.strip()

def fix_mode(text):

    text = text.upper()

    if "STAND" in text or len(text) >= 7:
        return "STANDARD"

    if "BAS" in text:
        return "BASIC"

    return "UNKNOWN"

# =========================
# OCR実行
# =========================

score = ocr_number(score_area)
rate = ocr_number(rate_area)
combo = ocr_number(combo_area)

title = ocr_text(title_area)
key = ocr_key(key_area)
mode_raw = ocr_vertical(mode_area)
mode = fix_mode(mode_raw)
difficulty = ocr_difficulty(difficulty_area)


# =========================
# 結果表示
# =========================

#print("========== RESULT ==========")
#print("TITLE      :", title)
#print("KEY        :", key)
#print("MODE       :", mode)
#print("DIFFICULTY :", difficulty)
#print("SCORE      :", score)
#print("RATE       :", rate)
#print("MAX COMBO  :", combo)


# =========================
# 参照エリア確認表示
# =========================

#cv2.imshow("TITLE", title_area)
#cv2.imshow("KEY", key_area)
#cv2.imshow("MODE", mode_area)
#cv2.imshow("DIFFICULTY", difficulty_area)

#cv2.imshow("SCORE", score_area)
#cv2.imshow("RATE", rate_area)
#cv2.imshow("MAX COMBO", combo_area)

#cv2.waitKey(0)
#cv2.destroyAllWindows()