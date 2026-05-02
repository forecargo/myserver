import SwiftUI

@main
struct ScheduleScannerApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(ScheduleViewModel())
        }
    }
}
