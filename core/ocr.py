import cv2
import numpy as np
import pytesseract

def ocr_text(area):
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, config="--psm 7").strip()

def ocr_number(area):
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray,150,255,cv2.THRESH_BINARY)[1]
    return pytesseract.image_to_string(
        thresh,
        config="--psm 7 -c tessedit_char_whitelist=0123456789.%"
    ).strip()

def ocr_title_auto(area):
    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    if mean_brightness > 180:
        gray = cv2.equalizeHist(gray)
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return pytesseract.image_to_string(thresh, config="--psm 7").strip()
    else:
        return pytesseract.image_to_string(gray, config="--psm 7").strip()
    
    
    #tuika 
def ocr_key(area):
    
    # 回転（今まで通り）
    rotated = cv2.rotate(area, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # HSV変換
    hsv = cv2.cvtColor(rotated, cv2.COLOR_BGR2HSV)

    # ⭐ 黄色フィルタ（ニトロの実測ベース）
    lower = np.array([20, 200, 200])
    upper = np.array([35, 255, 255])

    mask = cv2.inRange(hsv, lower, upper)

    # ⭐ ノイズ除去（ここ重要）
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # ⭐ ぼかし → 二値化
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    _, mask = cv2.threshold(mask, 180, 255, cv2.THRESH_BINARY)

    # ⭐ OCR
    text = pytesseract.image_to_string(
        mask,
        config="--psm 10 -c tessedit_char_whitelist=4568"
    ).strip()

    # ⭐ デバッグ用（必要なら表示）
    # cv2.imshow("key_mask", mask)
    # cv2.waitKey(1)

    if text in ["4", "5", "6", "8"]:
        return text + "K"

    return "UNKNOWN"

def ocr_vertical(area):

    gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
    gray = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)

    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    text = pytesseract.image_to_string(
        thresh,
        config="--psm 6"
    ).strip()

    return text

# 2026-03-20 OCR安定版
# 現在はHSV固定値フィルタでKEY認識は安定動作
# 
# ▼将来案（必要になったら実装）
# ・KEY横の「K」座標から色サンプル取得
# ・HSV動的生成 → フィルタ適用
# ・必要なら複数点平均
#
# ※現段階では過剰実装になるため保留

#▼座標から色サンプルを取得する際のサンプルコード▼

#    USE_DYNAMIC_COLOR = False  # ← 今はOFF
#
#    if USE_DYNAMIC_COLOR:
#        # 座標からHSV取得
#        hsv_color = sample_color_from_position(img)
#    else:
#        # 固定値
#        hsv_color = (25, 255, 255)
    