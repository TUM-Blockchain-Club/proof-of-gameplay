import torch
from torch.utils.data import Dataset
import numpy as np
import os
from glob import glob

class KeypressDataset(Dataset):
    def __init__(self, data_dir, sequence_length=16, transform=None):
        """
        Args:
            data_dir (str): Directory with all the processed .npy and _labels.npy files.
            sequence_length (int): Number of frames in each sequence.
            transform (callable, optional): Optional transform to be applied on a sample.
        """
        self.data_dir = data_dir
        self.sequence_length = sequence_length
        self.transform = transform
        self.file_pairs = self._get_file_pairs()
        self.sequence_indices = self._get_sequence_indices()
    
    def _get_file_pairs(self):
        """
        Get list of tuples containing data file paths and their corresponding label file paths.
        """
        data_files = sorted(glob(os.path.join(self.data_dir, '*.npy')))
        # Exclude label files
        data_files = [f for f in data_files if not f.endswith('_labels.npy')]
        label_files = [f.replace('.npy', '_labels.npy') for f in data_files]
        return list(zip(data_files, label_files))
    
    def _get_sequence_indices(self):
        """
        Prepare a list of indices indicating the starting frame of each sequence.
        Each element is a tuple: (file_idx, frame_idx)
        """
        sequence_indices = []
        for file_idx, (data_file, label_file) in enumerate(self.file_pairs):
            # Get the number of frames in this video
            data_shape = np.load(data_file, mmap_mode='r').shape
            num_frames = data_shape[0]
            # For each possible sequence in this file
            # Ensure there are enough frames for a full sequence
            if num_frames >= self.sequence_length:
                for frame_idx in range(0, num_frames - self.sequence_length + 1):
                    sequence_indices.append((file_idx, frame_idx))
        return sequence_indices

    def __len__(self):
        return len(self.sequence_indices)

    def __getitem__(self, idx):
        """
        Returns:
            frames: Tensor of shape (1, T, H, W)
            label: Tensor of shape (num_classes)
        """
        file_idx, frame_idx = self.sequence_indices[idx]
        data_file, label_file = self.file_pairs[file_idx]
        
        # Use np.memmap to access the frames and labels without loading the entire file
        frames_memmap = np.load(data_file, mmap_mode='r')
        labels_memmap = np.load(label_file, mmap_mode='r')

        # Extract the sequence of frames and labels
        frames = frames_memmap[frame_idx:frame_idx + self.sequence_length]  # Shape: (T, H, W)
        labels_seq = labels_memmap[frame_idx:frame_idx + self.sequence_length]  # Shape: (T, 2)

        # Preprocess frames
        frames = frames.astype(np.float32) / 255.0  # Normalize to [0, 1]
        frames = np.expand_dims(frames, axis=1)  # Add channel dimension: (T, 1, H, W)
        frames = frames.transpose((1, 0, 2, 3))  # Rearrange to (C=1, T, H, W)
        
        # Generate label for the sequence
        label_vector = self._generate_label_vector(labels_seq)

        # Convert to tensors
        frames = torch.from_numpy(frames)
        label_vector = torch.from_numpy(label_vector)

        if self.transform:
            frames = self.transform(frames)
        
        return frames, label_vector

    def _generate_label_vector(self, labels_seq):
        """
        Generate a label vector for the sequence based on the labels in labels_seq.
        """
        # Initialize label vector
        label_vector = np.zeros(num_classes, dtype=np.float32)
        
        # Map key-vk and event-type to class index
        for label in labels_seq:
            key_vk = int(label[0])
            event_type = int(label[1])
            if key_vk != -1:
                class_idx = key_to_index(key_vk, event_type)
                label_vector[class_idx] = 1.0  # Multi-label classification

        return label_vector
