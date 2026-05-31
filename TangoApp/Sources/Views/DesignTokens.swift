import SwiftUI

// SPEC_SwiftUI.md §10

enum DesignTokens {
    enum Spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let xl: CGFloat = 32
    }

    enum Radius {
        static let badge: CGFloat = 999
        static let card: CGFloat = 14
        static let chip: CGFloat = 6
    }
}

extension Color {
    static let taPrimary = Color(red: 0xA0/255, green: 0x20/255, blue: 0x40/255)
    static let taSurface = Color(.systemBackground)
    static let taOnSurface = Color(.label)
    static let taOnSurfaceVariant = Color(.secondaryLabel)
    static let taOutline = Color(.separator)
    /// 語源カードの背景。ライト時は薄い黄、ダーク時はディープブラウン。
    static let taOriginBg = Color(uiColor: UIColor { trait in
        if trait.userInterfaceStyle == .dark {
            return UIColor(red: 0x3A/255, green: 0x2F/255, blue: 0x12/255, alpha: 1)
        } else {
            return UIColor(red: 0xFF/255, green: 0xF9/255, blue: 0xE6/255, alpha: 1)
        }
    })

    // レベルバッジ
    static let taLevelA1 = Color(red: 0x8F/255, green: 0xBF/255, blue: 0x7F/255)
    static let taLevelA2 = Color(red: 0x5F/255, green: 0x9F/255, blue: 0xE0/255)
    static let taLevelMax = Color(red: 0xC0/255, green: 0x40/255, blue: 0x20/255)
    static let taLevelDefault = Color(red: 0x86/255, green: 0x86/255, blue: 0x8B/255)
}

enum LevelStyle {
    static func color(for tag: String?) -> Color {
        guard let tag = tag?.uppercased() else { return .taLevelDefault }
        if tag.contains("A1") { return .taLevelA1 }
        if tag.contains("A2") { return .taLevelA2 }
        if tag.contains("最難関") || tag.contains("最難") { return .taLevelMax }
        return .taLevelDefault
    }
}

struct LevelBadge: View {
    let tag: String?

    var body: some View {
        Text(tag ?? "—")
            .font(.system(size: 11, weight: .heavy))
            .tracking(0.5)
            .foregroundStyle(.white)
            .padding(.horizontal, 10)
            .padding(.vertical, 3)
            .background(
                Capsule().fill(tag == nil ? Color.taLevelDefault.opacity(0.5)
                                          : LevelStyle.color(for: tag))
            )
    }
}

struct POSChip: View {
    let pos: String
    var body: some View {
        Text(pos)
            .font(.system(size: 12, weight: .semibold))
            .foregroundStyle(Color.taOnSurface)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(
                RoundedRectangle(cornerRadius: DesignTokens.Radius.chip)
                    .fill(Color(.systemGray6))
            )
    }
}
