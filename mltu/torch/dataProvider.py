import os
import typing
import numpy as np
import pandas as pd
import concurrent.futures

from ..augmentors import Augmentor
from ..transformers import Transformer
from ..dataProvider import DataProvider


class ThreadExecutor:
    def __init__(self, workers: int) -> None:
        self.workers = workers
        
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        # self._executor = concurrent.futures.ProcessPoolExecutor(max_workers=workers) # Doesn't work

    def __call__(self, function, data) -> typing.Any:

        results = self._executor.map(function, data)

        return results

class DataProvider(DataProvider):
    """ DataProvider for PyTorch with multiprocessing and multithreading support.
    """
    def __init__(
            self, 
            dataset: typing.Union[str, list, pd.DataFrame],
            data_preprocessors: typing.List[typing.Callable] = None,
            batch_size: int = 4,
            shuffle: bool = True,
            initial_epoch: int = 1,
            augmentors: typing.List[Augmentor] = None,
            transformers: typing.List[Transformer] = None,
            batch_postprocessors: typing.List[typing.Callable] = None,
            skip_validation: bool = True,
            limit: int = None,
            use_cache: bool = False,
            workers: int = os.cpu_count(),
            use_multiprocessing: bool = False,
        ):
        """ Standardised object for providing data to a model while training.

        Args:
            dataset (str, list, pd.DataFrame): Path to dataset, list of data or pandas dataframe of data.
            data_preprocessors (list): List of data preprocessors. (e.g. [read image, read audio, etc.])
            batch_size (int): The number of samples to include in each batch. Defaults to 4.
            shuffle (bool): Whether to shuffle the data. Defaults to True.
            initial_epoch (int): The initial epoch. Defaults to 1.
            augmentors (list, optional): List of augmentor functions. Defaults to None.
            transformers (list, optional): List of transformer functions. Defaults to None.
            batch_postprocessors (list, optional): List of batch postprocessor functions. Defaults to None.
            skip_validation (bool, optional): Whether to skip validation. Defaults to True.
            limit (int, optional): Limit the number of samples in the dataset. Defaults to None.
            use_cache (bool, optional): Whether to cache the dataset. Defaults to False.
            workers (int, optional): Number of workers to use for multiprocessing or multithreading. Defaults to os.cpu_count().
            use_multiprocessing (bool, optional): Whether to use multiprocessing or multithreading. Defaults to multithreading (False).
        """
        super(DataProvider, self).__init__(dataset=dataset, data_preprocessors=data_preprocessors, batch_size=batch_size, 
                                           shuffle=shuffle, initial_epoch=initial_epoch, augmentors=augmentors, transformers=transformers, batch_postprocessors=batch_postprocessors,
                                           skip_validation=skip_validation, limit=limit, use_cache=use_cache)
        self.workers = workers
        self.use_multiprocessing = use_multiprocessing

    def start_executor(self) -> None:
        """ Start the executor for multiprocessing or multithreading"""
        self._executor = ThreadExecutor(min(self._batch_size, self.workers))

    def __getitem__(self, index: int):
        """ Returns a batch of processed data by index
        
        Args:
            index (int): index of batch
            
        Returns:
            tuple: batch of data and batch of annotations
        """
        dataset_batch = self.get_batch_annotations(index)

        if hasattr(self, "_executor") is False:
            self.start_executor()

        batch_data, batch_annotations = [], []
        for data, annotation in self._executor(self.process_data, dataset_batch):
            if data is None or annotation is None:
                continue
            batch_data.append(data)
            batch_annotations.append(annotation)

        if self._batch_postprocessors:
            for batch_postprocessor in self._batch_postprocessors:
                batch_data, batch_annotations = batch_postprocessor(batch_data, batch_annotations)

            return batch_data, batch_annotations

        return np.array(batch_data), np.array(batch_annotations)