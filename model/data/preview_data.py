import numpy as np
import cv2
import os
import argparse

def preview_data(video_npy_path, labels_npy_path, key_names_file, show_all_events, frame_rate=30):
    """
    Play the video and mark every frame where a key-press event has been detected.

    Args:
        video_npy_path (str): Path to the video numpy file.
        labels_npy_path (str): Path to the labels numpy file.
        key_names_file (str): Path to the .names file containing key names.
        frame_rate (int): Frame rate of the video.
    """
    # Load video frames
    video_frames = np.load(video_npy_path)  # Shape: (num_frames, H, W)
    num_frames, H, W = video_frames.shape

    # Load labels
    labels = np.load(labels_npy_path)       # Shape: (num_frames, 2)
    # Each label is [key_index, event_type_bit]

    # Load key names
    with open(key_names_file, 'r') as f:
        key_names = [line.strip() for line in f.readlines()]

    # Create a named window
    cv2.namedWindow('Video Preview', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Video Preview', 800, 600)

    # Video playback controls
    is_playing = True
    frame_idx = 0

    print("Instructions:")
    print("Spacebar: Play/Pause")
    print("Right Arrow: Next Frame")
    print("Left Arrow: Previous Frame")
    print("Esc or 'q': Exit")

    while True:
        # Ensure frame_idx is within valid range
        frame_idx = max(0, min(frame_idx, num_frames - 1))

        # Get the current frame and label
        frame = video_frames[frame_idx]  # Shape: (H, W)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)  # Convert to BGR for color display

        label = labels[frame_idx]  # [key_index, event_type_bit]
        key_index, event_type_bit = label

        # Check if there's a key-press event in this frame
        if key_index != -1:
            # By default only show key-down events
            if event_type_bit == 1 or show_all_events:
                key_name = key_names[key_index]
                event_type = 'Key Down' if event_type_bit == 1 else 'Key Up'
                # Overlay text on the frame
                cv2.putText(frame_rgb, f"{key_name} ({event_type})", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                # Draw a rectangle around the frame to indicate an event
                cv2.rectangle(frame_rgb, (0, 0), (W - 1, H - 1), (0, 0, 255), 5)
        else:
            # No event, you can choose to overlay a message or leave it blank
            pass

        # Display frame number
        cv2.putText(frame_rgb, f"Frame: {frame_idx}/{num_frames - 1}", (10, H - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Show the frame
        cv2.imshow('Video Preview', frame_rgb)

        if is_playing:
            # Delay according to frame rate
            key = cv2.waitKey(int(1000 / frame_rate)) & 0xFF
            frame_idx += 1
            if frame_idx >= num_frames:
                frame_idx = 0  # Loop back to the beginning
        else:
            # Wait indefinitely for a key press
            key = cv2.waitKey(0) & 0xFF

        # Handle key presses
        if key == 27 or key == ord('q'):  # Esc or 'q' key to exit
            print("Exiting.")
            break
        elif key == ord(' '):  # Spacebar to play/pause
            is_playing = not is_playing
        elif key == ord('d') or key == 83:  # Right Arrow or 'd' key for next frame
            is_playing = False
            frame_idx += 1
        elif key == ord('a') or key == 81:  # Left Arrow or 'a' key for previous frame
            is_playing = False
            frame_idx -= 1

    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Preview the video data with key press events.")
    parser.add_argument('-a', '--all', action='store_true', help="Show all key-events in preview. By default, only key-down events are shown.")
    parser.add_argument('file_names', nargs='+', help="List of file names without extension.")
    args = parser.parse_args()

    show_all_events = args.all

    for file_name in sys.argv[1:]:
        inputs_path = os.path.join('processed', f"{file_name}.npy")
        labels_path = os.path.join('processed', f"{file_name}_labels.npy")

        preview_data(inputs_path, labels_path, 'keys.names', show_all_events)
