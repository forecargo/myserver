import SwiftUI
import SwiftData

struct BatchWordListView: View {
    let batch: String
    @State private var vm: BatchWordListViewModel
    @State private var showDiagnostic = false
    @Environment(\.modelContext) private var modelContext
    @Query private var progresses: [WordProgress]

    init(batch: String) {
        self.batch = batch
        _vm = State(initialValue: BatchWordListViewModel(batch: batch))
    }

    var body: some View {
        @Bindable var vmBindable = vm

        content
            .navigationTitle(batch.formattedBatchName)
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $vmBindable.searchText, prompt: "単語・意味・発音で検索")
            .toolbar { toolbarContent }
            .alert("ロード状況", isPresented: $showDiagnostic) {
                Button("OK") {}
                Button("再取得") {
                    Task { await vm.load(forceRefresh: true) }
                }
            } message: {
                Text(makeDiagnosticMessage())
            }
            .task {
                if vm.words.isEmpty { await vm.load() }
            }
            .refreshable {
                await vm.load(forceRefresh: true)
            }
    }

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            if vm.isLoading {
                ProgressView()
            } else {
                countBadge
            }
        }
    }

    @ViewBuilder
    private var countBadge: some View {
        let actual = vm.filteredWords.count
        let expected = vm.expectedCount
        if !vm.failedStems.isEmpty || (expected > 0 && actual != expected && vm.searchText.isEmpty) {
            Button {
                showDiagnostic = true
            } label: {
                Text("\(actual) / \(expected) 語")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.orange)
            }
        } else {
            Text("\(actual) 語")
                .font(.caption.weight(.semibold))
                .foregroundStyle(Color.taOnSurfaceVariant)
        }
    }

    private func makeDiagnosticMessage() -> String {
        var lines: [String] = []
        lines.append("API: \(TangoAPIService.currentBaseURLString)")
        lines.append("実際 \(vm.words.count) / 期待 \(vm.expectedCount) / 重複 \(vm.duplicateSkipCount)")
        if !vm.failedStems.isEmpty {
            lines.append("取得失敗 \(vm.failedStems.count) 件:")
            for (stem, reason) in vm.failedStems.prefix(3) {
                lines.append("• \(stem): \(reason.prefix(60))")
            }
        }
        if !vm.perFileMismatch.isEmpty {
            lines.append("不一致 \(vm.perFileMismatch.count) ファイル (期待→実際/重複):")
            for m in vm.perFileMismatch.prefix(10) {
                let short = m.stem.replacingOccurrences(of: "LEAP - ", with: "")
                lines.append("• \(short): \(m.expected)→\(m.actualInPayload)/dup\(m.dups)")
            }
            if vm.perFileMismatch.count > 10 {
                lines.append("…他 \(vm.perFileMismatch.count - 10) 件")
            }
        }
        return lines.joined(separator: "\n")
    }

    @ViewBuilder
    private var content: some View {
        if vm.isLoading && vm.words.isEmpty {
            loadingView
        } else if let error = vm.errorMessage {
            errorView(error)
        } else if vm.words.isEmpty {
            ContentUnavailableView(
                "単語がありません",
                systemImage: "text.book.closed",
                description: Text("このバッチには単語が登録されていません")
            )
        } else {
            wordList
        }
    }

    private var loadingView: some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            ProgressView(value: vm.loadProgress)
                .progressViewStyle(.linear)
                .padding(.horizontal, DesignTokens.Spacing.xl)
            Text("読み込み中…\(Int(vm.loadProgress * 100))%")
                .font(.caption)
                .foregroundStyle(Color.taOnSurfaceVariant)
        }
    }

    private var wordList: some View {
        let words = vm.filteredWords
        return List(Array(words.enumerated()), id: \.element.id) { idx, w in
            NavigationLink(value: BrowseRoute.wordDetail(
                WordDetailContext(words: words, startIndex: idx)
            )) {
                WordRow(
                    domain: w,
                    progress: progressFor(domain: w),
                    query: vm.searchText
                )
            }
            .swipeActions(edge: .trailing) {
                Button {
                    toggleFavorite(domain: w)
                } label: {
                    let isFav = progressFor(domain: w)?.isFavorite == true
                    Image(systemName: isFav ? "star.slash" : "star.fill")
                }
                .tint(.yellow)
            }
        }
    }

    private func progressFor(domain: DomainWord) -> WordProgress? {
        progresses.first { $0.key == domain.id }
    }

    private func toggleFavorite(domain: DomainWord) {
        if let p = progresses.first(where: { $0.key == domain.id }) {
            p.isFavorite.toggle()
        } else {
            let new = WordProgress(
                key: domain.id,
                batch: domain.batch,
                stem: domain.stem,
                wordId: domain.item.id,
                wordSnapshot: domain.item.word,
                phoneticSnapshot: domain.item.phonetic,
                isFavorite: true
            )
            modelContext.insert(new)
        }
        try? modelContext.save()
    }

    private func errorView(_ message: String) -> some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundStyle(.orange)
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundStyle(Color.taOnSurfaceVariant)
            Button("再試行") {
                Task { await vm.load(forceRefresh: true) }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}

private struct WordRow: View {
    let domain: DomainWord
    let progress: WordProgress?
    let query: String

    var body: some View {
        HStack(alignment: .center, spacing: DesignTokens.Spacing.sm) {
            Text("#\(domain.item.id)")
                .font(.caption.monospacedDigit())
                .foregroundStyle(Color.taOnSurfaceVariant)
                .frame(width: 48, alignment: .leading)

            VStack(alignment: .leading, spacing: 2) {
                Text(highlight(domain.item.word))
                    .font(.body.weight(.semibold))
                Text(domain.item.phonetic)
                    .font(.caption.italic())
                    .foregroundStyle(Color.taOnSurfaceVariant)
            }

            Spacer()
            trailingIcons
        }
    }

    @ViewBuilder
    private var trailingIcons: some View {
        HStack(spacing: 6) {
            if progress?.isLearned == true {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
                    .font(.callout)
            }
            if progress?.isFavorite == true {
                Image(systemName: "star.fill")
                    .foregroundStyle(.yellow)
                    .font(.callout)
            }
            if domain.item.level_tag != nil {
                LevelBadge(tag: domain.item.level_tag)
            }
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
