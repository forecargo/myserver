import AVFoundation

/// 効果音（ワンショット）プレイヤー。BGM とは別インスタンスで重ねて再生できる。
@MainActor
final class SFXPlayer {
    static let shared = SFXPlayer()

    // 再生完了まで参照を保持する（解放されると途中で止まるため）。
    private var players: [AVAudioPlayer] = []

    private init() {}

    /// 効果音を1回再生する。
    func play(_ name: String, ext: String = "mp3", volume: Float = 1.0) {
        guard let url = Bundle.main.url(forResource: name, withExtension: ext) else { return }

        // BGM が無効でも鳴るようセッションを有効化（.playback は BGM と共通・アプリ内は自動でミックス）。
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback)
        try? session.setActive(true)

        guard let p = try? AVAudioPlayer(contentsOf: url) else { return }
        p.volume = volume
        p.prepareToPlay()

        players.removeAll { !$0.isPlaying }   // 再生済みを掃除
        players.append(p)
        p.play()
    }
}
