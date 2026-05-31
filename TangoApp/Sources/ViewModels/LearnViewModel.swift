import Foundation
import Observation

@MainActor
@Observable
final class LearnViewModel {
    var favoriteWords: [DomainWord] = []
    var reviewWords: [DomainWord] = []
    var isLoading: Bool = false
    var errorMessage: String?

    private let api = TangoAPIService.shared

    func reload(progresses: [WordProgress]) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        let favs = progresses.filter { $0.isFavorite }
        // 復習対象 = 既習でなく、かつ「閲覧経験あり」もしくは「クイズで間違えた」単語。
        // クイズで間違えると QuizViewModel が isLearned を false に戻すので、再度復習に復活する。
        let reviews = progresses.filter {
            !$0.isLearned && ($0.viewCount > 0 || $0.wrongCount > 0)
        }

        async let resolvedFavs = resolve(progresses: favs)
        async let resolvedReviews = resolve(progresses: reviews)
        favoriteWords = await resolvedFavs
        reviewWords = await resolvedReviews
    }

    // MARK: - 内部

    private func resolve(progresses: [WordProgress]) async -> [DomainWord] {
        // (batch, stem) でグルーピングしてファイル単位で API を一度叩く。
        var byStem: [String: [WordProgress]] = [:]
        for p in progresses {
            let groupKey = "\(p.batch)\u{1F}\(p.stem)"
            byStem[groupKey, default: []].append(p)
        }

        // 並び順保持用のオリジナルインデックス
        var rank: [String: Int] = [:]
        for (idx, p) in progresses.enumerated() { rank[p.key] = idx }

        var domains: [DomainWord] = []
        for (groupKey, list) in byStem {
            let parts = groupKey.split(separator: "\u{1F}", maxSplits: 1)
            guard parts.count == 2 else { continue }
            let batch = String(parts[0])
            let stem = String(parts[1])
            do {
                let result = try await api.loadData(batch: batch, stem: stem)
                var itemsById: [String: APIVocabularyItem] = [:]
                for item in result.vocabulary_list { itemsById[item.id] = item }
                for p in list {
                    if let item = itemsById[p.wordId] {
                        domains.append(DomainWord(batch: batch, stem: stem, item: item))
                    }
                }
            } catch {
                continue
            }
        }

        // progresses の順 (lastViewedAt 降順) を維持
        domains.sort { (a, b) -> Bool in
            (rank[a.id] ?? Int.max) < (rank[b.id] ?? Int.max)
        }
        return domains
    }
}
