import Foundation
import Observation
import SwiftData

@MainActor
@Observable
final class SettingsViewModel {
    static let defaultBaseURL = "https://forecargo.ngrok.app/tango"
    static let baseURLDefaultsKey = "api_base_url"

    var draftBaseURL: String
    var urlValidationError: String?

    init() {
        self.draftBaseURL = UserDefaults.standard.string(forKey: Self.baseURLDefaultsKey)
            ?? Self.defaultBaseURL
    }

    func saveBaseURL() async -> Bool {
        let trimmed = draftBaseURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URL(string: trimmed),
              url.scheme == "https" || url.scheme == "http" else {
            urlValidationError = "URL の形式が不正です (http:// または https:// で始めてください)"
            return false
        }
        urlValidationError = nil
        UserDefaults.standard.set(trimmed, forKey: Self.baseURLDefaultsKey)
        await TangoAPIService.shared.setBaseURL(url)
        return true
    }

    func clearFavorites(context: ModelContext) {
        let descriptor = FetchDescriptor<WordProgress>(
            predicate: #Predicate { $0.isFavorite == true }
        )
        if let items = try? context.fetch(descriptor) {
            for item in items {
                item.isFavorite = false
            }
            try? context.save()
        }
    }

    func clearHistory(context: ModelContext) {
        let descriptor = FetchDescriptor<WordProgress>()
        if let items = try? context.fetch(descriptor) {
            for item in items {
                item.viewCount = 0
                item.lastViewedAt = nil
                item.correctCount = 0
                item.wrongCount = 0
                item.isLearned = false
            }
            try? context.save()
        }
    }

    func clearQuizHistory(context: ModelContext) {
        let descriptor = FetchDescriptor<QuizAttempt>()
        if let items = try? context.fetch(descriptor) {
            for item in items {
                context.delete(item)
            }
            try? context.save()
        }
    }
}
