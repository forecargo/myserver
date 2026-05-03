# myserver プロジェクト

## 構成概要

- `ocr-api/` — FastAPI による OCR バックエンド (Python)
- `ScheduleScanner/` — iOS クライアントアプリ (Xcode)
- `guidline-api/` — 金融庁ガイドライン セマンティック検索 API (Python/FastAPI)
- `GuidlineSearch/` — iOS ガイドライン検索アプリ (Xcode/SwiftUI)
- `docker-compose.yml` — OCR API + Caddy をまとめて起動

## ドキュメント参照

- ocr-api の詳細構造 → [ocr-api.md](./ocr-api.md)
- iOS クライアントの詳細構造 → [Scanner.md](./Scanner.md)
- ガイドライン検索システムの実装計画 → [guideline-search-plan.md](./guideline-search-plan.md)
- ガイドライン検索 API 仕様書 → [guidline-api/guideline-api.md](./guidline-api/guideline-api.md)
- ガイドライン検索 iOS アプリ仕様書 → [GuidlineSearch/GuidlineSearch.md](./GuidlineSearch/GuidlineSearch.md)
