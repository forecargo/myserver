import Foundation

// kobun-api（FastAPI）のレスポンスと 1:1 対応する Codable DTO。
// フィールド名は API の snake_case に合わせる（CodingKeys 不要）。
// 詳細系は response_model_exclude_none=True のため null 許容フィールドは欠落しうる → Optional。

struct Meaning: Codable, Hashable {
    var no: Int?
    var gloss: String
}

// MARK: - 単語

struct WordListItem: Codable, Hashable, Identifiable {
    var entry_no: String
    var section: String
    var pos_category: String?
    var headword: String
    var reading: String?
    var image_url: String?
    var short_gloss: String
    var id: String { entry_no }
}

struct SemanticShift: Codable, Hashable {
    var modern: String?
    var classical: String?
}

struct Honorific: Codable, Hashable {
    var type: String
    var base_word: String?
}

struct RelatedWord: Codable, Hashable {
    var marker: String?
    var word: String?
    var reading: String?
    var meanings: [Meaning]?
}

struct Example: Codable, Hashable {
    var sense_no: Int?
    var marker: String?
    var text: String
    var target_words: [String]?
    var translation: String?
    var source: String?
}

struct MistakeNote: Codable, Hashable {
    var wrong: String?
    var correct: String?
    var note: String?
}

struct WordDetail: Codable, Hashable, Identifiable {
    var entry_no: String
    var section: String
    var pos_category: String?
    var headword: String
    var reading: String?
    var image_url: String?
    var headword_variants: [String]?
    var sub_glosses: [String]?
    var conjugation_type: String?
    var meanings: [Meaning]?
    var word_formation: String?
    var semantic_shift: SemanticShift?
    var honorific: Honorific?
    var related_words: [RelatedWord]?
    var commentary: String?
    var examples: [Example]?
    var mistake_note: MistakeNote?
    var tip_box: String?
    var qr_code: Bool?
    var pages: [Int]?
    var id: String { entry_no }
}

struct WordListResponse: Codable {
    var total: Int
    var limit: Int?
    var offset: Int
    var items: [WordListItem]
}

// MARK: - 慣用句

struct IdiomListItem: Codable, Hashable, Identifiable {
    var idiom_id: String
    var headword: String
    var reading: String?
    var image_url: String?
    var short_gloss: String
    var id: String { idiom_id }
}

struct IdiomSense: Codable, Hashable {
    var label: String?
    var writing: String?
    var meanings: [Meaning]?
}

struct IdiomExample: Codable, Hashable {
    var sense_label: String?
    var marker: String?
    var text: String
    var target_words: [String]?
    var translation: String?
    var source: String?
}

struct IdiomDetail: Codable, Hashable, Identifiable {
    var idiom_id: String
    var headword: String
    var reading: String?
    var image_url: String?
    var meanings: [Meaning]?
    var senses: [IdiomSense]?
    var commentary: String?
    var examples: [IdiomExample]?
    var related: [RelatedWord]?
    var printed_page: Int?
    var id: String { idiom_id }
}

struct IdiomListResponse: Codable {
    var total: Int
    var limit: Int?
    var offset: Int
    var items: [IdiomListItem]
}

// MARK: - 横断検索

struct SearchResponse: Codable {
    var words: [WordListItem]
    var idioms: [IdiomListItem]
}

// MARK: - メタ

struct PosCount: Codable, Hashable, Identifiable {
    var key: String
    var count: Int
    var id: String { key }
}

struct SectionMeta: Codable, Hashable, Identifiable {
    var key: String
    var label: String
    var type: String
    var count: Int
    var pos: [PosCount]?
    var id: String { key }
}

struct MetaResponse: Codable {
    var words: Int
    var idioms: Int
    var sections: [SectionMeta]
}

// MARK: - クイズ

struct QuizPrompt: Codable, Hashable {
    var headword: String
    var reading: String?
}

struct QuizChoice: Codable, Hashable, Identifiable {
    var index: Int
    var gloss: String
    var id: Int { index }
}

struct QuizQuestion: Codable, Hashable, Identifiable {
    var question_id: String
    var entry_no: String
    var pos_category: String?
    var prompt: QuizPrompt
    var choices: [QuizChoice]
    var answer_index: Int
    var id: String { question_id }
}

struct QuizResponse: Codable {
    var count: Int
    var questions: [QuizQuestion]
}

// MARK: - ヘルス

struct HealthResponse: Codable {
    var status: String
    var words: Int
    var idioms: Int
}
