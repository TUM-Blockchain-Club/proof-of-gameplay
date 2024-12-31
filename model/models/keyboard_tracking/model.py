import torch
import torch.nn as nn

class KeyboardTrackingModel(torch.nn.Module):
    def __init__(self, hparams):
        super(KeyboardTrackingModel, self).__init__()
        self.hparams = hparams

        num_classes = hparams['num_classes']

        self.layers = nn.Sequential(
            # input: 1x192x108,
            nn.Conv2d(1, 16, kernel_size=7, stride=1, padding=0),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=5, stride=1, padding=0),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=3, stride=3),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=0),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Flatten(),
            nn.Linear(4992, 256),
            nn.ReLU(),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.layers(x)
