# ocr-api 詳細構造

## 概要

FastAPI + Google Gemini API を使って、スケジュール表の画像をアップロードするとJSON形式のスケジュールデータを返すバックエンドAPI。

## ディレクトリ構成

```
ocr-api/
├── main.py              # FastAPI アプリ本体
├── requirements.txt     # Python 依存パッケージ
├── Dockerfile           # コンテナビルド定義
├── .dockerignore
├── static/
│   └── index.html       # テスト用 Web UI
└── scedule.jpg          # サンプル画像
```

## エンドポイント

| メソッド | パス        | 説明                                      |
|--------|------------|------------------------------------------|
| GET    | `/`        | `/static/index.html` へリダイレクト        |
| GET    | `/health`  | ヘルスチェック (`{"status": "ok"}` を返す) |
| POST   | `/schedule`| 画像からスケジュールをJSON化して返す         |

### POST /schedule

- **リクエスト**: `multipart/form-data` で `file` フィールドに画像を添付
- **対応形式**: `image/jpeg` / `image/png` / `image/webp`
- **レスポンス**:
  ```json
  {
    "schedules": [
      {
        "date": "YYYY/MM/DD",
        "day_of_week": "月〜日のいずれか",
        "start_time": "HH:MM",
        "end_time": "HH:MM",
        "category": "会議 など",
        "title": "予定のタイトル",
        "location": "場所",
        "reserver": "予約者名"
      }
    ]
  }
  ```

## 処理フロー

1. 画像ファイルを受信し、MIME タイプを検証
2. 画像データを Base64 エンコードして Gemini API へ送信
3. Gemini のレスポンスから JSON コードブロックを正規表現で抽出
4. JSON をパースして `{"schedules": [...]}` 形式で返す

## 使用モデル

- `gemini-3.1-flash-lite-preview` (google-generativeai ライブラリ経由)

## 環境変数

| 変数名           | 必須 | 説明                  |
|----------------|------|----------------------|
| `GEMINI_API_KEY` | 必須 | Google Gemini API キー |

## 依存パッケージ (`requirements.txt`)

```
fastapi==0.115.0
uvicorn==0.30.0
python-multipart==0.0.9
google-generativeai==0.8.3
```

## Docker

- ベースイメージ: `python:3.11-slim`
- 起動コマンド: `uvicorn main:app --host 0.0.0.0 --port 8000`

## テスト UI (`static/index.html`)

ブラウザから直接 API をテストできる Web UI。

- 画像のドラッグ&ドロップまたはファイル選択に対応
- 「スケジュール変換」ボタンで `POST /schedule` を呼び出し
- 結果をテーブル形式で表示
