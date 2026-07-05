import SwiftData
import SwiftUI

/// 単語詳細のページャ。リスト順を引き継ぎ、横スワイプで前後の単語へめくる。
/// タイトルと下部バー（暗記に追加/覚えた）は現在表示中の単語に対して動作する。
struct WordPagerView: View {
    /// 先読みする前後の単語数（±prefetchRadius）。
    private static let prefetchRadius = 2

    let items: [WordListItem]

    @Environment(\.modelContext) private var context
    @AppStorage("api_base_url") private var apiBaseURL = KobunAPIService.defaultBaseURL
    @Query private var allProgress: [WordProgress]
    @State private var selection: String
    @State private var masterTick = 0   // 「覚えた」確定時の手応え演出トリガ

    init(items: [WordListItem], startEntryNo: String) {
        self.items = items
        _selection = State(initialValue: startEntryNo)
    }

    private var currentItem: WordListItem? {
        items.first { $0.entry_no == selection }
    }

    /// 表示中の語が「覚えた」状態か。
    private var isMastered: Bool {
        allProgress.first { $0.key == selection }?.status == .mastered
    }

    /// 区分キー（part1/part2/keigo）を表示用ラベルへ変換する。
    private func sectionLabel(_ key: String) -> String {
        switch key {
        case "part1": return "第一章"
        case "part2": return "第二章"
        case "keigo": return "敬語"
        default: return key
        }
    }

    private var navTitle: String {
        guard let item = currentItem else { return selection }
        let label = sectionLabel(item.section)
        return label.isEmpty ? item.entry_no : "\(label) · \(item.entry_no)"
    }

    var body: some View {
        TabView(selection: $selection) {
            ForEach(items) { item in
                WordDetailView(entryNo: item.entry_no)
                    .tag(item.entry_no)
            }
        }
        .tabViewStyle(.page(indexDisplayMode: .never))
        .background(Color.kbBackground)
        .navigationTitle(navTitle)
        .navigationBarTitleDisplayMode(.inline)
        .safeAreaInset(edge: .bottom) { bottomBar }
        // 「覚えた」確定時に success ハプティクス
        .sensoryFeedback(.success, trigger: masterTick)
        // 表示中の単語が変わるたびに前後の画像・詳細を先読みする
        .task(id: selection) { prefetchAround(selection) }
    }

    /// 「覚えた」をトグルする。新規習得時のみ今日の学習量を加算し、手応え演出を出す。
    private func toggleMastered() {
        let p = ProgressStore.progress(for: selection, in: context)
        if p.status == .mastered {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { p.status = .unlearned }
        } else {
            withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) { p.status = .mastered }
            ProgressStore.bumpToday(in: context)
            masterTick += 1
        }
    }

    /// 指定単語の前後（±prefetchRadius）の画像と詳細をキャッシュへ先読みする。
    private func prefetchAround(_ entryNo: String) {
        guard let idx = items.firstIndex(where: { $0.entry_no == entryNo }) else { return }
        let base = URL(string: apiBaseURL) ?? URL(string: KobunAPIService.defaultBaseURL)!
        for offset in -Self.prefetchRadius...Self.prefetchRadius where offset != 0 {
            let j = idx + offset
            guard items.indices.contains(j) else { continue }
            let item = items[j]
            Task { await KobunAPIService.shared.prefetchWord(item.entry_no) }
            if let url = KobunAPIService.imageURL(item.image_url, base: base) {
                ImageCache.shared.prefetch(url)
            }
        }
    }

    private var bottomBar: some View {
        HStack(spacing: 10) {
            Button {
                let p = ProgressStore.progress(for: selection, in: context)
                p.inFlashcardDeck.toggle()
            } label: {
                Text("＋ 暗記に追加")
                    .font(KBFont.gothic(14, weight: .bold))
                    .frame(maxWidth: .infinity).padding(.vertical, 13)
                    .foregroundStyle(Color.kbPrimaryDeep)
                    .background(Color.kbSurface, in: RoundedRectangle(cornerRadius: Radius.m))
                    .overlay(RoundedRectangle(cornerRadius: Radius.m).stroke(Color.kbBubbleBorder))
            }
            Button(action: toggleMastered) {
                HStack(spacing: 7) {
                    Image(systemName: isMastered ? "checkmark.seal.fill" : "checkmark")
                        .symbolEffect(.bounce, value: masterTick)
                    Text(isMastered ? "覚えた！" : "覚えた")
                }
                .font(KBFont.gothic(14, weight: .bold))
                .frame(maxWidth: .infinity).padding(.vertical, 13)
                .foregroundStyle(.white)
                .background {
                    RoundedRectangle(cornerRadius: Radius.m)
                        .fill(isMastered ? AnyShapeStyle(Color.kbGreenDeep) : AnyShapeStyle(Color.kbPrimaryGradient))
                }
            }
        }
        .buttonStyle(.plain)
        .padding(.horizontal, Spacing.l)
        .padding(.vertical, Spacing.s)
        .background(.ultraThinMaterial)
    }
}
