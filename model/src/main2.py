import cv2
import mediapipe as mp
import numpy as np

from keyboard_tracking import calibrate_keyboard, get_homography_matrix, warp_frame
from finger_key_mapping import create_keyboard_layout, map_fingertip_to_key, draw_keyboard_layout

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

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Unable to read from webcam. Exiting...")
            break

        frame = cv2.flip(frame, 1)

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
                            key = map_fingertip_to_key(tx, ty, keyboard_layout)
                            if key:
                                print(f"Key Press Detected: {key}")
                                cv2.putText(warped_frame, f"Pressed: {key}", (tx, ty - 30),
                                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                                press_detected[idx] = True
                        elif velocity < -threshold / 2:
                            # Reset press_detected when finger moves up
                            press_detected[idx] = False

                    # Draw the fingertip on the warped frame
                    cv2.circle(warped_frame, (tx, ty), 5, (0, 0, 255), -1)

        # Display the original frame and the warped frame
        cv2.imshow('Original Frame', image)
        cv2.imshow('Warped Keyboard View', warped_frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    main()
