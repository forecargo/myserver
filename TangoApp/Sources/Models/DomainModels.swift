import Foundation

// バッチ間の `id` 衝突を防ぐため、API 単語に batch/stem を付与した識別子型。

struct DomainWord: Identifiable, Hashable {
    let batch: String
    let stem: String
    let item: APIVocabularyItem

    var id: String { Self.makeKey(batch: batch, stem: stem, wordId: item.id) }

    static func makeKey(batch: String, stem: String, wordId: String) -> String {
        "\(batch)::\(stem)::\(wordId)"
    }
}

// 詳細画面用の文脈情報。左右スワイプで前後単語へ移動するため、
// バッチ横断の単語配列と開始インデックスを保持する。
struct WordDetailContext: Hashable {
    let words: [DomainWord]
    let startIndex: Int
}

// 画面遷移先 (NavigationStack.navigationDestination 用)。
// バッチ単位の統合表示 (`batchWords`) と詳細 (`wordDetail`) の 2 階層。
enum BrowseRoute: Hashable {
    case batchWords(batch: String)
    case wordDetail(WordDetailContext)
}

extension String {
    /// バッチ名を表示用に整形する。
    /// - "part1" → "Part.1"、"part12" → "Part.12"
    /// - "plusplpha" → "+α"
    /// マッチしない名前はそのまま返す。
    var formattedBatchName: String {
        if lowercased() == "plusalpha" {
            return "+α"
        }
        guard let regex = try? NSRegularExpression(
            pattern: #"^part(\d+)$"#,
            options: .caseInsensitive
        ) else { return self }
        let range = NSRange(startIndex..., in: self)
        if let match = regex.firstMatch(in: self, options: [], range: range),
           let numRange = Range(match.range(at: 1), in: self) {
            return "Part.\(self[numRange])"
        }
        return self
    }
}
