import SwiftUI
import Combine
import AVFoundation

class CameraViewModel: ObservableObject {
    @Published var isRecording = false
    @Published var showPostRecordingOptions = false
    @Published var showCodeInput = false
    @Published var previewLayer: AVCaptureVideoPreviewLayer?
    
    private var cameraService = CameraService()
    private var cancellables = Set<AnyCancellable>()
    private var recordedVideoURL: URL?
    
    init() {
        // Subscribe to cameraService's previewLayer
        cameraService.$previewLayer
            .receive(on: DispatchQueue.main)
            .sink { [weak self] layer in
                if let layer = layer {
                    print("Preview layer received in ViewModel")
                    self?.previewLayer = layer
                } else {
                    print("Preview layer is nil in ViewModel")
                }
            }
            .store(in: &cancellables)
        
        // Subscribe to recording finished notification
        NotificationCenter.default.publisher(for: .didFinishRecording)
            .sink { [weak self] notification in
                if let url = notification.object as? URL {
                    self?.recordedVideoURL = url
                    self?.showPostRecordingOptions = true
                }
            }
            .store(in: &cancellables)

        // Start camera session after setting up subscriptions
        cameraService.startSession()
    }
    
    func toggleRecording() {
        if isRecording {
            stopRecording()
        } else {
            startRecording()
        }
    }
    
    func startRecording() {
        isRecording = true
        showPostRecordingOptions = false
        cameraService.startRecording()
    }
    
    func stopRecording() {
        isRecording = false
        cameraService.stopRecording()
    }
    
    func discardRecording() {
        if let url = recordedVideoURL {
            try? FileManager.default.removeItem(at: url)
        }
        recordedVideoURL = nil
        showPostRecordingOptions = false
    }
    
    func uploadVideo(with code: String) {
        guard let url = recordedVideoURL else { return }
        // Implement upload logic using UploadService
        recordedVideoURL = nil
        showPostRecordingOptions = false
    }
}
