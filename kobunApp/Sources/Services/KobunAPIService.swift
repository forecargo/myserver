import Foundation

/// API エラー（日本語メッセージ）。
enum KobunAPIError: LocalizedError {
    case invalidBaseURL
    case networkError(Error)
    case httpError(Int, String)
    case decodingError(Error)
    case notFound

    var errorDescription: String? {
        switch self {
        case .invalidBaseURL: return "API の接続先が正しくありません。"
        case .networkError: return "通信に失敗しました。接続を確認してください。"
        case .httpError(let code, _): return "サーバーエラーが発生しました（\(code)）。"
        case .decodingError: return "データの読み取りに失敗しました。"
        case .notFound: return "データが見つかりませんでした。"
        }
    }
}

/// kobun-api への読み取り専用クライアント。URLSession + async/await を actor でラップ。
actor KobunAPIService {
    static let shared = KobunAPIService()
    static let defaultBaseURL = "https://forecargo.ngrok.app/kobun"

    private var baseURL = URL(string: defaultBaseURL)!
    private let decoder = JSONDecoder()

    /// 単語詳細のメモリキャッシュと進行中リクエスト（先読み・スワイプ用）。
    /// entry_no をキーに、同一語の二重取得を抑止する。
    private var wordCache: [String: WordDetail] = [:]
    private var wordInFlight: [String: Task<WordDetail, Error>] = [:]

    func setBaseURL(_ string: String) {
        if let url = URL(string: string) { baseURL = url }
        // 接続先が変わったら entry_no キーの詳細キャッシュは無効化する
        wordCache.removeAll()
        wordInFlight.removeAll()
    }

    nonisolated var defaultBase: URL { URL(string: Self.defaultBaseURL)! }

    /// 画像 URL（ホスト相対）を baseURL に結合して絶対 URL を作る。
    /// `/kobun` プレフィックスを保つため `URL(string:relativeTo:)` は使わない。
    nonisolated static func imageURL(_ imageURL: String?, base: URL) -> URL? {
        guard let imageURL, !imageURL.isEmpty else { return nil }
        let rel = imageURL.hasPrefix("/") ? String(imageURL.dropFirst()) : imageURL
        guard var comps = URLComponents(url: base, resolvingAgainstBaseURL: false) else { return nil }
        var path = comps.path
        if path.hasSuffix("/") { path.removeLast() }
        comps.path = path + "/" + rel
        return comps.url
    }

    private func makeURL(_ path: String, query: [URLQueryItem]) -> URL? {
        guard var comps = URLComponents(url: baseURL, resolvingAgainstBaseURL: false) else { return nil }
        var basePath = comps.path
        if basePath.hasSuffix("/") { basePath.removeLast() }
        comps.path = basePath + "/" + path
        if !query.isEmpty { comps.queryItems = query }
        return comps.url
    }

    private func get<T: Decodable>(_ path: String, query: [URLQueryItem] = []) async throws -> T {
        guard let url = makeURL(path, query: query) else { throw KobunAPIError.invalidBaseURL }
        var request = URLRequest(url: url)
        request.timeoutInterval = 30

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw KobunAPIError.networkError(error)
        }

        if let http = response as? HTTPURLResponse {
            if http.statusCode == 404 { throw KobunAPIError.notFound }
            guard (200..<300).contains(http.statusCode) else {
                throw KobunAPIError.httpError(http.statusCode, String(data: data, encoding: .utf8) ?? "")
            }
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw KobunAPIError.decodingError(error)
        }
    }

    // MARK: - エンドポイント

    func health() async throws -> HealthResponse { try await get("healthz") }

    func meta() async throws -> MetaResponse { try await get("api/meta") }

    func words(
        section: String? = nil,
        pos: String? = nil,
        q: String? = nil,
        ids: [String]? = nil,
        limit: Int? = nil,
        offset: Int = 0
    ) async throws -> WordListResponse {
        var items: [URLQueryItem] = []
        if let section { items.append(.init(name: "section", value: section)) }
        if let pos { items.append(.init(name: "pos", value: pos)) }
        if let q, !q.isEmpty { items.append(.init(name: "q", value: q)) }
        if let ids, !ids.isEmpty { items.append(.init(name: "ids", value: ids.joined(separator: ","))) }
        if let limit { items.append(.init(name: "limit", value: String(limit))) }
        if offset > 0 { items.append(.init(name: "offset", value: String(offset))) }
        return try await get("api/words", query: items)
    }

    /// 単語詳細を取得する。キャッシュ・進行中リクエストがあれば再利用する。
    func word(_ entryNo: String) async throws -> WordDetail {
        if let cached = wordCache[entryNo] { return cached }
        if let task = wordInFlight[entryNo] { return try await task.value }

        let task = Task { try await get("api/words/\(entryNo)") as WordDetail }
        wordInFlight[entryNo] = task
        defer { wordInFlight[entryNo] = nil }
        do {
            let detail = try await task.value
            wordCache[entryNo] = detail
            return detail
        } catch {
            throw error
        }
    }

    /// 単語詳細を先読みしてキャッシュへ載せる（結果は破棄・失敗は無視）。
    func prefetchWord(_ entryNo: String) {
        guard wordCache[entryNo] == nil, wordInFlight[entryNo] == nil else { return }
        Task { _ = try? await word(entryNo) }
    }

    func idioms(q: String? = nil, ids: [String]? = nil, limit: Int? = nil, offset: Int = 0) async throws -> IdiomListResponse {
        var items: [URLQueryItem] = []
        if let q, !q.isEmpty { items.append(.init(name: "q", value: q)) }
        if let ids, !ids.isEmpty { items.append(.init(name: "ids", value: ids.joined(separator: ","))) }
        if let limit { items.append(.init(name: "limit", value: String(limit))) }
        if offset > 0 { items.append(.init(name: "offset", value: String(offset))) }
        return try await get("api/idioms", query: items)
    }

    func idiom(_ id: String) async throws -> IdiomDetail { try await get("api/idioms/\(id)") }

    func search(_ q: String, limit: Int = 20) async throws -> SearchResponse {
        try await get("api/search", query: [.init(name: "q", value: q), .init(name: "limit", value: String(limit))])
    }

    func quiz(section: String? = nil, pos: String? = nil, count: Int = 10, choices: Int = 4) async throws -> QuizResponse {
        var items: [URLQueryItem] = [
            .init(name: "count", value: String(count)),
            .init(name: "choices", value: String(choices)),
        ]
        if let section { items.append(.init(name: "section", value: section)) }
        if let pos { items.append(.init(name: "pos", value: pos)) }
        return try await get("api/quiz", query: items)
    }
}
