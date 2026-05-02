import SwiftUI

enum AppPhase {
    case idle
    case cropping(UIImage)
    case uploading
    case reviewing([ScheduleItem])
    case saving
    case done(Int)
    case error(String)
}

@MainActor
final class ScheduleViewModel: ObservableObject {
    @Published var phase: AppPhase = .idle
    @Published var selectedIDs: Set<UUID> = []
    @Published var showCamera = false

    func startCropping(_ image: UIImage) {
        phase = .cropping(image)
    }

    func cancelCrop() {
        phase = .idle
    }

    func uploadImage(_ image: UIImage) {
        phase = .uploading
        Task {
            do {
                let items = try await APIService.shared.uploadImage(image)
                phase = .reviewing(items)
                selectedIDs = Set(items.map(\.id))
            } catch {
                phase = .error(error.localizedDescription)
            }
        }
    }

    func saveSelected(_ items: [ScheduleItem]) {
        let toSave = items.filter { selectedIDs.contains($0.id) }
        phase = .saving
        Task {
            do {
                try await CalendarService.shared.requestAccess()
                try await CalendarService.shared.save(toSave)
                phase = .done(toSave.count)
            } catch {
                phase = .error(error.localizedDescription)
            }
        }
    }

    func reset() {
        phase = .idle
        selectedIDs = []
    }
}
