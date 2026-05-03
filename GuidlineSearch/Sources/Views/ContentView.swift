import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var vm: SearchViewModel

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Search bar
                SearchBarView(text: $vm.query, onSubmit: vm.search)
                    .padding(.horizontal, Spacing.md)
                    .padding(.vertical, Spacing.sm)
                    .background(Color.glSurface)

                Divider()

                // Content area
                Group {
                    if vm.isLoading {
                        loadingView
                    } else if let error = vm.errorMessage {
                        errorView(message: error)
                    } else if vm.results.isEmpty && !vm.query.isEmpty {
                        emptyView
                    } else {
                        resultList
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
            .background(Color.glSurface)
            .navigationTitle("ガイドライン検索")
            .navigationBarTitleDisplayMode(.large)
            .navigationDestination(item: $vm.selectedResult) { result in
                DetailView(result: result)
            }
        }
        .tint(Color.glPrimary)
    }

    // MARK: - Sub-views

    private var resultList: some View {
        ScrollView {
            LazyVStack(spacing: Spacing.sm) {
                if !vm.results.isEmpty {
                    HStack {
                        Text("\(vm.results.count)件 / \(vm.totalChunks)チャンク中")
                            .font(.system(size: 12))
                            .foregroundStyle(Color.glOnSurfaceVariant)
                        Spacer()
                    }
                    .padding(.horizontal, Spacing.md)
                    .padding(.top, Spacing.sm)
                }

                ForEach(vm.results) { result in
                    ResultCardView(result: result, highlightQuery: vm.query)
                        .padding(.horizontal, Spacing.md)
                        .onTapGesture {
                            vm.selectedResult = result
                        }
                }

                Color.clear.frame(height: Spacing.md)
            }
        }
    }

    private var loadingView: some View {
        VStack(spacing: Spacing.md) {
            ProgressView()
                .scaleEffect(1.2)
                .tint(Color.glPrimary)
            Text("検索中…")
                .font(.system(size: 14))
                .foregroundStyle(Color.glOnSurfaceVariant)
        }
    }

    private var emptyView: some View {
        VStack(spacing: Spacing.md) {
            Image(systemName: "doc.text.magnifyingglass")
                .font(.system(size: 48))
                .foregroundStyle(Color.glOutlineVariant)
            Text("該当するガイドラインが見つかりません")
                .font(.system(size: 15))
                .foregroundStyle(Color.glOnSurfaceVariant)
        }
    }

    private func errorView(message: String) -> some View {
        VStack(spacing: Spacing.md) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 40))
                .foregroundStyle(Color.red)
            Text(message)
                .font(.system(size: 14))
                .foregroundStyle(Color.glOnSurface)
                .multilineTextAlignment(.center)
                .padding(.horizontal, Spacing.lg)
            Button("再試行") {
                vm.clearError()
                vm.search()
            }
            .buttonStyle(.borderedProminent)
            .tint(Color.glPrimary)
        }
    }
}
