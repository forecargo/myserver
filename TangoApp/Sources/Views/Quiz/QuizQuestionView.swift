import SwiftUI
import SwiftData

struct QuizQuestionView: View {
    @Bindable var vm: QuizViewModel
    @Environment(\.modelContext) private var modelContext
    @State private var showAbortConfirm = false

    var body: some View {
        if let q = vm.currentQuestion {
            VStack(spacing: DesignTokens.Spacing.md) {
                progressHeader

                VStack(spacing: DesignTokens.Spacing.sm) {
                    Text(q.item.word)
                        .font(.system(size: 36, weight: .bold))
                    Text(q.item.phonetic)
                        .font(.callout.italic())
                        .foregroundStyle(Color.taOnSurfaceVariant)
                    Button {
                        SpeechService.shared.speakWord(q.item)
                    } label: {
                        Image(systemName: "speaker.wave.2.fill")
                            .font(.title3)
                            .foregroundStyle(Color.taPrimary)
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(DesignTokens.Spacing.lg)
                .background(
                    RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
                        .fill(Color(.secondarySystemGroupedBackground))
                )

                feedbackBanner(question: q)

                choicesGrid(question: q)

                if vm.selectedChoice != nil {
                    Button {
                        vm.next(context: modelContext)
                    } label: {
                        Text(vm.currentIndex + 1 >= vm.questions.count ? "結果を見る" : "次へ")
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

                Spacer()
            }
            .padding()
            .background(Color(.systemGroupedBackground))
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("終了") { showAbortConfirm = true }
                        .foregroundStyle(.red)
                }
            }
            .alert("クイズを終了しますか？", isPresented: $showAbortConfirm) {
                Button("終了する", role: .destructive) {
                    vm.abort()
                }
                Button("続ける", role: .cancel) {}
            } message: {
                Text("ここまでの正答数 \(vm.correctCount) / \(vm.currentIndex + (vm.selectedChoice == nil ? 0 : 1)) は記録されません")
            }
            .task(id: vm.currentIndex) {
                try? await Task.sleep(for: .milliseconds(500))
                guard !Task.isCancelled else { return }
                if let current = vm.currentQuestion {
                    SpeechService.shared.speakWord(current.item)
                }
            }
        } else {
            Text("問題が見つかりません")
        }
    }

    @ViewBuilder
    private func feedbackBanner(question: QuizGenerator.Question) -> some View {
        if let selected = vm.selectedChoice {
            let isCorrect = selected == question.correctIndex
            HStack(alignment: .top, spacing: 10) {
                Image(systemName: isCorrect ? "checkmark.seal.fill" : "xmark.octagon.fill")
                    .font(.title2)
                VStack(alignment: .leading, spacing: 2) {
                    Text(isCorrect ? "正解！" : "不正解")
                        .font(.title3.weight(.heavy))
                    if !isCorrect {
                        Text("正解: \(question.correctText)")
                            .font(.caption)
                            .foregroundStyle(Color.taOnSurface)
                    }
                }
                Spacer()
            }
            .padding()
            .background(
                RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
                    .fill(isCorrect
                          ? Color.green.opacity(0.18)
                          : Color.red.opacity(0.18))
            )
            .foregroundStyle(isCorrect ? Color.green : Color.red)
            .transition(.scale.combined(with: .opacity))
        }
    }

    private var progressHeader: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(vm.progressText)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(Color.taOnSurfaceVariant)
                Spacer()
                Text("正解 \(vm.correctCount)")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.green)
            }
            ProgressView(value: Double(vm.currentIndex), total: Double(max(vm.questions.count, 1)))
                .tint(.taPrimary)
        }
    }

    private func choicesGrid(question: QuizGenerator.Question) -> some View {
        VStack(spacing: DesignTokens.Spacing.sm) {
            ForEach(Array(question.choices.enumerated()), id: \.offset) { idx, choice in
                Button {
                    vm.answer(choice: idx, context: modelContext)
                } label: {
                    HStack {
                        Text("\(letterFor(idx))")
                            .font(.body.weight(.heavy))
                            .frame(width: 28, height: 28)
                            .background(Circle().fill(Color(.systemGray5)))
                        Text(choice)
                            .font(.body)
                            .multilineTextAlignment(.leading)
                        Spacer()
                        if vm.selectedChoice != nil {
                            if idx == question.correctIndex {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.green)
                            } else if idx == vm.selectedChoice {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundStyle(.red)
                            }
                        }
                    }
                    .padding()
                    .background(background(for: idx, question: question))
                    .foregroundStyle(Color.taOnSurface)
                }
                .disabled(vm.selectedChoice != nil)
                .buttonStyle(.plain)
            }
        }
    }

    private func background(for idx: Int, question: QuizGenerator.Question) -> some View {
        let shape = RoundedRectangle(cornerRadius: DesignTokens.Radius.card)
        guard vm.selectedChoice != nil else {
            return shape.fill(Color(.secondarySystemGroupedBackground))
        }
        if idx == question.correctIndex {
            return shape.fill(Color.green.opacity(0.18))
        }
        if idx == vm.selectedChoice {
            return shape.fill(Color.red.opacity(0.18))
        }
        return shape.fill(Color(.secondarySystemGroupedBackground))
    }

    private func letterFor(_ idx: Int) -> String {
        let letters = ["A", "B", "C", "D"]
        return idx < letters.count ? letters[idx] : "\(idx + 1)"
    }
}
