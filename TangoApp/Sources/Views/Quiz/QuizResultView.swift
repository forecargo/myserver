import SwiftUI

struct QuizResultView: View {
    @Bindable var vm: QuizViewModel

    var body: some View {
        ScrollView {
            VStack(spacing: DesignTokens.Spacing.lg) {
                VStack(spacing: 6) {
                    Text("\(vm.accuracyPercent)%")
                        .font(.system(size: 56, weight: .heavy))
                        .foregroundStyle(Color.taPrimary)
                    Text("\(vm.correctCount) / \(vm.questions.count) 問正解")
                        .font(.body)
                        .foregroundStyle(Color.taOnSurfaceVariant)
                }
                .padding(DesignTokens.Spacing.lg)
                .frame(maxWidth: .infinity)
                .background(
                    RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
                        .fill(Color(.secondarySystemGroupedBackground))
                )

                if !vm.wrongDomains.isEmpty {
                    VStack(alignment: .leading, spacing: DesignTokens.Spacing.sm) {
                        Text("間違えた単語")
                            .font(.system(size: 12, weight: .heavy))
                            .tracking(1)
                            .foregroundStyle(Color.taOnSurfaceVariant)
                        ForEach(vm.wrongDomains, id: \.id) { domain in
                            VStack(alignment: .leading, spacing: 2) {
                                HStack {
                                    Text(domain.item.word).font(.body.weight(.semibold))
                                    Spacer()
                                    Text(domain.item.phonetic)
                                        .font(.caption.italic())
                                        .foregroundStyle(Color.taOnSurfaceVariant)
                                }
                                let meanings = formattedMeanings(domain.item)
                                if !meanings.isEmpty {
                                    Text(meanings)
                                        .font(.caption)
                                        .foregroundStyle(Color.taOnSurfaceVariant)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                        .fixedSize(horizontal: false, vertical: true)
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
                            .fill(Color(.secondarySystemGroupedBackground))
                    )
                }

                Button {
                    vm.restart()
                } label: {
                    Text("もう一度")
                        .font(.body.weight(.semibold))
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(
                            RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
                                .fill(Color.taPrimary)
                        )
                        .foregroundStyle(.white)
                }
            }
            .padding()
        }
        .background(Color(.systemGroupedBackground))
    }

    private func formattedMeanings(_ item: APIVocabularyItem) -> String {
        item.definitions.compactMap { group -> String? in
            let joined = group.meanings
                .map(stripLeadingCircledNumber)
                .filter { !$0.isEmpty }
                .joined(separator: "、")
            guard !joined.isEmpty else { return nil }
            return group.part_of_speech.isEmpty
                ? joined
                : "(\(group.part_of_speech)) \(joined)"
        }.joined(separator: " / ")
    }

    // ① ② など先頭の丸数字を除去する
    private func stripLeadingCircledNumber(_ s: String) -> String {
        guard let first = s.unicodeScalars.first,
              (0x2460...0x2473).contains(first.value)
        else { return s }
        return String(s.dropFirst()).trimmingCharacters(in: .whitespaces)
    }
}
