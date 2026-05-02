import Foundation
import UIKit

enum APIError: LocalizedError {
    case invalidImage
    case networkError(Error)
    case httpError(Int, String)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidImage:
            return "画像の変換に失敗しました"
        case .networkError(let e):
            return "ネットワークエラー: \(e.localizedDescription)"
        case .httpError(let code, let message):
            return "サーバーエラー (\(code)): \(message)"
        case .decodingError(let e):
            return "データ解析エラー: \(e.localizedDescription)"
        }
    }
}

actor APIService {
    static let shared = APIService()

    private let endpoint = URL(string: "https://forecargo.ngrok.app/schedule")!

    func uploadImage(_ image: UIImage) async throws -> [ScheduleItem] {
        guard let jpeg = image.jpegData(compressionQuality: 0.85) else {
            throw APIError.invalidImage
        }

        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: endpoint)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = buildMultipartBody(jpeg, boundary: boundary)

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
            return try JSONDecoder().decode(ScheduleResponse.self, from: data).schedules
        } catch {
            throw APIError.decodingError(error)
        }
    }

    private func buildMultipartBody(_ jpeg: Data, boundary: String) -> Data {
        var body = Data()
        let crlf = "\r\n"

        body.append("--\(boundary)\(crlf)".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"file\"; filename=\"schedule.jpg\"\(crlf)".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\(crlf)\(crlf)".data(using: .utf8)!)
        body.append(jpeg)
        body.append("\(crlf)--\(boundary)--\(crlf)".data(using: .utf8)!)
        return body
    }
}
