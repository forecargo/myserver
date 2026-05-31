import SwiftUI

struct BatchListView: View {
    @State private var vm = BatchListViewModel()

    var body: some View {
        content
            .navigationTitle("単語帳")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await vm.load(forceRefresh: true) }
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
            .navigationDestination(for: BrowseRoute.self, destination: destination)
            .task {
                if vm.batches.isEmpty { await vm.load() }
            }
    }

    @ViewBuilder
    private var content: some View {
        if vm.isLoading {
            ProgressView().controlSize(.large)
        } else if let error = vm.errorMessage {
            errorView(error)
        } else if vm.batches.isEmpty {
            ContentUnavailableView(
                "バッチがありません",
                systemImage: "tray",
                description: Text("tango/data/ に JSON を配置してください")
            )
        } else {
            batchList
        }
    }

    private var batchList: some View {
        List(vm.batches, id: \.self) { batch in
            NavigationLink(value: BrowseRoute.batchWords(batch: batch)) {
                HStack {
                    Image(systemName: "folder.fill")
                        .foregroundStyle(Color.taPrimary)
                    Text(batch.formattedBatchName)
                        .font(.body.weight(.medium))
                }
            }
        }
    }

    private func errorView(_ message: String) -> some View {
        VStack(spacing: DesignTokens.Spacing.md) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundStyle(.orange)
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundStyle(Color.taOnSurfaceVariant)
            Button("再試行") {
                Task { await vm.load(forceRefresh: true) }
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
    }

    @ViewBuilder
    private func destination(_ route: BrowseRoute) -> some View {
        switch route {
        case .batchWords(let batch):
            BatchWordListView(batch: batch)
        case .wordDetail(let ctx):
            WordDetailView(context: ctx)
        }
    }
}
