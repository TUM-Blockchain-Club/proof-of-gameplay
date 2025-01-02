import os
import pandas as pd
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from PIL import Image

class KeyboardTrackingDataset(Dataset):
    def __init__(self, labels_dir, images_dir, transform=None, device='cpu'):
        self.labels_dir = labels_dir
        self.images_dir = images_dir
        self.transform = transform

        self.labels = []
        self.images = []
        for file in os.listdir(labels_dir):
            if file.endswith('.csv'):
                scene_name = file.split('.')[0]
                df = pd.read_csv(os.path.join(labels_dir, file))
                for i, row in df.iterrows():
                    # Image
                    frame_num = int(row['Frame'])
                    image_path = os.path.join(images_dir, f'{scene_name}/{scene_name}-{frame_num:04d}.png')
                    if not os.path.exists(image_path):
                        print(f'Image not found: {image_path}')
                        continue
                    image = Image.open(image_path).convert('L').resize((192, 108))
                    image = transforms.ToTensor()(image)
                    self.images.append(image.to(device))
                    # Label
                    coords = row[1:].values
                    label = torch.tensor(coords, dtype=torch.float32)
                    label = label / 5
                    self.labels.append(label.to(device))

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        label = self.labels[idx]
        image = self.images[idx]
        if self.transform:
            image = self.transform(image)

        return image, label
