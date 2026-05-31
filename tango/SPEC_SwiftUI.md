SPECIFICATION: SwiftUI 単語帳アプリ (Tango iOS Client)

1. プロジェクト概要 (Overview)

本仕様書は、tango プロジェクトが抽出する構造化 JSON データ (`data/<batch>/*.json`) を消費する iOS クライアントアプリの実装仕様を定義する。SPEC.md §1 で言及されている「娘向けのオリジナル単語帳アプリ開発」の第二段階に相当する。

想定ユーザーは小〜中学生 (英単語学習を始めたばかりの娘) を主軸とし、iPhone 上で以下を提供する:

- viewer.py の確認 UI 体験を iPhone 上で再現する閲覧機能 (バッチ → ファイル → 単語カード)
- お気に入り (★) / 既習・未習フラグ / 閲覧履歴の学習補助機能
- 4 択クイズ (英→日) による反復練習
- AVSpeechSynthesizer による見出し語・例文の発音再生

データ供給元は tango Python 側の `viewer.py` (FastAPI) を **そのまま API サーバーとして利用** する。ngrok 経由で `https://forecargo.ngrok.app/tango` に公開し、iOS クライアントは HTTPS でアクセスする。アプリ側にデータ本体は同梱しない (再抽出運用でデータが更新されるため)。

本仕様書は SPEC.md と対をなし、tango Pydantic スキーマ (`models.py`) と Swift Codable モデルの **契約整合性** を文書化する。`models.py` 変更時は本仕様書および SwiftUI 実装の両方を更新する義務を負う (CLAUDE.md「モデル/プロンプト変更時の影響」参照)。

2. 動作環境・技術スタック (Technology Stack)

| 項目 | 採用技術 |
| --- | --- |
| 言語 | Swift 5.9+ |
| UI フレームワーク | SwiftUI |
| 最小対応 OS | iOS 17.0 |
| 状態管理 | Observation (`@Observable` + `@Bindable`) |
| 永続化 | SwiftData (`@Model`) |
| 音声合成 | AVFoundation の `AVSpeechSynthesizer` |
| ネットワーク | 標準 `URLSession` + `JSONDecoder` |
| プロジェクト生成 | XcodeGen (`project.yml`) |
| 外部依存 | なし (SPM パッケージ追加禁止、標準ライブラリのみ) |

iOS 17 を最低条件にすることで Observation フレームワーク (`@Observable`) を採用し、`ObservableObject` / `@Published` ベースのボイラープレートを排除する。既存 iOS アプリ (`GuidlineSearch/`, `ScheduleScanner/`) は iOS 16/17 と SwiftUI を採用しているが、本アプリは Observation 前提のため iOS 17 専用とする。

3. ディレクトリ構成と XcodeGen 設定 (Project Layout)

物理配置は **`/Users/nobuhiro/Python/myserver/TangoApp/`** とし、tango Python リポジトリ (`/Users/nobuhiro/Python/myserver/tango/`) とは分離する。既存 iOS アプリ (`GuidlineSearch/`, `ScheduleScanner/`) と同階層に揃えることで、サーバー側と独立した iOS 開発ワークフローを維持する。

```
myserver/
├── tango/                            # サーバ側 (Python)
│   ├── SPEC.md
│   └── SPEC_SwiftUI.md               # 本仕様書
└── TangoApp/                         # iOS クライアント
    ├── project.yml                   # XcodeGen 設定
    ├── Info.plist                    # XcodeGen が生成・上書き
    ├── TangoApp.xcodeproj/           # .gitignore 対象
    ├── README.md                     # ビルド手順 (本仕様書と相互参照)
    └── Sources/
        ├── App.swift                 # @main、ModelContainer 構築
        ├── Assets.xcassets/
        ├── Models/
        │   ├── APIModels.swift       # Codable (Pydantic 写経)
        │   ├── DomainModels.swift    # batch/stem 付与の identity 型
        │   └── PersistedModels.swift # @Model (SwiftData)
        ├── Services/
        │   ├── TangoAPIService.swift # actor、URLSession ラッパ
        │   ├── SpeechService.swift   # AVSpeechSynthesizer ラッパ
        │   └── QuizGenerator.swift   # 純粋ロジック (テスト対象)
        ├── ViewModels/
        │   ├── BatchListViewModel.swift
        │   ├── FileListViewModel.swift
        │   ├── WordListViewModel.swift
        │   ├── WordDetailViewModel.swift
        │   ├── FavoritesViewModel.swift
        │   ├── QuizViewModel.swift
        │   └── SettingsViewModel.swift
        └── Views/
            ├── RootTabView.swift
            ├── DesignTokens.swift
            ├── Browse/               # BatchList, FileList, WordList, WordDetail, WordCardView
            ├── Learn/                # FavoritesView, ReviewView
            ├── Quiz/                 # QuizStartView, QuizQuestionView, QuizResultView
            └── Settings/             # SettingsView
```

