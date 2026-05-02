# myserver プロジェクト

## 構成概要

- `ocr-api/` — FastAPI による OCR バックエンド (Python)
- `ScheduleScanner.swiftpm/` — iOS クライアントアプリ (Swift Playgrounds)
- `docker-compose.yml` — OCR API + Caddy をまとめて起動

## ドキュメント参照

- iOS クライアントの詳細構造 → [Scanner.md](./Scanner.md)
