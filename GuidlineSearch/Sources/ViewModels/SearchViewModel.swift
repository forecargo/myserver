import SwiftUI

@MainActor
final class SearchViewModel: ObservableObject {
    @Published var query: String = ""
    @Published var results: [SearchResult] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String? = nil
    @Published var selectedResult: SearchResult? = nil
    @Published var totalChunks: Int = 0

    func search() {
        let trimmed = query.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        errorMessage = nil
        isLoading = true
        results = []
        Task {
            do {
                let response = try await SearchAPIService.shared.search(query: trimmed, topK: 8)
                results = response.results
                totalChunks = response.total_chunks
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }

    func clearError() {
        errorMessage = nil
    }
}
