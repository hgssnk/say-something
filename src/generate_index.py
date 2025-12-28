from pathlib import Path
from datetime import datetime

# ==========================================
# Configuration & Paths
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
VOICES_DIR = PUBLIC_DIR / "voices"

# ==========================================
# HTML Templates
# ==========================================
def render_page(title: str, content: str, show_back: bool = True) -> str:
    """共通のHTMLテンプレートを適用する"""
    back_link = '<p><a href="index.html">← 戻る</a></p>' if show_back else ""
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                padding: 2rem; line-height: 1.6; max-width: 800px; margin: 0 auto; background: #f9f9f9; color: #333; }}
        h1 {{ border-bottom: 3px solid #007bff; padding-bottom: 0.5rem; }}
        .card {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 1.2rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
        .filename {{ font-weight: bold; font-size: 0.9rem; color: #555; display: block; margin-bottom: 0.5rem; }}
        audio {{ width: 100%; }}
        .menu-item {{ display: flex; justify-content: space-between; align-items: center; 
                      padding: 1.2rem; background: white; margin: 0.8rem 0; text-decoration: none; 
                      color: #333; border-radius: 8px; border: 1px solid #ddd; transition: transform 0.1s; }}
        .menu-item:hover {{ transform: translateX(5px); border-color: #007bff; }}
        .count {{ background: #007bff; color: white; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.8rem; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {content}
    {back_link}
</body>
</html>
"""

# ==========================================
# Logic Functions
# ==========================================
def collect_voices() -> list[Path]:
    """voicesディレクトリ内のmp3ファイルを降順で取得"""
    return sorted(VOICES_DIR.glob("*.mp3"), reverse=True)

def group_by_month(files: list[Path]) -> dict[str, list[Path]]:
    """ファイルを年月(YYYYMM)ごとに辞書へ分類"""
    grouped = {}
    for f in files:
        ym = f.stem[:6]  # 先頭6文字を年月とする
        grouped.setdefault(ym, []).append(f)
    return grouped

def save_month_page(ym: str, files: list[Path]) -> str:
    """月別の個別ページを生成・保存し、目次用のリンクを返す"""
    dt = datetime.strptime(ym, "%Y%m")
    title = f"{dt.year}年{dt.month}月"
    file_name = f"{ym}.html"
    
    # リスト生成
    items = []
    for f in files:
        items.append(f"""
        <div class="card">
            <span class="filename">{f.name}</span>
            <audio controls src="voices/{f.name}" preload="none"></audio>
        </div>""")
    
    html_content = render_page(title, "\n".join(items))
    (PUBLIC_DIR / file_name).write_text(html_content, encoding="utf-8")
    
    return f'<a href="{file_name}" class="menu-item"><span>{title}</span> <span class="count">{len(files)}件</span></a>'

def save_index_page(links: list[str]):
    """メインの目次ページを生成・保存"""
    content = "\n".join(links)
    html_content = render_page("Voices Archive", content, show_back=False)
    (PUBLIC_DIR / "index.html").write_text(html_content, encoding="utf-8")

# ==========================================
# Main Orchestration
# ==========================================
def main():
    # 1. データの収集と整理
    voice_files = collect_voices()
    grouped_data = group_by_month(voice_files)
    
    # 2. 各月ページの生成
    index_links = []
    for ym, files in grouped_data.items():
        link_html = save_month_page(ym, files)
        index_links.append(link_html)
    
    # 3. 目次ペーの生成
    save_index_page(index_links)
    
    print(f"Success: Processed {len(voice_files)} files across {len(grouped_data)} months.")

if __name__ == "__main__":
    main()
