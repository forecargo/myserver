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
