import cv2

def fix_mode(text):
    t = text.upper().replace(" ", "")
    if "BAS" in t: return "BASIC"
    if "ST" in t or len(t) >= 6: return "STANDARD"
    return "UNKNOWN"

def detect_difficulty(areas):
    diff_areas = {k: areas[k] for k in ["EZ","NM","HD","SHD"]}
    for name, area in diff_areas.items():
        gray = cv2.cvtColor(area, cv2.COLOR_BGR2GRAY)
        bright = cv2.countNonZero(cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)[1])
        if bright > 40: return name
    return "UNKNOWN"