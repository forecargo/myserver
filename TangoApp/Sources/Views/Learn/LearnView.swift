import SwiftUI
import SwiftData

struct LearnView: View {

    enum Mode: String, CaseIterable, Identifiable {
        case favorites = "お気に入り"
        case review = "復習"
        var id: String { rawValue }
    }

    @State private var mode: Mode = .favorites
    @State private var vm = LearnViewModel()
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \WordProgress.lastViewedAt, order: .reverse)
    private var allProgress: [WordProgress]

    var body: some View {
        VStack(spacing: 0) {
            modePicker
            content
        }
        .navigationTitle("学習")
        .navigationDestination(for: BrowseRoute.self, destination: destination)
        .task(id: progressSignature) {
            await vm.reload(progresses: allProgress)
        }
    }

    // @Query 変化検知用のシグネチャ (key + flag のハッシュ)
    private var progressSignature: String {
        allProgress
            .map { "\($0.key)|\($0.isFavorite ? 1 : 0)|\($0.isLearned ? 1 : 0)|\($0.viewCount)" }
            .joined(separator: ",")
    }

    private var modePicker: some View {
        Picker("モード", selection: $mode) {
            ForEach(Mode.allCases) { m in
                Text(m.rawValue).tag(m)
            }
        }
        .pickerStyle(.segmented)
        .padding()
    }

    @ViewBuilder
    private var content: some View {
        if vm.isLoading && currentList.isEmpty {
            ProgressView("読み込み中…")
                .frame(maxHeight: .infinity)
        } else if currentList.isEmpty {
            emptyState
        } else {
            wordList
        }
    }

    private var currentList: [DomainWord] {
        switch mode {
        case .favorites: return vm.favoriteWords
        case .review: return vm.reviewWords
        }
    }

    private var emptyState: some View {
        ContentUnavailableView(
            mode == .favorites ? "お気に入りはまだありません" : "復習対象はまだありません",
            systemImage: mode == .favorites ? "star" : "arrow.triangle.2.circlepath",
            description: Text(mode == .favorites
                              ? "単語帳で ★ をタップすると追加されます"
                              : "閲覧した単語の中から、未習のものが表示されます")
        )
    }

    private var wordList: some View {
        let list = currentList
        return List(Array(list.enumerated()), id: \.element.id) { idx, w in
            NavigationLink(value: BrowseRoute.wordDetail(
                WordDetailContext(words: list, startIndex: idx)
            )) {
                WordRow(domain: w, progress: progressFor(domain: w))
            }
        }
    }

    private func progressFor(domain: DomainWord) -> WordProgress? {
        allProgress.first { $0.key == domain.id }
    }

    @ViewBuilder
    private func destination(_ route: BrowseRoute) -> some View {
        switch route {
        case .batchWords(let b): BatchWordListView(batch: b)
        case .wordDetail(let ctx): WordDetailView(context: ctx)
        }
    }
}

private struct WordRow: View {
    let domain: DomainWord
    let progress: WordProgress?

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(domain.item.word)
                    .font(.body.weight(.semibold))
                Text(domain.item.phonetic)
                    .font(.caption.italic())
                    .foregroundStyle(Color.taOnSurfaceVariant)
                Text("\(domain.batch.formattedBatchName) / \(domain.stem)")
                    .font(.caption2)
                    .foregroundStyle(Color.taOnSurfaceVariant)
                    .lineLimit(1)
            }
            Spacer()
            trailingIcons
            if domain.item.level_tag != nil {
                LevelBadge(tag: domain.item.level_tag)
            }
        }
    }

    @ViewBuilder
    private var trailingIcons: some View {
        HStack(spacing: 6) {
            if progress?.isFavorite == true {
                Image(systemName: "star.fill").foregroundStyle(.yellow)
            }
            if progress?.isLearned == true {
                Image(systemName: "checkmark.circle.fill").foregroundStyle(.green)
            }
        }
    }
}
