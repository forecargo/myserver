# CLAUDE.md — kobunApp（古文単語アプリ「ことだま」/ SwiftUI）

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクトの目的

古文単語学習 iOS アプリ **「ことだま」** の SwiftUI 実装。

データ（単語・慣用句・暗記カード画像）は本リポジトリには持たず、**バックエンド `kobun-api`（FastAPI, 読み取り専用コンテンツ配信 API）から取得**する。学習進捗・SRS・お気に入り・設定など**ユーザー状態は端末内（SwiftData / UserDefaults）に保持**する（API は content-only・認証なし）。

- バックエンド本体・データ仕様 → `../kobun/CLAUDE.md`・`../kobun/README.md`（**API レスポンスの正**）。
- 世界観: **水彩 × 藤色 × 明朝**。固定マスコット **子フクロウ「ことだま」** が全画面でナビゲートする。

### 実装状況（スケルトン実装済み・ビルド確認済み）

- **全 7 画面**（ホーム/単語帳/詳細/暗記/クイズ/復習/設定）＋通信層＋SwiftData モデル＋デザイントークンを実装済み。
- `xcodegen generate` → `xcodebuild -sdk iphonesimulator ...` で **BUILD SUCCEEDED** を確認済み。
- 動作: 単語帳（章・品詞フィルタ＋学習ドット）／詳細（カード画像＋意味・例文・解説タブ＋「暗記に追加」「覚えた」）／暗記（スワイプ仕分け＋SRS 反映）／クイズ（4 択採点＋履歴）／復習（忘却度 3 分類＋due 取得）／設定（目標・表示・ことだま・接続先＋ヘルス確認）。
- **未了 TODO**:
  - マスコット画像 `kotodama` 未配置（現状 SF Symbol のプレースホルダ。`Components.swift` の `KotodamaView` に `TODO`）。
  - カスタムフォント未同梱（システム明朝/ゴシックで代替。`DesignTokens.swift` の `KBFont`）。
  - `ViewModels/` 分離・`Tests/` は未着手（現スケルトンは各 View に `@State` で保持）。
  - 既定接続先 `https://forecargo.ngrok.app/kobun` を使うには、API 側で `docker compose up -d --build kobun-api` ＋ `docker compose restart caddy`（`/kobun` ルート反映）が必要。手軽にはローカル API（`http://localhost:8006`）を設定画面で指定。

***

## 技術スタック / 開発環境

- **言語/SDK**: Swift（Xcode 26 系・Swift 6 ツールチェーンで開発可）。**iOS 17.0** 最低対応・**iPhone 専用・縦向き固定**（兄弟アプリ `TangoApp` に合わせる）。
- **UI**: SwiftUI（MVVM）。
- **永続化**: **SwiftData**（学習進捗など）＋ `@AppStorage`/`UserDefaults`（設定・API ベース URL）。CoreData は使わない。
- **通信**: `URLSession` + async/await を **`actor` シングルトン**でラップ。
- **プロジェクト生成**: **XcodeGen**。`project.yml` が正で、`.xcodeproj` は生成物（手編集しない・原則 Git 追跡外）。
- **バンドル ID**: `com.hoshinoji.kobun`（プレフィックスは兄弟アプリ準拠）。

### よく使うコマンド

```bash
# 依存ツール（未導入時）
brew install xcodegen

# プロジェクト生成 → 起動
cd kobunApp
xcodegen generate
open kobunApp.xcodeproj

# CLI でビルド検証（シミュレータ・署名不要）
xcodebuild -project kobunApp.xcodeproj -scheme kobunApp \
  -sdk iphonesimulator -destination 'generic/platform=iOS Simulator' \
  build CODE_SIGNING_ALLOWED=NO

# バックエンドのヘルスチェック（Caddy/ngrok 経由）。要: kobun-api 起動＋caddy 再読込
curl -s https://forecargo.ngrok.app/kobun/healthz
# ローカル起動の API を使う場合（設定画面で接続先を http://localhost:8006 に）
cd ../kobun && uv run uvicorn app.main:app --port 8006   # 別ターミナル
curl -s http://localhost:8006/healthz
```

> `xcodegen generate` はソース構成（`Sources/` 配下のファイル追加・削除）を変えたら都度実行する。

***

## ディレクトリ構成（実装済み）

