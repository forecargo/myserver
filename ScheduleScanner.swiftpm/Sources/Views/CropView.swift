import SwiftUI

enum Corner: CaseIterable, Identifiable {
    case topLeft, topRight, bottomLeft, bottomRight
    var id: Self { self }
}

private func updatedRect(_ rect: CGRect, for corner: Corner, to point: CGPoint, within bounds: CGRect) -> CGRect {
    let minSize: CGFloat = 40
    switch corner {
    case .topLeft:
        let newMinX = max(bounds.minX, min(point.x, rect.maxX - minSize))
        let newMinY = max(bounds.minY, min(point.y, rect.maxY - minSize))
        return CGRect(x: newMinX, y: newMinY, width: rect.maxX - newMinX, height: rect.maxY - newMinY)
    case .topRight:
        let newMaxX = min(bounds.maxX, max(point.x, rect.minX + minSize))
        let newMinY = max(bounds.minY, min(point.y, rect.maxY - minSize))
        return CGRect(x: rect.minX, y: newMinY, width: newMaxX - rect.minX, height: rect.maxY - newMinY)
    case .bottomLeft:
        let newMinX = max(bounds.minX, min(point.x, rect.maxX - minSize))
        let newMaxY = min(bounds.maxY, max(point.y, rect.minY + minSize))
        return CGRect(x: newMinX, y: rect.minY, width: rect.maxX - newMinX, height: newMaxY - rect.minY)
    case .bottomRight:
        let newMaxX = min(bounds.maxX, max(point.x, rect.minX + minSize))
        let newMaxY = min(bounds.maxY, max(point.y, rect.minY + minSize))
        return CGRect(x: rect.minX, y: rect.minY, width: newMaxX - rect.minX, height: newMaxY - rect.minY)
    }
}

private struct CropHandle: View {
    let corner: Corner
    @Binding var cropRect: CGRect
    let imageFrame: CGRect

    private var position: CGPoint {
        switch corner {
        case .topLeft:     return CGPoint(x: cropRect.minX, y: cropRect.minY)
        case .topRight:    return CGPoint(x: cropRect.maxX, y: cropRect.minY)
        case .bottomLeft:  return CGPoint(x: cropRect.minX, y: cropRect.maxY)
        case .bottomRight: return CGPoint(x: cropRect.maxX, y: cropRect.maxY)
        }
    }

    var body: some View {
        Circle()
            .fill(Color.white)
            .frame(width: 22, height: 22)
            .shadow(radius: 3)
            .overlay(Circle().fill(Color.clear).frame(width: 44, height: 44))
            .position(position)
            .gesture(
                DragGesture(minimumDistance: 0, coordinateSpace: .named("cropSpace"))
                    .onChanged { value in
                        cropRect = updatedRect(cropRect, for: corner,
                                               to: value.location, within: imageFrame)
                    }
            )
    }
}

struct CropView: View {
    let image: UIImage
    let onCrop: (UIImage) -> Void
    let onCancel: () -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var cropRect: CGRect = .zero
    @State private var imageFrame: CGRect = .zero

    var body: some View {
        ZStack(alignment: .bottom) {
            Color.black.ignoresSafeArea()

            GeometryReader { geo in
                ZStack {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFit()
                        .frame(width: geo.size.width, height: geo.size.height)

                    Canvas { ctx, size in
                        ctx.fill(Path(CGRect(origin: .zero, size: size)),
                                 with: .color(.black.opacity(0.55)))
                        ctx.blendMode = .destinationOut
                        ctx.fill(Path(cropRect), with: .color(.black))
                    }
                    .compositingGroup()
                    .allowsHitTesting(false)

                    Rectangle()
                        .stroke(Color.white, lineWidth: 1.5)
                        .frame(width: cropRect.width, height: cropRect.height)
                        .position(x: cropRect.midX, y: cropRect.midY)
                        .allowsHitTesting(false)

                    ForEach(Corner.allCases) { corner in
                        CropHandle(corner: corner,
                                   cropRect: $cropRect,
                                   imageFrame: imageFrame)
                    }
                }
                .coordinateSpace(name: "cropSpace")
                .onAppear {
                    let frame = computeImageFrame(imageSize: image.size,
                                                 containerSize: geo.size)
                    imageFrame = frame
                    cropRect = frame
                }
                .onChange(of: geo.size) { newSize in
                    guard !imageFrame.isEmpty else { return }
                    let newFrame = computeImageFrame(imageSize: image.size,
                                                    containerSize: newSize)
                    let scaleX = newFrame.width / imageFrame.width
                    let scaleY = newFrame.height / imageFrame.height
                    cropRect = CGRect(
                        x: newFrame.minX + (cropRect.minX - imageFrame.minX) * scaleX,
                        y: newFrame.minY + (cropRect.minY - imageFrame.minY) * scaleY,
                        width: cropRect.width * scaleX,
                        height: cropRect.height * scaleY
                    )
                    imageFrame = newFrame
                }
            }

            HStack {
                Button("キャンセル") {
                    onCancel()
                    dismiss()
                }
                .foregroundColor(.white)
                .font(.body)

                Spacer()

                Button("切り抜く") {
                    if let cropped = performCrop() {
                        onCrop(cropped)
                    }
                }
                .foregroundColor(.yellow)
                .font(.headline)
            }
            .padding(.horizontal, 32)
            .padding(.vertical, 16)
            .padding(.bottom, 24)
            .background(Color.black.opacity(0.6).ignoresSafeArea(edges: .bottom))
        }
    }

    private func computeImageFrame(imageSize: CGSize, containerSize: CGSize) -> CGRect {
        let scale = min(containerSize.width / imageSize.width,
                        containerSize.height / imageSize.height)
        let w = imageSize.width * scale
        let h = imageSize.height * scale
        return CGRect(x: (containerSize.width - w) / 2,
                      y: (containerSize.height - h) / 2,
                      width: w, height: h)
    }

    private func performCrop() -> UIImage? {
        guard !imageFrame.isEmpty else { return nil }

        // 正規化座標を 0〜1 にクランプ
        let relX = max(0, min(1, (cropRect.minX - imageFrame.minX) / imageFrame.width))
        let relY = max(0, min(1, (cropRect.minY - imageFrame.minY) / imageFrame.height))
        let relW = max(0, min(1 - relX, cropRect.width / imageFrame.width))
        let relH = max(0, min(1 - relY, cropRect.height / imageFrame.height))

        let normalized = image.normalizedToUpOrientation()
        guard let cgImage = normalized.cgImage else { return nil }
        let pixW = CGFloat(cgImage.width)
        let pixH = CGFloat(cgImage.height)
        let cropPixelRect = CGRect(x: relX * pixW, y: relY * pixH,
                                   width: relW * pixW, height: relH * pixH)
        // cgImage.cropping(to:) は整数座標を要求するため丸める
        let rounded = CGRect(
            x: round(cropPixelRect.origin.x),
            y: round(cropPixelRect.origin.y),
            width: round(cropPixelRect.size.width),
            height: round(cropPixelRect.size.height)
        )
        guard let cropped = cgImage.cropping(to: rounded) else { return nil }
        return UIImage(cgImage: cropped)
    }
}

extension UIImage {
    func normalizedToUpOrientation() -> UIImage {
        guard imageOrientation != .up else { return self }
        return UIGraphicsImageRenderer(size: size).image { _ in
            draw(in: CGRect(origin: .zero, size: size))
        }
    }
}
