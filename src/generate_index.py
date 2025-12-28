from pathlib import Path
from datetime import datetime

# =========================
# Paths
# =========================
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
VOICES_DIR = PUBLIC_DIR / "voices"
INDEX_FILE = PUBLIC_DIR / "index.html"

# =========================
# HTMLテンプレート
# =========================
HTML_HEAD = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>Voices Archive</title>
<style>
body { font-family: sans-serif; padding: 2rem; }
h2 { margin-top: 2rem; }
audio { display: block; margin: 0.5rem 0 1rem; }
</style>
</head>
<body>
<h1>Voices Archive</h1>
"""

HTML_TAIL = """
</body>
</html>
"""

# =========================
# ファイル整理
# =========================
def collect_files():
    """
    voices ディレクトリをスキャンし、年月ごとに分類
    例: 202512_01.mp3 → 2025-12
    """
    files = sorted(VOICES_DIR.glob("*.mp3"))
    grouped = {}
    for f in files:
        # ファイ名先頭から年月を抽出
        stem = f.stem  # 20251228_152843_タイトル
        year_month = stem[:6]  # YYYYMM
        grouped.setdefault(year_month, []).append(f.name)
    return grouped

# =========================
# HTML生成
# =========================
def generate_html(grouped_files):
    lines = [HTML_HEAD]
    for ym, files in sorted(grouped_files.items(), reverse=True):
        dt = datetime.strptime(ym, "%Y%m")
        lines.append(f"<h2>{dt.year}年{dt.month}月</h2>\n<ul>")
        for fn in files:
            lines.append(f"<li>{fn}<br><audio controls src='voices/{fn}'></audio></li>")
        lines.append("</ul>\n")
    lines.append(HTML_TAIL)
    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {INDEX_FILE} with {len(grouped_files)} months")

# =========================
# Main
# =========================
def main():
    grouped = collect_files()
    generate_html(grouped)

if __name__ == "__main__":
    main()

