from pathlib import Path

SUCCESS_SOUND = r"C:\Users\user\Desktop\頂ーITADAKIー\EZ2ST\success.wav"
FAIL_SOUND    = r"C:\Users\user\Desktop\頂ーITADAKIー\EZ2ST\fail.wav"

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

DB_SCORE_PATH = "ez2score.db"
DB_SONG_PATH  = "songs.db"

# settings.py
BASE_DIR = Path(__file__).resolve().parent.parent
FONT_PATH = BASE_DIR / "assets" / "fonts" / "trs-million rg.ttf"