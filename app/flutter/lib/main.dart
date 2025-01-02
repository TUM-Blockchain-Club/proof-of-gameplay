import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import 'package:web_socket_channel/io.dart';

void main() {
  runApp(const HawkEyeApp());
}

class HawkEyeApp extends StatefulWidget {
  const HawkEyeApp({super.key});

  @override
  State<HawkEyeApp> createState() => _HawkEyeAppState();
}

class _HawkEyeAppState extends State<HawkEyeApp> {
  final _localRenderer = RTCVideoRenderer();
  MediaStream? _localStream;
  RTCPeerConnection? _peerConnection;
  bool _isConnected = false;
  late IOWebSocketChannel _channel;

  @override
  void initState() {
    super.initState();
    _initRenderers();
    _connectToServer();
  }

  @override
  void dispose() {
    _localRenderer.dispose();
    _localStream?.dispose();
    _peerConnection?.close();
    _channel.sink.close();
    super.dispose();
  }

  Future<void> _initRenderers() async {
    await _localRenderer.initialize();
    await _startLocalStream();
  }

  Future<void> _startLocalStream() async {
    _localStream = await navigator.mediaDevices.getUserMedia({
      'audio': false,
      'video': {
        'facingMode': 'environment',
        'width': 1920,
        'height': 1080,
        'frameRate': 30,
      },
    });

    _localRenderer.srcObject = _localStream;
    setState(() {});
  }

  void _connectToServer() {
    _channel = IOWebSocketChannel.connect('ws://10.51.2.233:8080'); // Replace with your server URL

    _channel.stream.listen((message) async {
      final Map<String, dynamic> data = jsonDecode(message);

      switch (data['type']) {
        case 'answer':
          await _peerConnection?.setRemoteDescription(
            RTCSessionDescription(data['sdp'], data['type']),
          );
          break;

        case 'candidate':
          await _peerConnection?.addCandidate(
            RTCIceCandidate(
              data['candidate'],
              data['sdpMid'],
              data['sdpMLineIndex'],
            ),
          );
          break;

        default:
          break;
      }
    }, onDone: () {
      print('WebSocket connection closed');
    }, onError: (error) {
      print('WebSocket error: $error');
    });

    _createPeerConnection().then((_) => _createOffer());
  }

  Future<void> _createPeerConnection() async {
    final configuration = {
      'iceServers': [
        {'urls': 'stun:stun.l.google.com:19302'}
      ],
    };

    _peerConnection = await createPeerConnection(configuration);

    _peerConnection?.onIceCandidate = (RTCIceCandidate candidate) {
      _channel.sink.add(jsonEncode({
        'type': 'candidate',
        'candidate': candidate.candidate,
        'sdpMid': candidate.sdpMid,
        'sdpMLineIndex': candidate.sdpMLineIndex,
      }));
    };

    _peerConnection?.onIceConnectionState = (state) {
      print('ICE Connection State: $state');
      if (state == RTCIceConnectionState.RTCIceConnectionStateConnected) {
        setState(() {
          _isConnected = true;
        });
      }
    };

    _localStream?.getTracks().forEach((track) {
      _peerConnection?.addTrack(track, _localStream!);
      print('Added track: ${track.kind}, ID: ${track.id}');
    });
  }

  Future<void> _createOffer() async {
    final offer = await _peerConnection!.createOffer();
    await _peerConnection!.setLocalDescription(offer);

    _channel.sink.add(jsonEncode({
      'type': offer.type,
      'sdp': offer.sdp,
    }));
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        body: _localRenderer.srcObject != null
            ? RTCVideoView(
                _localRenderer,
                objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitCover,
              )
            : const Center(child: CircularProgressIndicator()),
      ),
      debugShowCheckedModeBanner: false,
    );
  }
}
