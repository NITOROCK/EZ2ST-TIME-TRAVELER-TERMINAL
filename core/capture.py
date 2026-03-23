# capture.py (BASIC用座標追加サンプル)
import mss
import numpy as np
import cv2

def crop_areas(img):
    areas = {}
    areas["score"] = img[637:694 , 1441:1650]
    areas["rate"]  = img[616:650 , 1131:1259]
    areas["combo"] = img[652:688 , 1132:1260]
    areas["title"] = img[179:221 , 843:1503]
    
    # ⭐ STANDARDキー座標
    areas["key"] = img[137:192, 50:130]
    
    # ⭐ BASICキー座標（少し余裕を持たせた座標）
    areas["key_basic"] = img[140:200, 52:132]  # 左上:52,140 右下:132,197 + 余裕
    
    # MODEの座標
    # ⭐ MODEの座標をマウス欄に変更
    areas["mode"]  = img[51:77 , 513:604]
    
    # 難易度の座標
    areas["EZ"]    = img[181:219, 1502:1550]
    areas["NM"]    = img[181:219, 1570:1610]
    areas["HD"]    = img[181:219, 1630:1675]
    areas["SHD"]   = img[181:219, 1695:1735]
    return areas

def capture_screen(monitor=1):
    with mss.mss() as sct:
        screenshot = sct.grab(sct.monitors[monitor])
        img = np.array(screenshot)
        return img[..., :3]  # BGRA -> BGR
    
def detect_difficulty(areas):
    diff_areas = {
        "EZ": areas["EZ"],
        "NM": areas["NM"],
        "HD": areas["HD"],
        "SHD": areas["SHD"]
    }

    for name, area in diff_areas.items():
        gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        bright = cv2.countNonZero(thresh)
        if bright > 40:
            return name

    return "UNKNOWN"