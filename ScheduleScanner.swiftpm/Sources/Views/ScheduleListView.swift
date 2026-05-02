import SwiftUI

struct ScheduleListView: View {
    let items: [ScheduleItem]
    @EnvironmentObject var vm: ScheduleViewModel

    var body: some View {
        List(items, selection: $vm.selectedIDs) { item in
            ScheduleRowView(item: item)
                .tag(item.id)
        }
        .listStyle(.insetGrouped)
        .environment(\.editMode, .constant(.active))
        .navigationTitle("確認・選択")
        .toolbar {
            ToolbarItem(placement: .bottomBar) {
                Button {
                    vm.saveSelected(items)
                } label: {
                    Label("選択した予定を登録 (\(vm.selectedIDs.count)件)", systemImage: "calendar.badge.plus")
                        .font(.headline)
                }
                .disabled(vm.selectedIDs.isEmpty)
                .buttonStyle(.borderedProminent)
            }
        }
    }
}
