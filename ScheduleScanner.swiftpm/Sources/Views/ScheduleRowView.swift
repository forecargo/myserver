import SwiftUI

struct ScheduleRowView: View {
    let item: ScheduleItem

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(item.title.isEmpty ? "(無題)" : item.title)
                .font(.headline)

            HStack {
                Text("\(item.date)\(item.dayOfWeek.isEmpty ? "" : " (\(item.dayOfWeek))")")
                Spacer()
                if !item.startTime.isEmpty || !item.endTime.isEmpty {
                    Text("\(item.startTime) – \(item.endTime)")
                }
            }
            .font(.subheadline)
            .foregroundStyle(.secondary)

            if !item.location.isEmpty {
                Label(item.location, systemImage: "mappin.and.ellipse")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }

            HStack(spacing: 6) {
                if !item.category.isEmpty {
                    Text(item.category)
                        .font(.caption2)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(.blue.opacity(0.15))
                        .foregroundStyle(.blue)
                        .clipShape(Capsule())
                }
                if !item.reserver.isEmpty {
                    Text(item.reserver)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}
