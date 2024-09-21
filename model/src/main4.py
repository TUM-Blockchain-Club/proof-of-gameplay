import cv2
import mediapipe as mp
import numpy as np
import threading
import pyaudio
import time

from keyboard_tracking import calibrate_keyboard, get_homography_matrix, warp_frame
from finger_key_mapping import create_keyboard_layout, map_fingertip_to_key, draw_keyboard_layout

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open the stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

# Shared variables
keystroke_sound_timestamps = []
keystroke_sound_lock = threading.Lock()  # Lock for thread-safe access

def detect_keystroke(audio_data, threshold=500, freq_threshold=10000):
    # Convert byte data to numpy array
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    # Compute the RMS (Root Mean Square) of the audio signal
    rms = np.sqrt(np.mean(np.square(audio_array)))

    # Perform FFT
    fft_result = np.fft.fft(audio_array)
    fft_magnitude = np.abs(fft_result)
    # Compute the frequency bins
    freqs = np.fft.fftfreq(len(fft_magnitude), 1.0 / RATE)

    # Focus on frequencies between 2 kHz and 10 kHz (common for keystroke sounds)
    idx = np.where((freqs >= 2000) & (freqs <= 10000))
    freq_magnitude = fft_magnitude[idx]

    # Compute the energy in the keystroke frequency band
    freq_energy = np.sum(freq_magnitude)

    # Thresholds for RMS and frequency energy
    if rms > threshold and freq_energy > freq_threshold:
        return True
    else:
        return False

def audio_detection_loop():
    global keystroke_sound_timestamps
    while True:
        try:
            audio_data = stream.read(CHUNK, exception_on_overflow=False)
            if detect_keystroke(audio_data):
                detection_time = time.time()
                with keystroke_sound_lock:
                    keystroke_sound_timestamps.append(detection_time)
                    # Keep only recent timestamps (last 1 second)
                    keystroke_sound_timestamps = [t for t in keystroke_sound_timestamps if time.time() - t <= 1.0]
        except Exception as e:
            print(f"Exception in audio_detection_loop: {e}")
            break  # Exit the loop or handle the exception appropriately



