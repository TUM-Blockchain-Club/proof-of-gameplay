import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import cv2
import os
import numpy as np
from glob import glob
import pandas as pd

def extract_frames(video_path, output_dir, frame_rate=30):
    """
    Extract frames from a video and save them as grayscale images.
    """
    cap = cv2.VideoCapture(video_path)
    count = 0
    success = True

    while success:
        success, frame = cap.read()
        if success:
            # Convert to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Crop to ROI (keyboard area) if necessary
            # gray_frame = gray_frame[y1:y2, x1:x2]
            # Resize frame
            resized_frame = cv2.resize(gray_frame, (512, 512))
            # Save frame as image
            frame_filename = os.path.join(output_dir, f"frame_{count:05d}.png")
            cv2.imwrite(frame_filename, resized_frame)
            count += 1
    cap.release()

def load_keypress_events(csv_path):
    """
    Load keypress events from a CSV file.
    """
    events = pd.read_csv(csv_path)
    return events

def generate_labels(frame_timestamps, keypress_events, sequence_length, fps=30):
    """
    Generate labels for each frame sequence.
    """
    labels = []
    num_frames = len(frame_timestamps)
    half_seq = sequence_length // 2

    for i in range(num_frames):
        # Get the time window for the sequence
        start_time = frame_timestamps[max(0, i - half_seq)]
        end_time = frame_timestamps[min(num_frames - 1, i + half_seq)]
        # Find events within this time window
        events_in_window = keypress_events[
            (keypress_events['timestamp'] >= start_time) &
            (keypress_events['timestamp'] <= end_time)
        ]
        # Create a label vector
        label = np.zeros(num_classes)  # num_classes = number of keys * 2 (key-down, key-up)
        for _, event in events_in_window.iterrows():
            key_index = key_to_index(event['key-name'], event['event-type'])
            label[key_index] = 1
        labels.append(label)
    return labels
