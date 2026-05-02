import SwiftUI

struct ContentView: View {
    @EnvironmentObject var vm: ScheduleViewModel
    @State private var capturedImage: UIImage?

    var body: some View {
        NavigationStack {
            Group {
                switch vm.phase {
                case .idle:
                    idleView
                case .cropping:
                    EmptyView()
                case .uploading:
                    VStack(spacing: 16) {
                        ProgressView()
                            .progressViewStyle(.circular)
                            .scaleEffect(1.5)
                        Text("AIが解析中…")
                            .foregroundStyle(.secondary)
                    }
                case .reviewing(let items):
                    ScheduleListView(items: items)
                case .saving:
                    VStack(spacing: 16) {
                        ProgressView()
                            .progressViewStyle(.circular)
                            .scaleEffect(1.5)
                        Text("カレンダーに保存中…")
                            .foregroundStyle(.secondary)
                    }
                case .done(let count):
                    doneView(count: count)
                case .error(let message):
                    errorView(message: message)
                }
            }
            .navigationTitle("スケジュールスキャナー")
            .sheet(isPresented: $vm.showCamera) {
                CameraPickerView(selectedImage: $capturedImage)
                    .ignoresSafeArea()
            }
            .onChange(of: capturedImage) { image in
                guard let image else { return }
                capturedImage = nil
                vm.startCropping(image)
            }
            .fullScreenCover(isPresented: Binding(
                get: { if case .cropping = vm.phase { return true } else { return false } },
                set: { if !$0 { vm.cancelCrop() } }
            )) {
                if case .cropping(let img) = vm.phase {
                    CropView(image: img, onCrop: { cropped in
                        vm.uploadImage(cropped)
                    }, onCancel: {
                        vm.cancelCrop()
                    })
                }
            }
        }
    }

    private var idleView: some View {
        VStack(spacing: 28) {
            Spacer()
            Image(systemName: "camera.viewfinder")
                .font(.system(size: 80))
                .foregroundStyle(.blue)
            Text("グループウェアの\nスケジュール画面を撮影してください")
                .font(.title3)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Button {
                vm.showCamera = true
            } label: {
                Label("カメラを起動", systemImage: "camera")
                    .font(.headline)
                    .frame(maxWidth: .infinity)
                    .padding()
            }
            .buttonStyle(.borderedProminent)
            .padding(.horizontal, 40)
            Spacer()
        }
        .padding()
    }

    private func doneView(count: Int) -> some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 72))
                .foregroundStyle(.green)
            Text("\(count)件の予定を\nカレンダーに登録しました")
                .font(.title2)
                .multilineTextAlignment(.center)
            Button("最初に戻る") { vm.reset() }
                .buttonStyle(.borderedProminent)
            Spacer()
        }
        .padding()
    }

    private func errorView(message: String) -> some View {
        VStack(spacing: 20) {
            Spacer()
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 72))
                .foregroundStyle(.orange)
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Button("やり直す") { vm.reset() }
                .buttonStyle(.borderedProminent)
            Spacer()
        }
        .padding()
    }
}
