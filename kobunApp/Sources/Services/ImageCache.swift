import CryptoKit
import UIKit

/// 暗記カード画像用の 2 段キャッシュ。
/// メモリ（NSCache・LRU）→ ディスク（Caches/KobunImageCache/）→ ネットワークの順に解決する。
/// API は read-only・画像は内容が変わらない静的アセットのため、URL をキーに永続キャッシュして良い。
final class ImageCache {
    static let shared = ImageCache()

    private let memory = NSCache<NSString, UIImage>()
    private let dir: URL
    private let fm = FileManager.default

    private var inFlight: Set<String> = []   // 先読み進行中の URL（二重取得の抑止）
    private let lock = NSLock()

    private init() {
        let base = fm.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        dir = base.appendingPathComponent("KobunImageCache", isDirectory: true)
        try? fm.createDirectory(at: dir, withIntermediateDirectories: true)
        memory.countLimit = 120                  // 保持枚数の上限（LRU）
        memory.totalCostLimit = 64 * 1024 * 1024 // 約 64MB（デコード後ピクセル概算）
    }

    /// 同期メモリヒット。表示直後のチラつき防止に使う（ヒットしなければ nil）。
    func cachedImage(for url: URL) -> UIImage? {
        memory.object(forKey: key(url))
    }

    /// メモリ → ディスク → ネットワークの順に画像を取得する。取得失敗時は nil。
    func image(for url: URL) async -> UIImage? {
        let k = key(url)
        if let img = memory.object(forKey: k) { return img }

        let file = dir.appendingPathComponent(filename(url))
        if let data = try? Data(contentsOf: file), let img = UIImage(data: data) {
            store(img, forKey: k)
            return img
        }

        guard let (data, response) = try? await URLSession.shared.data(from: url) else { return nil }
        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) { return nil }
        guard let img = UIImage(data: data) else { return nil }

        try? data.write(to: file, options: .atomic)
        store(img, forKey: k)
        return img
    }

    /// 画像をバックグラウンドで先読みしてキャッシュへ載せる（結果は破棄）。
    /// 既にメモリにある／先読み進行中の URL はスキップする。
    func prefetch(_ url: URL) {
        if memory.object(forKey: key(url)) != nil { return }
        let k = url.absoluteString
        lock.lock()
        if inFlight.contains(k) { lock.unlock(); return }
        inFlight.insert(k)
        lock.unlock()
        Task.detached(priority: .utility) { [weak self] in
            _ = await self?.image(for: url)
            guard let self else { return }
            self.lock.lock()
            self.inFlight.remove(k)
            self.lock.unlock()
        }
    }

    /// メモリ・ディスク双方のキャッシュを破棄する。
    func clear() {
        memory.removeAllObjects()
        try? fm.removeItem(at: dir)
        try? fm.createDirectory(at: dir, withIntermediateDirectories: true)
    }

    private func store(_ img: UIImage, forKey key: NSString) {
        memory.setObject(img, forKey: key, cost: cost(of: img))
    }

    private func cost(of img: UIImage) -> Int {
        let px = img.size.width * img.scale * img.size.height * img.scale
        return Int(px) * 4 // RGBA 概算
    }

    private func key(_ url: URL) -> NSString { url.absoluteString as NSString }

    private func filename(_ url: URL) -> String {
        let digest = SHA256.hash(data: Data(url.absoluteString.utf8))
        let hex = digest.map { String(format: "%02x", $0) }.joined()
        let ext = url.pathExtension.isEmpty ? "img" : url.pathExtension
        return "\(hex).\(ext)"
    }
}
