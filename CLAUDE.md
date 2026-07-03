# myserver プロジェクト

## 構成概要

- `ocr-api/` — FastAPI による OCR バックエンド (Python)
- `ScheduleScanner/` — iOS クライアントアプリ (Xcode)
- `guidline-api/` — 金融庁ガイドライン セマンティック検索 API (Python/FastAPI)
- `GuidlineSearch/` — iOS ガイドライン検索アプリ (Xcode/SwiftUI)
- `trouble-api/` — NCBオンライン障害通知メール収集・管理 API (Python/FastAPI)
- `transcribe-api/` — 音声文字起こし(mlx-whisper)+話者分離(pyannote.audio) API (Python/FastAPI, ホストnative実行)
- `docker-compose.yml` — 全サービス + Caddy + PostgreSQL をまとめて起動

## ドキュメント参照

- ocr-api の詳細構造 → [ocr-api.md](./ocr-api.md)
- iOS クライアントの詳細構造 → [Scanner.md](./Scanner.md)
- ガイドライン検索システムの実装計画 → [guideline-search-plan.md](./guideline-search-plan.md)
- ガイドライン検索 API 仕様書 → [guidline-api/guideline-api.md](./guidline-api/guideline-api.md)
- ガイドライン検索 iOS アプリ仕様書 → [GuidlineSearch/GuidlineSearch.md](./GuidlineSearch/GuidlineSearch.md)
- trouble-api の詳細構造・開発ポイント → [trouble-api.md](./trouble-api.md)
- transcribe-api の要件定義 → [transcribe-api/SPEC.md](./transcribe-api/SPEC.md)
- transcribe-api のテスト計画 → [transcribe-api/TESTPLAN.md](./transcribe-api/TESTPLAN.md)
