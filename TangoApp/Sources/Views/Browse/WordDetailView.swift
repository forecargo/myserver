import SwiftUI
import SwiftData

struct WordDetailView: View {
    let context: WordDetailContext
    @State private var currentIndex: Int
    @Environment(\.modelContext) private var modelContext
    @AppStorage("tts_autoplay") private var ttsAutoplay: Bool = false

    init(context: WordDetailContext) {
        self.context = context
        _currentIndex = State(initialValue: min(max(context.startIndex, 0), max(context.words.count - 1, 0)))
    }

    private var currentDomain: DomainWord? {
        guard context.words.indices.contains(currentIndex) else { return nil }
        return context.words[currentIndex]
    }

    var body: some View {
        TabView(selection: $currentIndex) {
            ForEach(Array(context.words.enumerated()), id: \.offset) { idx, w in
                WordDetailPage(
                    item: w.item,
                    batch: w.batch,
                    stem: w.stem
                )
                .tag(idx)
            }
        }
        .tabViewStyle(.page(indexDisplayMode: .never))
        .indexViewStyle(.page(backgroundDisplayMode: .never))
        .background(Color(.systemGroupedBackground))
        .navigationTitle(currentDomain?.item.word ?? "")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                if context.words.count > 1 {
                    Text("\(currentIndex + 1) / \(context.words.count)")
                        .font(.caption.monospacedDigit())
                        .foregroundStyle(Color.taOnSurfaceVariant)
                }
            }
        }
        // 現在表示中のページに対してのみ発音する (TabView の prefetch による誤発音を防ぐ)
        .task(id: currentIndex) {
            guard ttsAutoplay else { return }
            try? await Task.sleep(for: .milliseconds(500))
            guard !Task.isCancelled else { return }
            if let domain = currentDomain {
                SpeechService.shared.speakWord(domain.item)
            }
        }
        .onDisappear {
            SpeechService.shared.stop()
        }
    }
}

private struct WordDetailPage: View {
    let item: APIVocabularyItem
    let batch: String
    let stem: String

    @State private var vm: WordDetailViewModel
    @Environment(\.modelContext) private var modelContext

