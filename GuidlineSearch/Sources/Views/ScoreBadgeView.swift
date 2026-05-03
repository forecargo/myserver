import SwiftUI

struct ScoreBadgeView: View {
    let score: Double

    var body: some View {
        Text(String(format: "%.1f%%", score))
            .font(.system(size: 12, weight: .semibold, design: .monospaced))
            .foregroundStyle(Color.glOnSurfaceVariant)
            .padding(.horizontal, Spacing.sm)
            .padding(.vertical, Spacing.xs)
            .background(Color.glSurfaceContainer)
            .clipShape(RoundedRectangle(cornerRadius: Radius.md))
    }
}
