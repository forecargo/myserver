import EventKit

enum CalendarError: LocalizedError {
    case denied
    case saveFailed(Error)

    var errorDescription: String? {
        switch self {
        case .denied:
            return "カレンダーへのアクセスが拒否されています。設定アプリから許可してください。"
        case .saveFailed(let e):
            return "保存エラー: \(e.localizedDescription)"
        }
    }
}

actor CalendarService {
    static let shared = CalendarService()

    private let store = EKEventStore()

    func requestAccess() async throws {
        let granted: Bool
        if #available(iOS 17, *) {
            granted = try await store.requestWriteOnlyAccessToEvents()
        } else {
            granted = await withCheckedContinuation { cont in
                store.requestAccess(to: .event) { ok, _ in cont.resume(returning: ok) }
            }
        }
        if !granted { throw CalendarError.denied }
    }

    func save(_ items: [ScheduleItem]) async throws {
        for item in items {
            guard let start = item.startDate(), let end = item.endDate() else { continue }
            let event = EKEvent(eventStore: store)
            event.title     = item.title.isEmpty ? "(無題)" : item.title
            event.startDate = start
            event.endDate   = end
            event.location  = item.location.isEmpty ? nil : item.location
            event.notes     = buildNotes(item)
            event.calendar  = store.defaultCalendarForNewEvents
            do {
                try store.save(event, span: .thisEvent)
            } catch {
                throw CalendarError.saveFailed(error)
            }
        }
    }

    private func buildNotes(_ item: ScheduleItem) -> String? {
        var parts: [String] = []
        if !item.category.isEmpty  { parts.append("カテゴリ: \(item.category)") }
        if !item.reserver.isEmpty  { parts.append("予約者: \(item.reserver)") }
        return parts.isEmpty ? nil : parts.joined(separator: "\n")
    }
}
