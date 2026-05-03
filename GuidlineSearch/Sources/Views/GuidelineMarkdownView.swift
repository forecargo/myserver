import SwiftUI

/// Renders guideline body text as structured Markdown.
/// Handles:
///   - Bullet lists: `- text` (indent 0) and `    - text` (indent 1+)
///   - Inline Markdown: **bold**, _italic_ via AttributedString
///   - Footnote markers `[^N]` are stripped (shown separately in DetailView)
struct GuidelineMarkdownView: View {
    let text: String

    // MARK: - Parsed model

    private struct Block: Identifiable {
        let id = UUID()
        enum Kind {
            case paragraph(String)
            case listItem(content: String, indent: Int)
        }
        let kind: Kind
    }

    // MARK: - Parsing

    private static let footnoteRefRegex = try! NSRegularExpression(pattern: #"\[\^[^\]]+\]"#)

    private static func normalizeFootnoteRefs(_ s: String) -> String {
        let range = NSRange(s.startIndex..., in: s)
        // Replace [^N] with ※N so the reference position stays visible in body text
        return footnoteRefRegex.stringByReplacingMatches(in: s, range: range, withTemplate: "※$1")
    }

    private var blocks: [Block] {
        var result: [Block] = []
        var paraLines: [String] = []

        func flushParagraph() {
            let para = paraLines.joined(separator: "\n").trimmingCharacters(in: .whitespaces)
            if !para.isEmpty { result.append(Block(kind: .paragraph(para))) }
            paraLines = []
        }

        for raw in text.components(separatedBy: "\n") {
            // Normalize tabs → 4 spaces, strip footnote refs
            let normalized = Self.normalizeFootnoteRefs(raw.replacingOccurrences(of: "\t", with: "    "))
            let leadingSpaces = normalized.prefix(while: { $0 == " " }).count
            let indent = leadingSpaces / 4
            let trimmed = normalized.trimmingCharacters(in: .whitespaces)

            if trimmed.isEmpty {
                flushParagraph()
                continue
            }

            if trimmed.hasPrefix("- ") {
                flushParagraph()
                let content = String(trimmed.dropFirst(2))
                result.append(Block(kind: .listItem(content: content, indent: indent)))
            } else {
                paraLines.append(trimmed)
            }
        }
        flushParagraph()
        return result
    }

    // MARK: - Body

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            ForEach(blocks) { block in
                switch block.kind {
                case .paragraph(let s):
                    inlineMarkdown(s)
                        .frame(maxWidth: .infinity, alignment: .leading)

                case .listItem(let content, let indent):
                    listItemView(content: content, indent: indent)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - List item

    @ViewBuilder
    private func listItemView(content: String, indent: Int) -> some View {
        HStack(alignment: .top, spacing: 0) {
            if let (marker, rest) = extractSpecialMarker(content) {
                Text(marker)
                    .font(.system(size: 16))
                    .foregroundStyle(Color.glOnSurface)
                    .lineSpacing(5)
                    .fixedSize(horizontal: true, vertical: false)
                    .padding(.trailing, 4)

                inlineMarkdown(rest)
                    .frame(maxWidth: .infinity, alignment: .leading)
            } else {
                Text("•")
                    .font(.system(size: 13))
                    .foregroundStyle(Color.glOnSurfaceVariant)
                    .frame(width: 16, alignment: .leading)
                    .padding(.top, 3)

                inlineMarkdown(content)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(.leading, CGFloat(indent) * 16)
    }

    // MARK: - Inline Markdown

    @ViewBuilder
    private func inlineMarkdown(_ markdown: String) -> some View {
        if let attributed = try? AttributedString(
            markdown: markdown,
            options: AttributedString.MarkdownParsingOptions(
                interpretedSyntax: .inlineOnlyPreservingWhitespace
            )
        ) {
            Text(attributed)
                .font(.system(size: 16))
                .foregroundStyle(Color.glOnSurface)
                .lineSpacing(5)
                .fixedSize(horizontal: false, vertical: true)
        } else {
            Text(markdown)
                .font(.system(size: 16))
                .foregroundStyle(Color.glOnSurface)
                .lineSpacing(5)
                .fixedSize(horizontal: false, vertical: true)
        }
    }

    // MARK: - Helpers

    private func isCircledNumber(_ c: Character) -> Bool {
        guard let scalar = c.unicodeScalars.first else { return false }
        // ① U+2460 … ⑳ U+2473, also ⑴-⒇, ⒜-⒵ etc.
        return (0x2460...0x24FF).contains(scalar.value)
    }

    private func extractSpecialMarker(_ content: String) -> (marker: String, rest: String)? {
        guard let first = content.first else { return nil }

        if isCircledNumber(first) {
            let afterFirst = content.dropFirst()
            let rest = afterFirst.hasPrefix(" ")
                ? String(afterFirst.dropFirst())
                : String(afterFirst)
            return (String(first), rest)
        }

        if first.isASCII && first.isLetter {
            let afterFirst = content.dropFirst()
            if afterFirst.hasPrefix(". ") {
                let marker = String(first) + "."
                let rest = String(afterFirst.dropFirst(2))
                return (marker, rest)
            }
        }

        return nil
    }
}
