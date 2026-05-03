import SwiftUI

struct DetailView: View {
    let result: SearchResult

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: Spacing.lg) {
                // Header
                VStack(alignment: .leading, spacing: Spacing.sm) {
                    Text(stripFootnoteRefs(result.breadcrumb))
                        .font(.system(size: 12))
                        .foregroundStyle(Color.glOnSurfaceVariant)

                    RequirementBadgeView(kind: result.requirementKind)
                }

                Divider()

                // Body text (Markdown-rendered)
                GuidelineMarkdownView(text: result.text)

                // Footnotes
                if !result.footnotes.isEmpty {
                    Divider()
                    DisclosureGroup("脚注 (\(result.footnotes.count)件)") {
                        VStack(alignment: .leading, spacing: Spacing.sm) {
                            ForEach(result.footnotes, id: \.ref) { fn in
                                HStack(alignment: .top, spacing: Spacing.sm) {
                                    Text("※" + fn.ref.trimmingCharacters(in: .init(charactersIn: "^")))
                                        .font(.system(size: 12, weight: .semibold, design: .monospaced))
                                        .foregroundStyle(Color.glPrimary)
                                        .frame(width: 40, alignment: .leading)
                                    Text(fn.text)
                                        .font(.system(size: 13))
                                        .foregroundStyle(Color.glOnSurfaceVariant)
                                        .fixedSize(horizontal: false, vertical: true)
                                }
                            }
                        }
                        .padding(.top, Spacing.sm)
                    }
                    .font(.system(size: 14, weight: .medium))
                    .foregroundStyle(Color.glOnSurfaceVariant)
                }
            }
            .padding(Spacing.lg)
        }
        .background(Color.glSurface)
        .navigationTitle("\(result.section_id) \(plainTitle(result.title))")
        .navigationBarTitleDisplayMode(.inline)
    }

    private static let footnoteRefRegex = try! NSRegularExpression(pattern: #"\[\^[^\]]+\]"#)

    private func stripFootnoteRefs(_ s: String) -> String {
        let range = NSRange(s.startIndex..., in: s)
        return Self.footnoteRefRegex.stringByReplacingMatches(in: s, range: range, withTemplate: "")
    }

    private func plainTitle(_ title: String) -> String {
        let parts = title.split(separator: " ", maxSplits: 1)
        let raw = parts.count > 1 ? String(parts[1]) : title
        return stripFootnoteRefs(raw)
    }
}
