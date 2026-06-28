import SwiftUI
import SwiftData

struct BatchListView: View {
    @State private var vm = BatchListViewModel()
    @State private var searchVM = GlobalSearchViewModel()
    @Query private var progresses: [WordProgress]

    var body: some View {
        @Bindable var search = searchVM

        content
            .navigationTitle("単語帳")
            .searchable(
                text: $search.searchText,
                prompt: "全バッチから単語・意味・発音で検索"
            )
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await vm.load(forceRefresh: true) }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .navigationDestination(for: BrowseRoute.self, destination: destination)
            .task {
                if vm.batches.isEmpty { await vm.load() }
            }
            .task(id: isSearching) {
                // 検索開始時に一度だけ全バッチの単語を一括ロードする (以降はメモリ上でフィルタ)。
                // id を Bool にすることで、1 文字ごとにタスクが再起動されてロードが
                // 中断するのを防ぐ。
                if isSearching { await searchVM.loadAllIfNeeded() }
            }
    }

    private var isSearching: Bool {
        !searchVM.searchText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    @ViewBuilder
    private var content: some View {
        if isSearching {
            searchContent
        } else {
            batchContent
        }
    }

    // MARK: - バッチ一覧

    @ViewBuilder
    private var batchContent: some View {
        if vm.isLoading {
            ProgressView().controlSize(.large)
        } else if let error = vm.errorMessage {
            errorView(error) { Task { await vm.load(forceRefresh: true) } }
        } else if vm.batches.isEmpty {
            ContentUnavailableView(
                "バッチがありません",
                systemImage: "tray",
                description: Text("tango/data/ に JSON を配置してください")
            )
        } else {
            batchList
        }
    }

    private var batchList: some View {
        List(vm.batches, id: \.self) { batch in
            NavigationLink(value: BrowseRoute.batchWords(batch: batch)) {
                HStack {
                    Image(systemName: "folder.fill")
                        .foregroundStyle(Color.taPrimary)
                    Text(batch.formattedBatchName)
                        .font(.body.weight(.medium))
                }
            }
        }
    }

    // MARK: - 横断検索結果

    @ViewBuilder
    private var searchContent: some View {
        if searchVM.isLoading && searchVM.allWords.isEmpty {
            loadingView
        } else if let error = searchVM.errorMessage {
            errorView(error) { Task { await searchVM.load(forceRefresh: true) } }
        } else {
            let results = searchVM.filteredWords
            if results.isEmpty {
                ContentUnavailableView.search(text: searchVM.searchText)
            } else {
                searchResultList(results)
            }
        }
    }

    private func searchResultList(_ results: [DomainWord]) -> some View {
        List {
            Section {
                ForEach(Array(results.enumerated()), id: \.element.id) { idx, w in
                    NavigationLink(value: BrowseRoute.wordDetail(
                        WordDetailContext(words: results, startIndex: idx)
                    )) {
                        GlobalWordRow(
                            domain: w,
                            progress: progressFor(domain: w),
                            query: searchVM.searchText
                        )
                    }
                }
            } header: {
                Text("\(results.count) 語")
            }
        }
    }

    private var loadingView: some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            ProgressView(value: searchVM.loadProgress)
                .progressViewStyle(.linear)
                .padding(.horizontal, DesignTokens.Spacing.xl)
            Text("全バッチを読み込み中…\(Int(searchVM.loadProgress * 100))%")
                .font(.caption)
                .foregroundStyle(Color.taOnSurfaceVariant)
        }
    }

    private func progressFor(domain: DomainWord) -> WordProgress? {
        progresses.first { $0.key == domain.id }
    }

    // MARK: - 共通

    private func errorView(_ message: String, retry: @escaping () -> Void) -> some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundStyle(.orange)
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundStyle(Color.taOnSurfaceVariant)
            Button("再試行", action: retry)
                .buttonStyle(.borderedProminent)
        }
        .padding()
    }

    @ViewBuilder
    private func destination(_ route: BrowseRoute) -> some View {
        switch route {
        case .batchWords(let batch):
            BatchWordListView(batch: batch)
        case .wordDetail(let ctx):
            WordDetailView(context: ctx)
        }
    }
}

// 横断検索結果用の行。どのバッチの単語かを示すチップを付ける。
private struct GlobalWordRow: View {
    let domain: DomainWord
    let progress: WordProgress?
    let query: String

    var body: some View {
        HStack(alignment: .center, spacing: 6) {
            statusIcon

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text(highlight(domain.item.word))
                        .font(.body.weight(.semibold))
                    Text(domain.item.phonetic)
                        .font(.caption.italic())
                        .foregroundStyle(Color.taOnSurfaceVariant)
                }
                if let meaning = firstMeaning {
                    Text(highlight(meaning))
                        .font(.caption)
                        .foregroundStyle(Color.taOnSurfaceVariant)
                        .lineLimit(1)
                }
            }

            Spacer()
            trailingIcons
        }
    }

    private var firstMeaning: String? {
        domain.item.definitions.first?.meanings.first
    }

    private var statusIcon: some View {
        ZStack {
            Image(systemName: "checkmark.circle.fill").opacity(0)
            if progress?.shouldShowWarning == true {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
            } else if progress?.isLearned == true {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
            }
        }
        .font(.callout)
    }

    @ViewBuilder
    private var trailingIcons: some View {
        HStack(spacing: 6) {
            if progress?.isFavorite == true {
                Image(systemName: "star.fill")
                    .foregroundStyle(.yellow)
                    .font(.callout)
            }
            Text(domain.batch.formattedBatchName)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(Color.taPrimary)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.taPrimary.opacity(0.12), in: Capsule())
        }
    }

    private func highlight(_ text: String) -> AttributedString {
        var attr = AttributedString(text)
        let q = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !q.isEmpty else { return attr }
        let lowerText = text.lowercased()
        let lowerQ = q.lowercased()
        var searchStart = lowerText.startIndex
        while let range = lowerText.range(of: lowerQ, range: searchStart..<lowerText.endIndex) {
            if let attrRange = Range(NSRange(range, in: text), in: attr) {
                attr[attrRange].backgroundColor = .yellow.opacity(0.4)
            }
            searchStart = range.upperBound
        }
        return attr
    }
}
