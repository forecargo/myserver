import Foundation

// viewer.py が公開する 4 エンドポイントへのクライアント。
// メモリ LRU + ディスクキャッシュ (Caches/TangoCache/) の 2 段構え。
// 詳細: SPEC_SwiftUI.md §6

actor TangoAPIService {
    static let shared = TangoAPIService()

    private var baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder

    private var batchListCache: [String]?
    private var fileListCache: [String: [APIFileEntry]] = [:]
    private var wordDataCache: [String: APIVocabularyResult] = [:]
    private var wordDataOrder: [String] = []
    private let wordCacheCapacity = 100

    // ディスクキャッシュのルートディレクトリ
    private let cacheDir: URL

    // キャッシュフォーマットを変更したり、バグ修正で過去キャッシュを無効化したい時に上げる。
    private static let cacheVersion = "v3"

    private init() {
        self.baseURL = URL(string: "https://forecargo.ngrok.app/tango")!
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
        self.decoder = JSONDecoder()

        let base = FileManager.default
            .urls(for: .cachesDirectory, in: .userDomainMask)
            .first!
        let dir = base.appendingPathComponent("TangoCache", isDirectory: true)
        self.cacheDir = dir

        Self.ensureFreshCacheDir(dir: dir)
    }

    /// キャッシュバージョンを照合し、不一致なら全ディスクキャッシュを破棄する。
    private static func ensureFreshCacheDir(dir: URL) {
        let versionFile = dir.appendingPathComponent(".version")
        let current = (try? String(contentsOf: versionFile, encoding: .utf8))?
            .trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        if current != cacheVersion {
            try? FileManager.default.removeItem(at: dir)
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
            try? cacheVersion.write(to: versionFile, atomically: true, encoding: .utf8)
        } else {
            try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        }
    }

    func setBaseURL(_ url: URL) {
        self.baseURL = url
        clearMemoryCache()
    }

    func currentBaseURL() -> URL { baseURL }

    func clearMemoryCache() {
        batchListCache = nil
        fileListCache.removeAll()
        wordDataCache.removeAll()
        wordDataOrder.removeAll()
    }

    /// メモリ + ディスクの両方をクリア
    func clearAllCache() {
        clearMemoryCache()
        try? FileManager.default.removeItem(at: cacheDir)
        try? FileManager.default.createDirectory(at: cacheDir, withIntermediateDirectories: true)
        let versionFile = cacheDir.appendingPathComponent(".version")
        try? Self.cacheVersion.write(to: versionFile, atomically: true, encoding: .utf8)
    }

    // MARK: - Endpoints

    func listBatches(forceRefresh: Bool = false) async throws -> [String] {
        if !forceRefresh, let cached = batchListCache {
            return cached
        }
        if !forceRefresh, let disk = readDiskCache(path: "batches.json"),
           let decoded = try? decoder.decode([String].self, from: disk) {
            batchListCache = decoded
            // バックグラウンドで再検証はせず、強制更新ボタンに任せる
            return decoded
        }
        let url = baseURL.appendingPathComponent("api/batches")
        let (data, result): (Data, [String]) = try await getJSONWithData(url)
        batchListCache = result
        writeDiskCache(path: "batches.json", data: data)
        return result
    }

    func listFiles(batch: String, forceRefresh: Bool = false) async throws -> [APIFileEntry] {
        // ファイル一覧は更新検知が必要なため、ディスクキャッシュには載せない (メモリのみ)。
        if !forceRefresh, let cached = fileListCache[batch] {
            return cached
        }
        let url = baseURL
            .appendingPathComponent("api/files")
            .appendingPathComponent(batch)
        do {
            let (_, result): (Data, [APIFileEntry]) = try await getJSONWithData(url)
            fileListCache[batch] = result
            return result
        } catch let TangoAPIError.httpError(404, _) {
            throw TangoAPIError.batchNotFound(batch)
        }
    }

    func loadData(batch: String, stem: String, forceRefresh: Bool = false) async throws -> APIVocabularyResult {
        let key = "\(batch)::\(stem)"
        if !forceRefresh, let cached = wordDataCache[key] {
            touchLRU(key)
            return cached
        }
        let relPath = "data/\(batch)/\(stem).json"
        if !forceRefresh, let disk = readDiskCache(path: relPath),
           let decoded = try? decoder.decode(APIVocabularyResult.self, from: disk) {
            insertLRU(key, value: decoded)
            return decoded
        }
        let url = baseURL
            .appendingPathComponent("api/data")
            .appendingPathComponent(batch)
            .appendingPathComponent(stem)
        do {
            let (data, result): (Data, APIVocabularyResult) = try await getJSONWithData(url)
            insertLRU(key, value: result)
            writeDiskCache(path: relPath, data: data)
            return result
        } catch let TangoAPIError.httpError(404, _) {
            throw TangoAPIError.fileNotFound(batch: batch, stem: stem)
        }
    }

    nonisolated func imageURL(batch: String, stem: String) -> URL {
        URL(string: TangoAPIService.cachedBaseURLString)!
            .appendingPathComponent("image")
            .appendingPathComponent(batch)
            .appendingPathComponent(stem)
    }

    // MARK: - 内部: HTTP

    private func getJSONWithData<T: Decodable>(_ url: URL) async throws -> (Data, T) {
        TangoAPIService.cachedBaseURLString = baseURL.absoluteString
        var req = URLRequest(url: url)
        req.httpMethod = "GET"
        req.setValue("application/json", forHTTPHeaderField: "Accept")

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: req)
        } catch {
            throw TangoAPIError.networkError(error)
        }
        guard let http = response as? HTTPURLResponse else {
            throw TangoAPIError.httpError(-1, "Invalid response")
        }
        guard (200..<300).contains(http.statusCode) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw TangoAPIError.httpError(http.statusCode, body)
        }
        do {
            let decoded = try decoder.decode(T.self, from: data)
            return (data, decoded)
        } catch {
            let preview = String(data: data.prefix(300), encoding: .utf8) ?? "<binary>"
            throw TangoAPIError.decodingError(error: error, url: url, bodyPreview: preview)
        }
    }

    // MARK: - 内部: LRU

    private func touchLRU(_ key: String) {
        if let idx = wordDataOrder.firstIndex(of: key) {
            wordDataOrder.remove(at: idx)
        }
        wordDataOrder.append(key)
    }

    private func insertLRU(_ key: String, value: APIVocabularyResult) {
        wordDataCache[key] = value
        touchLRU(key)
        while wordDataOrder.count > wordCacheCapacity {
            let evicted = wordDataOrder.removeFirst()
            wordDataCache.removeValue(forKey: evicted)
        }
    }

    // MARK: - 内部: ディスク I/O

    private func diskURL(_ relPath: String) -> URL {
        cacheDir.appendingPathComponent(relPath)
    }

    private func readDiskCache(path: String) -> Data? {
        try? Data(contentsOf: diskURL(path))
    }

    private func writeDiskCache(path: String, data: Data) {
        let url = diskURL(path)
        try? FileManager.default.createDirectory(
            at: url.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try? data.write(to: url, options: .atomic)
    }

    nonisolated(unsafe) private static var cachedBaseURLString: String =
        "https://forecargo.ngrok.app/tango"

    /// UI 表示用に現在の baseURL を読む (nonisolated)
    nonisolated static var currentBaseURLString: String {
        cachedBaseURLString
    }
}
