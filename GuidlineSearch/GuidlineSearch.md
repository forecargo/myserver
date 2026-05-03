# GuidlineSearch アプリ仕様書

金融庁「金融分野におけるサイバーセキュリティに関するガイドライン」をセマンティック検索する iOS アプリ。

## 概要

| 項目 | 内容 |
|------|------|
| プラットフォーム | iOS 17.0+ |
| 言語 | Swift 5.9 / SwiftUI |
| Bundle ID | `com.hoshinoji.guidelinesearch` |
| ビルドツール | XcodeGen (`project.yml`) |
| バックエンド | `guidline-api`（`guideline-api.md` 参照） |

## ディレクトリ構成

```
GuidlineSearch/
├── DESIGN.md                        # デザイン仕様（カラー・タイポ・コンポーネント）
├── GuidlineSearch.md                # 本仕様書
├── project.yml                      # XcodeGen プロジェクト定義
├── GuidlineSearch.xcodeproj/        # xcodegen generate で生成
└── Sources/
    ├── App.swift
    ├── Assets.xcassets/
    ├── Models/
    │   └── GuidelineModels.swift
    ├── Services/
    │   └── SearchAPIService.swift
    ├── ViewModels/
    │   └── SearchViewModel.swift
    └── Views/
        ├── ContentView.swift
        ├── DesignTokens.swift
        ├── DetailView.swift
        ├── GuidelineMarkdownView.swift
        ├── RequirementBadgeView.swift
        ├── ResultCardView.swift
        ├── ScoreBadgeView.swift
        └── SearchBarView.swift
```

## アーキテクチャ

```
ContentView
  └── EnvironmentObject: SearchViewModel (@MainActor ObservableObject)
        └── SearchAPIService (actor)
              └── POST http://localhost:8001/search
```

MVVM パターン。ViewModel は `@MainActor` で UI スレッドに固定し、API 呼び出しは `async/await` で非同期実行する。

## データモデル（`GuidelineModels.swift`）

### SearchRequest

```swift
struct SearchRequest: Encodable {
    let query: String   // 検索キーワード
    let top_k: Int      // 返却件数
}
```

### SearchResult

```swift
struct SearchResult: Decodable, Identifiable, Hashable {
    var id: String { section_id + requirement_type + title }
    let section_id: String        // "2.3.1"
    let title: String             // "2.3.1. 認証・アクセス管理"
    let text: String              // チャンク本文
    let snippet: String           // 先頭200文字プレビュー
    let similarity_score: Double  // 類似度スコア（0〜100）
    let requirement_type: String  // "basic" | "desirable" | "general"
    let breadcrumb: String        // "2. ... > 2.3. ... > 2.3.1. ..."
    let footnotes: [Footnote]
    var requirementKind: RequirementKind  // 計算プロパティ
}
```

### RequirementKind

| 値 | `requirement_type` | バッジ表示 |
|----|-------------------|-----------|
| `.basic` | `"basic"` | 「基本対応」（青） |
| `.desirable` | `"desirable"` | 「望ましい対応」（緑） |
| `.general` | `"general"` | 非表示 |

## API クライアント（`SearchAPIService.swift`）

```swift
actor SearchAPIService {
    static let shared = SearchAPIService()
    private let baseURL = URL(string: "http://localhost:8001")!

    func search(query: String, topK: Int = 5) async throws -> SearchResponse
}
```

- `actor` でスレッドセーフを保証
- `POST /search` に JSON ボディを送信、`JSONDecoder` でデコード
- タイムアウト: 30 秒
- エラー型: `APIError`（`networkError` / `httpError` / `decodingError`）

**接続先の変更**（`SearchAPIService.swift:27`）:

| 環境 | URL |
|------|-----|
| シミュレータ（開発） | `http://localhost:8001` |
| 実機（同一 LAN） | `http://<MacのIP>:8001` |
| Caddy 経由 | `http://<サーバーIP>/guideline` |
| Tailscale 経由 | `http://<TailscaleIP>/guideline` |

## ViewModel（`SearchViewModel.swift`）

```swift
@MainActor
final class SearchViewModel: ObservableObject {
    @Published var query: String          // 検索クエリ
    @Published var results: [SearchResult] // 検索結果
    @Published var isLoading: Bool         // ローディング状態
    @Published var errorMessage: String?   // エラーメッセージ
    @Published var selectedResult: SearchResult?  // 詳細表示中の結果
    @Published var totalChunks: Int        // インデックス総チャンク数

    func search()      // 検索実行（query が空なら無視）
    func clearError()  // エラー状態をリセット
}
```

## 画面構成

### ContentView（検索画面）

```
NavigationStack
├── SearchBarView          ← query バインディング + onSubmit
├── Divider
└── 状態に応じたコンテンツ
    ├── isLoading == true  → ProgressView + "検索中…"
    ├── errorMessage != nil → エラー表示 + 再試行ボタン
    ├── results.isEmpty && query != "" → 空状態
    └── それ以外 → ScrollView / LazyVStack
            └── ResultCardView × results.count
                    .onTapGesture → selectedResult = result
```

