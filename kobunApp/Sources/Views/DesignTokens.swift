import SwiftUI
import UIKit

// MARK: - 配色（デザイン由来 / 水彩 × 藤色 × 明朝）
// ライト＝水彩クリーム、ダーク＝夜の勉強向けの暖かい藤色がかった夜。
// すべて adaptive(light:dark:) でライト/ダークの色を持ち、システム/設定の外観に追従する。

extension Color {
    init(hex: String) {
        let (r, g, b) = Color.rgbComponents(hex)
        self.init(red: r, green: g, blue: b)
    }

    fileprivate static func rgbComponents(_ hex: String) -> (Double, Double, Double) {
        let s = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
        var v: UInt64 = 0
        Scanner(string: s).scanHexInt64(&v)
        return (Double((v >> 16) & 0xFF) / 255, Double((v >> 8) & 0xFF) / 255, Double(v & 0xFF) / 255)
    }

    /// ライト/ダークで切り替わる動的カラー（外観に追従）。
    static func adaptive(light: String, dark: String) -> Color {
        Color(UIColor { traits in
            let (r, g, b) = traits.userInterfaceStyle == .dark
                ? rgbComponents(dark) : rgbComponents(light)
            return UIColor(red: r, green: g, blue: b, alpha: 1)
        })
    }

    static let kbBackground = adaptive(light: "F2EADA", dark: "211C28")
    static let kbSurface = adaptive(light: "FCF9F1", dark: "2D2736")
    static let kbBorder = adaptive(light: "EBE2D0", dark: "3C3548")
    static let kbBorderStrong = adaptive(light: "E6DCC8", dark: "4A4159")
    static let kbPrimary = adaptive(light: "8A77B0", dark: "A593CC")
    static let kbPrimaryDeep = adaptive(light: "6B5A93", dark: "C2B2E0")
    static let kbAccent = adaptive(light: "C15B43", dark: "E08368")
    static let kbAccentSoft = adaptive(light: "C08579", dark: "D2A294")
    static let kbGreen = adaptive(light: "7E9A78", dark: "9BBD93")
    static let kbGreenDeep = adaptive(light: "5E8158", dark: "8CB385")
    static let kbGold = adaptive(light: "C9A24B", dark: "E2C070")
    static let kbText = adaptive(light: "36302A", dark: "ECE4D6")
    static let kbTextSub = adaptive(light: "8C8273", dark: "B3A893")
    static let kbTextMuted = adaptive(light: "9C9384", dark: "968C7C")
    static let kbBody = adaptive(light: "5B554C", dark: "C9C1B4")
    // クイズ正解のベタ塗り。白文字がはっきり読める濃さ（ライト/ダーク両対応）。
    static let kbCorrectFill = adaptive(light: "3C6033", dark: "2F5A2A")
    static let kbDotMastered = adaptive(light: "7E9A78", dark: "9BBD93")
    static let kbDotLearning = adaptive(light: "8A77B0", dark: "A593CC")
    static let kbDotUnlearned = adaptive(light: "D8CDBA", dark: "5A5247")
    static let kbBubble = adaptive(light: "EEE9F4", dark: "332C42")
    static let kbBubbleBorder = adaptive(light: "E0D7EC", dark: "4C4166")

    static let kbPrimaryGradient = LinearGradient(
        colors: [adaptive(light: "9281B8", dark: "8E7CB8"), adaptive(light: "6B5A93", dark: "5E4E84")],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )
}

// MARK: - フォント
// 正式なカスタムフォント（Shippori Mincho / Zen Kaku Gothic New / Klee One）を Sources/Fonts/ に
// 同梱し Info.plist の UIAppFonts に登録するまでは、システムフォントで代替する。

enum KBFont {
    static func mincho(_ size: CGFloat, weight: Font.Weight = .bold) -> Font {
        .system(size: size, weight: weight, design: .serif)
    }

    static func gothic(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight)
    }

    static func hand(_ size: CGFloat) -> Font {
        .system(size: size, design: .rounded)
    }
}

// MARK: - 余白・角丸

enum Spacing {
    static let xs: CGFloat = 4
    static let s: CGFloat = 8
    static let m: CGFloat = 12
    static let l: CGFloat = 16
    static let xl: CGFloat = 24
}

enum Radius {
    static let s: CGFloat = 9
    static let m: CGFloat = 14
    static let l: CGFloat = 18
    static let xl: CGFloat = 26
}
