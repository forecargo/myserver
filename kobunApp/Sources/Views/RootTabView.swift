import SwiftUI

/// 5 タブのルート（ホーム / 単語帳 / 暗記 / 復習 / 設定）。
struct RootTabView: View {
    @Environment(\.scenePhase) private var scenePhase
    @AppStorage("bgm_enabled") private var bgmEnabled = true
    @AppStorage("bgm_volume") private var bgmVolume = 0.15

    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("ホーム", systemImage: "house") }
            WordListView()
                .tabItem { Label("単語帳", systemImage: "book") }
            FlashcardView()
                .tabItem { Label("暗記", systemImage: "rectangle.on.rectangle") }
            ReviewView()
                .tabItem { Label("復習", systemImage: "arrow.triangle.2.circlepath") }
            SettingsView()
                .tabItem { Label("設定", systemImage: "gearshape") }
        }
        // アプリ全体でBGMをループ再生。設定トグル/音量に追従し、バックグラウンドで一時停止。
        .onAppear {
            if bgmEnabled { BGMPlayer.shared.start("kobun-bgm", ext: "mp3", volume: Float(bgmVolume)) }
        }
        .onChange(of: bgmEnabled) { _, on in
            if on { BGMPlayer.shared.start("kobun-bgm", ext: "mp3", volume: Float(bgmVolume)) }
            else { BGMPlayer.shared.stop() }
        }
        .onChange(of: bgmVolume) { _, v in BGMPlayer.shared.setVolume(Float(v)) }
        .onChange(of: scenePhase) { _, phase in
            guard bgmEnabled else { return }
            switch phase {
            case .active: BGMPlayer.shared.resume()
            case .background, .inactive: BGMPlayer.shared.pause()
            @unknown default: break
            }
        }
    }
}
