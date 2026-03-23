import pygame
from pathlib import Path

# 初期化（1回だけ）
pygame.mixer.init()

# パス
BASE_DIR = Path(__file__).resolve().parent.parent
SOUND_DIR = BASE_DIR / "assets" / "sounds"

# 音読み込み
beep = pygame.mixer.Sound(str(SOUND_DIR / "beep.mp3"))
click = pygame.mixer.Sound(str(SOUND_DIR / "click.mp3"))

# ===== 基本音 =====

def play_beep():
    beep.play()

def play_click():
    click.play()

# ===== テスト用 =====

def test_beep():
    play_beep()

# ===== 操作音 =====

def move():
    play_click()  # UP/DOWN/LEFT

def decide():
    play_beep()   # RIGHT

def cancel(root):
    # ピッピッ
    play_beep()
    root.after(120)
    play_beep()

def play_beep_sequence(root, count=3, interval=80, on_complete=None):
    def _play(n):
        if n <= 0:
            if on_complete:
                on_complete()
            return
        play_beep()
        root.after(interval, lambda: _play(n - 1))

    _play(count)

def play_double_sequence(root):
    def second_loop():
        play_beep_sequence(root, count=3)

    play_beep_sequence(root, count=3, on_complete=lambda: root.after(200, second_loop))

def scan_start(root):
    # ピピッ
    play_beep()
    root.after(80)
    play_beep()

# ===== ランクイン（重要🔥） =====

def rank_in(root, flashes=6):
    def play_flash(count):
        if count <= 0:
            return

        play_beep()
        root.after(140, lambda: play_flash(count - 1))

    play_flash(flashes)