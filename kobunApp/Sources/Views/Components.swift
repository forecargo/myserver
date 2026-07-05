import SwiftData
import SwiftUI

// MARK: - マスコット「ことだま」

/// マスコット表示。正式画像（Assets: "kotodama"）に差し替えるまでの仮表示。
struct KotodamaView: View {
    var size: CGFloat = 80

    var body: some View {
        ZStack {
            Circle().fill(Color(hex: "F3E9D7"))
            // TODO: 正式なマスコット画像 "kotodama" を Assets.xcassets に追加して差し替える。
            Image(systemName: "bird.fill")
                .font(.system(size: size * 0.42))
                .foregroundStyle(Color.kbPrimaryDeep)
        }
        .frame(width: size, height: size)
        .overlay(Circle().stroke(.white, lineWidth: 2))
        .shadow(color: Color.kbPrimary.opacity(0.25), radius: 6, y: 3)
    }
}

/// ことだまの吹き出し（応援メッセージ）。
struct KotodamaBubble: View {
    var text: String

    var body: some View {
        Text(text)
            .font(KBFont.hand(13))
            .foregroundStyle(Color.kbPrimaryDeep)
            .padding(.horizontal, 13)
            .padding(.vertical, 7)
            .background(Color.kbBubble, in: RoundedRectangle(cornerRadius: 13))
            .overlay(RoundedRectangle(cornerRadius: 13).stroke(Color.kbBubbleBorder))
    }
}

// MARK: - カード画像

/// API の image_url（ホスト相対）を解決して表示する暗記カード画像。
struct CardImage: View {
    let imageURL: String?
    @AppStorage("api_base_url") private var apiBaseURL = KobunAPIService.defaultBaseURL
    @State private var uiImage: UIImage?
    @State private var failed = false

    var body: some View {
        let base = URL(string: apiBaseURL) ?? URL(string: KobunAPIService.defaultBaseURL)!
        let resolved = KobunAPIService.imageURL(imageURL, base: base)
        content
            .task(id: resolved) { await load(resolved) }
    }

    @ViewBuilder private var content: some View {
        if let uiImage {
            Image(uiImage: uiImage).resizable().scaledToFit()
        } else if failed {
            ZStack {
                Color.kbSurface
                Image(systemName: "photo").font(.largeTitle).foregroundStyle(Color.kbTextMuted)
            }
        } else {
            ZStack { Color.kbSurface; ProgressView() }
        }
    }

    private func load(_ url: URL?) async {
        guard let url else { uiImage = nil; failed = true; return }
        // 同期メモリヒットなら即時表示してチラつきを防ぐ
        if let hit = ImageCache.shared.cachedImage(for: url) {
            uiImage = hit; failed = false; return
        }
        uiImage = nil; failed = false
        if let img = await ImageCache.shared.image(for: url) {
            uiImage = img
        } else {
            failed = true
        }
    }
}

// MARK: - 学習状態ドット

struct StatusDot: View {
    var status: LearnStatus

    var body: some View {
        Circle().fill(color).frame(width: 9, height: 9)
    }

    private var color: Color {
        switch status {
        case .mastered: return .kbDotMastered
        case .learning: return .kbDotLearning
        case .unlearned: return .kbDotUnlearned
        }
    }
}

// MARK: - 品詞チップ

struct POSChip: View {
    var text: String

    var body: some View {
        Text(text)
            .font(KBFont.gothic(12, weight: .bold))
            .foregroundStyle(Color.kbPrimaryDeep)
            .padding(.horizontal, 12)
            .padding(.vertical, 5)
            .background(Color.kbBubble, in: Capsule())
    }
}

// MARK: - 達成リング

struct ProgressRing: View {
    var progress: Double  // 0...1

    var body: some View {
        ZStack {
            Circle().stroke(Color.kbBorderStrong, lineWidth: 13)
            Circle()
                .trim(from: 0, to: max(0.0001, min(progress, 1)))
                .stroke(Color.kbPrimary, style: StrokeStyle(lineWidth: 13, lineCap: .round))
                .rotationEffect(.degrees(-90))
        }
    }
}

// MARK: - ホームメニュー行

struct HomeMenuRow: View {
    var title: String
    var subtitle: String
    var systemImage: String
    var filled: Bool
    var badge: String?

    var body: some View {
        HStack(spacing: 13) {
            ZStack {
                RoundedRectangle(cornerRadius: 12)
                    .fill(filled ? Color.white.opacity(0.22) : Color.kbBubble)
                    .frame(width: 40, height: 40)
                Image(systemName: systemImage)
                    .foregroundStyle(filled ? .white : Color.kbPrimary)
            }
            VStack(alignment: .leading, spacing: 1) {
                Text(title).font(KBFont.gothic(15, weight: .bold))
                Text(subtitle).font(KBFont.gothic(11.5))
                    .foregroundStyle(filled ? Color.white.opacity(0.85) : Color.kbTextMuted)
            }
            Spacer()
            if let badge {
                Text(badge)
                    .font(KBFont.gothic(11, weight: .bold))
                    .foregroundStyle(.white)
                    .padding(.horizontal, 8).padding(.vertical, 3)
                    .background(Color.kbAccent, in: Capsule())
            } else {
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .bold))
                    .foregroundStyle(filled ? Color.white.opacity(0.8) : Color.kbBorderStrong)
            }
        }
        .foregroundStyle(filled ? .white : Color.kbText)
        .padding(15)
        .background {
            if filled {
                RoundedRectangle(cornerRadius: Radius.l).fill(Color.kbPrimaryGradient)
            } else {
                RoundedRectangle(cornerRadius: Radius.l).fill(Color.kbSurface)
            }
        }
        .overlay(
            RoundedRectangle(cornerRadius: Radius.l)
                .stroke(filled ? Color.clear : Color.kbBorder)
        )
    }
}

// MARK: - SwiftData ヘルパ

/// 進捗レコードの取得・生成、学習量の加算をまとめる。
@MainActor
enum ProgressStore {
    static func progress(for key: String, in context: ModelContext) -> WordProgress {
        var descriptor = FetchDescriptor<WordProgress>(predicate: #Predicate { $0.key == key })
        descriptor.fetchLimit = 1
        if let found = try? context.fetch(descriptor).first { return found }
        let created = WordProgress(key: key)
        context.insert(created)
        return created
    }

    static func bumpToday(in context: ModelContext) {
        let key = DayKey.today
        var descriptor = FetchDescriptor<DailyStudyLog>(predicate: #Predicate { $0.dayKey == key })
        descriptor.fetchLimit = 1
        if let log = try? context.fetch(descriptor).first {
            log.learnedCount += 1
        } else {
            context.insert(DailyStudyLog(dayKey: key, learnedCount: 1))
        }
    }
}
