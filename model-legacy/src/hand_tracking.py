import cv2
import mediapipe as mp

def main():
    # Initialize MediaPipe Hands.
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,        # For real-time processing.
        max_num_hands=2,                # Detect up to 2 hands.
        min_detection_confidence=0.5,   # Minimum confidence for hand detection.
        min_tracking_confidence=0.5     # Minimum confidence for hand tracking.
    )

    # Initialize the drawing utility.
    mp_drawing = mp.solutions.drawing_utils

    # Start capturing video input.
    cap = cv2.VideoCapture(0)  # Use the default webcam (index 0).

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Unable to read from webcam. Exiting...")
            break

        # Flip the image horizontally for a later selfie-view display.
        frame = cv2.flip(frame, 1)

        # Convert the BGR image to RGB before processing.
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False  # Improve performance by marking the image as not writeable.

        # Process the image and detect hands.
        results = hands.process(image)

        # Draw hand landmarks on the image.
        image.flags.writeable = True   # Mark the image as writeable again.
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks and connections.
                mp_drawing.draw_landmarks(
                    image, 
                    hand_landmarks, 
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2)
                )

                # Extract fingertip coordinates (landmark indices 4, 8, 12, 16, 20).
                h, w, _ = image.shape
                fingertips = [4, 8, 12, 16, 20]
                for idx in fingertips:
                    landmark = hand_landmarks.landmark[idx]
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    # Draw a circle at each fingertip.
                    cv2.circle(image, (cx, cy), 5, (255, 0, 0), cv2.FILLED)
                    # Optionally, display the index of the fingertip.
                    cv2.putText(image, str(idx), (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Display the processed image.
        cv2.imshow('MediaPipe Hands', image)

        # Exit on pressing 'q'.
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    # Release resources.
    cap.release()
    cv2.destroyAllWindows()
    hands.close()

if __name__ == "__main__":
    main()