兄弟アプリ `TangoApp` 準拠。現状は View をフラットに配置（規模拡大時に機能別サブフォルダへ分割可）。

```
kobunApp/
├── project.yml                 # XcodeGen 仕様（正）。iPhone専用・縦・iOS17・bundleId・info ブロックで Info.plist 生成
├── Info.plist                  # 生成物（ATS で localhost 許可）。.gitignore 対象
├── .gitignore                  # .xcodeproj / Info.plist など生成物を除外
├── CLAUDE.md
├── Sources/
│   ├── App.swift               # @main・modelContainer・起動時に APIService へ baseURL 注入
│   ├── Assets.xcassets/        # AppIcon / AccentColor（マスコット画像は未配置）
│   ├── Models/
│   │   ├── APIModels.swift     # kobun-api のレスポンスと 1:1 の Codable DTO
│   │   └── PersistedModels.swift  # SwiftData @Model（WordProgress / QuizAttempt / DailyStudyLog）＋ DayKey
│   ├── Services/
│   │   ├── KobunAPIService.swift  # actor・URLSession・全エンドポイント・画像URL結合
│   │   └── SRSScheduler.swift     # 間隔反復（SM-2 簡易版）・忘却度分類
│   └── Views/
│       ├── DesignTokens.swift  # 配色（kb*）・KBFont・Spacing/Radius
│       ├── Components.swift    # KotodamaView/Bubble・CardImage・StatusDot・POSChip・ProgressRing・HomeMenuRow・ProgressStore
│       ├── RootTabView.swift   # 5 タブ（ホーム/単語帳/暗記/復習/設定）
│       ├── HomeView.swift
│       ├── WordListView.swift  # WordRow を含む
│       ├── WordDetailView.swift
│       ├── FlashcardView.swift
│       ├── QuizView.swift
│       ├── ReviewView.swift
│       └── SettingsView.swift
└── （将来）Fonts/・ViewModels/・Tests/   # 未着手
```

***

## バックエンド連携（最重要）

### ベース URL

- **本番（Caddy/ngrok 経由）**: `https://forecargo.ngrok.app/kobun`
  - Caddy は `/kobun*` を `kobun-api:8006` に reverse_proxy（`/kobun` は strip_prefix）。
  - **前提**: 親リポジトリ `../docker-compose.yml` に `kobun-api`、`../caddy/Caddyfile` に `/kobun*` ルートが追加済みであること（未追加なら 502/404 になる）。
- **ローカル開発**: `http://localhost:8006`（`uv run uvicorn app.main:app --port 8006`）。`Info.plist` の ATS で localhost の平文通信と `NSAllowsLocalNetworking` を許可する。
- 既定値はコードにハードコードし、**`@AppStorage("api_base_url")` で上書き可**（設定画面）。起動時に `App.swift` から `KobunAPIService` へ注入する（`TangoApp` 方式）。

### エンドポイント（`kobun-api` 実装済み・すべて GET・読み取り専用）

ベース URL に対する相対パス。

| パス | 用途（画面） |
|---|---|
| `GET /healthz` | 死活確認 |
| `GET /api/meta` | 区分・件数・品詞内訳（単語帳の章ヘッダ・品詞タブ） |
| `GET /api/words?section=&pos=&q=&ids=&limit=&offset=` | 単語一覧（`ids` はカンマ区切り・順序保持＝暗記/復習の集合取得） |
| `GET /api/words/{entry_no}` | 単語詳細（例 `001`） |
| `GET /api/idioms?q=&ids=&limit=&offset=` | 慣用句一覧 |
| `GET /api/idioms/{idiom_id}` | 慣用句詳細（例 `kobun-kanyouku-10_0`） |
| `GET /api/search?q=&limit=` | 単語・慣用句の横断検索 |
| `GET /api/quiz?section=&pos=&count=&choices=` | 4 択クイズ素材（`answer_index` 同梱・採点は端末側） |
| `GET /assets/manga/...` | 暗記カード画像（静的） |

### 画像 URL の組み立て（注意）

API のレスポンスの `image_url` は **ホスト相対パス**（既定 `"/assets/manga/part1/001.png"`）で返る。Caddy の `/kobun` プレフィックスを保つため、**`baseURL`（`.../kobun`）に対して相対結合**して絶対 URL を作る:

