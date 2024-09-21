import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:http/http.dart' as http;

late List<CameraDescription> _cameras;

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  _cameras = await availableCameras();
  runApp(const ProofOfGameplayApp());
}

class ProofOfGameplayApp extends StatefulWidget {
  const ProofOfGameplayApp({super.key});

  @override
  State<ProofOfGameplayApp> createState() => _ProofOfGameplayAppState();
}

class _ProofOfGameplayAppState extends State<ProofOfGameplayApp> {
  CameraController? _cameraController;
  bool _isCameraInitialized = false;

  late RTCVideoRenderer _localRenderer;
  MediaStream? _localStream;
  RTCPeerConnection? _peerConnection;

  @override
  void initState() {
    super.initState();
    initializeCamera();
    initializeWebRTC();
  }

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
        print("start recording before");
        startRecording();
      }
    } catch (e) {
      if (e is CameraException) {
        print('Camera error: ${e.code}');
      }
    }
  }

  Future<void> initializeWebRTC() async {
    _localRenderer = RTCVideoRenderer();
    await _localRenderer.initialize();
  }

  Future<void> startRecording() async {
    print("start recording after");
    // Get video stream from back camera to occupy the whole screen
    _localStream = await navigator.mediaDevices.getUserMedia({
      'audio': false,
      'video': {
        'facingMode': 'environment', // Use 'user' for the front camera
        'width': 1920,
        'height': 1080,
        'frameRate': 30,
      },
    });

    _localRenderer.srcObject = _localStream;
    await sendStreamToServer();
  }

  Future<void> sendStreamToServer() async {
    // Create the PeerConnection with Unified Plan configuration
    final configuration = {
      'iceServers': [
        {'urls': 'stun:stun.l.google.com:19302'}
      ],
      'sdpSemantics': 'unified-plan',
    };

    try {
      // Create a new RTCPeerConnection with the specified configuration
      _peerConnection = await createPeerConnection(configuration);
      print('PeerConnection created.');

      // Add a listener to check the ICE connection state
      _peerConnection!.onIceConnectionState = (RTCIceConnectionState state) {
        print('ICE Connection State: $state');
        if (state == RTCIceConnectionState.RTCIceConnectionStateConnected) {
          print('Connected to the server successfully!');
        }
      };

      // Add the local media stream to the PeerConnection
      if (_localStream != null) {
        for (var track in _localStream!.getTracks()) {
          _peerConnection?.addTrack(track, _localStream!);
          print('Track added: ${track.id}');
        }
      }

      // Create an offer and send it to the server via HTTP POST
      RTCSessionDescription offer = await _peerConnection!.createOffer();
      await _peerConnection!.setLocalDescription(offer);
      print('Offer created and set as local description.');

      // Send the offer SDP to the signaling server
      final offerResponse = await http.post(
        Uri.parse('http://localhost:8081/offer'),
        headers: {'Content-Type': 'application/json'},
        body: '{"sdp": "${offer.sdp}"}',
      );

      if (offerResponse.statusCode == 200) {
        print('Offer sent to the server successfully.');
      } else {
        print('Failed to send offer: ${offerResponse.reasonPhrase}');
        return;
      }

      // Receive the answer SDP from the signaling server
      final answerResponse = await http.get(
        Uri.parse('http://localhost:8081/answer'),
      );

      if (answerResponse.statusCode == 200) {
        final answerSdp = answerResponse.body;
        RTCSessionDescription answer =
            RTCSessionDescription(answerSdp, 'answer');
        await _peerConnection!.setRemoteDescription(answer);
        print('Received and set remote description with server\'s answer.');
      } else {
        print('Failed to receive answer: ${answerResponse.reasonPhrase}');
      }
    } catch (e) {
      print('Error creating PeerConnection: $e');
    }
  }

  @override
  void dispose() {
    _cameraController?.dispose();
    _localRenderer.dispose();
    _localStream?.dispose();
    _peerConnection?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isCameraInitialized ||
        _cameraController == null ||
        !_cameraController!.value.isInitialized) {
      return const MaterialApp(
        home: Scaffold(
          body: Center(
            child: CircularProgressIndicator(),
          ),
        ),
      );
    }

    return MaterialApp(
      home: Scaffold(
        body: Center(
          child: RTCVideoView(
            _localRenderer,
            objectFit: RTCVideoViewObjectFit
                .RTCVideoViewObjectFitCover, // Ensure full-screen fit
          ),
        ),
      ),
    );
  }
}
