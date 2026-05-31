import Foundation
import Observation
import SwiftData

@MainActor
@Observable
final class QuizViewModel {

    enum Phase {
        case setup
        case loading
        case running
        case finished
    }

    // セットアップ
    var availableBatches: [String] = []
    var selectedBatch: String?
    var questionCount: Int = 10
    var filterFavoritesOnly: Bool = false
    var filterUnlearnedOnly: Bool = false

    // ランタイム
    var phase: Phase = .setup
    var loadProgress: Double = 0
    var errorMessage: String?
    var questions: [QuizGenerator.Question] = []
    var currentIndex: Int = 0
    var selectedChoice: Int?
    var correctCount: Int = 0
    var wrongDomains: [DomainWord] = []

    private let api = TangoAPIService.shared

    var currentQuestion: QuizGenerator.Question? {
        guard currentIndex < questions.count else { return nil }
        return questions[currentIndex]
    }

    var progressText: String {
        "\(min(currentIndex + 1, questions.count)) / \(questions.count)"
    }

    var accuracyPercent: Int {
        guard !questions.isEmpty else { return 0 }
        return Int(round(Double(correctCount) / Double(questions.count) * 100))
    }

    // MARK: - セットアップフェーズ

    func loadBatches() async {
        do {
            availableBatches = try await api.listBatches()
            if selectedBatch == nil {
                selectedBatch = availableBatches.first
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    // MARK: - 開始

    func start(context: ModelContext) async {
        guard let batch = selectedBatch else { return }
        phase = .loading
        loadProgress = 0
        errorMessage = nil
        do {
            // バッチ全ファイルをロードして [DomainWord] プールを構築
            let files = try await api.listFiles(batch: batch)
            let usableFiles = files.filter { $0.count > 0 }
            var pool: [DomainWord] = []
            for (idx, f) in usableFiles.enumerated() {
                do {
                    let result = try await api.loadData(batch: batch, stem: f.stem)
                    for item in result.vocabulary_list {
                        pool.append(DomainWord(batch: batch, stem: f.stem, item: item))
                    }
                } catch {
                    continue
                }
                loadProgress = Double(idx + 1) / Double(max(usableFiles.count, 1))
            }

            // SwiftData フィルタ
            if filterFavoritesOnly || filterUnlearnedOnly {
                pool = filterByProgress(pool: pool, context: context)
            }

            self.questions = try QuizGenerator.makeQuestions(
                pool: pool,
                count: questionCount
            )
            currentIndex = 0
            correctCount = 0
            wrongDomains = []
            selectedChoice = nil
            phase = .running
        } catch {
            errorMessage = error.localizedDescription
            phase = .setup
        }
    }

    private func filterByProgress(
        pool: [DomainWord],
        context: ModelContext
    ) -> [DomainWord] {
        let descriptor = FetchDescriptor<WordProgress>()
        let progresses = (try? context.fetch(descriptor)) ?? []
        var byKey: [String: WordProgress] = [:]
        for p in progresses { byKey[p.key] = p }

        let filtered = pool.filter { domain in
            guard let p = byKey[domain.id] else {
                // 進捗未登録の単語は「未習」扱いだが、「お気に入りのみ」フィルタ時は除外
                if filterFavoritesOnly { return false }
                return true
            }
            if filterFavoritesOnly && !p.isFavorite { return false }
            if filterUnlearnedOnly && p.isLearned { return false }
            return true
        }
        // フィルタで 0 件 ÷ 元プールに戻すと意図に反するので、空のまま投げて UI でエラー表示
        return filtered
    }

    // MARK: - 回答

    func answer(choice: Int, context: ModelContext) {
        guard let q = currentQuestion, selectedChoice == nil else { return }
        selectedChoice = choice
        let isCorrect = choice == q.correctIndex
        if isCorrect {
            correctCount += 1
            FeedbackService.shared.playCorrect()
        } else {
            wrongDomains.append(q.promptDomain)
            FeedbackService.shared.playWrong()
        }
        recordProgress(for: q.promptDomain, isCorrect: isCorrect, context: context)
    }

    func next(context: ModelContext) {
        selectedChoice = nil
        if currentIndex + 1 >= questions.count {
            saveAttempt(context: context)
            phase = .finished
        } else {
            currentIndex += 1
        }
    }

    func restart() {
        questions = []
        currentIndex = 0
        correctCount = 0
        wrongDomains = []
        selectedChoice = nil
        phase = .setup
    }

    /// 実行中のクイズを中断して setup へ戻す。
    /// クイズ履歴 (`QuizAttempt`) は保存せず、各問の `WordProgress` 加算のみ残る。
    func abort() {
        SpeechService.shared.stop()
        restart()
    }

    // MARK: - 永続化

    private func recordProgress(for domain: DomainWord, isCorrect: Bool, context: ModelContext) {
        let key = domain.id
        let descriptor = FetchDescriptor<WordProgress>(
            predicate: #Predicate { $0.key == key }
        )
        let progress: WordProgress
        if let existing = try? context.fetch(descriptor).first {
            progress = existing
        } else {
            progress = WordProgress(
                key: key,
                batch: domain.batch,
                stem: domain.stem,
                wordId: domain.item.id,
                wordSnapshot: domain.item.word,
                phoneticSnapshot: domain.item.phonetic
            )
            context.insert(progress)
        }
        if isCorrect {
            progress.correctCount += 1
        } else {
            progress.wrongCount += 1
            // 復習リストで間違えた直後の単語が上位に来るよう、最終閲覧時刻も更新する。
            progress.lastViewedAt = .now
            // 既習にしていてもクイズで間違えたら未習に戻し、復習対象に復活させる。
            progress.isLearned = false
        }
        try? context.save()
    }

    private func saveAttempt(context: ModelContext) {
        guard let batch = selectedBatch else { return }
        let attempt = QuizAttempt(
            startedAt: Date().addingTimeInterval(-Double(questions.count * 10)),
            finishedAt: .now,
            batch: batch,
            stem: nil,
            totalQuestions: questions.count,
            correctAnswers: correctCount
        )
        context.insert(attempt)
        try? context.save()
    }
}