```swift
// 例: baseURL = https://forecargo.ngrok.app/kobun, image_url = /assets/manga/part1/001.png
//  → https://forecargo.ngrok.app/kobun/assets/manga/part1/001.png
func absoluteImageURL(_ imageURL: String) -> URL? {
    baseURL.appendingPathComponent(imageURL.trimmingPrefix("/").description)
}
```

- `URL(string:relativeTo:)` は `/` 始まりだとホスト直下に解決し `/kobun` が落ちるため使わない。
- 画像は `AsyncImage` で `AsyncImagePhase`（`.empty`→ProgressView / `.success`→resizable scaledToFit / `.failure`→日本語エラー）を明示処理する（`TangoApp/WordDetailView` 準拠）。

### DTO（`APIModels.swift`）方針

- `kobun-api` の Pydantic と **フィールド名を snake_case のまま**一致させる（`CodingKeys` 不要）。null 許容フィールドは Swift の Optional。
- 詳細系は `response_model_exclude_none=True` のため **欠落キーが普通に発生**する → DTO は欠落に強い Optional/デフォルトで定義する。
- 主な型: `MetaResponse{words,idioms,sections:[Section{key,label,type,count,pos:[PosCount{key,count}]}]}`、`WordListResponse{total,limit?,offset,items:[WordListItem]}`、`WordListItem{entry_no,section,pos_category?,headword,reading?,image_url?,short_gloss}`、`WordDetail{...,conjugation_type?,meanings:[Meaning{no?,gloss}],semantic_shift?{modern?,classical?},honorific?{type,base_word?},related_words:[],commentary?,examples:[Example{sense_no?,text,target_words[],translation?,source?}],mistake_note?{wrong,correct,note},tip_box?,qr_code?,pages[]}`、`IdiomListResponse/IdiomDetail{...,senses:[{label?,writing?,meanings[]}] | meanings[]}`、`SearchResponse{words,idioms}`、`QuizResponse{count,questions:[{question_id,entry_no,pos_category?,prompt{headword,reading?},choices:[{index,gloss}],answer_index}]}`。
- 通信層は `actor KobunAPIService { static let shared }`＋日本語メッセージの `LocalizedError`（`networkError`/`httpError(Int,String)`/`decodingError`/`notFound`）。`GuidlineSearch/SearchAPIService` を雛形に、必要なら `TangoApp` の LRU＋ディスクキャッシュを足す。

***

## 端末内データモデル（SwiftData / API 範囲外）

API は content-only のため、**学習に関する状態はすべて端末で持つ**。単語の同定キーは `entry_no`（慣用句は `idiom_id`）。

- `@Model WordProgress`：`@Attribute(.unique) var key`（`entry_no` か `idiom_id`）、`status`（未学習/学習中/覚えた）、SRS フィールド（`ease`・`intervalDays`・`dueDate`・`lastReviewedAt`・`correctStreak`・`lastResult`）、`isFavorite`、`inFlashcardDeck`。
- `@Model QuizAttempt`：`questionKey`・`isCorrect`・`answeredAt`。
- `@Model DailyStudyLog`：`date`・`learnedCount`（ホームの達成リング・今週の学習・連続日数の算出）。
- SwiftData の軽量マイグレーションのため、**新規プロパティには必ずデフォルト値**を付ける。
- 設定（`@AppStorage`）：`dailyGoal`(既定20)・`reminderTime`・`srsEnabled`・`verticalText`・`showFurigana`・`darkMode`・`mascotMessages`・`characterVoice`・`api_base_url`。

### SRS（復習出題）

復習タブは「もうすぐ忘れる / そろそろ確認 / まだ余裕」に分類して出題する。間隔反復（**Leitner か SM-2 の簡易版**）を `SRSScheduler` に実装し、`WordProgress.dueDate` を更新する。出題対象の `entry_no` を集めて `GET /api/words?ids=...` で本文を取得する（本文は永続化せずキャッシュのみ）。

***

## 画面構成（全 7 スクリーン）

タブは **ホーム / 単語帳 / 暗記 / 復習 / 設定** の 5 つ。クイズはホームから起動、単語詳細は単語帳から push。