**project.yml 骨子** (XcodeGen で `TangoApp.xcodeproj` を生成):

```yaml
name: TangoApp
options:
  bundleIdPrefix: com.hoshinoji
  deploymentTarget:
    iOS: "17.0"
targets:
  TangoApp:
    type: application
    platform: iOS
    sources: [Sources]
    info:
      path: Info.plist
      properties:
        CFBundleDisplayName: たんご
        UISupportedInterfaceOrientations:
          - UIInterfaceOrientationPortrait
        NSAppTransportSecurity:
          NSAllowsLocalNetworking: true
    settings:
      SWIFT_VERSION: "5.9"
      PRODUCT_BUNDLE_IDENTIFIER: com.hoshinoji.tango
      MARKETING_VERSION: "1.0"
      CURRENT_PROJECT_VERSION: "1"
  TangoAppTests:
    type: bundle.unit-test
    platform: iOS
    sources: [Tests]
    dependencies:
      - target: TangoApp
```

| 項目 | 値 |
| --- | --- |
| アプリ表示名 | たんご (ひらがな) |
| Bundle ID | `com.hoshinoji.tango` |
| 画面回転 | 縦のみ (Portrait 固定、MVP) |
| ATS | HTTPS 経由が原則、`NSAllowsLocalNetworking` のみ true (開発時の LAN 動作用) |

`.gitignore` 追記: `TangoApp.xcodeproj/`, `DerivedData/`, `*.xcuserstate`。

4. アーキテクチャ (Architecture)

MVVM + Repository 層構成。GuidlineSearch / ScheduleScanner のアーキテクチャ規約を踏襲しつつ、iOS 17 限定のため Observation フレームワーク (`@Observable`) を採用する。

```
RootTabView (TabView)
├── BrowseFlow (NavigationStack)
│     BatchListView → FileListView → WordListView → WordDetailView
├── LearnFlow (NavigationStack)
│     FavoritesView / ReviewView → WordDetailView
├── QuizFlow (NavigationStack)
│     QuizStartView → QuizQuestionView → QuizResultView
└── SettingsFlow (NavigationStack)
      SettingsView

各 View
  └── @Bindable ViewModel  (@MainActor @Observable final class)
        ├── TangoAPIService.shared (actor)       ← URLSession + JSONDecoder
        ├── SpeechService.shared (@MainActor)    ← AVSpeechSynthesizer
        ├── QuizGenerator (struct, 副作用なし)    ← テスト容易
        └── ModelContext (SwiftData)             ← @Environment(\.modelContext)
```

責務マトリクス:

| レイヤ | 責務 | 例 |
| --- | --- | --- |
| View | レイアウト・ユーザー入力受付 | `WordDetailView` |
| ViewModel | 状態保持・コーディネーション・SwiftData CRUD | `WordDetailViewModel` |
| Service | I/O・外部 SDK ラップ・スレッド境界 | `actor TangoAPIService` |
| Generator | 副作用なしの純粋ロジック | `QuizGenerator` |
| Model | データ型・契約 | `APIVocabularyItem` / `WordProgress` |

5. データモデル (Data Models)

5.1 API Codable モデル (Pydantic 写経)

