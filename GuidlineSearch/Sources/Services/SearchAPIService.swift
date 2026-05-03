import Foundation

enum APIError: LocalizedError {
    case networkError(Error)
    case httpError(Int, String)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .networkError(let e):   return "ネットワークエラー: \(e.localizedDescription)"
        case .httpError(let c, let m): return "サーバーエラー (\(c)): \(m)"
        case .decodingError(let e):  return "データ解析エラー: \(e.localizedDescription)"
        }
    }
}

actor SearchAPIService {
    static let shared = SearchAPIService()

    private let baseURL = URL(string: "https://forecargo.ngrok.app/guideline")!

    func search(query: String, topK: Int = 5) async throws -> SearchResponse {
        let url = baseURL.appendingPathComponent("search")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(SearchRequest(query: query, top_k: topK))
        request.timeoutInterval = 30

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw APIError.httpError(http.statusCode, body)
        }

        do {
            return try JSONDecoder().decode(SearchResponse.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }
}
