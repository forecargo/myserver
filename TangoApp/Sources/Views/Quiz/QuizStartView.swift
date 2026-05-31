import SwiftUI
import SwiftData

struct QuizStartView: View {
    @State private var vm = QuizViewModel()
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        phaseContent
            .navigationTitle("クイズ")
            .task {
                if vm.availableBatches.isEmpty { await vm.loadBatches() }
            }
    }

    @ViewBuilder
    private var phaseContent: some View {
        switch vm.phase {
        case .setup:
            setupForm
        case .loading:
            loadingView
        case .running:
            QuizQuestionView(vm: vm)
        case .finished:
            QuizResultView(vm: vm)
        }
    }

    private var setupForm: some View {
        @Bindable var vmBindable = vm
        return Form {
            batchSection(vm: vmBindable)
            countSection(vm: vmBindable)
            filterSection(vm: vmBindable)
            errorSection
            startSection
        }
    }

    private func batchSection(vm: QuizViewModel) -> some View {
        @Bindable var vmBindable = vm
        return Section("バッチ") {
            Picker("バッチ", selection: Binding(
                get: { vm.selectedBatch ?? "" },
                set: { vmBindable.selectedBatch = $0 }
            )) {
                ForEach(vm.availableBatches, id: \.self) { batch in
                    Text(batch.formattedBatchName).tag(batch)
                }
            }
            .pickerStyle(.menu)
        }
    }

    private func countSection(vm: QuizViewModel) -> some View {
        @Bindable var vmBindable = vm
        return Section("出題数") {
            Picker("問題数", selection: $vmBindable.questionCount) {
                Text("5 問").tag(5)
                Text("10 問").tag(10)
                Text("20 問").tag(20)
            }
            .pickerStyle(.segmented)
        }
    }

    private func filterSection(vm: QuizViewModel) -> some View {
        @Bindable var vmBindable = vm
        return Section("フィルタ") {
            Toggle("お気に入りのみ", isOn: $vmBindable.filterFavoritesOnly)
            Toggle("未習のみ", isOn: $vmBindable.filterUnlearnedOnly)
        }
    }

    @ViewBuilder
    private var errorSection: some View {
        if let error = vm.errorMessage {
            Section {
                Text(error).foregroundStyle(.red).font(.caption)
            }
        }
    }

    private var startSection: some View {
        Section {
            Button {
                Task { await vm.start(context: modelContext) }
            } label: {
                HStack {
                    Spacer()
                    Text("開始")
                        .font(.body.weight(.semibold))
                    Spacer()
                }
            }
            .disabled(vm.selectedBatch == nil)
        }
    }

    private var loadingView: some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            ProgressView(value: vm.loadProgress)
                .progressViewStyle(.linear)
                .padding(.horizontal, DesignTokens.Spacing.xl)
            Text("問題を準備中…\(Int(vm.loadProgress * 100))%")
                .font(.caption)
                .foregroundStyle(Color.taOnSurfaceVariant)
        }
    }
}