`Sources/Models/APIModels.swift` に tango `models.py` と 1 対 1 対応する Codable struct を定義する。フィールド名は **Pydantic スネークケースのまま** とし、`CodingKeys` を省略する。これは契約原文との差分追跡を優先する意図的な選択である。

```swift
struct APIVocabularyResult: Codable {
    let vocabulary_list: [APIVocabularyItem]
}

struct APIVocabularyItem: Codable, Identifiable, Hashable {
    let id: String                       // "001"、ゼロパディング維持
    let word: String
    let phonetic: String                 // 例 "[əgríː]"
    let level_tag: String?               // null 許容 (A1 / A2 / 最難関 等)
    let definitions: [APIMeaningGroup]   // ≥1 (Pydantic 契約)
    let usages_and_notes: [String]       // 空配列許容、Optional ではない
    let word_origin: APIWordOrigin?      // null 許容
    let examples: [APIExampleSentence]   // 空配列許容、Optional ではない
}

struct APIMeaningGroup: Codable, Hashable {
    let part_of_speech: String           // "自動詞" / "他動詞" / "名詞" など
    let meanings: [String]
}

struct APIWordOrigin: Codable, Hashable {
    let formula: String?                 // 語源パーツ分解式
    let description: String?             // 派生語・補足説明
}

struct APIExampleSentence: Codable, Hashable {
    let en: String
    let ja: String
}

struct APIFileEntry: Codable, Hashable {
    let stem: String                     // "LEAP - part1 - 01"
    let count: Int                       // -1 は viewer.py 側のパース失敗を意味する
    let has_image: Bool
}
```

**契約遵守ルール**:

- `id` は **文字列で保持**。Int への変換は禁止 (ゼロパディング情報が失われる)
- `level_tag` / `word_origin` のみ Optional。それ以外は Optional 化しない
- `usages_and_notes` / `examples` は Pydantic 側で `default_factory=list` のため、欠落時は `[]` で到達する。Swift 側でも非 Optional 配列で受ける
- `definitions` が空のレスポンスは Pydantic 側で禁じられているが、念のため Swift 側はデコードを許容し、UI 側で警告表示する
- `count == -1` は `viewer.py` が JSON パースに失敗したファイルを示すマジックナンバー。UI で "err" バッジを表示する

5.2 ドメインモデル

API モデルに `batch` / `stem` を付与した識別子型を別途定義する。これにより SwiftData 層・UI 層でのバッチ間 `id` 衝突を防ぐ。

```swift
struct DomainWord: Identifiable, Hashable {
    let batch: String
    let stem: String
    let item: APIVocabularyItem

    var id: String { "\(batch)::\(stem)::\(item.id)" }
}
```

5.3 SwiftData 永続化モデル

§11 を参照。

6. API クライアント設計 (API Client)

`actor TangoAPIService` を中心に設計し、GuidlineSearch の `SearchAPIService` と同パターンを踏襲する。**書き込み API は持たない** (お気に入り等はローカル SwiftData のみで完結)。

エンドポイント表:

| メソッド | パス | レスポンス Swift 型 | キャッシュ戦略 |
| --- | --- | --- | --- |
| GET | `/api/batches` | `[String]` | プロセス中 1 回 |
| GET | `/api/files/{batch}` | `[APIFileEntry]` | 5 分間メモリ |
| GET | `/api/data/{batch}/{stem}` | `APIVocabularyResult` | 50 件 LRU |
| GET | `/image/{batch}/{stem}` | `Data` (image/jpeg) | `URLSession.shared.urlCache` 任せ |

actor 骨子:

```swift
actor TangoAPIService {
    static let shared = TangoAPIService()

    private var baseURL: URL = URL(string: "https://forecargo.ngrok.app/tango")!
    private var batchListCache: [String]?
    private var fileListCache: [String: (Date, [APIFileEntry])] = [:]
    private var wordDataCache: LRUCache<String, APIVocabularyResult> = .init(capacity: 50)

    func setBaseURL(_ url: URL) { self.baseURL = url; invalidateAll() }
    func listBatches(forceRefresh: Bool = false) async throws -> [String]
    func listFiles(batch: String) async throws -> [APIFileEntry]
    func loadData(batch: String, stem: String) async throws -> APIVocabularyResult
    nonisolated func imageURL(batch: String, stem: String) -> URL
}

enum TangoAPIError: LocalizedError {
    case invalidBaseURL
    case networkError(Error)
    case httpError(Int, String)
    case decodingError(Error)
    case batchNotFound(String)
    case fileNotFound(batch: String, stem: String)
}
```

