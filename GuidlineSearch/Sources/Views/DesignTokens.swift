import SwiftUI

// Color tokens derived from GuidlineSearch/DESIGN.md
extension Color {
    static let glPrimary         = Color(hex: "#002045")  // Deep Navy
    static let glPrimaryContainer = Color(hex: "#1A365D")
    static let glOnPrimary       = Color.white
    static let glSurface         = Color(hex: "#FAF9FD")
    static let glOnSurface       = Color(hex: "#1A1C1E")
    static let glOnSurfaceVariant = Color(hex: "#43474E")
    static let glOutline         = Color(hex: "#74777F")
    static let glOutlineVariant  = Color(hex: "#C4C6CF")
    static let glSurfaceContainerLow = Color(hex: "#F4F3F7")
    static let glSurfaceContainer    = Color(hex: "#EFEDF1")

    // Requirement type badge colors
    static let glBasicBg   = Color(hex: "#D6E3FF")  // primary-fixed
    static let glBasicText = Color(hex: "#001B3C")  // on-primary-fixed
    static let glDesirableBg   = Color(hex: "#D4EDDA")
    static let glDesirableText = Color(hex: "#1A5C2A")

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

// Spacing constants (8px base grid)
enum Spacing {
    static let xs: CGFloat  = 4
    static let sm: CGFloat  = 8
    static let md: CGFloat  = 16
    static let lg: CGFloat  = 24
    static let xl: CGFloat  = 32
    static let page: CGFloat = 40
}

// Corner radius tokens
enum Radius {
    static let sm:   CGFloat = 2
    static let md:   CGFloat = 6
    static let lg:   CGFloat = 8
    static let full: CGFloat = 9999
}