def main():
    # Start capturing video input
    # live webcam feed
    #   0 => default webcam
    #   1 => external webcam
    cap = cv2.VideoCapture(1)
    # recorded video feed
    # cap = cv2.VideoCapture('data/key_log_typing_1.mp4')

    # Calibrate the keyboard
    pts_src = calibrate_keyboard(cap)
    if pts_src is None:
        print("Keyboard calibration failed.")
        return

    # Compute the homography matrix
    h_matrix, (width, height) = get_homography_matrix(pts_src)

    # Create the keyboard layout
    keyboard_layout = create_keyboard_layout(width, height)

    # Initialize MediaPipe Hands
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    mp_drawing = mp.solutions.drawing_utils

    # Initialize fingertip history for press detection
    fingertips = [4, 8, 12, 16, 20]
    fingertip_history = {idx: [] for idx in fingertips}
    press_detected = {idx: False for idx in fingertips}
    threshold = 14  # Adjust based on testing

    # Initialize keystroke management
    max_simultaneous_keystrokes = 1
    current_keystrokes = 0  # Counter for current keystrokes displayed

    # Initialize keystroke rate limiter
    keystroke_timestamps = []
    max_keystrokes_per_window = 2  # Maximum keystrokes allowed in the time window
    time_window = 1.0  # Time window in seconds
    suppress_keystrokes = False
    cooldown_start_time = None
    cooldown_duration = 3.0  # Duration to suppress keystrokes after overload

    # Start the audio detection thread
    audio_thread = threading.Thread(target=audio_detection_loop)
    audio_thread.daemon = True
    audio_thread.start()

    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Unable to read from webcam. Exiting...")
                break

            frame = cv2.flip(frame, 1)

            # Get the current time
            current_time = time.time()

            # Remove old timestamps outside the time window
            keystroke_timestamps = [t for t in keystroke_timestamps if current_time - t <= time_window]

            # Check if the number of keystrokes exceeds the maximum allowed
            if len(keystroke_timestamps) > max_keystrokes_per_window:
                if not suppress_keystrokes:
                    suppress_keystrokes = True
                    cooldown_start_time = current_time
                    print("Keystroke overload detected. Suppressing outputs.")

            # Handle cooldown period
            if suppress_keystrokes:
                if current_time - cooldown_start_time >= cooldown_duration:
                    suppress_keystrokes = False
                    keystroke_timestamps.clear()
                    print("Resuming keystroke outputs.")

            # Convert the BGR image to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Process the image and detect hands
            results = hands.process(image)

            # Prepare for drawing
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Transform the image to top-down view
            warped_frame = warp_frame(frame, h_matrix, (width, height))

            # Draw the keyboard layout on the warped frame
            draw_keyboard_layout(warped_frame, keyboard_layout)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks on the original frame
                    mp_drawing.draw_landmarks(
                        image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Extract fingertip coordinates
                    h_orig, w_orig, _ = image.shape
                    for idx in fingertips:
                        landmark = hand_landmarks.landmark[idx]
                        x, y = int(landmark.x * w_orig), int(landmark.y * h_orig)

                        # Transform the fingertip coordinate to the keyboard coordinate system
                        point = np.array([[[x, y]]], dtype='float32')
                        transformed_point = cv2.perspectiveTransform(point, h_matrix)

                        tx, ty = transformed_point[0][0]
                        tx = int(tx)
                        ty = int(ty)

                        # Ensure transformed points are within bounds
                        if not (0 <= tx < width and 0 <= ty < height):
                            continue

                        # Update fingertip history with ty
                        if len(fingertip_history[idx]) >= 5:
                            fingertip_history[idx].pop(0)
                        fingertip_history[idx].append(ty)

                        # Compute velocity for press detection
                        if len(fingertip_history[idx]) == 5:
                            y_values = fingertip_history[idx]
                            velocity = y_values[-1] - y_values[0]

                            # Detect downward motion for key press
                            if velocity > threshold and not press_detected[idx]:
                                if current_keystrokes < max_simultaneous_keystrokes:
                                    key = map_fingertip_to_key(tx, ty, keyboard_layout)
                                    if key:
                                        # Check for a matching keystroke sound
                                        with keystroke_sound_lock:
                                            # Copy the list to avoid holding the lock for too long
                                            sound_timestamps_copy = keystroke_sound_timestamps.copy()

                                        # Check if a keystroke sound was detected within the last 0.2 seconds
                                        keystroke_sound_detected = any(
                                            abs(current_time - t) <= 0.2 for t in sound_timestamps_copy)

                                        if keystroke_sound_detected and not suppress_keystrokes:
                                            print(f"Key Press Detected: {key}")
                                            cv2.putText(warped_frame, f"Pressed: {key}", (tx, ty - 30),
                                                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                                            current_keystrokes += 1  # Increment counter
                                            # Record the timestamp of the keystroke
                                            keystroke_timestamps.append(current_time)
                                            # Remove the used keystroke sound timestamp
                                            with keystroke_sound_lock:
                                                keystroke_sound_timestamps = [t for t in keystroke_sound_timestamps if abs(current_time - t) > 0.2]
                                        else:
                                            # No matching keystroke sound detected
                                            pass
                                press_detected[idx] = True
                            elif velocity < -threshold / 2 and press_detected[idx]:
                                # Reset press_detected when finger moves up
                                press_detected[idx] = False
                                if current_keystrokes > 0:
                                    current_keystrokes -= 1  # Decrement counter

                        # Draw the fingertip on the warped frame
                        cv2.circle(warped_frame, (tx, ty), 5, (0, 0, 255), -1)
            else:
                # No hands detected; reset counters and states
                fingertip_history = {idx: [] for idx in fingertips}
                press_detected = {idx: False for idx in fingertips}
                keystroke_timestamps.clear()
                current_keystrokes = 0  # Reset the keystroke counter

            # Display the original frame and the warped frame
            cv2.imshow('Original Frame', image)
            cv2.imshow('Warped Keyboard View', warped_frame)

            # Exit on pressing 'q'
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                print(f"Key pressed: {key}")
            if key == ord('q'):
                break
    finally:
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    main()
