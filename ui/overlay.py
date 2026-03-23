import tkinter as tk
import ctypes
from pathlib import Path
import datetime
import random
import keyboard
from score import db
from config import settings
from ui import sound

# ===== 状態＆変数 =====
phase = 0
timer = 0
dot_count = 0
scan_type = "RESULT"
scan_result = True

level = 180
direction = -1
noise_timer = 0
scroll_x = 0
scroll_wait = 0
scroll_interval = 3  # 大きいほど遅くなる

texts = [
    "EZ2ST STANDBY",
    "HOME KEY : RESULT SCAN",
    "END KEY : SELECT SCAN",
    "FREE PLAY"
]

root = None
label = None

scan_sound = False
rank_in_sound = False
cancel_sound = False
decide_sound = False

# 名前入力用
name_chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!?-+: ")
name_index = 0
entry_name = ""
max_name_len = 6

cursor_visible = True
cursor_timer = 0
cursor_interval = 500  # msで点滅

key_hold_time = {"up": 0, "down": 0}
key_repeat_delay = 10   # 長押し開始まで
key_repeat_interval = 2 # リピート速度

# prev_keys
prev_keys = {"up": False, "down": False, "left": False, "right": False}

# フォント追加
ctypes.windll.gdi32.AddFontResourceExW(str(settings.FONT_PATH), 0x10, 0)

# OCR結果保持
ocr_result = None  # OCRスキャン結果を保持

# 下段ランクイン演出用
ranking_flash_count = 0
ranking_flash_max = 12
ranking_text = ""

# ===== 下段ランクイン演出 =====
def show_rank_in(rank_position, player_name, score, ocr_data=None):
    global ranking_flash_count, ranking_flash_max, ranking_text, phase, ocr_result
    ranking_text = f"#{rank_position} RANK IN!"
    ranking_flash_count = 0
    ranking_flash_max = 12
    phase = 3
    if ocr_data:
        ocr_result = ocr_data
    global rank_in_sound
    rank_in_sound = False

# ===== 外部操作API =====
def show_scanning(mode):
    global phase, timer, dot_count, scan_type, scan_sound
    phase = 1
    timer = 180
    dot_count = 0
    scan_type = mode
    scan_sound = False

def show_result_saved():
    global phase, timer, scan_result
    phase = 2
    timer = 120
    scan_result = True

def show_scan_failed():
    global phase, timer, scan_result
    phase = 2
    timer = 120
    scan_result = False

# ===== 名前入力操作 =====
def name_input_up():
    global name_index
    name_index = (name_index + 1) % len(name_chars)

def name_input_down():
    global name_index
    name_index = (name_index - 1) % len(name_chars)

def name_input_enter():
    global entry_name
    if len(entry_name) < max_name_len:
        entry_name += name_chars[name_index]

def name_input_back():
    global entry_name
    if entry_name:
        entry_name = entry_name[:-1]

# ===== 名前入力開始 =====
def start_name_input():
    global phase, name_index, entry_name
    phase = 4
    name_index = 0
    entry_name = ""

def on_enter_pressed(event):
    global entry_name, ocr_result, decide_sound, phase

    if phase != 4:
        return

    if not entry_name:
        return

    if not ocr_result:
        return

    db.register_score(
        song_id=ocr_result['song_id'],
        key=ocr_result['key'],
        mode=ocr_result['mode'],
        difficulty=ocr_result['difficulty'],
        score=ocr_result['score'],
        rate=ocr_result['rate'],
        combo=ocr_result['combo'],
        entry_name=entry_name
    )

    if not decide_sound:
        sound.play_beep_sequence(root, count=3)
        decide_sound = True

    phase = 2

def on_esc_pressed(event):
    global phase, entry_name, cancel_sound

    if phase != 4:
        return

    phase = 0
    entry_name = ""

    if not cancel_sound:
        sound.cancel(root)
        cancel_sound = True
        
def stop_name_input():
    keyboard.unhook_key("enter")
    keyboard.unhook_key("esc")

keyboard.on_press_key("enter", on_enter_pressed)
keyboard.on_press_key("esc", on_esc_pressed)
    
def on_name_confirm(event):
    global phase, entry_name, ocr_result
    if entry_name and ocr_result:
        # OCRデータと名前をまとめてDB登録
        #print("DEBUG REGISTER SCORE:", ocr_result, entry_name)
        db.register_score(
            song_id=ocr_result.get('song_id'),
            key=ocr_result['key'],
            mode=ocr_result['mode'],
            difficulty=ocr_result['difficulty'],
            score=ocr_result['score'],
            rate=ocr_result['rate'],
            combo=ocr_result['combo'],
            entry_name=entry_name
        )

        # 保存後ランキング表示
        ranking = db.get_ranking(
            ocr_result['song_id'],
            ocr_result['key'],
            ocr_result['mode'],
            ocr_result['difficulty']
        )
        for i, r in enumerate(ranking[:5], start=1):
            score_val = r[0]
            player_name = r[2] if len(r) > 2 else "NONAME"
            show_rank_in(rank_position=i, player_name=player_name, score=score_val)

    #print(f"NAME CONFIRMED: {entry_name}")
    phase = 2  # 保存表示フェーズへ

def on_name_cancel(event):
    global phase, entry_name
    phase = 0
    entry_name = ""

# ===== 内部UI =====
def start_overlay():
    global root, label
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#220000")

    w, h = 340, 36
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{sw-w-790}+{sh-h}")

    label = tk.Label(
        root,
        text="",
        fg="#ff3b3b",
        bg="#220000",
        font=("TRS Million", 18)
    )
    label.pack(expand=True)

    update_clock()
    fade_loop()
    root.mainloop()

