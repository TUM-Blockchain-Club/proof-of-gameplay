const remoteVideo = document.getElementById('remoteVideo');
let peerConnection;
const config = {
    'iceServers': [{ 'urls': 'TODO' }] // todo fill this
};
const signalingServer = new WebSocket('TODO');

// Create a peer connection and set up event listeners
function startCall() {
    peerConnection = new RTCPeerConnection(config);

    peerConnection.ontrack = function(event) {
        remoteVideo.srcObject = event.streams[0];
    };

    signalingServer.onmessage = async (message) => {
        const data = JSON.parse(message.data);

        if (data.offer) {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            signalingServer.send(JSON.stringify({ answer: peerConnection.localDescription }));
        } else if (data.answer) {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        } else if (data.candidate) {
            peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        }
    };

    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            signalingServer.send(JSON.stringify({ candidate: event.candidate }));
        }
    };
}
startCall();

// capture frames from the video element
function captureFrame() {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    canvas.width = remoteVideo.videoWidth;
    canvas.height = remoteVideo.videoHeight;
    context.drawImage(remoteVideo, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL('image/jpeg');
}

// send captured frames to python backend for processing
async function sendFrameToMLModel() {
    const frame = captureFrame();
    const response = await fetch('TODO/process_frame', {
        method: 'POST',
        body: JSON.stringify({ frame: frame }),
        headers: {
            'Content-Type': 'application/json'
        }
    });
    const result = await response.json();
    console.log(result); // log result from the model
}

// Send frames in 30 fps
setInterval(sendFrameToMLModel, 1000/30);
