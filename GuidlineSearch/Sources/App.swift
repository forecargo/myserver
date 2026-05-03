import SwiftUI

@main
struct GuidlineSearchApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(SearchViewModel())
        }
    }
}
