import os
import random
import datetime
import time
from pathlib import Path
import requests
from openai import OpenAI

# =========================
# Paths
# =========================
BASE_DIR = Path(__file__).resolve().parent  # src/
TEXT_DIR = BASE_DIR / "texts"
PUBLIC_DIR = BASE_DIR.parent / "public"
VOICE_DIR = PUBLIC_DIR / "voices"
LOG_DIR = PUBLIC_DIR / "log"
ARCHIVE_THEMES_FILE = PUBLIC_DIR / "archive_themes.txt"

VOICE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# Files
# =========================
THEMES_FILE = TEXT_DIR / "themes.txt"

CHARACTER_FILES = {
    "moe": TEXT_DIR / "moe.txt",
    "saikawa": TEXT_DIR / "saikawa.txt",
    "shiki": TEXT_DIR / "shiki.txt",
}

VOICE_MAP = {
    "moe": "sage",
    "saikawa": "onyx",
    "shiki": "alloy",
}

# =========================
# API Keys
# =========================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)

# GEMINI_ENDPOINT = (
#     "https://generativelanguage.googleapis.com/v1beta/models/"
#     "gemini-1.5-flash:generateContent"
# )

# =========================
# Helpers
# =========================

def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # 簡易的なリトライ処理 (429対策)
    for i in range(3):
        r = requests.post(GEMINI_ENDPOINT, params={"key": GEMINI_API_KEY}, json=payload, timeout=60)
        if r.status_code == 429:
            time.sleep(2 ** (i + 1)) # 2, 4, 8秒と待機時間を増やす
            continue
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    
    raise RuntimeError("Gemini API Rate Limit exceeded after retries.")

# ... (pick_theme, get_text, generate_voice はそのまま) ...

# =========================
# Main
# =========================
def main() -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M_%S")
    theme = pick_theme()
    character = random.choice(list(CHARACTER_FILES.keys()))
    
    # プロンプトを工夫して1回で両方出させる
    character_prompt = get_text(CHARACTER_FILES[character])
    combined_prompt = f"""
{character_prompt}

テーマ: {theme}

上記を踏まえて回答してください。
また、最後に回答内容を詩的に表した10文字以内のタイトルを [TITLE:タイトル名] という形式で必ず書き添えてください。
"""

    # LLMリクエスト (1回だけ)
    raw_response = ask_gemini(combined_prompt)
    
    # 本文とタイトルを分離
    if "[TITLE:" in raw_response:
        answer_part, title_part = raw_response.split("[TITLE:", 1)
        answer = answer_part.strip().replace(" ", "").replace("\n", "")
        title = title_part.split("]")[0].strip().replace(" ", "").replace("\n", "")
    else:
        answer = raw_response.strip().replace(" ", "").replace("\n", "")
        title = "無題"

    print(f"Answer: {answer}")
    print(f"Title: {title}")

    # Log
    log_file = LOG_DIR / f"{timestamp}.log"
    log_file.write_text(f"Theme: {theme}\nTitle: {title}\nCharacter: {character}\n\n{answer}", encoding="utf-8")

    # Voice
    mp3_path = VOICE_DIR / f"{timestamp}.mp3"
    generate_voice(answer, mp3_path, VOICE_MAP[character])

    # Rename with Title
    final_path = VOICE_DIR / f"{timestamp}_{title}.mp3"
    mp3_path.rename(final_path)
    print(f"generated: {final_path}")

if __name__ == "__main__":
    main()



# =========================
# Helpers
# =========================
def pick_theme() -> str:
    # 現在のテーマを読み込み
    lines = THEMES_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    if not lines:
        raise RuntimeError("No themes left in themes.txt")

    theme_line = random.choice(lines)
    theme = theme_line.strip()

    # 1. themes.txt から削除して更新
    lines.remove(theme_line)
    THEMES_FILE.write_text("".join(lines), encoding="utf-8")

    # 2. archive_themes.txt に追記（ここを追加）
    with ARCHIVE_THEMES_FILE.open("a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {theme}\n")

    return theme

def get_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()

def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(GEMINI_ENDPOINT, params={"key": GEMINI_API_KEY}, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def generate_voice(text: str, out_path: Path, voice: str) -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=OPENAI_API_KEY)
    with client.audio.speech.with_streaming_response.create(
        model="tts-1-hd", voice=voice, input=text
    ) as response:
        response.stream_to_file(out_path)

# =========================
# Main
# =========================
def main() -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M_%S")
    theme = pick_theme()
    character = random.choice(list(CHARACTER_FILES.keys()))
    prompt = get_text(CHARACTER_FILES[character]) + theme

    # LLM
    answer = ask_gemini(prompt).replace(" ", "").replace("\n", "")
    print(answer)

    # Log
    log_file = LOG_DIR / f"{timestamp}.log"
    log_file.write_text(answer, encoding="utf-8")

    # Voice
    mp3_path = VOICE_DIR / f"{timestamp}.mp3"
    generate_voice(answer, mp3_path, VOICE_MAP[character])

    # Short poetic title
    title_prompt = "次の内容を一言で(10字以内)かつ詩的に表してください。" + answer
    title = ask_gemini(title_prompt).replace(" ", "").replace("\n", "")
    final_path = VOICE_DIR / f"{timestamp}_{title}.mp3"
    mp3_path.rename(final_path)
    print(f"generated: {final_path}")

    # LINEは将来対応
    # post_line_message(...)
    # post_line_voice(...)

if __name__ == "__main__":
    main()

