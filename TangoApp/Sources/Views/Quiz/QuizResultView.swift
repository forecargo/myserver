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
                            HStack {
                                Text(domain.item.word).font(.body.weight(.semibold))
                                Spacer()
                                Text(domain.item.phonetic)
                                    .font(.caption.italic())
                                    .foregroundStyle(Color.taOnSurfaceVariant)
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
}
