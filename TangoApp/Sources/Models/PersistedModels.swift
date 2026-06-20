import Foundation
import SwiftData

// SwiftData Schema V1。学習進捗 (ユーザー固有データ) のみを永続化する。
// 単語データ本体は API メモリキャッシュに留める (SPEC_SwiftUI.md §11)。

@Model
final class WordProgress {
    @Attribute(.unique) var key: String
    var batch: String
    var stem: String
    var wordId: String
    var wordSnapshot: String
    var phoneticSnapshot: String
    var isFavorite: Bool
    var isLearned: Bool
    var viewCount: Int
    var lastViewedAt: Date?
    var correctCount: Int
    var wrongCount: Int
    /// クイズの連続記録。正なら連続正解数、負なら連続不正解数、0 は記録なし。
    /// 後付けフィールドのため宣言側に `= 0` の既定値が必須 (SwiftData 軽量マイグレーション要件)。
    var currentStreak: Int = 0
    var note: String

    init(
        key: String,
        batch: String,
        stem: String,
        wordId: String,
        wordSnapshot: String,
        phoneticSnapshot: String,
        isFavorite: Bool = false,
        isLearned: Bool = false,
        viewCount: Int = 0,
        lastViewedAt: Date? = nil,
        correctCount: Int = 0,
        wrongCount: Int = 0,
        currentStreak: Int = 0,
        note: String = ""
    ) {
        self.key = key
        self.batch = batch
        self.stem = stem
        self.wordId = wordId
        self.wordSnapshot = wordSnapshot
        self.phoneticSnapshot = phoneticSnapshot
        self.isFavorite = isFavorite
        self.isLearned = isLearned
        self.viewCount = viewCount
        self.lastViewedAt = lastViewedAt
        self.correctCount = correctCount
        self.wrongCount = wrongCount
        self.currentStreak = currentStreak
        self.note = note
    }
}

extension WordProgress {
    /// 3 連続正解で自動既習化する閾値
    static let autoLearnThreshold = 3
    /// 3 連敗で警告マークを出す閾値
    static let warnLosingStreakThreshold = 3

    var shouldShowWarning: Bool {
        currentStreak <= -Self.warnLosingStreakThreshold
    }
}

@Model
final class QuizAttempt {
    var startedAt: Date
    var finishedAt: Date?
    var batch: String
    var stem: String?
    var totalQuestions: Int
    var correctAnswers: Int

    init(
        startedAt: Date,
        finishedAt: Date? = nil,
        batch: String,
        stem: String? = nil,
        totalQuestions: Int,
        correctAnswers: Int
    ) {
        self.startedAt = startedAt
        self.finishedAt = finishedAt
        self.batch = batch
        self.stem = stem
        self.totalQuestions = totalQuestions
        self.correctAnswers = correctAnswers
    }
}
