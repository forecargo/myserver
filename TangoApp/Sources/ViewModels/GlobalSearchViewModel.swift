import Foundation
import Observation

// 単語帳トップ (BatchListView) の全バッチ横断検索用 ViewModel。
// 初回検索時に全バッチ・全ファイルの単語を一括ロードしてメモリに保持し、
// 以降はメモリ上でフィルタする。検索条件は BatchWordListViewModel と揃える
// (単語・発音・意味の部分一致、大文字小文字無視)。
@MainActor
@Observable
final class GlobalSearchViewModel {
    var searchText: String = ""
    var allWords: [DomainWord] = []
    var isLoading: Bool = false
    var loadProgress: Double = 0
    var errorMessage: String?
    private(set) var hasLoaded = false

    private let api = TangoAPIService.shared

    /// 検索文字が空のときは結果を返さない (空配列)。
    var filteredWords: [DomainWord] {
        let q = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return [] }
        let lower = q.lowercased()
        return allWords.filter { w in
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

    /// 未ロードかつ非ロード中のときだけ一括ロードする (キーストロークごとの再ロードを防ぐ)。
    func loadAllIfNeeded() async {
        guard !hasLoaded, !isLoading else { return }
        await load()
    }

    func load(forceRefresh: Bool = false) async {
        isLoading = true
        loadProgress = 0
        errorMessage = nil
        defer { isLoading = false }

        do {
            let batches = try await api.listBatches(forceRefresh: forceRefresh)

            // 進捗計算のため、先に全ファイルを列挙する。
            var jobs: [(batch: String, stem: String)] = []
            for batch in batches {
                let files = (try? await api.listFiles(batch: batch, forceRefresh: forceRefresh)) ?? []
                for f in files where f.count > 0 {
                    jobs.append((batch: batch, stem: f.stem))
                }
            }

            let total = max(jobs.count, 1)
            var all: [DomainWord] = []
            // 同一バッチ内の重複単語 (複数ファイルに跨る同じ id) を除外する。
            var seen: Set<String> = []
            for (idx, job) in jobs.enumerated() {
                if let result = try? await api.loadData(
                    batch: job.batch,
                    stem: job.stem,
                    forceRefresh: forceRefresh
                ) {
                    for item in result.vocabulary_list {
                        let dedupKey = "\(job.batch)::\(item.id)"
                        if seen.contains(dedupKey) { continue }
                        seen.insert(dedupKey)
                        all.append(DomainWord(batch: job.batch, stem: job.stem, item: item))
                    }
                }
                loadProgress = Double(idx + 1) / Double(total)
            }
            allWords = all
            hasLoaded = true
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
