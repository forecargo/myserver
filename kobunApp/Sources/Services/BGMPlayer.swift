import AVFoundation

/// ゲーム中の BGM を管理するシングルトン。ループ再生・一時停止/再開を担う。
/// カテゴリは .playback（消音スイッチでも鳴る＝ゲームBGM想定）。
@MainActor
final class BGMPlayer {
    static let shared = BGMPlayer()

    private var player: AVAudioPlayer?

    private init() {
        // 割り込み（電話・Siri・他アプリ音など）終了後に自動でループ再生を再開する。
        NotificationCenter.default.addObserver(
            forName: AVAudioSession.interruptionNotification, object: nil, queue: .main
        ) { note in
            Task { @MainActor in BGMPlayer.shared.handleInterruption(note) }
        }
    }

    private func handleInterruption(_ note: Notification) {
        guard let info = note.userInfo,
              let raw = info[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: raw) else { return }
        switch type {
        case .began:
            break   // システムが自動で一時停止する
        case .ended:
            if let optRaw = info[AVAudioSessionInterruptionOptionKey] as? UInt,
               AVAudioSession.InterruptionOptions(rawValue: optRaw).contains(.shouldResume) {
                try? AVAudioSession.sharedInstance().setActive(true)
                player?.play()
            }
        @unknown default:
            break
        }
    }

    /// 指定音源をループ再生する。既に再生中なら何もしない。
    func start(_ name: String, ext: String, volume: Float = 0.35) {
        if player != nil {                 // 既に用意済みなら再開のみ
            player?.play()
            return
        }
        guard let url = Bundle.main.url(forResource: name, withExtension: ext) else { return }

        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback)
        try? session.setActive(true)

        guard let p = try? AVAudioPlayer(contentsOf: url) else { return }
        p.numberOfLoops = -1               // 無限ループ
        p.volume = volume
        p.prepareToPlay()
        p.play()
        player = p
    }

    /// 再生中の音量を即時反映する（設定スライダー用）。
    func setVolume(_ volume: Float) { player?.volume = volume }

    /// バックグラウンド等での一時停止。
    func pause() { player?.pause() }

    /// フォアグラウンド復帰時などの再開。
    func resume() { player?.play() }

    /// 停止して破棄。オーディオセッションも明け渡す。
    func stop() {
        player?.stop()
        player = nil
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
    }
}
