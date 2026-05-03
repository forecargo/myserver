import SwiftUI

struct ResultCardView: View {
    let result: SearchResult
    var highlightQuery: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: Spacing.sm) {
            // Title row + score badge
            HStack(alignment: .top) {
                Text(result.title)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(Color.glPrimary)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: Spacing.sm)
                ScoreBadgeView(score: result.similarity_score)
            }

            // Breadcrumb
            Text(result.breadcrumb)
                .font(.system(size: 11))
                .foregroundStyle(Color.glOnSurfaceVariant)
                .lineLimit(2)

            // Requirement badge
            RequirementBadgeView(kind: result.requirementKind)

            // Snippet with keyword highlighting
            highlightedText(result.snippet, query: highlightQuery)
                .font(.system(size: 14))
                .foregroundStyle(Color.glOnSurface)
                .lineSpacing(4)
                .lineLimit(4)
        }
        .padding(Spacing.md)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.glSurface)
        .clipShape(RoundedRectangle(cornerRadius: Radius.lg))
        .overlay(
            RoundedRectangle(cornerRadius: Radius.lg)
                .stroke(Color.glOutlineVariant, lineWidth: 1)
        )
    }

    private func highlightedText(_ text: String, query: String) -> Text {
        guard !query.isEmpty else { return Text(text) }
        let keywords = query.split(separator: " ").map(String.init).filter { !$0.isEmpty }
        var attributed = AttributedString(text)
        for keyword in keywords {
            var searchRange = attributed.startIndex..<attributed.endIndex
            while let range = attributed[searchRange].range(of: keyword, options: .caseInsensitive) {
                attributed[range].backgroundColor = UIColor.systemYellow.withAlphaComponent(0.4)
                guard range.upperBound < attributed.endIndex else { break }
                searchRange = range.upperBound..<attributed.endIndex
            }
        }
        return Text(attributed)
    }
}
