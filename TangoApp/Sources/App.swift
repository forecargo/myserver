import SwiftUI
import SwiftData
import AVFoundation

@main
struct TangoAppApp: App {
    @AppStorage("api_base_url") private var apiBaseURL: String = "https://forecargo.ngrok.app/tango"

    init() {
        configureAudioSession()
    }

    var body: some Scene {
        WindowGroup {
            RootTabView()
                .task {
                    if let url = URL(string: apiBaseURL) {
                        await TangoAPIService.shared.setBaseURL(url)
                    }
                }
        }
        .modelContainer(for: [WordProgress.self, QuizAttempt.self])
    }

    /// 消音モード (サイレントスイッチ ON) では発音しないよう `.ambient` カテゴリを使う。
    /// `.mixWithOthers` で他アプリの音楽を遮らない。Haptic はサイレントでも動作する。
    private func configureAudioSession() {
        do {
            let session = AVAudioSession.sharedInstance()
            try session.setCategory(
                .ambient,
                mode: .default,
                options: [.mixWithOthers]
            )
            try session.setActive(true)
        } catch {
            // 失敗時は既定動作のまま継続
        }
    }
}
