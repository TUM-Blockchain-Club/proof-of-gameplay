import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import cv2
import os
import numpy as np
from glob import glob

from sklearn.metrics import precision_recall_fscore_support

def evaluate_model(model, data_loader):
    model.eval()
    all_labels = []
    all_preds = []
    with torch.no_grad():
        for inputs, labels in data_loader:
            inputs = inputs.to(device)
            labels = labels.cpu().numpy()
            outputs = model(inputs).cpu().numpy()
            preds = (outputs > 0.5).astype(int)
            all_labels.extend(labels)
            all_preds.extend(preds)
    all_labels = np.array(all_labels)
    all_preds = np.array(all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average='macro')
    print(f'Precision: {precision:.4f}, Recall: {recall:.4f}, F1-Score: {f1:.4f}')
