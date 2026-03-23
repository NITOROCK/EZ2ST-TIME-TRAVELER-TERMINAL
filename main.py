import time
import threading
import mss
from core import scan        # RESULT OCR
from ui import overlay
from score import db
import keyboard

hold_time_required = 3  # HOME長押し秒数

# ===== キーボード監視ループ =====
def keyboard_loop():
    with mss.mss() as sct:
        while True:
            # HOME長押し → RESULTスキャン
            if keyboard.is_pressed("home"):
                start_time = time.time()
                triggered = False
                while keyboard.is_pressed("home"):
                    time.sleep(0.05)
                    if not triggered and time.time() - start_time >= hold_time_required:
                        triggered = True
                        overlay.show_scanning("RESULT")
                        #print("RESULTスキャン開始")

                        result = scan.start_scan()
                        if result["success"]:
                            #print("OCR成功:", result)

                            # ランクイン演出
                            ranking = db.get_ranking(result["song_id"], result["key"], result["mode"], result["difficulty"])
                            rank = 1
                            for r in ranking:
                                if int(result["score"]) < r[0]:
                                    rank += 1

                            overlay.show_rank_in(rank, "PLAYER", result["score"])
                            
                            # ネーム入力は overlay 内で処理
                            # 入力が確定されたら phase 2 (SCORE SAVED) に自動移行
                            # DB登録も overlay から呼び出せる
                            
                        else:
                            overlay.show_scan_failed()

                        while keyboard.is_pressed("home"):
                            time.sleep(0.05)
                        break

            # END押し → 選曲スキャン（簡易）
            elif keyboard.is_pressed("end"):
                overlay.show_scanning("SELECT")
                #print("SELECTスキャン開始")
                # scan_select を呼ぶならここで
                while keyboard.is_pressed("end"):
                    time.sleep(0.05)

            time.sleep(0.05)

# ===== メイン =====
def main():
    #print("EZ2ST 統合待機中…")
    #print("HOME長押し → RESULT取得")
    #print("END長押し → 選曲取得")

    # ⭐ キーボード監視は別スレッド
    threading.Thread(target=keyboard_loop, daemon=True).start()

    # ⭐ Tkinter はメインスレッドで起動
    overlay.start_overlay()

if __name__ == "__main__":
    main()