**実装方針**:

- baseURL は `@AppStorage("api_base_url")` で永続化し、アプリ起動時に `setBaseURL(...)` で actor に反映する
- 既定値は `https://forecargo.ngrok.app/tango` (Caddy で 8765 番に逆プロキシする前提、§14 参照)
- HTTP ステータス検査: `(200..<300)` 以外は `httpError` に変換。404 は `batchNotFound` / `fileNotFound` に分岐
- リトライは初期版で実装しない。タイムアウト 30 秒
- 画像取得は `AsyncImage(url:)` に任せ、Service 層は URL を返すだけ (`nonisolated` メソッド)

7. 画面構成 (Screens & Navigation)

タブ構成:

```
TabView
├── 単語帳 (book.fill)              → BrowseFlow
├── 学習   (star.fill)              → LearnFlow
├── クイズ (questionmark.circle.fill) → QuizFlow
└── 設定   (gearshape.fill)         → SettingsFlow
```

各 NavigationStack で `navigationDestination(item:)` を使った型安全な遷移を行う。

7.1 BrowseFlow (単語帳タブ)

階層: **BatchListView → FileListView → WordListView → WordDetailView**

| 画面 | 主要要素 |
| --- | --- |
| BatchListView | バッチ名 (例: `part1`) を List 表示。各行に件数バッジ・最終閲覧日時 |
| FileListView | `APIFileEntry` を List 表示。`stem` / 抽出件数バッジ / 画像有無アイコン。`count == -1` は赤バッジで "err" 表示 |
| WordListView | 単語一覧。各行: `id` / `word` / `phonetic` / `level_tag バッジ` / ★ / 既習チェック。検索バー (word / 日本語 meaning / phonetic を部分一致) |
| WordDetailView | viewer.py のカードを iOS で 1:1 再現 + 学習機能 + TTS + 折りたたみ画像 |

**WordDetailView 構成**:

- ヘッダ: `#id` (グレー) / `word` (24pt bold) / `phonetic` (italic) / `level_tag` (capsule) / ★ お気に入りトグル / 🔊 TTS
- `definitions`: 品詞バッジ + 番号付きリスト (品詞ごとに `pos-block` ブロック)
- `usages_and_notes`: 灰色背景の bullet list
- `word_origin`: 薄黄背景 (`taOriginBg`) のカード、`formula` は等幅フォント (`SF Mono`)
- `examples`: 左 3px ボーダーの引用調リスト、各例文に 🔊 ボタン
- フッタ: 「既習にする」トグルボタン
- DisclosureGroup「ページ画像を表示」(デフォルト閉) → `AsyncImage(url: api.imageURL(...))`

**検索ハイライト**: GuidlineSearch の `ResultCardView` 方式を踏襲し、`AttributedString.backgroundColor = UIColor.systemYellow.withAlphaComponent(0.4)` で大文字小文字無視・複数キーワード対応のハイライトを行う。

7.2 LearnFlow (学習タブ)

セグメント切替で 2 ビュー:

- **お気に入り**: `WordProgress.isFavorite == true` を List 表示。タップで WordDetailView へ
- **復習 (未習)**: `isLearned == false` のうち最近閲覧したものを優先表示。「ランダム 10 件」ボタンでカードめくり UI (ZStack でカード重ね合わせ、左右スワイプで既習/スキップ)

7.3 QuizFlow (クイズタブ)

階層: **QuizStartView → QuizQuestionView → QuizResultView**

