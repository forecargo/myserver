import SwiftData
import SwiftUI

/// 単語詳細（カード画像を主役に・意味/例文/解説タブ）。
struct WordDetailView: View {
    let entryNo: String

    @State private var detail: WordDetail?
    @State private var tab = 0
    @State private var errorMessage: String?

    var body: some View {
        ScrollView {
            if let detail {
                VStack(alignment: .leading, spacing: Spacing.l) {
                    CardImage(imageURL: detail.image_url)
                        .frame(maxWidth: .infinity)
                        .clipShape(RoundedRectangle(cornerRadius: Radius.l))
                        .shadow(color: Color.kbText.opacity(0.12), radius: 10, y: 6)

                    header(detail)

                    Picker("", selection: $tab) {
                        Text("意味").tag(0)
                        Text("例文").tag(1)
                        Text("解説").tag(2)
                    }
                    .pickerStyle(.segmented)

                    switch tab {
                    case 0: meaningsView(detail)
                    case 1: examplesView(detail)
                    default: commentaryView(detail)
                    }
                }
                .padding(Spacing.l)
            } else if let errorMessage {
                Text(errorMessage).font(KBFont.gothic(13)).foregroundStyle(Color.kbTextMuted).padding()
            } else {
                ProgressView().padding(.top, 80)
            }
        }
        .background(Color.kbBackground)
        .task { await load() }
    }

    private func header(_ d: WordDetail) -> some View {
        HStack(alignment: .lastTextBaseline, spacing: 11) {
            Text(d.headword).font(KBFont.mincho(34))
            if let reading = d.reading {
                Text(reading).font(KBFont.gothic(14)).foregroundStyle(Color.kbTextMuted)
            }
            Spacer()
            if let conj = d.conjugation_type {
                POSChip(text: conj)
            } else if let pos = d.pos_category {
                POSChip(text: pos)
            }
        }
    }

    private func meaningsView(_ d: WordDetail) -> some View {
        VStack(spacing: 0) {
            ForEach(Array((d.meanings ?? []).enumerated()), id: \.offset) { _, m in
                HStack(alignment: .top, spacing: 11) {
                    Text("\(m.no ?? 0)")
                        .font(KBFont.gothic(12, weight: .bold))
                        .foregroundStyle(.white)
                        .frame(width: 22, height: 22)
                        .background(Color.kbPrimary, in: Circle())
                    Text(m.gloss).font(KBFont.mincho(15, weight: .regular)).foregroundStyle(Color.kbText)
                    Spacer()
                }
                .padding(.vertical, 11).padding(.horizontal, 14)
                Divider()
            }
        }
        .background(Color.kbSurface, in: RoundedRectangle(cornerRadius: Radius.l))
        .overlay(RoundedRectangle(cornerRadius: Radius.l).stroke(Color.kbBorder))
    }

    private func examplesView(_ d: WordDetail) -> some View {
        VStack(alignment: .leading, spacing: Spacing.m) {
            if (d.examples ?? []).isEmpty {
                Text("例文はありません。").font(KBFont.gothic(13)).foregroundStyle(Color.kbTextMuted)
            }
            ForEach(Array((d.examples ?? []).enumerated()), id: \.offset) { _, ex in
                VStack(alignment: .leading, spacing: 4) {
                    Text(ex.text).font(KBFont.mincho(15, weight: .regular))
                    if let t = ex.translation {
                        Text(t).font(KBFont.gothic(12)).foregroundStyle(Color.kbBody)
                    }
                    if let s = ex.source {
                        Text("〈\(s)〉").font(KBFont.gothic(11)).foregroundStyle(Color.kbTextMuted)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(14)
                .background(Color.kbSurface, in: RoundedRectangle(cornerRadius: Radius.m))
                .overlay(RoundedRectangle(cornerRadius: Radius.m).stroke(Color.kbBorder))
            }
        }
    }

    private func commentaryView(_ d: WordDetail) -> some View {
        VStack(alignment: .leading, spacing: Spacing.m) {
            Text(d.commentary ?? "解説はありません。")
                .font(KBFont.gothic(13))
                .foregroundStyle(Color.kbBody)
                .lineSpacing(6)
            if let hon = d.honorific {
                Text("敬語: \(hon.type)\(hon.base_word.map { "（「\($0)」）" } ?? "")")
                    .font(KBFont.gothic(12, weight: .bold))
                    .foregroundStyle(Color.kbPrimaryDeep)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color.kbSurface, in: RoundedRectangle(cornerRadius: Radius.m))
        .overlay(RoundedRectangle(cornerRadius: Radius.m).stroke(Color.kbBorder))
    }

    private func load() async {
        do {
            detail = try await KobunAPIService.shared.word(entryNo)
        } catch {
            errorMessage = (error as? LocalizedError)?.errorDescription ?? "読み込みに失敗しました。"
        }
    }
}
