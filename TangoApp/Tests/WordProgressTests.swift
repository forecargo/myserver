import XCTest
import SwiftData
@testable import TangoApp

final class WordProgressTests: XCTestCase {

    @MainActor
    private func makeContext() throws -> ModelContext {
        let schema = Schema([WordProgress.self, QuizAttempt.self])
        let config = ModelConfiguration(isStoredInMemoryOnly: true)
        let container = try ModelContainer(for: schema, configurations: [config])
        return ModelContext(container)
    }

    @MainActor
    func testInsertAndFetch() throws {
        let context = try makeContext()
        let p = WordProgress(
            key: "part1::LEAP - part1 - 01::001",
            batch: "part1",
            stem: "LEAP - part1 - 01",
            wordId: "001",
            wordSnapshot: "agree",
            phoneticSnapshot: "[əgríː]",
            isFavorite: true
        )
        context.insert(p)
        try context.save()

        let descriptor = FetchDescriptor<WordProgress>()
        let fetched = try context.fetch(descriptor)
        XCTAssertEqual(fetched.count, 1)
        XCTAssertEqual(fetched.first?.wordSnapshot, "agree")
        XCTAssertTrue(fetched.first?.isFavorite ?? false)
    }

    @MainActor
    func testToggleFavorite() throws {
        let context = try makeContext()
        let p = WordProgress(
            key: "k",
            batch: "b",
            stem: "s",
            wordId: "1",
            wordSnapshot: "w",
            phoneticSnapshot: "p"
        )
        context.insert(p)
        XCTAssertFalse(p.isFavorite)
        p.isFavorite.toggle()
        XCTAssertTrue(p.isFavorite)
        try context.save()
    }

    @MainActor
    func testKeyMustBeUnique() throws {
        let context = try makeContext()
        let key = "part1::file::001"
        context.insert(WordProgress(key: key, batch: "part1", stem: "file", wordId: "001", wordSnapshot: "w", phoneticSnapshot: "p"))
        try context.save()

        // 同一キーで 2 件目を挿入 → 制約違反で save が失敗する想定。
        context.insert(WordProgress(key: key, batch: "part1", stem: "file", wordId: "001", wordSnapshot: "w2", phoneticSnapshot: "p2"))
        XCTAssertThrowsError(try context.save())
    }

    // MARK: - クイズ自動既習化 (SPEC_SwiftUI.md §8.1 / §8.2)

    private func makeItem(id: String = "001", word: String = "test") -> APIVocabularyItem {
        APIVocabularyItem(
            id: id, word: word, phonetic: "[test]", level_tag: nil,
            definitions: [], usages_and_notes: [], word_origin: nil, examples: []
        )
    }

    private func makeDomain(id: String = "001") -> DomainWord {
        DomainWord(batch: "test", stem: "stem", item: makeItem(id: id))
    }

    private func makeQuestion(domain: DomainWord) -> QuizGenerator.Question {
        QuizGenerator.Question(
            id: UUID(), promptDomain: domain,
            choices: ["A", "B", "C", "D"], correctIndex: 0
        )
    }

    /// (A) 同一単語に 3 連続正解 → isLearned=true / currentStreak=3。
    @MainActor
    func testThreeConsecutiveCorrectOnSameWord_marksLearned() throws {
        let context = try makeContext()
        let vm = QuizViewModel()
        let domain = makeDomain()
        vm.questions = [makeQuestion(domain: domain), makeQuestion(domain: domain), makeQuestion(domain: domain)]
        vm.currentIndex = 0

        vm.answer(choice: 0, context: context); vm.next(context: context)
        vm.answer(choice: 0, context: context); vm.next(context: context)
        vm.answer(choice: 0, context: context)

        let fetched = try context.fetch(FetchDescriptor<WordProgress>())
        XCTAssertEqual(fetched.count, 1, "同じ key で 1 件に統合されているはず")
        XCTAssertEqual(fetched.first?.currentStreak, 3)
        XCTAssertTrue(fetched.first?.isLearned ?? false, "3 連勝で自動既習化されない")
    }

    /// (B) 別単語 3 つに 1 回ずつ正解 (= 1 セッション内 3 連続正解) → 自動既習化されない。
    @MainActor
    func testOneCorrectEachOnThreeWords_doesNotMarkLearned() throws {
        let context = try makeContext()
        let vm = QuizViewModel()
        let domains = (0..<3).map { makeDomain(id: String(format: "%03d", $0)) }
        vm.questions = domains.map { makeQuestion(domain: $0) }
        vm.currentIndex = 0

        vm.answer(choice: 0, context: context); vm.next(context: context)
        vm.answer(choice: 0, context: context); vm.next(context: context)
        vm.answer(choice: 0, context: context)

        let fetched = try context.fetch(FetchDescriptor<WordProgress>())
        XCTAssertEqual(fetched.count, 3)
        for p in fetched {
            XCTAssertEqual(p.currentStreak, 1, "別単語の連続正解は各単語 streak=1 にしかならない")
            XCTAssertFalse(p.isLearned)
        }
    }

    /// (リセット) 連勝 2 回 → 不正解 1 回 → 連勝 3 回で isLearned=true。
    @MainActor
    func testStreakResetAfterWrong_thenThreeMoreCorrect_marksLearned() throws {
        let context = try makeContext()
        let vm = QuizViewModel()
        let domain = makeDomain()
        vm.questions = (0..<6).map { _ in makeQuestion(domain: domain) }
        vm.currentIndex = 0

        vm.answer(choice: 0, context: context); vm.next(context: context)  // streak=1
        vm.answer(choice: 0, context: context); vm.next(context: context)  // streak=2
        vm.answer(choice: 1, context: context); vm.next(context: context)  // streak=-1
        vm.answer(choice: 0, context: context); vm.next(context: context)  // streak=1
        vm.answer(choice: 0, context: context); vm.next(context: context)  // streak=2
        vm.answer(choice: 0, context: context)                              // streak=3, isLearned=true

        let fetched = try context.fetch(FetchDescriptor<WordProgress>())
        XCTAssertEqual(fetched.count, 1)
        XCTAssertEqual(fetched.first?.currentStreak, 3)
        XCTAssertTrue(fetched.first?.isLearned ?? false)
    }

    @MainActor
    func testQuizAttemptInsert() throws {
        let context = try makeContext()
        context.insert(QuizAttempt(
            startedAt: Date(timeIntervalSince1970: 1_700_000_000),
            finishedAt: Date(timeIntervalSince1970: 1_700_000_100),
            batch: "part1",
            stem: nil,
            totalQuestions: 10,
            correctAnswers: 7
        ))
        try context.save()
        let attempts = try context.fetch(FetchDescriptor<QuizAttempt>())
        XCTAssertEqual(attempts.count, 1)
        XCTAssertEqual(attempts.first?.correctAnswers, 7)
    }
}
