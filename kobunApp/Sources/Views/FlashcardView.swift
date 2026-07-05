import SwiftData
import SwiftUI

/// 暗記カード。デッキ（暗記に追加した語）をスワイプで「覚えた / まだ」に仕分け。
struct FlashcardView: View {
    /// 復習セッションの出題 ID（entry_no）。nil なら暗記デッキ（inFlashcardDeck）を使う。
    let reviewIDs: [String]?

    @Environment(\.modelContext) private var context
    @Query(filter: #Predicate<WordProgress> { $0.inFlashcardDeck }) private var deck: [WordProgress]

    @State private var cards: [WordDetail] = []
    @State private var index = 0
    @State private var dragX: CGFloat = 0
    @State private var loading = false

    private var isReview: Bool { reviewIDs != nil }

    init(reviewIDs: [String]? = nil) {
        self.reviewIDs = reviewIDs
    }

    var body: some View {
        ZStack {
            Color.kbBackground.ignoresSafeArea()
            if loading {
                ProgressView()
            } else if cards.isEmpty {
                emptyState
            } else if index < cards.count {
                cardStack
            } else {
                doneState
            }
        }
        .navigationTitle(isReview ? "今日の復習" : "暗記")
        .navigationBarTitleDisplayMode(.inline)
        .task { await loadDeck() }
    }

    private var emptyState: some View {
        VStack(spacing: Spacing.m) {
            KotodamaView(size: 88)
            Text(isReview ? "今日の復習はありません" : "暗記する語がありません")
                .font(KBFont.gothic(15, weight: .bold))
            Text(isReview ? "また忘れたころに会いましょう" : "単語詳細から「＋ 暗記に追加」してね")
                .font(KBFont.gothic(12)).foregroundStyle(Color.kbTextMuted)
        }
        .padding()
    }

    private var doneState: some View {
        VStack(spacing: Spacing.m) {
            KotodamaView(size: 96)
            KotodamaBubble(text: "全部めくれたね。よくがんばりました！")
            Button("もう一度") { index = 0 }
                .font(KBFont.gothic(14, weight: .bold))
                .foregroundStyle(Color.kbPrimaryDeep)
        }
    }

    private var cardStack: some View {
        let card = cards[index]
        return VStack(spacing: Spacing.l) {
            HStack {
                Spacer()
                Text("\(index + 1) / \(cards.count)")
                    .font(KBFont.gothic(13, weight: .bold)).foregroundStyle(Color.kbTextSub)
            }
            .padding(.horizontal, Spacing.l)

            HStack(spacing: 9) {
                KotodamaView(size: 40)
                KotodamaBubble(text: "右で「覚えた」、左で「まだ」だよ")
            }

            CardImage(imageURL: card.image_url)
                .frame(width: 300, height: 300)
                .clipShape(RoundedRectangle(cornerRadius: Radius.xl))
                .overlay(RoundedRectangle(cornerRadius: Radius.xl).stroke(Color.kbBorder))
                .shadow(color: Color.kbText.opacity(0.18), radius: 18, y: 10)
                .rotationEffect(.degrees(Double(dragX / 20)))
                .offset(x: dragX)
                .overlay(swipeHint)
                .gesture(
                    DragGesture()
                        .onChanged { dragX = $0.translation.width }
                        .onEnded { value in
                            if value.translation.width > 110 { swipe(remembered: true) }
                            else if value.translation.width < -110 { swipe(remembered: false) }
                            else { withAnimation(.spring) { dragX = 0 } }
                        }
                )

            VStack(spacing: 2) {
                Text(card.headword).font(KBFont.mincho(20))
                if let reading = card.reading {
                    Text(reading).font(KBFont.gothic(11)).foregroundStyle(Color.kbTextMuted)
                }
            }

            HStack(spacing: 40) {
                swipeButton(title: "まだ", color: .kbAccentSoft, system: "xmark") { swipe(remembered: false) }
                swipeButton(title: "覚えた", color: .kbGreenDeep, system: "checkmark") { swipe(remembered: true) }
            }
            .padding(.top, Spacing.s)
        }
    }

    @ViewBuilder private var swipeHint: some View {
        if dragX > 40 {
            badge("覚えた", .kbGreenDeep)
        } else if dragX < -40 {
            badge("まだ", .kbAccentSoft)
        }
    }

    private func badge(_ text: String, _ color: Color) -> some View {
        Text(text)
            .font(KBFont.gothic(16, weight: .bold))
            .foregroundStyle(.white)
            .padding(.horizontal, 14).padding(.vertical, 7)
            .background(color, in: Capsule())
    }

    private func swipeButton(title: String, color: Color, system: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: system)
                    .font(.title2).foregroundStyle(color)
                    .frame(width: 62, height: 62)
                    .background(.white, in: Circle())
                    .overlay(Circle().stroke(color.opacity(0.4)))
                Text(title).font(KBFont.gothic(12, weight: .bold)).foregroundStyle(color)
            }
        }
        .buttonStyle(.plain)
    }

    private func swipe(remembered: Bool) {
        guard index < cards.count else { return }
        let key = cards[index].entry_no
        let p = ProgressStore.progress(for: key, in: context)
        SRSScheduler.apply(remembered: remembered, to: p)
        if remembered {
            ProgressStore.bumpToday(in: context)
            p.inFlashcardDeck = false   // 覚えた語はデッキから卒業（次回は表示しない）
        }
        // 「まだ」はデッキに残し、引き続き練習対象にする
        withAnimation(.spring) {
            dragX = 0
            index += 1
        }
    }

    private func loadDeck() async {
        loading = true
        defer { loading = false }
        // 復習なら指定IDを、通常は暗記デッキを対象に。慣用句キーは除外（entry_no は数字）。
        let ids = (reviewIDs ?? deck.map(\.key)).filter { $0.allSatisfy(\.isNumber) }
        var result: [WordDetail] = []
        for id in ids {
            if let detail = try? await KobunAPIService.shared.word(id) { result.append(detail) }
        }
        cards = result
        index = 0
    }
}
