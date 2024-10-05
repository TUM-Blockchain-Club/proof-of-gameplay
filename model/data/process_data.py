import cv2
import os
import sys
import argparse
import yaml
import numpy as np
import pandas as pd


def process_video(video_path, output_path, force=False):
    """
    Convert video into a sequence of square grayscale frames and save as a numpy array.
    """
    if os.path.exists(output_path) and not force:
        print(f"Processed video file {output_path} already exists. Use -f to overwrite.")
        return

    cap = cv2.VideoCapture(video_path)
    success = True
    frames = []

    while success:
        success, frame = cap.read()
        if success:
            # Convert to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Crop to ROI (keyboard area) if necessary
            # gray_frame = gray_frame[y1:y2, x1:x2]
            # Resize frame
            resized_frame = cv2.resize(gray_frame, (512, 512))
            # Save processed frame
            frames.append(resized_frame)
    # Save frames as a numpy array
    video = np.stack(frames, axis=0)
    np.save(output_path, video)

    cap.release()
    print(f"Video processed and saved to {output_path}")


def sync_video(video_path, keypress_csv, config_path, force=False):
    """
    Allows the user to synchronize the video with keypress events by selecting the frame corresponding to the first keypress.

    Args:
        video_path (str): Path to the video file.
        keypress_csv (str): Path to the CSV file containing keypress events.

    Returns:
        sync_offset (float): Time offset between the video start and the first keypress event.
    """
    # Initialize variables
    current_frame = 0
    is_playing = False
    sync_frame = None

    # Check if <file_name>_config.yaml already exists with synchronization info
    if os.path.exists(config_path) and not force:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config['frame_start'] and config['frame_num'] and config['frame_rate']:
                print("Synchronization info taken from config file. Use -f to overwrite.")
                return config['frame_start'], config['frame_num'], config['frame_rate']
            elif config['frame_start']:
                print("Synchronization info taken from config file. Use -f to overwrite.")
                sync_frame = config['frame_start']
    
    # Load keypress events
    keypress_events = pd.read_csv(keypress_csv)
    # Ensure keypress_events is sorted by timestamp
    keypress_events = keypress_events.sort_values('timestamp').reset_index(drop=True)

    # Extract the timestamp and details of the first keypress event
    first_keypress_event = keypress_events.iloc[0]
    first_keypress_timestamp = first_keypress_event['timestamp']
    first_key_name = first_keypress_event['key-name']
    first_event_type = first_keypress_event['event-type']

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if sync_frame is None:
    
        # Create a named window
        cv2.namedWindow('Video Synchronization', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Video Synchronization', 800, 600)

        # Instructions to display in the video frame
        instructions = [
            "Controls:",
            "Spacebar: Play/Pause",
            "D: Next Frame",
            "A: Previous Frame",
            "Shift + D: Skip Forward 30 Frames",
            "Shift + A: Skip Backward 30 Frames",
            "Enter: Select Current Frame as Synchronization Point",
            "Esc or 'q': Exit"
        ]

        print("Instructions:")
        for line in instructions:
            print(line)

        while True:
            if is_playing or sync_frame is None:
                # Set the frame position
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                ret, frame = cap.read()
                if not ret:
                    print("End of video.")
                    is_playing = False
                    current_frame = total_frames - 1
                    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                    ret, frame = cap.read()
                # Display the frame number and first keypress info
                cv2.putText(frame, f'Frame: {current_frame}/{total_frames}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f'First Keypress: {first_key_name} ({first_event_type})', (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                # Display controls
                y0, dy = frame.shape[0] - 190, 25
                for i, line in enumerate(instructions):
                    y = y0 + i*dy
                    cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                # Show the frame
                cv2.imshow('Video Synchronization', frame)
                if is_playing:
                    current_frame += 1
            else:
                # When paused, just display the current frame
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
                ret, frame = cap.read()
                # Display the frame number and first keypress info
                cv2.putText(frame, f'Frame: {current_frame}/{total_frames}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f'First Keypress: {first_event_type} {first_key_name}', (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                # Indicate synchronization frame
                cv2.putText(frame, 'Synchronization Frame Selected', (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                # Display controls
                y0, dy = frame.shape[0] - 150, 25
                for i, line in enumerate(instructions):
                    y = y0 + i*dy
                    cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                cv2.imshow('Video Synchronization', frame)

            key = cv2.waitKey(30) & 0xFF

            if key == 27 or key == ord('q'):  # Esc or 'q' key to exit
                print("Exiting without synchronization.")
                cap.release()
                cv2.destroyAllWindows()
                return None
            elif key == ord(' '):  # Spacebar to play/pause
                is_playing = not is_playing
            elif key == ord('\r') or key == ord('\n'):  # Enter key to select sync frame
                sync_frame = current_frame
                is_playing = False
                print(f"Synchronization frame selected: {sync_frame}")
            elif key == ord('D'):  # Key: Shift + D
                is_playing = False
                current_frame = min(current_frame + 30, total_frames - 1)
            elif key == ord('A'):  # Key: Shift + A
                is_playing = False
                current_frame = max(current_frame - 30, 0)
            elif key == ord('d'):  # Key: D
                is_playing = False
                current_frame = min(current_frame + 1, total_frames - 1)
            elif key == ord('a'):  # Key: A
                is_playing = False
                current_frame = max(current_frame - 1, 0)

            # Ensure current_frame stays within bounds
            current_frame = max(0, min(current_frame, total_frames - 1))

            if sync_frame is not None and not is_playing:
                # Synchronization frame selected, break the loop
                break

    cap.release()
    cv2.destroyAllWindows()

    # Save synchronization info to a config file
    if config_path is not None:
        config = {
            'frame_start': sync_frame,
            'frame_num': total_frames,
            'frame_rate': fps
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        print(f"Synchronization info saved to {config_path}")

    return sync_frame, total_frames, fps


def update_key_names(csv_path, keymap_path="keys.names"):
    """
    Extract unique key names from keypress event CSV files and save them to a .names file.

    Args:
        csv_path (str): List of paths to keypress event CSV files.
        keymap_path (str): Path to the output .names file.
    """
    keypress_events = pd.read_csv(csv_path)
    keypress_vk = keypress_events['key-vk'].unique()
    with open(keymap_path, 'r+') as f:
        keymap = [line.strip() for line in f.readlines()]
        for vk in keypress_vk:
            if str(vk) not in keymap:
                f.write(f"{vk}\n")
    print(f"Key Value Keys saved to {keymap_path}")


def generate_labels(keypress_csv, key_vks_file, labels_path, frame_start, frame_num, frame_rate=30, force=False):
    """
    Generate a label file mapping frame indices to key events.

    Args:
        keypress_csv (str): Path to the keypress events CSV file.
        key_names_file (str): Path to the .names file containing key names.
        frame_start (int): Synchronization offset between video and keypress events.
        frame_num (int): Number of frames in the video.
        frame_rate (int): Frame rate of the video.
        output_dir (str): Directory to save the label file.
    """
    if os.path.exists(labels_path) and not force:
        print(f"Labels file {labels_path} already exists. Use -f to overwrite.")
        return

    # Load key names and create mappings
    with open(key_vks_file, 'r') as f:
        key_vks = [line.strip() for line in f.readlines()]
    key_vk_to_index = {key_vk: idx for idx, key_vk in enumerate(key_vks)}

    # Initialize labels array
    # Each label is [key_index, event_type_bit]
    # Default is [-1, -1], indicating no event
    labels = np.full((frame_num, 2), -1, dtype=int)

    # Load keypress events
    keypress_events = pd.read_csv(keypress_csv)

    frame_start_time = keypress_events.iloc[0]['timestamp']

    for _, keypress_event in keypress_events.iterrows():
        time_diff = keypress_event['timestamp'] - frame_start_time
        frame_diff = time_diff * frame_rate
        frame_idx = int(frame_start + frame_diff)

        # Key vk to index, merge key-name and key-char
        key_vk = str(keypress_event['key-vk'])
        key_index = key_vk_to_index[key_vk]
        # Event type to bit: 1 for key-down, 0 for key-up
        event_type = keypress_event['event-type']
        event_type_bit = 1 if event_type == 'key down' else 0
        # Assign the event to the current frame
        labels[frame_idx] = [key_index, event_type_bit]

    # Save labels to a file
    np.save(labels_path, labels)
    print(f"Labels saved to {labels_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video data for keypress recognition.")
    parser.add_argument('-f', '--force', action='store_true', help="Overwrite existing files.")
    parser.add_argument('file_names', nargs='+', help="List of file names to process.")
    args = parser.parse_args()

    force = args.force

    for file_name in args.file_names:
        video_path = os.path.join('raw', file_name + '.mp4')
        csv_path = os.path.join('raw', file_name + '.csv')
        input_path = os.path.join('processed', file_name + '.npy')
        config_path = os.path.join('processed', file_name + '_config.yaml')
        labels_path = os.path.join('processed', file_name + '_labels.npy')

        process_video(video_path, input_path, force)

        update_key_names(csv_path)

        frame_start, frame_num, frame_rate = sync_video(video_path, csv_path, config_path, force)
        generate_labels(csv_path, 'keys.names', labels_path, frame_start, frame_num, frame_rate, force)
