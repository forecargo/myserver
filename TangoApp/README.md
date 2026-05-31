# TangoApp

tango プロジェクトの単語帳データを iPhone で閲覧・学習する SwiftUI クライアント。仕様は `/Users/nobuhiro/Python/myserver/tango/SPEC_SwiftUI.md` を参照。

## 必要なもの

- macOS + Xcode 15+ (iOS 17 SDK)
- [XcodeGen](https://github.com/yonaskolb/XcodeGen) (`brew install xcodegen`)
- tango Python サーバが起動済み (`viewer.py`) で `https://forecargo.ngrok.app/tango/*` 経由でアクセス可能なこと

## セットアップ

```bash
# プロジェクト生成
cd /Users/nobuhiro/Python/myserver/TangoApp
xcodegen generate

# Xcode で開く
open TangoApp.xcodeproj
```

## バックエンドの起動

```bash
cd /Users/nobuhiro/Python/myserver/tango
.venv/bin/python viewer.py
```

`viewer.py` は `http://127.0.0.1:8765/` で起動する。実機からアクセスするには Caddy で `forecargo.ngrok.app/tango/*` を `127.0.0.1:8765/*` にリバースプロキシする必要がある (myserver リポジトリの Caddy 設定参照)。

LAN 上のシミュレータ・実機で試す場合は、アプリの「設定 → API 接続」で `http://<mac-ip>:8765` に切り替える。`project.yml` で `NSAllowsLocalNetworking: true` を設定済み。

## テスト

```bash
xcodebuild test \
  -project TangoApp.xcodeproj \
  -scheme TangoApp \
  -destination 'platform=iOS Simulator,name=iPhone 15'
```

カバレッジ:
- `CodableTests` — Pydantic スキーマとの往復デコード
- `QuizGeneratorTests` — 4 択生成ロジックの seed 再現性・品詞優先
- `WordProgressTests` — SwiftData CRUD と一意制約

## ディレクトリ構成

```
TangoApp/
├── project.yml                 # XcodeGen
├── Info.plist                  # XcodeGen が一部上書き
├── Sources/
│   ├── App.swift               # @main、ModelContainer
│   ├── Models/                 # APIModels / DomainModels / PersistedModels
│   ├── Services/               # TangoAPIService / SpeechService / QuizGenerator
│   ├── ViewModels/             # @Observable ViewModels
│   ├── Views/                  # SwiftUI Views (Browse / Learn / Quiz / Settings)
│   └── Assets.xcassets/
└── Tests/                      # XCTest
```

## 注意

- `tango/models.py` (Pydantic スキーマ) を変更したら、`Sources/Models/APIModels.swift` も同時に更新する。`CodableTests` で契約整合を検証している。
- TTS は `word` と `examples.en` のみ読み上げる。`phonetic` (IPA) は読まない (記号として読まれて意味不明な音になるため)。
- 学習進捗は SwiftData にローカル保存のみ。iCloud 同期は将来検討。
