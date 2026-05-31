import XCTest
@testable import TangoApp

final class QuizGeneratorTests: XCTestCase {

    private func makeItem(id: String, word: String, meaning: String, pos: String = "名詞", level: String? = nil) -> APIVocabularyItem {
        APIVocabularyItem(
            id: id,
            word: word,
            phonetic: "[\(word)]",
            level_tag: level,
            definitions: [APIMeaningGroup(part_of_speech: pos, meanings: [meaning])],
            usages_and_notes: [],
            word_origin: nil,
            examples: []
        )
    }

    private func makeDomain(_ item: APIVocabularyItem, batch: String = "part1", stem: String = "LEAP - part1 - 01") -> DomainWord {
        DomainWord(batch: batch, stem: stem, item: item)
    }

    private func makePool(size: Int) -> [DomainWord] {
        (0..<size).map { i in
            let item = makeItem(id: String(format: "%03d", i), word: "w\(i)", meaning: "意味\(i)")
            return makeDomain(item)
        }
    }

    func testInsufficientPoolThrows() {
        let pool = makePool(size: 3)
        XCTAssertThrowsError(
            try QuizGenerator.makeQuestions(pool: pool, count: 4, seed: 1)
        ) { error in
            guard case QuizGenerator.QuizError.insufficientPool = error else {
                return XCTFail("Expected insufficientPool, got \(error)")
            }
        }
    }

    func testSeedProducesReproducibleQuestions() throws {
        let pool = makePool(size: 20)
        let qs1 = try QuizGenerator.makeQuestions(pool: pool, count: 5, seed: 42)
        let qs2 = try QuizGenerator.makeQuestions(pool: pool, count: 5, seed: 42)
        XCTAssertEqual(qs1.count, qs2.count)
        for (a, b) in zip(qs1, qs2) {
            XCTAssertEqual(a.promptDomain.id, b.promptDomain.id)
            XCTAssertEqual(a.choices, b.choices)
            XCTAssertEqual(a.correctIndex, b.correctIndex)
        }
    }

    func testEachQuestionHasFourUniqueChoices() throws {
        let pool = makePool(size: 30)
        let questions = try QuizGenerator.makeQuestions(pool: pool, count: 10, seed: 7)
        for q in questions {
            XCTAssertEqual(q.choices.count, 4)
            XCTAssertEqual(Set(q.choices).count, 4, "choices must be unique")
            XCTAssertTrue((0..<4).contains(q.correctIndex))
            XCTAssertEqual(q.choices[q.correctIndex], q.item.definitions[0].meanings[0])
        }
    }

    func testPartOfSpeechPrioritization() throws {
        let verbs = (0..<4).map { makeDomain(makeItem(id: "v\($0)", word: "verb\($0)", meaning: "動詞意味\($0)", pos: "動詞")) }
        let nouns = (0..<4).map { makeDomain(makeItem(id: "n\($0)", word: "noun\($0)", meaning: "名詞意味\($0)", pos: "名詞")) }
        let pool = verbs + nouns
        let questions = try QuizGenerator.makeQuestions(pool: pool, count: 4, seed: 99)
        let verbQuestion = questions.first { $0.item.definitions[0].part_of_speech == "動詞" }
        guard let q = verbQuestion else { return }
        let verbMeanings = Set(verbs.map { $0.item.definitions[0].meanings[0] })
        let verbDummies = q.choices.filter { verbMeanings.contains($0) }.count
        XCTAssertGreaterThanOrEqual(verbDummies, 3)
    }
}
