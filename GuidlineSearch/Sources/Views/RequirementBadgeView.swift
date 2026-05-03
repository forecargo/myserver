import SwiftUI

struct RequirementBadgeView: View {
    let kind: RequirementKind

    private var label: String {
        switch kind {
        case .basic:     return "基本対応"
        case .desirable: return "望ましい対応"
        case .general:   return ""
        }
    }

    private var bgColor: Color {
        switch kind {
        case .basic:     return Color.glBasicBg
        case .desirable: return Color.glDesirableBg
        case .general:   return .clear
        }
    }

    private var textColor: Color {
        switch kind {
        case .basic:     return Color.glBasicText
        case .desirable: return Color.glDesirableText
        case .general:   return .clear
        }
    }

    var body: some View {
        if kind != .general {
            Text(label)
                .font(.system(size: 11, weight: .bold))
                .foregroundStyle(textColor)
                .padding(.horizontal, Spacing.sm)
                .padding(.vertical, Spacing.xs)
                .background(bgColor)
                .clipShape(.capsule)
        }
    }
}
