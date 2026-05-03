import SwiftUI
#if canImport(UIKit)
import UIKit
#endif

// MARK: - Adaptive color helper

#if canImport(UIKit)
private extension UIColor {
    convenience init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        self.init(
            red:   CGFloat((int >> 16) & 0xFF) / 255,
            green: CGFloat((int >> 8)  & 0xFF) / 255,
            blue:  CGFloat(int         & 0xFF) / 255,
            alpha: 1
        )
    }
}
#endif

// MARK: - Color tokens

extension Color {
    #if canImport(UIKit)
    private static func adaptive(light: String, dark: String) -> Color {
        Color(uiColor: UIColor { $0.userInterfaceStyle == .dark
            ? UIColor(hex: dark)
            : UIColor(hex: light)
        })
    }
    #else
    private static func adaptive(light: String, dark: String) -> Color {
        Color(hex: light)
    }
    #endif

    static let glPrimary             = adaptive(light: "#002045", dark: "#9FCBFF")
    static let glPrimaryContainer    = adaptive(light: "#1A365D", dark: "#003066")
    static let glOnPrimary           = adaptive(light: "#FFFFFF", dark: "#002045")
    static let glSurface             = adaptive(light: "#FAF9FD", dark: "#1C1B1F")
    static let glOnSurface           = adaptive(light: "#1A1C1E", dark: "#E4E2E6")
    static let glOnSurfaceVariant    = adaptive(light: "#43474E", dark: "#CAC4D0")
    static let glOutline             = adaptive(light: "#74777F", dark: "#938F99")
    static let glOutlineVariant      = adaptive(light: "#C4C6CF", dark: "#49454F")
    static let glSurfaceContainerLow = adaptive(light: "#F4F3F7", dark: "#211F26")
    static let glSurfaceContainer    = adaptive(light: "#EFEDF1", dark: "#2B2930")

    // Requirement type badge colors
    static let glBasicBg       = adaptive(light: "#D6E3FF", dark: "#004A8F")
    static let glBasicText     = adaptive(light: "#001B3C", dark: "#D6E3FF")
    static let glDesirableBg   = adaptive(light: "#D4EDDA", dark: "#1E4A2A")
    static let glDesirableText = adaptive(light: "#1A5C2A", dark: "#B5DFBE")

    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r = Double((int >> 16) & 0xFF) / 255
        let g = Double((int >> 8)  & 0xFF) / 255
        let b = Double(int         & 0xFF) / 255
        self.init(red: r, green: g, blue: b)
    }
}

// MARK: - Spacing tokens (8px base grid)

enum Spacing {
    static let xs: CGFloat   = 4
    static let sm: CGFloat   = 8
    static let md: CGFloat   = 16
    static let lg: CGFloat   = 24
    static let xl: CGFloat   = 32
    static let page: CGFloat = 40
}

// MARK: - Corner radius tokens

enum Radius {
    static let sm:   CGFloat = 2
    static let md:   CGFloat = 6
    static let lg:   CGFloat = 8
    static let full: CGFloat = 9999
}
