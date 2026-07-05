import Foundation
import SwiftData

/// 学習状態（API 範囲外・端末保持）。
enum LearnStatus: String, Codable, CaseIterable {
    case unlearned  // 未学習
    case learning   // 学習中
    case mastered   // 覚えた
}

/// 単語/慣用句ごとの学習進捗・SRS 状態。同定キーは entry_no または idiom_id。
@Model
final class WordProgress {
    @Attribute(.unique) var key: String
    var statusRaw: String = LearnStatus.unlearned.rawValue
    var ease: Double = 2.5
    var intervalDays: Int = 0
    var dueDate: Date?
    var lastReviewedAt: Date?
    var correctStreak: Int = 0
    var isFavorite: Bool = false
    var inFlashcardDeck: Bool = false

    init(key: String) {
        self.key = key
    }

    var status: LearnStatus {
        get { LearnStatus(rawValue: statusRaw) ?? .unlearned }
        set { statusRaw = newValue.rawValue }
    }
}

/// クイズ回答履歴。
@Model
final class QuizAttempt {
    var questionKey: String = ""
    var isCorrect: Bool = false
    var answeredAt: Date = Date.now

    init(questionKey: String, isCorrect: Bool, answeredAt: Date = .now) {
        self.questionKey = questionKey
        self.isCorrect = isCorrect
        self.answeredAt = answeredAt
    }
}

/// 1 日の学習量（達成リング・連続日数の算出用）。
@Model
final class DailyStudyLog {
    @Attribute(.unique) var dayKey: String = ""  // "yyyy-MM-dd"
    var learnedCount: Int = 0

    init(dayKey: String, learnedCount: Int = 0) {
        self.dayKey = dayKey
        self.learnedCount = learnedCount
    }
}

/// 日付キーのユーティリティ。
enum DayKey {
    static func string(for date: Date) -> String {
        let f = DateFormatter()
        f.calendar = Calendar(identifier: .gregorian)
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: date)
    }

    static var today: String { string(for: .now) }
}
