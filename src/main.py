import os
import random
import datetime
from pathlib import Path

import requests
from openai import OpenAI


# =========================
# Paths
# =========================

BASE_DIR = Path(__file__).resolve().parent          # src/
ROOT_DIR = BASE_DIR.parent                          # repo root

TEXT_DIR = BASE_DIR / "texts"
LOG_DIR = BASE_DIR / "log"
VOICE_DIR = ROOT_DIR / "public" / "voices"         # public/voices/

LOG_DIR.mkdir(exist_ok=True)
VOICE_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# Files
# =========================

THEMES_FILE = TEXT_DIR / "themes.txt"
ARCHIVE_THEMES_FILE = LOG_DIR / "archive_themes.txt"

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
# API (safe: secrets via env)
# =========================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash:generateContent"
)


# =========================
# Helpers
# =========================

def pick_theme_and_archive() -> str:
    lines = THEMES_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    theme = random.choice(lines)
    lines.remove(theme)

    THEMES_FILE.write_text("".join(lines), encoding="utf-8")
    ARCHIVE_THEMES_FILE.open("a", encoding="utf-8").write(theme)

    return theme.strip()


def get_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    response = requests.post(
        GEMINI_ENDPOINT,
        params={"key": GEMINI_API_KEY},
        json=payload,
        timeout=180,
    )
    response.raise_for_status()

    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def generate_voice(text: str, out_path: Path, voice: str) -> None:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=OPENAI_API_KEY)

    with client.audio.speech.with_streaming_response.create(
        model="tts-1-hd",
        voice=voice,
        input=text,
    ) as response:
        response.stream_to_file(out_path)


# =========================
# Main
# =========================

def main() -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M_%S")

    # Theme & character
    theme = pick_theme_and_archive()
    character = random.choice(list(CHARACTER_FILES.keys()))

    base_text = get_text(CHARACTER_FILES[character])
    prompt = base_text + theme

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

    # =========================
    # LINE POST (future use)
    # =========================
    # post_line_message(...)
    # post_line_voice(...)


if __name__ == "__main__":
    main()