| 画面 | 主要要素 |
| --- | --- |
| QuizStartView | バッチ選択 / ファイル選択 (複数選択可) / 出題数 (5・10・20) / フィルタ (お気に入りのみ・未習のみ・全体) / 開始ボタン |
| QuizQuestionView | 進捗 "3 / 10" / 問題 (`word` + `phonetic` + 🔊) / 4 択ボタン / 正誤フラッシュ / 自動遷移 |
| QuizResultView | 正答率 / 不正解単語一覧 (タップで詳細へ) / 「もう一度」「終了」 |

**出題モード**: 初期版は **英→日のみ (MVP)**。日→英 / スペル入力は §16 将来拡張に倒す。

7.4 SettingsFlow

§12 参照。

8. 学習機能 (Learning Features)

8.1 お気に入りと既習/未習

- **お気に入り (★)**: WordListView / WordDetailView 両方に配置。タップで `WordProgress.isFavorite` をトグル。`ModelContext` に upsert (`fetchProgress(key:) ?? new()`)
- **既習/未習**: WordDetailView のフッタに「既習にする」トグル + WordListView の右端にチェックアイコン

8.2 学習履歴の記録粒度

WordDetailView を開いた瞬間に以下を更新:

- `viewCount += 1`
- `lastViewedAt = .now`

クイズで出題された結果は `correctCount` / `wrongCount` に蓄積する。

8.3 4 択クイズ問題生成ロジック (QuizGenerator)

純粋関数として実装し、テスト容易性を確保する。

```swift
struct QuizGenerator {
    struct Question: Identifiable {
        let id = UUID()
        let promptWord: APIVocabularyItem   // 出題対象 (TTS 用)
        let choices: [String]               // 4 つ、シャッフル済み (日本語 meaning)
        let correctIndex: Int
    }

    enum QuizError: Error {
        case insufficientPool                // プールが 4 未満
    }

    static func makeQuestions(
        pool: [APIVocabularyItem],
        count: Int,
        seed: UInt64? = nil
    ) throws -> [Question]
}
```

**ダミー選択肢生成方針**:

1. プールから対象単語を `count` 個選ぶ
2. 各設問について、**同じプール内の他 3 単語の最初の `meaning`** をダミーに選ぶ
3. **品詞 (`part_of_speech`) が同じ** 単語を優先 (動詞問題には動詞ダミー)
4. **`level_tag` が同じ** 単語をさらに優先 (フォールバックあり)
5. プールが 4 未満なら `QuizError.insufficientPool` を投げる
6. `seed` を受け取れば再現可能 (テスト用、`SystemRandomNumberGenerator` ではなく seedable RNG を使用)

プール構築は ViewModel が担う: QuizStartView で選択された (batch, stems, filter) から該当 `APIVocabularyItem` を集約 (現状はファイル単位で API を順次呼び出し、§14 の将来エンドポイントで一括取得に置換予定)。

9. TTS 統合 (Text-to-Speech)

`SpeechService` (@MainActor) を `AVSpeechSynthesizer` のラッパとして実装する。

```swift
@MainActor
final class SpeechService: NSObject, AVSpeechSynthesizerDelegate {
    static let shared = SpeechService()
    private let synthesizer = AVSpeechSynthesizer()
    var rate: Float = 0.45                    // UserDefaults と同期

    func speak(_ text: String, language: String = "en-US")
    func speakWord(_ item: APIVocabularyItem)            // word のみ
    func speakExample(_ ex: APIExampleSentence)          // ex.en のみ
    func speakAll(_ item: APIVocabularyItem)             // word → ex1 → ex2 ... をキュー再生
    func stop()
}
```

**仕様**:

| 項目 | 内容 |
| --- | --- |
| 言語 | `en-US` 固定 (MVP)。`ja-JP` 対応は将来 |
| 対象 | `word` および `examples[].en` のみ |
| **禁則** | **`phonetic` (IPA) は読まない** |
| 自動再生 | 設定で ON にすると WordDetailView 表示時に `word` を 1 回読む |
| 同時発声防止 | 新規 `speak` 前に `synthesizer.stopSpeaking(at: .immediate)` を呼ぶ |
| 速度 | 0.30–0.60 のスライダーで設定 (既定 0.45) |
| Voice 優先度 | Enhanced voice (`com.apple.voice.enhanced.en-US.Samantha`) を優先、未インストール時はデフォルトへフォールバック |
| AVAudioSession | 既定カテゴリのまま (MVP では明示的に変更しない) |

