import SwiftData
import SwiftUI

/// 復習 / SRS。忘却度で分類し、期限が来た語を出題する。
struct ReviewView: View {
    @Query private var progress: [WordProgress]
    @State private var dueWords: [WordListItem] = []
    @State private var loading = false

    private var soon: [WordProgress] { progress.filter { SRSScheduler.Bucket.of($0) == .soon } }
    private var check: [WordProgress] { progress.filter { SRSScheduler.Bucket.of($0) == .check } }
    private var relaxed: [WordProgress] {
        progress.filter { $0.lastReviewedAt != nil && SRSScheduler.Bucket.of($0) == .relaxed }
    }

    /// 今日の復習（soon + check）の出題ID。単語のみ（慣用句キーは除外）。
    private var reviewIDs: [String] {
        (soon + check).map(\.key).filter { $0.allSatisfy(\.isNumber) }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: Spacing.l) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("復習").font(KBFont.mincho(30))
                        Text("忘れる前に、もう一度").font(KBFont.gothic(12)).foregroundStyle(Color.kbTextMuted)
                    }

                    HStack(spacing: Spacing.s) {
                        bucketCard(count: soon.count, title: "もうすぐ\n忘れる", color: .kbAccent, bg: Color(hex: "FBF1EF"))
                        bucketCard(count: check.count, title: "そろそろ\n確認", color: .kbGold, bg: Color(hex: "FBF6EA"))
                        bucketCard(count: relaxed.count, title: "まだ\n余裕", color: .kbGreen, bg: Color(hex: "EDF1EA"))
                    }

                    NavigationLink {
                        FlashcardView(reviewIDs: reviewIDs)
                    } label: {
                        HStack(spacing: 11) {
                            KotodamaView(size: 42)
                            VStack(alignment: .leading, spacing: 1) {
                                Text("今日の復習 \(soon.count + check.count)語")
                                    .font(KBFont.gothic(15, weight: .bold)).foregroundStyle(.white)
                                Text("5分くらいで終わるよ")
                                    .font(KBFont.gothic(11.5)).foregroundStyle(Color.white.opacity(0.85))
                            }
                            Spacer()
                            Text("はじめる")
                                .font(KBFont.gothic(13, weight: .bold)).foregroundStyle(Color.kbPrimaryDeep)
                                .padding(.horizontal, 16).padding(.vertical, 9)
                                .background(.white, in: Capsule())
                        }
                        .padding(15)
                        .background(Color.kbPrimaryGradient, in: RoundedRectangle(cornerRadius: Radius.l))
                    }
                    .buttonStyle(.plain)

                    if !dueWords.isEmpty {
                        Text("まもなく忘れそうな語")
                            .font(KBFont.gothic(13, weight: .bold)).foregroundStyle(Color.kbTextSub)
                        VStack(spacing: 0) {
                            ForEach(dueWords) { item in
                                NavigationLink {
                                    WordPagerView(items: dueWords, startEntryNo: item.entry_no)
                                } label: {
                                    WordRow(item: item, status: .learning)
                                        .padding(.horizontal, 14)
                                }
                                .buttonStyle(.plain)
                                Divider()
                            }
                        }
                        .background(Color.kbSurface, in: RoundedRectangle(cornerRadius: Radius.l))
                        .overlay(RoundedRectangle(cornerRadius: Radius.l).stroke(Color.kbBorder))
                    }
                }
                .padding(Spacing.l)
            }
            .background(Color.kbBackground)
            .navigationBarTitleDisplayMode(.inline)
            .task { await loadDue() }
        }
    }

    private func bucketCard(count: Int, title: String, color: Color, bg: Color) -> some View {
        VStack(spacing: 3) {
            Text("\(count)").font(KBFont.mincho(26)).foregroundStyle(color)
            Text(title).font(KBFont.gothic(10.5)).foregroundStyle(Color.kbTextMuted)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity).padding(.vertical, 13)
        .background(bg, in: RoundedRectangle(cornerRadius: Radius.m))
        .overlay(RoundedRectangle(cornerRadius: Radius.m).stroke(color.opacity(0.3)))
    }

    private func loadDue() async {
        let ids = (soon + check).map(\.key).filter { $0.allSatisfy(\.isNumber) }
        guard !ids.isEmpty else { dueWords = []; return }
        loading = true
        if let resp = try? await KobunAPIService.shared.words(ids: Array(ids.prefix(20))) {
            dueWords = resp.items
        }
        loading = false
    }
}
