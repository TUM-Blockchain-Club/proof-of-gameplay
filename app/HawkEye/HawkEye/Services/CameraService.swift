import AVFoundation
import UIKit

class CameraService: NSObject, ObservableObject {
    private let session = AVCaptureSession()
    private let sessionQueue = DispatchQueue(label: "camera.session.queue")
    private var deviceInput: AVCaptureDeviceInput?
    private let syxtemPreferredCamera = AVCaptureDevice.default(for: .video)
    
    @Published var isSessionRunning = false
    @Published var videoOutput = AVCaptureMovieFileOutput()
    @Published var previewLayer: AVCaptureVideoPreviewLayer?
    
    override init() {
        super.init()
        checkPermissions()
        configureSession()
    }
    
    private func configureSession() {
        sessionQueue.async {
            self.session.beginConfiguration()
            
            // Input
            guard let videoDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
                print("Default video device is unavailable.")
                return
            }
            
            guard let videoDeviceInput = try? AVCaptureDeviceInput(device: videoDevice) else {
                print("Couldn't create video device input.")
                return
            }
            
            if self.session.canAddInput(videoDeviceInput) {
                self.session.addInput(videoDeviceInput)
            } else {
                print("Couldn't add video device input to the session.")
                return
            }
            
            // Output
            if self.session.canAddOutput(self.videoOutput) {
                self.session.addOutput(self.videoOutput)
            } else {
                print("Could not add movie file output to the session")
                return
            }
            
            self.session.commitConfiguration()
            self.preparePreviewLayer()
        }
    }
    
    private func checkPermissions() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            // Already authorized
            break
        case .notDetermined:
            AVCaptureDevice.requestAccess(for: .video) { granted in
                if !granted {
                    // Handle the case where the user denied the permission
                }
            }
        default:
            // The user has previously denied or restricted access
            // Provide instructions on how to enable permissions
            break
        }
    }
    
    private func preparePreviewLayer() {
        DispatchQueue.main.async {
            self.previewLayer = AVCaptureVideoPreviewLayer(session: self.session)
            self.previewLayer?.videoGravity = .resizeAspectFill
            if self.previewLayer != nil {
                print("Preview layer prepared")
            } else {
                print("Error: Preview layer is nil")
            }
        }
    }
    
    func startSession() {
        sessionQueue.async {
            if !self.session.isRunning {
                self.session.startRunning()
                DispatchQueue.main.async {
                    self.isSessionRunning = true
                }
            }
        }
    }
    
    func stopSession() {
        sessionQueue.async {
            if self.session.isRunning {
                self.session.stopRunning()
                DispatchQueue.main.async {
                    self.isSessionRunning = false
                }
            }
        }
    }
    
    func startRecording() {
        let outputURL = URL(fileURLWithPath: NSTemporaryDirectory())
            .appendingPathComponent(UUID().uuidString)
            .appendingPathExtension("mov")
        videoOutput.startRecording(to: outputURL, recordingDelegate: self)
    }
    
    func stopRecording() {
        if videoOutput.isRecording {
            videoOutput.stopRecording()
        }
    }
}

extension CameraService: AVCaptureFileOutputRecordingDelegate {
    func fileOutput(_ output: AVCaptureFileOutput,
                    didFinishRecordingTo outputFileURL: URL,
                    from connections: [AVCaptureConnection],
                    error: Error?) {
        // Handle the recorded file
        if let error = error {
            print("Error recording movie: \(error.localizedDescription)")
            return
        }
        
        // Notify that recording is finished and provide the URL
        DispatchQueue.main.async {
            NotificationCenter.default.post(name: .didFinishRecording, object: outputFileURL)
        }
    }
}
