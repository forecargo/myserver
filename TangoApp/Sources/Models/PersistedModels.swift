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
        self.note = note
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
