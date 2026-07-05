import SwiftData
import SwiftUI

/// 単語帳 / 品詞別リスト。章選択＋品詞タブ＋単語行。
struct WordListView: View {
    @Query private var allProgress: [WordProgress]

    @State private var meta: MetaResponse?
    @State private var section = "part1"
    @State private var pos: String?
    @State private var items: [WordListItem] = []
    @State private var loading = false
    @State private var errorMessage: String?

    private var progressByKey: [String: LearnStatus] {
        Dictionary(allProgress.map { ($0.key, $0.status) }, uniquingKeysWith: { a, _ in a })
    }

    private var currentSection: SectionMeta? {
        meta?.sections.first { $0.key == section }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                sectionPicker
                posTabs
                content
            }
            .background(Color.kbBackground)
            .navigationTitle("単語帳")
            .navigationBarTitleDisplayMode(.inline)
            .task { await loadMeta() }
            .task(id: "\(section)-\(pos ?? "")") { await loadWords() }
        }
    }

    private var sectionPicker: some View {
        Picker("章", selection: $section) {
            Text("第一章").tag("part1")
            Text("第二章").tag("part2")
            Text("敬語").tag("keigo")
        }
        .pickerStyle(.segmented)
        .padding(.horizontal, Spacing.l)
        .padding(.top, Spacing.s)
        .onChange(of: section) { _, _ in pos = nil }
    }

    @ViewBuilder private var posTabs: some View {
        if let posList = currentSection?.pos, !posList.isEmpty {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: Spacing.s) {
                    posChip(title: "すべて", value: nil)
                    ForEach(posList) { p in
                        posChip(title: p.key, value: p.key)
                    }
                }
                .padding(.horizontal, Spacing.l)
            }
            .padding(.vertical, Spacing.s)
        }
    }

    private func posChip(title: String, value: String?) -> some View {
        let selected = pos == value
        return Text(title)
            .font(KBFont.gothic(13, weight: selected ? .bold : .regular))
            .foregroundStyle(selected ? Color.kbPrimaryDeep : Color.kbTextMuted)
            .padding(.horizontal, 14).padding(.vertical, 7)
            .background(selected ? Color.white : Color.kbSurface, in: Capsule())
            .overlay(Capsule().stroke(Color.kbBorder))
            .onTapGesture { pos = value }
    }

    @ViewBuilder private var content: some View {
        if loading && items.isEmpty {
            Spacer(); ProgressView(); Spacer()
        } else if let errorMessage {
            Spacer()
            VStack(spacing: Spacing.s) {
                Image(systemName: "wifi.slash").font(.largeTitle).foregroundStyle(Color.kbTextMuted)
                Text(errorMessage).font(KBFont.gothic(13)).foregroundStyle(Color.kbTextMuted)
                Button("再読み込み") { Task { await loadWords() } }
            }
            Spacer()
        } else {
            List(items) { item in
                NavigationLink {
                    WordPagerView(items: items, startEntryNo: item.entry_no)
                } label: {
                    WordRow(item: item, status: progressByKey[item.entry_no] ?? .unlearned)
                }
                .listRowBackground(Color.kbSurface)
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
        }
    }

    private func loadMeta() async {
        guard meta == nil else { return }
        meta = try? await KobunAPIService.shared.meta()
    }

    private func loadWords() async {
        loading = true
        errorMessage = nil
        do {
            let resp = try await KobunAPIService.shared.words(section: section, pos: pos)
            items = resp.items
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "読み込みに失敗しました。"
        }
        loading = false
    }
}

/// 単語リストの 1 行。
struct WordRow: View {
    let item: WordListItem
    let status: LearnStatus

    var body: some View {
        HStack(spacing: 12) {
            Text(item.entry_no)
                .font(KBFont.mincho(13))
                .foregroundStyle(Color.kbAccent)
                .frame(width: 30, alignment: .center)
            VStack(alignment: .leading, spacing: 1) {
                HStack(alignment: .firstTextBaseline, spacing: 7) {
                    Text(item.headword).font(KBFont.mincho(19))
                    if let reading = item.reading {
                        Text(reading).font(KBFont.gothic(11)).foregroundStyle(Color.kbTextMuted)
                    }
                }
                Text(item.short_gloss)
                    .font(KBFont.gothic(12))
                    .foregroundStyle(Color.kbBody)
                    .lineLimit(1)
            }
            Spacer()
            StatusDot(status: status)
        }
        .padding(.vertical, 4)
    }
}
