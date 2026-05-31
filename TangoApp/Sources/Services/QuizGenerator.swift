import Foundation

// 4 択クイズの問題生成。純粋関数として実装し、seed 指定で再現可能にする。
// 詳細: SPEC_SwiftUI.md §8.3

struct QuizGenerator {

    struct Question: Identifiable, Hashable {
        let id: UUID
        let promptDomain: DomainWord
        let choices: [String]              // 4 件、シャッフル済み (日本語 meaning)
        let correctIndex: Int

        var correctText: String { choices[correctIndex] }
        var item: APIVocabularyItem { promptDomain.item }
    }

    enum QuizError: Error, LocalizedError {
        case insufficientPool

        var errorDescription: String? {
            switch self {
            case .insufficientPool:
                return "プールに 4 単語以上必要です。"
            }
        }
    }

    static func makeQuestions(
        pool: [DomainWord],
        count: Int,
        seed: UInt64? = nil
    ) throws -> [Question] {
        guard pool.count >= 4 else { throw QuizError.insufficientPool }
        guard count > 0 else { return [] }

        var rng: any RandomNumberGenerator = seed.map { SeededGenerator(seed: $0) }
            ?? SeededGenerator(seed: UInt64.random(in: 0..<UInt64.max))

        let take = min(count, pool.count)
        let targets = shuffled(pool, using: &rng).prefix(take)

        var questions: [Question] = []
        for target in targets {
            let dummies = pickDummies(for: target, pool: pool, rng: &rng)
            let correct = firstMeaning(of: target.item)
            var choices = dummies + [correct]
            choices = shuffled(choices, using: &rng)
            let correctIndex = choices.firstIndex(of: correct) ?? 0
            questions.append(Question(
                id: UUID(),
                promptDomain: target,
                choices: choices,
                correctIndex: correctIndex
            ))
        }
        return questions
    }

    // MARK: - 内部

    private static func firstMeaning(of item: APIVocabularyItem) -> String {
        let raw = item.definitions.first?.meanings.first
            ?? item.definitions.first.map { "(\($0.part_of_speech))" }
            ?? "—"
        return stripLeadingCircledNumber(raw)
    }

    /// クイズ選択肢用に、文字列先頭の丸数字 (①〜⑳) と続く空白を除去する。
    /// 例: "①〜を申し出る" → "〜を申し出る"
    private static func stripLeadingCircledNumber(_ text: String) -> String {
        var s = Substring(text)
        let circled: ClosedRange<Character> = "①"..."⑳"
        while let first = s.first, circled.contains(first) {
            s = s.dropFirst()
            s = s.drop(while: { $0.isWhitespace })
        }
        return String(s)
    }

    private static func pickDummies(
        for target: DomainWord,
        pool: [DomainWord],
        rng: inout any RandomNumberGenerator
    ) -> [String] {
        let correct = firstMeaning(of: target.item)
        let candidates = pool.filter { $0.id != target.id }

        let targetPOS = target.item.definitions.first?.part_of_speech
        let targetLevel = target.item.level_tag

        let tier1 = candidates.filter {
            $0.item.definitions.first?.part_of_speech == targetPOS && $0.item.level_tag == targetLevel
        }
        let tier2 = candidates.filter {
            $0.item.definitions.first?.part_of_speech == targetPOS
        }

        var picked: [String] = []
        var seen: Set<String> = [correct]

        for tier in [tier1, tier2, candidates] {
            if picked.count >= 3 { break }
            let shuffledTier = shuffled(tier, using: &rng)
            for cand in shuffledTier {
                if picked.count >= 3 { break }
                let m = firstMeaning(of: cand.item)
                if seen.contains(m) { continue }
                picked.append(m)
                seen.insert(m)
            }
        }
        return picked
    }

    private static func shuffled<T>(
        _ array: some Collection<T>,
        using rng: inout any RandomNumberGenerator
    ) -> [T] {
        var result = Array(array)
        for i in stride(from: result.count - 1, through: 1, by: -1) {
            let j = Int(rng.next() % UInt64(i + 1))
            result.swapAt(i, j)
        }
        return result
    }
}

struct SeededGenerator: RandomNumberGenerator {
    private var state: UInt64

    init(seed: UInt64) {
        self.state = seed != 0 ? seed : 0xDEADBEEFCAFEBABE
    }

    mutating func next() -> UInt64 {
        state ^= state >> 12
        state ^= state << 25
        state ^= state >> 27
        return state &* 0x2545F4914F6CDD1D
    }
}