| 画面 | 役割 | 主な取得元 |
|---|---|---|
| **ホーム** | 達成リング（本日 n/目標）・今週の学習・メニュー（暗記/クイズ/復習導線） | DailyStudyLog（端末）＋ `/api/meta` |
| **単語帳** | 章選択＋品詞タブ＋単語行（番号/見出し/読み/略意味/学習状態ドット） | `/api/meta`・`/api/words?section=&pos=`、ドットは `WordProgress` |
| **単語詳細** | カード画像（主役）＋見出し/読み/活用＋意味/例文/解説タブ | `/api/words/{entry_no}` |
| **暗記カード** | カード画像＋見出しをスワイプ仕分け（覚えた/まだ/戻す） | 端末が選んだ集合 → `/api/words?ids=` |
| **クイズ** | 4 択（古語→意味）・正誤フィードバック | `/api/quiz`、採点は `answer_index` で端末側 |
| **復習(SRS)** | 忘却度分類・本日の復習・まもなく忘れそうな語 | `WordProgress`/`SRSScheduler` ＋ `/api/words?ids=` |
| **設定** | 目標語数・リマインド・出題アルゴリズム・表示（縦書き/ふりがな/ダーク）・ことだま | `@AppStorage` |

> 「入試重要」フラグ・学習状態ドットの色は **端末側の責務**（現 API は重要度フラグを返さない）。

***

## デザインシステム（`DesignTokens.swift`）

世界観: **水彩 × 藤色 × 明朝**。`Color` 拡張に `kb*` プレフィックスのトークン、`enum Spacing`/`enum Radius` を定義し、ルートに `.tint(.kbPrimary)` を設定する（`GuidlineSearch` の `Color(hex:)`＋`adaptive(light:dark:)` ヘルパ方式を踏襲）。

### 配色（デザイン由来）

| 用途 | 色 |
|---|---|
| 背景 | `#F2EADA` |
| カード面 / セル | `#FCF9F1` |
| 枠線 | `#EBE2D0` / `#E6DCC8` |
| 主色（藤） | `#8A77B0`、濃: `#6B5A93`、グラデ `#9281B8→#6B5A93` |
| アクセント赤（重要・誤答・まだ） | `#C15B43` / `#C08579` |
| 緑（覚えた・正解） | `#7E9A78` / `#5E8158` |
| 金（星・確認） | `#C9A24B` |
| テキスト | 主 `#36302A` / 副 `#8C8273`・`#9C9384` / 本文 `#5B554C` |
| 学習状態ドット | 覚えた `#7E9A78` / 学習中 `#8A77B0` / 未学習 `#D8CDBA` |

### フォント（Google Fonts・OFL）

`.ttf` を `Sources/Fonts/` に同梱し、`Info.plist` の `UIAppFonts` に登録、`Font.custom(...)` で使う。

- **Shippori Mincho**（明朝）… 見出し語・赤字番号・大きな数字・章見出し。
- **Zen Kaku Gothic New**（ゴシック）… 本文・UI・ラベル。
- **Klee One**（手書き体）… マスコット「ことだま」の吹き出しセリフ。

### マスコット「ことだま」

- 設定: 丸い**コノハズク風の子フクロウ**。体=生成り〜淡い小麦色、ほっぺ=淡いピンク、つぶらな黒目、小さな羽角、**藤色のリボン**。褒めて励ます癒し系の敬体（女子高生に寄り添う）。
- ホーム達成リング中央・暗記/クイズ/復習のヒント吹き出し・設定ヘッダ等に常駐させる。
- 画像は**アプリ同梱アセット**（`Assets.xcassets`）として持つ（語データではないため API では配信しない）。ない場合は別途用意する。**既存の商用キャラクターに似せない**。

***

## 開発の方針 / 注意

- **API は読み取り専用・content-only**。進捗/SRS/設定/お気に入りはサーバへ送らず端末で完結させる（オフライン前提）。
- DTO は API の正（`../kobun`）に追従する。API 仕様変更時は両者を同期する。**勝手にエンドポイントを増やさない**（必要なら `../kobun` 側と合わせて確認する）。
- 縦書き・旧字・異体字・繰り返し記号は原文どおり表示する（読みやすさのための現代語化はしない）。
- 機密情報はハードコードしない。ngrok ドメイン等の接続先は定数＋`@AppStorage` 上書きで管理する。
- グローバル規約（結論先出し・スコープ厳守・推測で先行実装しない・確認優先）に従う。
- スクショ/実機確認は `xcodegen generate` → Xcode でビルドして行う。
