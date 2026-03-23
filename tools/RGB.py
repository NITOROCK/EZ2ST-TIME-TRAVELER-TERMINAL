import cv2
import numpy as np

image_path = "sample.png"
selected_color = None
click_pos = None  # ← 座標保持
tolerance_h = 10
tolerance_sv = 60

def get_color(event, x, y, flags, param):
    global selected_color, click_pos
    if event == cv2.EVENT_LBUTTONDOWN:
        b, g, r = img[y, x]
        selected_color = cv2.cvtColor(
            np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV
        )[0][0]
        click_pos = (x, y)

        print(f"クリック位置 ({x}, {y})")
        print(f"選択色 HSV: H={selected_color[0]}, S={selected_color[1]}, V={selected_color[2]}")

img = cv2.imread(image_path)
cv2.namedWindow("Image")
cv2.setMouseCallback("Image", get_color)

while True:
    display = img.copy()

    if selected_color is not None:
        # HSVフィルタ範囲
        lower = np.array([
            max(int(selected_color[0]) - tolerance_h, 0),
            max(int(selected_color[1]) - tolerance_sv, 0),
            max(int(selected_color[2]) - tolerance_sv, 0)
        ])
        upper = np.array([
            min(int(selected_color[0]) + tolerance_h, 179),
            min(int(selected_color[1]) + tolerance_sv, 255),
            min(int(selected_color[2]) + tolerance_sv, 255)
        ])

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)

        mask = cv2.GaussianBlur(mask, (3, 3), 0)
        _, mask = cv2.threshold(mask, 180, 255, cv2.THRESH_BINARY)

        display = cv2.bitwise_and(display, display, mask=mask)

    # ⭐ 座標を画面に描画
    if click_pos is not None:
        x, y = click_pos

        # 赤い丸
        cv2.circle(display, (x, y), 5, (0, 0, 255), -1)

        # 座標テキスト
        cv2.putText(
            display,
            f"({x}, {y})",
            (x + 10, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1
        )

    cv2.imshow("Image", display)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()