    init(item: APIVocabularyItem, batch: String, stem: String) {
        self.item = item
        self.batch = batch
        self.stem = stem
        let domain = DomainWord(batch: batch, stem: stem, item: item)
        _vm = State(initialValue: WordDetailViewModel(domain: domain))
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.md) {
                header
                definitionsSection
                usagesSection
                originSection
                examplesSection
                learnedToggle
                imageSection
            }
            .padding(DesignTokens.Spacing.md)
            .padding(.bottom, DesignTokens.Spacing.xl)
        }
        .onAppear {
            // 進捗加算のみ (発音は親 View が currentIndex 変化を見て一括処理)
            vm.onAppear(context: modelContext)
        }
    }

    // MARK: - セクション

    private var header: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
            HStack(alignment: .firstTextBaseline, spacing: DesignTokens.Spacing.sm) {
                Text("#\(item.id)")
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(Color.taOnSurfaceVariant)
                Text(item.word)
                    .font(.system(size: 30, weight: .bold))
                Spacer()
                favoriteButton
                if item.level_tag != nil {
                    LevelBadge(tag: item.level_tag)
                }
            }
            HStack(spacing: DesignTokens.Spacing.sm) {
                Text(item.phonetic)
                    .font(.callout.italic())
                    .foregroundStyle(Color.taOnSurfaceVariant)
                Spacer()
                Button {
                    vm.speakWord()
                } label: {
                    Image(systemName: "speaker.wave.2.fill")
                        .foregroundStyle(Color.taPrimary)
                }
                Button {
                    vm.speakAll()
                } label: {
                    Image(systemName: "play.rectangle.fill")
                        .foregroundStyle(Color.taPrimary)
                }
            }
        }
        .padding()
        .background(cardBackground)
    }

    private var favoriteButton: some View {
        Button {
            vm.toggleFavorite(context: modelContext)
        } label: {
            Image(systemName: vm.progress?.isFavorite == true ? "star.fill" : "star")
                .foregroundStyle(.yellow)
        }
        .buttonStyle(.plain)
    }

    private var definitionsSection: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
            sectionTitle("意味")
            definitionsBody
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(cardBackground)
    }

    @ViewBuilder
    private var definitionsBody: some View {
        if item.definitions.isEmpty {
            Text("(definitions が空です)")
                .font(.caption)
                .foregroundStyle(.orange)
        } else {
            ForEach(item.definitions, id: \.self) { def in
                DefinitionBlock(definition: def)
            }
        }
    }

    @ViewBuilder
    private var usagesSection: some View {
        if !item.usages_and_notes.isEmpty {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                sectionTitle("語法・注意・派生")
                ForEach(Array(item.usages_and_notes.enumerated()), id: \.offset) { _, note in
                    HStack(alignment: .top, spacing: 6) {
                        Text("•")
                            .foregroundStyle(Color.taOnSurfaceVariant)
                        Text(note)
                            .font(.callout)
                            .foregroundStyle(Color.taOnSurface)
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(cardBackground)
        }
    }

    @ViewBuilder
    private var originSection: some View {
        if let origin = item.word_origin,
           origin.formula != nil || origin.description != nil {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                sectionTitle("語源")
                originBody(origin: origin)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(cardBackground)
        }
    }

    private func originBody(origin: APIWordOrigin) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            if let formula = origin.formula {
                Text(formula)
                    .font(.system(.callout, design: .monospaced))
                    .foregroundStyle(Color.taOnSurface)
            }
            if let desc = origin.description {
                Text(desc).font(.callout)
            }
        }
        .padding()
        .background(
            RoundedRectangle(cornerRadius: 8).fill(Color.taOriginBg)
        )
    }

    @ViewBuilder
    private var examplesSection: some View {
        if !item.examples.isEmpty {
            VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                sectionTitle("例文")
                ForEach(Array(item.examples.enumerated()), id: \.offset) { _, ex in
                    ExampleRow(example: ex) { vm.speakExample(ex) }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(cardBackground)
        }
    }

    private var learnedToggle: some View {
        Button {
            vm.toggleLearned(context: modelContext)
        } label: {
            HStack {
                Image(systemName: vm.progress?.isLearned == true
                      ? "checkmark.circle.fill" : "circle")
                Text(vm.progress?.isLearned == true ? "既習にした" : "既習にする")
            }
            .font(.body.weight(.semibold))
            .frame(maxWidth: .infinity)
            .padding()
            .background(
                RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
                    .fill(vm.progress?.isLearned == true
                          ? Color.green.opacity(0.15)
                          : Color.taPrimary.opacity(0.1))
            )
            .foregroundStyle(vm.progress?.isLearned == true
                             ? Color.green : Color.taPrimary)
        }
        .buttonStyle(.plain)
    }

    private var imageSection: some View {
        DisclosureGroup("ページ画像を表示") {
            PageImage(batch: batch, stem: stem)
                .padding(.top, DesignTokens.Spacing.sm)
        }
        .padding()
        .background(cardBackground)
    }

    // MARK: - helpers

    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
            .fill(Color(.secondarySystemGroupedBackground))
    }

    private func sectionTitle(_ text: String) -> some View {
        Text(text.uppercased())
            .font(.system(size: 11, weight: .heavy))
            .tracking(1)
            .foregroundStyle(Color.taOnSurfaceVariant)
    }
}

private struct DefinitionBlock: View {
    let definition: APIMeaningGroup

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            POSChip(pos: definition.part_of_speech)
            ForEach(Array(definition.meanings.enumerated()), id: \.offset) { _, meaning in
                Text(meaning)
                    .font(.body)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
    }
}

private struct ExampleRow: View {
    let example: APIExampleSentence
    let onSpeak: () -> Void

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Rectangle()
                .fill(Color.taPrimary.opacity(0.4))
                .frame(width: 3)
            VStack(alignment: .leading, spacing: 4) {
                Text(example.en).font(.body.weight(.medium))
                Text(example.ja)
                    .font(.callout)
                    .foregroundStyle(Color.taOnSurfaceVariant)
            }
            Spacer()
            Button(action: onSpeak) {
                Image(systemName: "speaker.wave.2")
                    .foregroundStyle(Color.taPrimary)
            }
        }
    }
}

