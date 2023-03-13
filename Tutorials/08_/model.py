import torch.nn as nn
import torch.nn.functional as F

def activation_layer(activation: str='relu', alpha: float=0.1, inplace: bool=True):
    """ Activation layer wrapper for LeakyReLU and ReLU activation functions
    Args:
        activation: str, activation function name (default: 'relu')
        alpha: float (LeakyReLU activation function parameter)
    Returns:
        torch.Tensor: activation layer
    """
    if activation == 'relu':
        return nn.ReLU(inplace=inplace)
    elif activation == 'leaky_relu':
        return nn.LeakyReLU(negative_slope=alpha, inplace=inplace)

class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, skip_conv=True, stride=1, dropout=0.2, activation='leaky_relu'):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.activation = nn.LeakyReLU(negative_slope=0.1) if activation == 'leaky_relu' else nn.ReLU(inplace=True)
        self.dropout = nn.Dropout2d(p=dropout)
        
        self.shortcut = None
        if skip_conv:
            if stride != 1 or in_channels != out_channels:
                self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride)
        
    def forward(self, x):
        skip = x
        
        out = self.activation(self.bn1(self.conv1(x)))
        out = self.dropout(out)
        out = self.bn2(self.conv2(out))
        if self.shortcut is not None:
            skip = self.shortcut(skip)
        out += skip
        out = self.activation(out)
        out = self.dropout(out)
        
        return out

class CaptchaModel(nn.Module):
    def __init__(self, num_chars, activation='leaky_relu', dropout=0.2):
        super(CaptchaModel, self).__init__()

        self.x1 = ResidualBlock(3, 16, skip_conv = True, stride=1, activation=activation, dropout=dropout)
        self.x2 = ResidualBlock(16, 16, skip_conv = True, stride=2, activation=activation, dropout=dropout)
        self.x3 = ResidualBlock(16, 16, skip_conv = False, stride=1, activation=activation, dropout=dropout)

        self.x4 = ResidualBlock(16, 32, skip_conv = True, stride=2, activation=activation, dropout=dropout)
        self.x5 = ResidualBlock(32, 32, skip_conv = False, stride=1, activation=activation, dropout=dropout)

        self.x6 = ResidualBlock(32, 64, skip_conv = True, stride=2, activation=activation, dropout=dropout)
        # self.x7 = ResidualBlock(64, 32, skip_conv = True, stride=1, activation=activation, dropout=dropout)

        # self.x8 = ResidualBlock(32, 64, skip_conv = True, stride=2, activation=activation, dropout=dropout)
        # self.x9 = ResidualBlock(64, 64, skip_conv = False, stride=1, activation=activation, dropout=dropout)

        self.lstm = nn.LSTM(64, 128, bidirectional=True, num_layers=1, dropout=0.5, batch_first=True)
        self.output = nn.Linear(256, num_chars + 1)
        
        # self.output = nn.Linear(64, num_chars + 1)
        self.softmax = nn.LogSoftmax(dim=2)

    def forward(self, images):
        # normalize images between 0 and 1
        images_flaot = images / 255.0

        # transpose image to channel first
        images_flaot = images_flaot.permute(0, 3, 1, 2)

        # apply convolutions
        x = self.x1(images_flaot)
        x = self.x2(x)
        x = self.x3(x)

        x = self.x4(x)
        x = self.x5(x)

        x = self.x6(x)
        # x = self.x7(x)

        # x = self.x8(x)
        # x = self.x9(x)

        x = x.reshape(x.size(0), -1, x.size(1))

        x, _ = self.lstm(x)
        x = self.output(x)
        # x = F.log_softmax(x, 2)
        x = self.softmax(x)

        return x