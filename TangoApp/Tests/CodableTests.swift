import XCTest
@testable import TangoApp

final class CodableTests: XCTestCase {

    func testDecodeMinimalItem() throws {
        let json = """
        {
          "vocabulary_list": [
            {
              "id": "001",
              "word": "agree",
              "phonetic": "[əgríː]",
              "level_tag": "A1",
              "definitions": [
                { "part_of_speech": "自動詞", "meanings": ["①(with~)に同意する"] }
              ],
              "usages_and_notes": [],
              "word_origin": null,
              "examples": []
            }
          ]
        }
        """.data(using: .utf8)!

        let result = try JSONDecoder().decode(APIVocabularyResult.self, from: json)
        XCTAssertEqual(result.vocabulary_list.count, 1)
        let item = result.vocabulary_list[0]
        XCTAssertEqual(item.id, "001")
        XCTAssertEqual(item.word, "agree")
        XCTAssertEqual(item.level_tag, "A1")
        XCTAssertNil(item.word_origin)
        XCTAssertTrue(item.usages_and_notes.isEmpty)
        XCTAssertTrue(item.examples.isEmpty)
    }

    func testDecodeWithWordOriginAndExamples() throws {
        let json = """
        {
          "vocabulary_list": [
            {
              "id": "2090",
              "word": "epidemic",
              "phonetic": "[èpədémik]",
              "level_tag": "最難関",
              "definitions": [
                { "part_of_speech": "名詞", "meanings": ["流行病"] }
              ],
              "usages_and_notes": ["注: pandemic と区別"],
              "word_origin": {
                "formula": "epi-[上] + -dem-[民衆] -> 民衆の上に来る",
                "description": "democracy「民主主義」, pandemic「全世界的な流行」"
              },
              "examples": [
                { "en": "an epidemic of flu", "ja": "インフルエンザの流行" }
              ]
            }
          ]
        }
        """.data(using: .utf8)!

        let result = try JSONDecoder().decode(APIVocabularyResult.self, from: json)
        let item = result.vocabulary_list[0]
        XCTAssertEqual(item.id, "2090")
        XCTAssertEqual(item.word_origin?.formula?.contains("epi-"), true)
        XCTAssertEqual(item.examples.count, 1)
        XCTAssertEqual(item.examples[0].en, "an epidemic of flu")
    }

    func testRoundTripEncodingPreservesIdZeroPadding() throws {
        let original = APIVocabularyItem(
            id: "007",
            word: "see",
            phonetic: "[siː]",
            level_tag: nil,
            definitions: [APIMeaningGroup(part_of_speech: "他動詞", meanings: ["見る"])],
            usages_and_notes: [],
            word_origin: nil,
            examples: []
        )
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(APIVocabularyItem.self, from: data)
        XCTAssertEqual(decoded.id, "007")
        XCTAssertNil(decoded.level_tag)
        XCTAssertNil(decoded.word_origin)
    }

    func testFileEntryCountNegativeIsAllowed() throws {
        let json = """
        { "stem": "broken", "count": -1, "has_image": false }
        """.data(using: .utf8)!
        let entry = try JSONDecoder().decode(APIFileEntry.self, from: json)
        XCTAssertEqual(entry.count, -1)
    }
}