private struct PageImage: View {
    let batch: String
    let stem: String
    @State private var showFullScreen = false

    var body: some View {
        let url = TangoAPIService.shared.imageURL(batch: batch, stem: stem)
        VStack(spacing: 4) {
            AsyncImage(url: url) { phase in
                imageContent(phase: phase)
            }
            .onTapGesture { showFullScreen = true }

            Text("タップで拡大 (ピンチでズーム)")
                .font(.caption2)
                .foregroundStyle(Color.taOnSurfaceVariant)
        }
        .fullScreenCover(isPresented: $showFullScreen) {
            PageImageZoomView(url: url)
        }
    }

    @ViewBuilder
    private func imageContent(phase: AsyncImagePhase) -> some View {
        switch phase {
        case .empty:
            ProgressView().frame(maxWidth: .infinity, minHeight: 200)
        case .success(let image):
            image
                .resizable()
                .scaledToFit()
                .clipShape(RoundedRectangle(cornerRadius: 8))
        case .failure:
            Text("画像を読み込めませんでした")
                .foregroundStyle(Color.taOnSurfaceVariant)
        @unknown default:
            EmptyView()
        }
    }
}

private struct PageImageZoomView: View {
    let url: URL
    @Environment(\.dismiss) private var dismiss
    @State private var scale: CGFloat = 1.0
    @State private var lastScale: CGFloat = 1.0
    @State private var offset: CGSize = .zero
    @State private var lastOffset: CGSize = .zero

    private let minScale: CGFloat = 1.0
    private let maxScale: CGFloat = 6.0

    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()
                AsyncImage(url: url) { phase in
                    zoomableContent(phase: phase)
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("閉じる") { dismiss() }
                        .foregroundStyle(.white)
                }
                ToolbarItem(placement: .topBarLeading) {
                    if scale > 1.01 {
                        Button("リセット") {
                            reset(animated: true)
                        }
                        .foregroundStyle(.white)
                    }
                }
            }
            .toolbarBackground(.black, for: .navigationBar)
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
        }
    }

    @ViewBuilder
    private func zoomableContent(phase: AsyncImagePhase) -> some View {
        switch phase {
        case .empty:
            ProgressView()
                .tint(.white)
        case .success(let image):
            image
                .resizable()
                .scaledToFit()
                .scaleEffect(scale)
                .offset(offset)
                .gesture(magnification)
                .simultaneousGesture(dragging)
                .gesture(doubleTap)
        case .failure:
            Text("画像を読み込めませんでした")
                .foregroundStyle(.white)
        @unknown default:
            EmptyView()
        }
    }

    private var magnification: some Gesture {
        MagnificationGesture()
            .onChanged { value in
                scale = min(max(lastScale * value, minScale), maxScale)
            }
            .onEnded { _ in
                lastScale = scale
                if scale <= minScale + 0.05 {
                    reset(animated: true)
                }
            }
    }

    private var dragging: some Gesture {
        DragGesture()
            .onChanged { value in
                // ズーム中だけドラッグでパン可能
                guard scale > 1.01 else { return }
                offset = CGSize(
                    width: lastOffset.width + value.translation.width,
                    height: lastOffset.height + value.translation.height
                )
            }
            .onEnded { _ in
                lastOffset = offset
            }
    }

    private var doubleTap: some Gesture {
        TapGesture(count: 2)
            .onEnded {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) {
                    if scale > 1.01 {
                        reset(animated: false)
                    } else {
                        scale = 2.5
                        lastScale = 2.5
                    }
                }
            }
    }

    private func reset(animated: Bool) {
        let action = {
            scale = minScale
            lastScale = minScale
            offset = .zero
            lastOffset = .zero
        }
        if animated {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.8)) { action() }
        } else {
            action()
        }
    }
}
