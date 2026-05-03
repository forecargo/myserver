# myserver プロジェクト

## 構成概要

- `ocr-api/` — FastAPI による OCR バックエンド (Python)
- `ScheduleScanner/` — iOS クライアントアプリ (Xcode)
- `guidline-api/` — 金融庁ガイドライン セマンティック検索 API (Python/FastAPI)
- `GuidlineSearch/` — iOS ガイドライン検索アプリ (Xcode/SwiftUI)
- `trouble-api/` — NCBオンライン障害通知メール収集・管理 API (Python/FastAPI)
- `docker-compose.yml` — 全サービス + Caddy + PostgreSQL をまとめて起動

## ドキュメント参照

- ocr-api の詳細構造 → [ocr-api.md](./ocr-api.md)
- iOS クライアントの詳細構造 → [Scanner.md](./Scanner.md)
- ガイドライン検索システムの実装計画 → [guideline-search-plan.md](./guideline-search-plan.md)
- ガイドライン検索 API 仕様書 → [guidline-api/guideline-api.md](./guidline-api/guideline-api.md)
- ガイドライン検索 iOS アプリ仕様書 → [GuidlineSearch/GuidlineSearch.md](./GuidlineSearch/GuidlineSearch.md)
- trouble-api の詳細構造・開発ポイント → [trouble-api.md](./trouble-api.md)