**phonetic を読まない理由**: AVSpeechSynthesizer は IPA 記号 ([əgríː] 等) を音素として解釈せず、記号を文字通り読み上げてしまうため意味不明な音になる。これは禁則事項として本仕様書と `SpeechService` 実装の両方にコメントで明記する。

10. デザイントークン (Design Tokens)

GuidlineSearch の `DesignTokens.swift` 構造を踏襲し、`Sources/Views/DesignTokens.swift` に色・スペーシング・Radius を定数化する。LEAP 単語帳のページがエンジ系のため、トーンを揃える:

| トークン | Light | Dark | 用途 |
| --- | --- | --- | --- |
| `taPrimary` | `#A02040` | `#FFB4B4` | 見出し・アクセント |
| `taSurface` | `#FFF9F6` | `#1F1B1A` | 背景 |
| `taOnSurface` | `#241817` | `#F5E9E5` | 本文 |
| `taOriginBg` | `#FFF9E6` | `#3A2F12` | 語源カード背景 |
| `taLevelA1` | `#8FBF7F` | `#3F7F2F` | A1 バッジ |
| `taLevelA2` | `#5F9FE0` | `#2F5F9F` | A2 バッジ |
| `taLevelMax` | `#C04020` | `#FF6040` | 最難関バッジ |

Spacing / Radius は GuidlineSearch と同値を流用 (`Spacing.sm=8`, `md=16`, `lg=24`, `Radius.card=14`)。

11. 永続化スキーマとマイグレーション (Persistence Schema)

**設計方針**: ユーザー固有データのみ SwiftData に永続化し、単語データ本体は API のメモリキャッシュに留める。

理由:
- 単語データは再抽出運用で更新される正本がサーバー側にある。ローカルに正本を持つとマイグレーション地獄を招く
- 学習進捗は数 KB 規模で軽量
- 例外: お気に入り一覧オフライン表示用に `wordSnapshot` / `phoneticSnapshot` のみスナップショット冗長化する

11.1 Schema V1

```swift
@Model
final class WordProgress {
    @Attribute(.unique) var key: String         // "<batch>::<stem>::<id>"
    var batch: String
    var stem: String
    var wordId: String                          // "001"
    var wordSnapshot: String                    // "agree" (オフライン表示用)
    var phoneticSnapshot: String                // "[əgríː]"
    var isFavorite: Bool = false
    var isLearned: Bool = false
    var viewCount: Int = 0
    var lastViewedAt: Date?
    var correctCount: Int = 0
    var wrongCount: Int = 0
    var note: String = ""                       // 自由メモ (将来用)

    init(key: String, batch: String, stem: String, wordId: String,
         wordSnapshot: String, phoneticSnapshot: String) { ... }
}

@Model
final class QuizAttempt {
    var startedAt: Date
    var finishedAt: Date?
    var batch: String
    var stem: String?                           // nil ならバッチ全体
    var totalQuestions: Int
    var correctAnswers: Int
}
```

11.2 初期化とマイグレーション

- `App.swift` で `.modelContainer(for: [WordProgress.self, QuizAttempt.self])` を Window に付与
- `Sources/Models/MigrationPlan.swift` に `SchemaMigrationPlan` を空実装で用意し、将来のバージョンアップに備える
- 初回起動でコンテナ生成に失敗した場合は `do/catch` で「データクリアして再起動」案内を表示

11.3 iCloud 同期

初期版は OFF (`cloudKitDatabase: nil`)。将来の iCloud 同期は §16 で検討。

12. 設定画面 (Settings)

`SettingsView` に以下を集約する:

