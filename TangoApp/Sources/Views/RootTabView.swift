import SwiftUI

struct RootTabView: View {
    var body: some View {
        TabView {
            NavigationStack {
                BatchListView()
            }
            .tabItem {
                Label("単語帳", systemImage: "book.fill")
            }

            NavigationStack {
                LearnView()
            }
            .tabItem {
                Label("学習", systemImage: "star.fill")
            }

            NavigationStack {
                QuizStartView()
            }
            .tabItem {
                Label("クイズ", systemImage: "questionmark.circle.fill")
            }

            NavigationStack {
                SettingsView()
            }
            .tabItem {
                Label("設定", systemImage: "gearshape.fill")
            }
        }
        .tint(.taPrimary)
    }
}
