import torch

class Metric:
    """ Base class for all metrics"""
    def __init__(self, name: str) -> None:
        """ Initialize metric with name

        Args:
            name (str): name of metric
        """
        self.name = name

    def reset(self):
        """ Reset metric state to initial values and return metric value"""
        self.__init__()

    def update(self, output: torch.Tensor, target: torch.Tensor):
        """ Update metric state with new data
        
        Args:
            output (torch.Tensor): output of model
            target (torch.Tensor): target of data
        """
        pass

    def result(self):
        """ Return metric value"""
        pass


class Accuracy(Metric):
    """ Accuracy metric class
    
    Args:
        name (str, optional): name of metric. Defaults to 'accuracy'.
    """
    def __init__(self, name='accuracy') -> None:
        super(Accuracy, self).__init__(name=name)
        self.correct = 0
        self.total = 0

    def update(self, output: torch.Tensor, target: torch.Tensor):
        """ Update metric state with new data

        Args:
            output (torch.Tensor): output of model
            target (torch.Tensor): target of data
        """
        _, predicted = torch.max(output.data, 1)
        self.total += target.size(0)
        self.correct += (predicted == target).sum().item()

    def result(self):
        """ Return metric value"""
        return self.correct / self.total
    
import numpy as np
from itertools import groupby
from mltu.utils.text_utils import get_cer

class CERMetric(Metric):
    """A custom PyTorch metric to compute the Character Error Rate (CER).
    
    Args:
        vocabulary: A string of the vocabulary used to encode the labels.
        name: (Optional) string name of the metric instance.
        **kwargs: Additional keyword arguments.
    """
    def __init__(self, vocabulary, name='CER', **kwargs):
        super(CERMetric, self).__init__(name=name)
        self.vocabulary = vocabulary
        self.reset()

    def reset(self):
        """ Reset metric state to initial values"""
        self.cer = 0
        self.counter = 0

    def update(self, output: torch.Tensor, target: torch.Tensor):

        # convert to numpy
        output = output.detach().cpu().numpy()
        target = target.detach().cpu().numpy()
        # use argmax to find the index of the highest probability
        argmax_preds = np.argmax(output, axis=-1)
        
        # use groupby to find continuous same indexes
        grouped_preds = [[k for k,_ in groupby(preds)] for preds in argmax_preds]

        # convert indexes to chars
        output_texts = ["".join([self.vocabulary[k] for k in group if k < len(self.vocabulary)]) for group in grouped_preds]
        target_texts = ["".join([self.vocabulary[k] for k in group if k < len(self.vocabulary)]) for group in target]

        cer = get_cer(output_texts, target_texts)

        self.cer += cer
        self.counter += 1

    def result(self):
        """ Return metric value"""
        return self.cer / self.counter