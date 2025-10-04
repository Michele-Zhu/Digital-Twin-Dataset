# PEP 8 Python Style guide
# Standard library imports
from pathlib import Path

# Third party imports
import numpy as np

# Local imports

"""
Usage example: 
datawriter = memmapManager("DTCI_data/test133.npy", dtype=np.complex128, mode='w+', grow_size=10, shape=(1, 3, 3))
for j in range(0, 13):
    # print(j)
    x = np.arange(9).reshape(3, 3)*j
    datawriter.write(x)
    # print(datawriter.get_memmap()[j])

datawriter.complete_write(log=True)
"""


class MemmapManager:
    def __init__(self, file_path, dtype, shape, mode='w+', grow_size=100, overwrite=False):
        if type(shape) is not tuple:
            raise TypeError("Shape must be a tuple")
        self.shape = shape
        self.dtype = dtype
        self.mode = mode
        self.file_path = Path(file_path)
        if self.file_path.is_file() and not overwrite:
            raise FileExistsError(self.file_path)
        elif self.file_path.is_file() and overwrite:
            self.memmap = np.memmap(self.file_path, dtype=self.dtype, mode='r+', shape=self.shape)
        else:
            self.memmap = np.memmap(self.file_path, dtype=self.dtype, mode=self.mode, shape=self.shape)

        self.grow_size = grow_size
        self.write_index = 0

    def get_memmap(self):
        return self.memmap

    def flush(self):
        self.memmap.flush()

    def write(self, write_data):
        if write_data.shape != self.memmap.shape[1:]:
            raise Exception("Shape mismatch in data writing")

        if self.write_index >= self.memmap.shape[0]:
            self.flush()
            self.grow()
        self.memmap[self.write_index] = write_data
        self.write_index += 1

    def grow(self):
        # grow memmap size
        self.memmap = np.memmap(self.file_path, dtype=self.dtype, mode='r+',
                                    shape=(self.shape[0] + self.grow_size, *self.shape[1:]))
        self.shape = self.memmap.shape

    def complete_write(self, log_file=True, overwrite=False):
        # adjust the memory to the written data and write log_file
        self.memmap = np.memmap(self.file_path, dtype=self.dtype, mode='r+', shape=(self.write_index, *self.shape[1:]))
        self.shape = self.memmap.shape
        self.flush()
        if overwrite:
            write_mode = "w"
        else:
            write_mode = "a"
        if log_file:
            log_path = self.file_path.parent / "log.txt"
            filename = self.file_path.name
            with open(log_path, write_mode) as f:
                f.write(filename + ", shape is : " + str(self.shape) + ", dtype is : " + str(self.dtype) + "\n")