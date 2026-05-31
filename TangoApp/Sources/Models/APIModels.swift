import Foundation

// tango/models.py (Pydantic) と 1:1 対応する Codable 型。
// フィールド名はスネークケースのまま (CodingKeys 省略)。
// 詳細: SPEC_SwiftUI.md §5

struct APIVocabularyResult: Codable, Hashable {
    let vocabulary_list: [APIVocabularyItem]
}

struct APIVocabularyItem: Codable, Identifiable, Hashable {
    let id: String                       // "001" のゼロパディング維持
    let word: String
    let phonetic: String
    let level_tag: String?
    let definitions: [APIMeaningGroup]
    let usages_and_notes: [String]
    let word_origin: APIWordOrigin?
    let examples: [APIExampleSentence]
}

struct APIMeaningGroup: Codable, Hashable {
    let part_of_speech: String
    let meanings: [String]
}

struct APIWordOrigin: Codable, Hashable {
    let formula: String?
    let description: String?
}

struct APIExampleSentence: Codable, Hashable {
    let en: String
    let ja: String
}

struct APIFileEntry: Codable, Hashable {
    let stem: String
    let count: Int          // -1 は viewer.py 側のパース失敗
    let has_image: Bool
}

enum TangoAPIError: LocalizedError {
    case invalidBaseURL
    case networkError(Error)
    case httpError(Int, String)
    case decodingError(error: Error, url: URL, bodyPreview: String)
    case batchNotFound(String)
    case fileNotFound(batch: String, stem: String)

    var errorDescription: String? {
        switch self {
        case .invalidBaseURL:
            return "API URL が不正です。設定画面を確認してください。"
        case .networkError(let err):
            return "通信エラー: \(err.localizedDescription)"
        case .httpError(let code, let body):
            let snippet = String(body.prefix(200))
            return "サーバーエラー (\(code)): \(snippet)"
        case .decodingError(_, let url, let bodyPreview):
            return "JSON 解析失敗\nURL: \(url.absoluteString)\nレスポンス先頭: \(bodyPreview)"
        case .batchNotFound(let batch):
            return "バッチが見つかりません: \(batch)"
        case .fileNotFound(let batch, let stem):
            return "ファイルが見つかりません: \(batch)/\(stem)"
        }
    }
}
