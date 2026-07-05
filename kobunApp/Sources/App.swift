import SwiftData
import SwiftUI

/// 古文単語アプリ「ことだま」エントリポイント。
@main
struct KobunApp: App {
    @AppStorage("api_base_url") private var apiBaseURL = KobunAPIService.defaultBaseURL
    @AppStorage("dark_mode") private var darkMode = false

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .tint(.kbPrimary)
                .preferredColorScheme(darkMode ? .dark : .light)
                .task {
                    // 起動時にユーザー設定の接続先を通信層へ反映する。
                    await KobunAPIService.shared.setBaseURL(apiBaseURL)
                }
        }
        .modelContainer(for: [WordProgress.self, QuizAttempt.self, DailyStudyLog.self])
    }
}
