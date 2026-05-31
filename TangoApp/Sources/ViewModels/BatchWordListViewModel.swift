import Foundation
import Observation

@MainActor
@Observable
final class BatchWordListViewModel {
    let batch: String
    var words: [DomainWord] = []
    var isLoading: Bool = false
    var loadProgress: Double = 0
    var errorMessage: String?
    var searchText: String = ""

    // 読込み診断: 失敗した stem と理由
    var failedStems: [(stem: String, reason: String)] = []
    var expectedCount: Int = 0
    var duplicateSkipCount: Int = 0
    // ファイル単位のズレ (listFiles の count と実際の vocabulary_list の差分、重複数)
    var perFileMismatch: [(stem: String, expected: Int, actualInPayload: Int, dups: Int)] = []

    private let api = TangoAPIService.shared

    init(batch: String) {
        self.batch = batch
    }

    var filteredWords: [DomainWord] {
        let q = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return words }
        let lower = q.lowercased()
        return words.filter { w in
            if w.item.word.lowercased().contains(lower) { return true }
            if w.item.phonetic.lowercased().contains(lower) { return true }
            for def in w.item.definitions {
                for m in def.meanings where m.lowercased().contains(lower) {
                    return true
                }
            }
            return false
        }
    }

    func load(forceRefresh: Bool = false) async {
        isLoading = true
        loadProgress = 0
        errorMessage = nil
        defer { isLoading = false }

        do {
            let files = try await api.listFiles(batch: batch, forceRefresh: forceRefresh)
            let usableFiles = files.filter { $0.count > 0 }
            expectedCount = usableFiles.reduce(0) { $0 + $1.count }
            failedStems = []
            duplicateSkipCount = 0
            perFileMismatch = []

            var all: [DomainWord] = []
            var seenWordIds: Set<String> = []
            for (idx, f) in usableFiles.enumerated() {
                do {
                    let result = try await api.loadData(batch: batch, stem: f.stem, forceRefresh: forceRefresh)
                    var fileDups = 0
                    for item in result.vocabulary_list {
                        if seenWordIds.contains(item.id) {
                            duplicateSkipCount += 1
                            fileDups += 1
                            continue
                        }
                        seenWordIds.insert(item.id)
                        all.append(DomainWord(batch: batch, stem: f.stem, item: item))
                    }
                    let actualInPayload = result.vocabulary_list.count
                    if fileDups > 0 || actualInPayload != f.count {
                        perFileMismatch.append((
                            stem: f.stem,
                            expected: f.count,
                            actualInPayload: actualInPayload,
                            dups: fileDups
                        ))
                    }
                } catch {
                    failedStems.append((stem: f.stem, reason: error.localizedDescription))
                    continue
                }
                loadProgress = Double(idx + 1) / Double(max(usableFiles.count, 1))
            }
            words = all
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
