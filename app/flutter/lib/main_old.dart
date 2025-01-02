import 'package:flutter/material.dart';
import 'package:image/image.dart' as img_lib;
import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:web_socket_channel/io.dart';
import 'dart:convert';


Future<void> main() async {
  // Ensure that plugin services are initialized before `runApp` is called.
  WidgetsFlutterBinding.ensureInitialized();

  // Obtain a list of the available cameras on the device.
  final cameras = await availableCameras();

  // Get a specific camera from the list of available cameras.
  final firstCamera = cameras.first;

  runApp(
    MaterialApp(
      title: 'HawkEye',
      theme: ThemeData(
        brightness: Brightness.dark,
        primarySwatch: Colors.lime,
      ),
      home: HawkEyeApp(camera: firstCamera),
      debugShowCheckedModeBanner: false,
    ),
  );
}

class HawkEyeApp extends StatefulWidget {
  final CameraDescription camera;

  const HawkEyeApp({super.key, required this.camera});

  @override
  _HawkEyeAppState createState() => _HawkEyeAppState();
}

class _HawkEyeAppState extends State<HawkEyeApp> {
  late IOWebSocketChannel _channel;
  late CameraController _cameraController;
  late Future<void> _initializeControllerFuture;

  @override
  void initState() {
    super.initState();

    // Initialize WebSocket connection
    _channel = IOWebSocketChannel.connect('ws://10.51.2.233:5001');

    // Initialize the camera controller.
    _cameraController = CameraController(
      widget.camera,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    _initializeControllerFuture = _cameraController.initialize().then((_) {
      _startImageStream();
    });
  }

  void _startImageStream() {
    _cameraController.startImageStream((CameraImage image) {
      _processCameraImage(image);
    });
  }

  void _processCameraImage(CameraImage image) async {
    try {
      // Convert the image to JPEG
      final img = await _convertBGRA8888ToImage(image);
      List<int> jpegData = img_lib.encodeJpg(img);

      // Convert to base64 string
      String base64Image = base64Encode(jpegData);

      // Send the image over WebSocket
      _channel.sink.add(base64Image);
    } catch (e) {
      print('Error processing camera image: $e');
    }
  }

  // Helper function to convert BGRA8888 to RGB image.
  Future<img_lib.Image> _convertBGRA8888ToImage(CameraImage image) async {
    // Create an empty Image buffer in RGBA format
    final img_lib.Image convertedImage = img_lib.Image(width: image.width, height: image.height);

    // Convert BGRA8888 to RGBA8888
    for (int y = 0; y < image.height; y++) {
      for (int x = 0; x < image.width; x++) {
        int pixelIndex = (y * image.planes[0].bytesPerRow) + (x * 4);

        int b = image.planes[0].bytes[pixelIndex];
        int g = image.planes[0].bytes[pixelIndex + 1];
        int r = image.planes[0].bytes[pixelIndex + 2];
        int a = image.planes[0].bytes[pixelIndex + 3];

        // Set pixel in the new image
        convertedImage.setPixel(x, y, img_lib.ColorFloat32.rgba(r, g, b, a));
      }
    }

    return convertedImage;
  }

  @override
  void dispose() {
  _cameraController.stopImageStream();
  _cameraController.dispose();
  _channel.sink.close();
  super.dispose();
  }

  Widget cameraWidget(context, cameraController) {
    var camera = cameraController.value;
    // fetch screen size
    final size = MediaQuery.of(context).size;
        
    // calculate scale depending on screen and camera ratios
    // this is actually size.aspectRatio / (1 / camera.aspectRatio)
    // because camera preview size is received as landscape
    // but we're calculating for portrait orientation
    var scale = size.aspectRatio * camera.aspectRatio;

    // to prevent scaling down, invert the value
    if (scale < 1) scale = 1 / scale;

    return Transform.scale(
      scale: scale,
      child: Center(
        child: CameraPreview(cameraController),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.black,
      child: FutureBuilder<void>(
        future: _initializeControllerFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.done) {
            // If the Future is complete, display the preview.
            return cameraWidget(context, _cameraController);
          } else {
            // Otherwise, display a loading indicator.
            return const Center(child: CircularProgressIndicator());
          }
        },
      ),
    );
  }
}
