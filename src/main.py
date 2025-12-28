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