| 項目 | 型 | 既定値 | 備考 |
| --- | --- | --- | --- |
| API ベース URL | TextField | `https://forecargo.ngrok.app/tango` | 保存時に URL バリデーション、保存後に `TangoAPIService.shared.setBaseURL(...)` を呼ぶ |
| TTS 自動再生 | Toggle | OFF | WordDetail 表示時に word を自動再生 |
| TTS 発話速度 | Slider | 0.45 | 範囲 0.30–0.60 |
| テーマ | Picker | システム追従 | 強制ライト / 強制ダーク |
| データクリア (お気に入り) | Button | — | 確認ダイアログ後、`WordProgress.isFavorite = false` を一括更新 |
| データクリア (学習履歴) | Button | — | `viewCount` / `correctCount` / `wrongCount` をリセット |
| データクリア (クイズ履歴) | Button | — | `QuizAttempt` を全削除 |
| バージョン情報 | Label | `MARKETING_VERSION` | — |

設定値は `@AppStorage` を用いて UserDefaults に永続化する (SwiftData には保存しない)。

13. テスト戦略 (Testing)

`TangoApp/Tests/` 配下に `TangoAppTests` ターゲットを project.yml で定義する。GuidlineSearch / ScheduleScanner はテストなしだが、本アプリは SwiftData とクイズロジックの正当性確保のため最小限のテストを置く。

| ファイル | カバー範囲 |
| --- | --- |
| `CodableTests.swift` | tango リポジトリの `output/*.json` を Bundle resource として梱包し、`APIVocabularyResult` への往復デコードを検証 (Pydantic との契約整合性) |
| `QuizGeneratorTests.swift` | 固定 seed で問題が再現生成されること、プール 4 未満で `insufficientPool` エラー、ダミー被り防止、品詞・level_tag 優先ロジック |
| `WordProgressTests.swift` | in-memory `ModelContainer` を使った upsert、`isFavorite` toggle、`key` 衝突なしの確認 |

ネットワーク層 (`TangoAPIService`) は `protocol TangoAPIServicing` を切って差し替え可能にしておくが、ViewModel の単体テストは MVP では作成しない (手動検証で許容)。

実行: Xcode のテストナビゲータ、または `xcodebuild test -scheme TangoApp -destination 'platform=iOS Simulator,name=iPhone 15'`。

14. viewer.py API 拡張要否 (Backend Considerations)

14.1 MVP で充足するエンドポイント

`tango/viewer.py` の既存 4 エンドポイント (`/api/batches`, `/api/files/{batch}`, `/api/data/{batch}/{stem}`, `/image/{batch}/{stem}`) で MVP は全機能を実装可能。

14.2 将来検討する追加エンドポイント

| エンドポイント | 用途 | 優先度 |
| --- | --- | --- |
| `GET /api/data/{batch}/all` | バッチ全単語をまとめて返す。クイズの「バッチ横断出題」とお気に入り一覧の高速化 | 中 |
| `GET /api/version` | データセットの最終更新タイムスタンプ。クライアント側キャッシュ無効化判定 | 低 |
| `GET /api/search?q=...&batch=...` | サーバー側横断検索。MVP はクライアント側ファイル単位検索で代替 | 低 |

14.3 公開経路の前提

`https://forecargo.ngrok.app/tango/*` を `viewer.py` (`127.0.0.1:8765`) にリバースプロキシする Caddy 設定の追加が必要 (myserver リポジトリの `caddy/` 配下を改修)。本仕様書は Caddy 改修自体を行わないが、ビルド・実行の前提条件として明記する。

CORS は Native アプリのため不要だが、開発時の SwiftUI Previews 動作確認のために `fastapi.middleware.cors.CORSMiddleware` を追加することは将来検討してよい。

15. ビルド・実行手順 (Build & Run)

```bash
# 1. tango Python サーバを起動
cd /Users/nobuhiro/Python/myserver/tango
.venv/bin/python viewer.py        # → http://127.0.0.1:8765/

# 2. Caddy で /tango 配下を 8765 にリバースプロキシ (要設定追加)
#    forecargo.ngrok.app/tango/* → 127.0.0.1:8765/*

# 3. iOS プロジェクト生成
cd /Users/nobuhiro/Python/myserver/TangoApp
xcodegen generate
open TangoApp.xcodeproj

# 4. Xcode でビルド → シミュレータ or 実機
```

