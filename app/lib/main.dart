import 'package:camera/camera.dart';
import 'package:flutter/material.dart';

late List<CameraDescription> _cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  _cameras = await availableCameras();
  runApp(const ProofOfGameplayApp());
}

/// CameraApp is the Main Application.
class ProofOfGameplayApp extends StatefulWidget {
  /// Default Constructor
  const ProofOfGameplayApp({super.key});

  @override
  State<ProofOfGameplayApp> createState() => _ProofOfGameplayAppState();
}

class _ProofOfGameplayAppState extends State<ProofOfGameplayApp> {
  CameraController? _cameraController;
  bool _isCameraInitialized = false;

  @override
  void initState() {
    super.initState();
    initializeCamera();
  }

  /// Initializes the camera controller and sets it up with the first available camera.
  Future<void> initializeCamera() async {
    _cameraController = CameraController(
      _cameras[0],
      ResolutionPreset.max,
    );

    try {
      await _cameraController!.initialize();
      if (mounted) {
        setState(() {
          _isCameraInitialized = true;
        });
      }
    } catch (e) {
      if (e is CameraException) {
        // Handle specific camera errors here if necessary
        print('Camera error: ${e.code}');
      }
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isCameraInitialized ||
        _cameraController == null ||
        !_cameraController!.value.isInitialized) {
      // Show a loading indicator while the camera is initializing
      return const MaterialApp(
        home: Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    return MaterialApp(
      home: Scaffold(
        body: Center(
          child: cameraWidget(context),
        ),
      ),
    );
  }

  /// Function to build the camera widget with correct aspect ratio and scale.
  Widget cameraWidget(BuildContext context) {
    var camera = _cameraController!.value;
    // Fetch screen size
    final size = MediaQuery.of(context).size;

    // Calculate scale depending on screen and camera ratios
    // This is actually size.aspectRatio / (1 / camera.aspectRatio)
    // because camera preview size is received as landscape
    // but we're calculating for portrait orientation
    var scale = size.aspectRatio * camera.aspectRatio;

    // To prevent scaling down, invert the value
    if (scale < 1) scale = 1 / scale;

    return Transform.scale(
      scale: scale,
      child: Center(
        child: CameraPreview(_cameraController!),
      ),
    );
  }
}
