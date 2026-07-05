import SwiftUI
import SwiftData

struct BatchWordListView: View {
    let batch: String
    @State private var vm: BatchWordListViewModel
    @State private var showDiagnostic = false
    @State private var countMode: CountDisplayMode = .total
    /// 3 連敗以上 (shouldShowWarning) の単語のみ表示するフィルタ
    @State private var showWarningOnly = false
    @Environment(\.modelContext) private var modelContext
    @Query private var progresses: [WordProgress]

    enum CountDisplayMode: CaseIterable {
        case total      // 総単語数
        case learned    // 既習単語数
        case rate       // 既習率

        var next: CountDisplayMode {
            switch self {
            case .total: return .learned
            case .learned: return .rate
            case .rate: return .total
            }
        }
    }

    init(batch: String) {
        self.batch = batch
        _vm = State(initialValue: BatchWordListViewModel(batch: batch))
        // 進捗フェッチを当該バッチに限定し、毎描画の辞書構築を全アプリ→1 バッチに縮める。
        _progresses = Query(filter: #Predicate<WordProgress> { $0.batch == batch })
    }

    var body: some View {
        @Bindable var vmBindable = vm

        // 進捗ルックアップ辞書を body で 1 回だけ構築し、各所へ渡す。
        // (毎要素ごとの線形探索 O(n×m) を O(n+m) に抑える)
        let lookup = progressByKey
        let shown = displayedWords(lookup: lookup)

        content(shown: shown, lookup: lookup)
            .navigationTitle(batch.formattedBatchName)
            .navigationBarTitleDisplayMode(.inline)
            .searchable(text: $vmBindable.searchText, prompt: "単語・意味・発音で検索")
            .toolbar { toolbarContent(shownCount: shown.count) }
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
    private func toolbarContent(shownCount: Int) -> some ToolbarContent {
        ToolbarItem(placement: .topBarTrailing) {
            Button {
                showWarningOnly.toggle()
            } label: {
                Image(systemName: showWarningOnly
                    ? "exclamationmark.triangle.fill"
                    : "exclamationmark.triangle")
            }
            .tint(showWarningOnly ? .orange : nil)
            .accessibilityLabel(showWarningOnly ? "苦手フィルタ解除" : "苦手な単語のみ表示")
        }
        ToolbarItem(placement: .topBarTrailing) {
            if vm.isLoading {
                ProgressView()
            } else {
                countBadge(actual: shownCount)
            }
        }
    }

    @ViewBuilder
    private func countBadge(actual: Int) -> some View {
        let expected = vm.expectedCount
        let isFiltering = isSearching || showWarningOnly
        let hasMismatch = !vm.failedStems.isEmpty
            || (expected > 0 && actual != expected)

        if isFiltering {
            Text("\(actual) 語")
                .font(.caption.weight(.semibold))
                .foregroundStyle(showWarningOnly ? .orange : Color.taOnSurfaceVariant)
        } else if hasMismatch {
            Button { showDiagnostic = true } label: {
                Text("\(actual) / \(expected) 語")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.orange)
            }
        } else {
            Button { countMode = countMode.next } label: {
                Text(countLabel)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(Color.taOnSurfaceVariant)
                    .contentTransition(.numericText())
            }
        }
    }

    private var isSearching: Bool {
        !vm.searchText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    /// key → WordProgress のルックアップ辞書。body で 1 回だけ構築して使い回す。
    private var progressByKey: [String: WordProgress] {
        Dictionary(progresses.map { ($0.key, $0) }, uniquingKeysWith: { first, _ in first })
    }

    /// 検索フィルタ後に、必要なら 3 連敗以上の単語だけに絞り込んだ表示用リスト。
    private func displayedWords(lookup: [String: WordProgress]) -> [DomainWord] {
        let base = vm.filteredWords
        guard showWarningOnly else { return base }
        return base.filter { lookup[$0.id]?.shouldShowWarning == true }
    }

    private var totalCount: Int { vm.words.count }

    private var learnedCount: Int {
        let target = batch
        return progresses.filter { $0.batch == target && $0.isLearned }.count
    }

    private var countLabel: String {
        switch countMode {
        case .total:
            return "\(totalCount) 語"
        case .learned:
            return "既習 \(learnedCount)"
        case .rate:
            guard totalCount > 0 else { return "既習 0%" }
            let rate = Double(learnedCount) / Double(totalCount) * 100
            return String(format: "既習 %.1f%%", rate)
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
    private func content(shown: [DomainWord], lookup: [String: WordProgress]) -> some View {
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
        } else if shown.isEmpty {
            emptyFilterView
        } else {
            wordList(words: shown, lookup: lookup)
        }
    }

    @ViewBuilder
    private var emptyFilterView: some View {
        if showWarningOnly {
            ContentUnavailableView(
                "苦手な単語はありません",
                systemImage: "checkmark.seal",
                description: Text("3 連続で間違えた単語がここに表示されます")
            )
        } else {
            ContentUnavailableView.search(text: vm.searchText)
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

    private func wordList(words: [DomainWord], lookup: [String: WordProgress]) -> some View {
        List(Array(words.enumerated()), id: \.element.id) { idx, w in
            NavigationLink(value: BrowseRoute.wordDetail(
                WordDetailContext(words: words, startIndex: idx)
            )) {
                WordRow(
                    domain: w,
                    progress: lookup[w.id],
                    query: vm.searchText
                )
            }
            .swipeActions(edge: .trailing) {
                Button {
                    toggleFavorite(domain: w)
                } label: {
                    let isFav = lookup[w.id]?.isFavorite == true
                    Image(systemName: isFav ? "star.slash" : "star.fill")
                }
                .tint(.yellow)
            }
        }
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
        HStack(alignment: .center, spacing: 6) {
            Text("#\(formattedId)")
                .font(.caption.monospacedDigit())
                .foregroundStyle(Color.taOnSurfaceVariant)
                .layoutPriority(1)

            statusIcon

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

    /// "1" → "0001", "2090" → "2090" のように 4 桁ゼロ埋め。
    private var formattedId: String {
        let raw = domain.item.id
        guard raw.count < 4 else { return raw }
        return String(repeating: "0", count: 4 - raw.count) + raw
    }

    /// ID と単語の間に表示する進捗ステータス。
    /// 警告と既習は両立しない (クイズで間違えると isLearned=false に戻る) ので、
    /// 1 アイコン分の幅で固定し、いずれかを表示する。
    private var statusIcon: some View {
        ZStack {
            // 幅確保用のダミー (透明)
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