`navigationDestination(item: $vm.selectedResult)` で詳細画面へ遷移。

### ResultCardView（検索結果カード）

```
VStack
├── HStack
│   ├── title（Deep Navy, 16pt semibold）
│   └── ScoreBadgeView（右端）
├── breadcrumb（グレー, 11pt, 最大2行）
├── RequirementBadgeView（capsule pill）
└── snippet（14pt, ハイライト付き, 最大4行）
```

スニペットのハイライト: クエリを空白分割したキーワードごとに `AttributedString` で `backgroundColor` を黄色に設定。

カードスタイル: `RoundedRectangle(cornerRadius: 8)`、`glOutlineVariant` 1px ボーダー、影なし（フラットデザイン）。

### DetailView（詳細・全文表示）

```
NavigationBar: "<section_id> <title>" (inline)
ScrollView
├── breadcrumb（12pt）
├── RequirementBadgeView
├── Divider
├── GuidelineMarkdownView(text: result.text)
└── footnotes が存在する場合:
    └── Divider + DisclosureGroup("脚注 (N件)")
            └── ForEach(footnotes) { ref: 40pt固定, text: 残り }
```

### GuidelineMarkdownView（Markdown レンダラー）

ガイドライン本文を構造化 Markdown としてレンダリングするカスタムビュー。

**対応する構文**

| 構文 | 処理 |
|------|------|
| `- text`（インデント 0） | 箇条書き（`•` 付き） |
| `    - text`（4スペース = 1段） | ネスト箇条書き（16pt 左パディング × 段数） |
| `①②③` など（U+2460〜U+24FF）で始まる項目 | `•` を付けずそのまま表示 |
| `**bold**`, `_italic_` | `AttributedString(markdown:)` でインライン適用 |
| `[^N]` 脚注参照 | 正規表現で除去（脚注本文は DisclosureGroup に別表示） |
| 空行 | 段落区切り |

**実装概要**（`GuidelineMarkdownView.swift`）

```swift
// 行を Block（paragraph / listItem）に変換し LazyVStack でレンダリング
// インライン書式は AttributedString(markdown:, options: .inlineOnlyPreservingWhitespace) を使用
// タブ → 4スペース正規化後に leadingSpaces / 4 でインデント算出
```

### SearchBarView

- `magnifyingglass` システムアイコン（先頭）
- `TextField`（`.submitLabel(.search)`、`.autocorrectionDisabled()`）
- クリアボタン（`xmark.circle.fill`、text が空でない場合）
- スタイル: `glOutlineVariant` 1px ボーダー、`cornerRadius: 6`

### RequirementBadgeView

| `RequirementKind` | 背景 | テキスト |
|-------------------|------|---------|
| `.basic` | `#D6E3FF` | `#001B3C` |
| `.desirable` | `#D4EDDA` | `#1A5C2A` |
| `.general` | 非表示 | — |

## デザイントークン（`DesignTokens.swift`）

DESIGN.md の Material Design 3 ベーストークンを Swift 定数として定義。

| トークン | 値 | 用途 |
|---------|-----|------|
| `Color.glPrimary` | `#002045` | タイトル、ナビゲーション |
| `Color.glSurface` | `#FAF9FD` | 背景全般 |
| `Color.glOnSurface` | `#1A1C1E` | 本文テキスト |
| `Color.glOnSurfaceVariant` | `#43474E` | サブテキスト、メタ情報 |
| `Color.glOutlineVariant` | `#C4C6CF` | カードボーダー |
| `Color.glSurfaceContainer` | `#EFEDF1` | スコアバッジ背景 |
| `Spacing.sm` | 8pt | 基本グリッド単位 |
| `Spacing.md` | 16pt | 標準パディング |
| `Spacing.lg` | 24pt | セクション間余白 |
| `Radius.lg` | 8pt | カード角丸 |

## ビルド手順

```bash
cd GuidlineSearch

# プロジェクト生成（初回・project.yml 変更後）
xcodegen generate

# Xcode で開く
open GuidlineSearch.xcodeproj
```

実行前に `guidline-api` コンテナが起動済みであること:

```bash
# プロジェクトルートで
docker compose up guideline-api -d

# ヘルスチェック
curl http://localhost:8001/health
# → {"status":"ok","chunks":66}
```

## Info.plist 設定

`project.yml` に以下を設定済み（`NSAppTransportSecurity`）:

```yaml
NSAppTransportSecurity:
  NSAllowsLocalNetworking: true
```

これにより HTTP での `localhost` 通信が許可される。本番環境では HTTPS エンドポイントに切り替えること。

## 既知の制限・今後の課題

- `baseURL` がハードコードされているため、サーバー URL を変更する際はコードの修正が必要
- 検索はサブミット時のみ実行（入力中のリアルタイム検索なし）
- オフライン時のエラー表示はあるが、キャッシュ機能なし
- アプリアイコン未設定（`Assets.xcassets/AppIcon.appiconset` はプレースホルダー）
