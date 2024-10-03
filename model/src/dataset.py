import cv2
import os
import numpy as np
import torch
from torch.utils.data import Dataset
import torchvision.transforms as transforms
from glob import glob

class KeypressDataset(Dataset):
    def __init__(self, frames_dir, labels, sequence_length=16, transform=None):
        self.frames_dir = frames_dir
        self.labels = labels
        self.sequence_length = sequence_length
        self.transform = transform
        self.frame_paths = sorted(glob(os.path.join(frames_dir, '*.png')))
    
    def __len__(self):
        return len(self.frame_paths) - self.sequence_length + 1
    
    def __getitem__(self, idx):
        # Load sequence of frames
        frames = []
        for i in range(idx, idx + self.sequence_length):
            frame = cv2.imread(self.frame_paths[i], cv2.IMREAD_GRAYSCALE)
            frame = np.expand_dims(frame, axis=0)  # Add channel dimension
            frames.append(frame)
        frames = np.stack(frames, axis=1)  # Shape: (1, T, H, W)
        frames = frames.astype(np.float32) / 255.0  # Normalize
        
        if self.transform:
            frames = self.transform(frames)
        
        # Get the corresponding label
        label = self.labels[idx + self.sequence_length // 2]  # Center frame label
        
        return frames, torch.tensor(label, dtype=torch.float32)