実機での `forecargo.ngrok.app` への HTTPS 接続は ATS を満たすため追加設定不要。LAN 開発時は設定画面で `http://192.168.x.x:8765` に切り替え (`NSAllowsLocalNetworking: true` で許可済み)。

16. 将来拡張 (Future Work)

- **日→英 クイズ / スペル入力クイズ**: `QuizGenerator` に `Mode` enum を追加し、出題文と選択肢のロールを反転
- **iCloud 同期**: SwiftData + CloudKit (`cloudKitDatabase: .private("iCloud.com.hoshinoji.tango")`) でお気に入り・履歴を複数デバイス間同期
- **Widget**: WidgetKit で「今日の 5 単語」ホーム画面ウィジェット
- **Spaced Repetition**: SM-2 / Leitner system による復習スケジューリング
- **複数書籍対応**: `data/<book>/<part>/` 階層化 (現状は `data/<batch>/` 単層)
- **オフライン全データキャッシュ**: 初回起動時に全バッチ・全ファイルを SwiftData にコピー、ネットワーク不要化
- **書き込み API 同期**: `POST /api/progress/{key}` を viewer.py に追加し、家族間で進捗共有
- **日本語 TTS**: `examples.ja` の `ja-JP` 読み上げ

17. リスクと既知の制約 (Risks & Limitations)

| リスク | 影響 | 緩和策 |
| --- | --- | --- |
| ngrok URL 失効 | アプリが API に到達不能 | `forecargo.ngrok.app` は有料プランで固定。設定画面で URL 書き換え可能 |
| ngrok レイテンシ | クイズ体験低下 | メモリ LRU キャッシュ + 開始時の事前読み込み |
| SwiftData 初回マイグレーション失敗 | 起動不能 | `do/catch` でユーザーへ「データクリアして再起動」案内 |
| IPA フォントレンダリング | 一部記号が豆腐化 | システムフォント (SF) は IPA を十分カバーするが、`.font(.system(.body, design: .serif))` でフォールバック確認 |
| AVSpeechSynthesizer の英語発音品質 | 不自然な箇所がある | Enhanced voice 優先利用 + 未インストール時はデフォルトへフォールバック |
| **TTS が phonetic を読むと意味不明** | UX 著しく悪化 | **`phonetic` は読み上げ対象から除外** (本仕様書 §9 / 実装コメント両方に明記) |
| バッチ間 `id` 衝突 | お気に入り誤認識 | `<batch>::<stem>::<id>` を主キーにする |
| `count == -1` のファイル | カード表示崩壊 | UI で "err" バッジ + 詳細遷移時にエラーアラート |
| Pydantic スキーマ変更時の追従漏れ | デコード失敗で起動不能 | `CodableTests.swift` で `tango/output/*.json` の回帰検証を必須化。SPEC.md §10「モデル変更時の影響」に SwiftUI 側更新義務を追記済み |
| 画像著作権 | スキャン画像 (紙の単語帳) は著作物 | アプリ内では `DisclosureGroup` で折りたたみ・既定で閉じる。第三者への配布禁止 |

18. 未確定で次フェーズに送る項目 (TODO)

- iCloud 同期の最終可否 (SwiftData + CloudKit のスキーマ制約評価が必要)
- viewer.py への `CORSMiddleware` 追加可否 (開発体験 vs セキュリティ)
- `/api/data/{batch}/all` 実装優先度 (クイズ用途で必須化するか)
- WordListView のファイル名表示整形 (「LEAP - part1 - 01」を「Part 1 - 01」等に短縮するか、原文のまま表示するか)
- 「クイズ連続 3 回正解で自動既習」等の自動フラグ付与ルールの有無
- 横画面 (Landscape) サポートの追加可否 (iPad 対応と合わせて検討)

***

本仕様書は SPEC.md と対をなす。`tango/models.py` または `tango/viewer.py` を変更する際は、本仕様書の §5 / §6 を同時に更新し、Swift 実装側の追従漏れがないか確認すること。
