import Foundation

struct ScheduleResponse: Decodable {
    let schedules: [ScheduleItem]
}

struct ScheduleItem: Decodable, Identifiable {
    let id = UUID()
    let date: String
    let dayOfWeek: String
    let startTime: String
    let endTime: String
    let category: String
    let title: String
    let location: String
    let reserver: String

    enum CodingKeys: String, CodingKey {
        case date, category, title, location, reserver
        case dayOfWeek = "day_of_week"
        case startTime = "start_time"
        case endTime   = "end_time"
    }

    func startDate() -> Date? { combine(date: date, time: startTime) }
    func endDate()   -> Date? { combine(date: date, time: endTime) }

    private func combine(date: String, time: String) -> Date? {
        guard !date.isEmpty, !time.isEmpty else { return nil }
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy/MM/dd HH:mm"
        formatter.locale = Locale(identifier: "ja_JP")
        return formatter.date(from: "\(date) \(time)")
    }
}
