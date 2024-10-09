import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, SubsetRandomSampler
import numpy as np
import os
from glob import glob
import time
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support

from dataset import KeypressDataset
from model import Keypress3DCNN

# Checkpoint functions
def save_checkpoint(state, filename='checkpoint.pth.tar'):
    torch.save(state, filename)
    print(f'Checkpoint saved to {filename}')

def load_checkpoint(model, optimizer, filename='checkpoint.pth.tar'):
    if os.path.isfile(filename):
        print(f'Loading checkpoint from {filename}...')
        checkpoint = torch.load(filename)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        epoch = checkpoint['epoch']
        loss = checkpoint['loss']
        print(f'Checkpoint loaded. Resuming from epoch {epoch}')
        return epoch, loss
    else:
        print(f'No checkpoint found at {filename}. Starting from scratch.')
        return 0, None

if __name__ == '__main__':

    # Check if hardware acceleration is available
    if torch.cuda.is_available():
        device = torch.device('cuda')
    # elif torch.backends.mps.is_available():
    #     device = torch.device('mps')
    else:
        device = torch.device('cpu')
    print(f'Using device: {device}')

    # Get number of classes from the key names file
    num_classes = None
    with open('data/keys.names', 'r') as f:
        num_classes = sum(1 for _ in f) + 2 # Number of keys + 2 (key-down, key-up)

    # Load processed data into Dataset
    dataset = KeypressDataset(
        data_dir='data/processed',
        ignore=['typing_alphabetic_1_gopi_1', 'typing_alphabetic_1_lucas_1'],
        num_classes=num_classes,
        sequence_length_past=8,
        sequence_length_future=8
    )

    # Split dataset into training and validation sets
    dataset_size = len(dataset)
    indices = list(range(dataset_size))
    train_indices, val_indices = train_test_split(indices, test_size=0.2, random_state=42)

    # Create SubsetRandomSampler
    train_sampler = SubsetRandomSampler(train_indices)
    val_sampler = SubsetRandomSampler(val_indices)

    batch_size = 2  # Adjust based on GPU memory

    # Create DataLoaders
    train_loader = DataLoader(dataset, batch_size=batch_size, sampler=train_sampler, num_workers=4, pin_memory=True)
    val_loader = DataLoader(dataset, batch_size=batch_size, sampler=val_sampler, num_workers=4, pin_memory=True)

    # Calculate class weights (inverse of class frequency)
    keypresses_weight = 1 / dataset.keypresses_num
    non_keypresses_weight = 1 / dataset.non_keypresses_num
    class_weights = torch.tensor([non_keypresses_weight, keypresses_weight], device=device)

    # Define model, loss function, and optimizer
    model = Keypress3DCNN(num_classes).to(device)
    # criterion = nn.BCELoss(weight=class_weights)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-4, weight_decay=1e-5)


    # Training loop
    num_epochs = 25

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        start_time = time.time()
        
        for i, (inputs, labels) in enumerate(train_loader):
            inputs = inputs.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            if (i + 1) % 10 == 0:
                avg_loss = running_loss / 10
                elapsed_time = time.time() - start_time
                print(f'Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{len(train_loader)}], Loss: {avg_loss:.4f}, Time: {elapsed_time:.2f}s')
                running_loss = 0.0
                start_time = time.time()
        
        # Validation step
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs = inputs.to(device)
                labels = labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
        avg_val_loss = val_loss / len(val_loader)
        print(f'Epoch [{epoch+1}/{num_epochs}], Validation Loss: {avg_val_loss:.4f}')

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

    # Evaluation
    print('Evaluating on validation set...')
    evaluate_model(model, val_loader)

    # Save the model
    model_save_path = 'saved_models/keypress_model.pth'
    torch.save(model.state_dict(), model_save_path)
    print(f'Model saved to {model_save_path}')
