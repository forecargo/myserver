import Foundation
import Observation

@MainActor
@Observable
final class BatchListViewModel {
    var batches: [String] = []
    var isLoading: Bool = false
    var errorMessage: String?

    private let api = TangoAPIService.shared

    func load(forceRefresh: Bool = false) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            batches = try await api.listBatches(forceRefresh: forceRefresh)
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
