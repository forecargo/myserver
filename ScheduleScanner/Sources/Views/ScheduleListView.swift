import SwiftUI

struct ScheduleListView: View {
    let items: [ScheduleItem]
    @EnvironmentObject var vm: ScheduleViewModel
    @State private var showConfirmation = false

    var body: some View {
        List(items, selection: $vm.selectedIDs) { item in
            ScheduleRowView(item: item)
                .tag(item.id)
        }
        .listStyle(.insetGrouped)
        .environment(\.editMode, .constant(.active))
        .navigationTitle("確認・選択")
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button("キャンセル", role: .destructive) {
                    vm.reset()
                }
            }
            ToolbarItem(placement: .bottomBar) {
                Button {
                    showConfirmation = true
                } label: {
                    Label("選択した予定を登録 (\(vm.selectedIDs.count)件)", systemImage: "calendar.badge.plus")
                        .font(.headline)
                }
                .disabled(vm.selectedIDs.isEmpty)
                .buttonStyle(.borderedProminent)
            }
        }
        .alert(
            "\(vm.selectedIDs.count)件の予定を登録しますか？",
            isPresented: $showConfirmation
        ) {
            Button("登録する") {
                vm.saveSelected(items)
            }
            Button("キャンセル", role: .cancel) {}
        }
    }
}
