```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Actions as GitHub Actions (run.yml)
    participant Main as main.py
    participant Gemini as Gemini API
    participant OpenAI as OpenAI TTS API

    User->>Actions: 手動実行
    Actions->>Main: python main.py
    Main->>Main: テーマ選択・テキスト生成
    Main->>Gemini: ask_gemini(prompt)
    Gemini-->>Main: 文章生成
    Main->>OpenAI: generate_voice(text, voice)
    OpenAI-->>Main: 音声ファイル生成
    Main-->>Actions: ログ保存・音声保存