def update_clock():
    now = datetime.datetime.now()
    texts[3] = now.strftime("%H : %M : %S")
    root.after(1000, update_clock)

def build_scroll_text():
    return (
        "          EZ2ST STANDBY          "
        "HOME KEY : RESULT SCAN          "
        "END KEY : SELECT SCAN           "
        f"{texts[3]}"
    )

# ===== フェード＆スクロールループ =====
def fade_loop():

    global phase, level, direction, timer, dot_count, scan_result
    global noise_timer, scroll_wait, scroll_x
    global ranking_flash_count, ranking_flash_max, ranking_text
    global name_index, entry_name, prev_keys
    global cursor_visible, cursor_timer
    global ocr_result
    global key_hold_time, key_repeat_delay, key_repeat_interval
    global scan_sound, rank_in_sound, decide_sound, cancel_sound, decide_sound

    display_width = 30
    current_text = build_scroll_text()
    scroll_buffer = current_text + "   " + current_text
    buffer_len = len(current_text) + 3

    # 通常スクロール
    if phase == 0:
        level += direction * 2 
        if level <= 100:
            level = 100
            direction = 1
        elif level >= 180:
            level = 180
            direction = -1
            noise_timer = 2

        if noise_timer > 0:
            level += random.randint(-4, 2)
            noise_timer -= 1

        scroll_wait += 1
        if scroll_wait >= scroll_interval:
            scroll_wait = 0
            scroll_x = (scroll_x + 1) % buffer_len

        display = scroll_buffer[scroll_x:scroll_x+display_width]
        color = f"#{max(22, min(180, level)):02x}0000"
        label.config(text=display, fg=color)

    # スキャン演出
    elif phase == 1:
        
        if not scan_sound:
            sound.scan_start(root)
            scan_sound = True
        
        dot_count = (dot_count + 1) % 4
        label.config(text=f"NOW SCANNING{'.'*dot_count}", fg="#ff3b3b")
        timer -= 1
        if timer <= 0:
            phase = 0

    # 保存表示
    elif phase == 2:
        label.config(text="RECORD SAVED" if scan_result else "SCAN FAILED", fg="#ff3b3b")
        timer -= 1
        if timer <= 0:
            phase = 0

    # ランクインフラッシュ
    elif phase == 3:

        if not rank_in_sound:
            sound.play_double_sequence(root)
            rank_in_sound = True

        if ranking_flash_count < ranking_flash_max:
            label.config(text=ranking_text if ranking_flash_count % 2 == 0 else "", fg="#ff3b3b")
            ranking_flash_count += 1
        else:
            start_name_input()

    # ===== ネーム入力フェーズ =====
    if phase == 4:
        decide_sound = False
        cancel_sound = False        
        cursor_timer += 70
        
        if cursor_timer >= cursor_interval:
            cursor_timer = 0
            cursor_visible = not cursor_visible
            
        cursor_char = "_" if cursor_visible else " "
        display = entry_name
        
        if len(entry_name) < max_name_len:
            display += name_chars[name_index] + cursor_char
        else:
            display += cursor_char
        label.config(text=display, fg="#ff3b3b")

        # ===== 入力処理（改良版） =====

        # --- UP / DOWN（キーリピートあり） ---
        for key in ["up", "down"]:
            pressed = keyboard.is_pressed(key)

            if pressed:
                key_hold_time[key] += 1

                # 押した瞬間
                if key_hold_time[key] == 1 and not prev_keys[key]:
                    
                    if key == "up":
                        name_input_up()
                        sound.move()
                        
                    elif key == "down":
                        name_input_down()
                        sound.move()

                # 長押しリピート
                elif key_hold_time[key] > key_repeat_delay:
                    if key_hold_time[key] % key_repeat_interval == 0:
                        if key == "up":
                            name_input_up()
                        elif key == "down":
                            name_input_down()

            else:
                key_hold_time[key] = 0


        # --- LEFT / RIGHT（1回だけ） ---
        for key in ["left", "right"]:
            pressed = keyboard.is_pressed(key)

            if pressed and not prev_keys[key]:
                if key == "left":
                    name_input_back()
                    sound.move()
                    
                elif key == "right":
                    name_input_enter()
                    sound.decide()

            prev_keys[key] = pressed


        # --- ENTER / ESC（そのまま） ---
            pressed = keyboard.is_pressed(key)

            if pressed and not prev_keys[key]:
                if key == "enter":
                    if not entry_name:
                        return
                    
                    if not ocr_result:
                        return
                    
                    db.register_score(
                        song_id=ocr_result['song_id'],
                        key=ocr_result['key'],
                        mode=ocr_result['mode'],
                        difficulty=ocr_result['difficulty'],
                        score=ocr_result['score'],
                        rate=ocr_result['rate'],
                        combo=ocr_result['combo'],
                        entry_name=entry_name
                    )
                            
                    if not decide_sound:
                        sound.play_beep_sequence(root, count=3)
                        decide_sound = True
                        phase = 2
                        stop_name_input()

                elif key == "esc":
                    phase = 0
                    entry_name = ""
                    
                    if not cancel_sound:
                        sound.cancel(root)
                        cancel_sound = True
                        stop_name_input()

            prev_keys[key] = pressed

    root.after(70, fade_loop)
    
#個人的なメモ
#★キー入力を受付けない場合は処理の最初で変数を初期化！！
#例）decide_sound = False ⇒変数内のTrueをFalseに初期化してループ処理を止めない

#ENTER,ESCだけkeyboard監視をネームエントリー時のみ使って監視