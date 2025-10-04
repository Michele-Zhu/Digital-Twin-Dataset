# PEP8 Python Style Import
# Standard library imports
import os 
import sys 
from pathlib import Path
sys.path.append(os.getcwd())
# Third party imports
import numpy as np
import pandas as pd
from scipy import constants
from tqdm import tqdm

# Local imports
from util.communication_channel_utility import compute_channel_matrix, compute_adcpm
from util.MemmapManager import MemmapManager

def user_args_parse():
  pass

def main():
    # parameters
    N=8  # N = columns
    M=16  # M = rows
    B=400*1e6  # Bandwidth
    Ts = 1/B  # sampling time
    Nc = 1024  # number of subcarriers
    delay_max = Ts*Nc  # maximum delay 
    Tc = Nc*Ts  # OFDM symbol duration
    f0 = 28*1e9  # carrier frequency
    c = constants.c  # speed of light
    wavelength = c/f0  # lambda
    d = wavelength/2  # Antenna spacing

    # paths
    data_path = Path("data/ray_tracing/28_GHz/DEIB_PARKED/i2v_grid/GRID_2x2/RT_sI2V_c2.8E+10_d5_p1.0E+06_iTTTT_l20/channel_dataset")
    channel_dataset_path = data_path / "channel_dataset.csv"
    grid_positions_path = data_path / "points_positions.csv"
    output_path = Path("data/space_frequency_dataset/")
    output_folder_name = "Nc_{}_{}x{}".format(Nc, M, N)
    output_folder_path = output_path / output_folder_name
    output_folder_path.mkdir(parents=True, exist_ok=True)

    print(f"Current working directory: {os.getcwd()}")

    # import data
    channel_dataset_df = pd.read_csv(channel_dataset_path)
    grid_positions_df = pd.read_csv(grid_positions_path)

    # Tip use numpy mem map, resize the array as needed. Managing grid_cell_id with memmap is abit cumbersome 
    # Iterate over all grid positions
    channel_datawriter = MemmapManager(output_folder_path/"channel_data.npy", dtype=np.complex128, mode='w+', grow_size=10, shape=(1, N*M, Nc), overwrite=True)
    position_datawriter = MemmapManager(output_folder_path/"positions.npy", dtype=np.float32, mode='w+', grow_size=10, shape=(1, 3), overwrite=True)
    adcpm_datawriter = MemmapManager(output_folder_path/"adcpm_data.npy", dtype=np.float32, mode='w+', grow_size=10, shape=(1, N*M, Nc), overwrite=True)
    blockage_flag_datawriter = MemmapManager(output_folder_path/"blockage_flags.npy", dtype=bool, mode='w+', grow_size=10, shape=(1,), overwrite=True)
    for grid_index in tqdm(range(0, len(grid_positions_df))): # len(grid_positions_df)
        grid_name = grid_positions_df.iloc[grid_index]['grid_cell_id']
        channel_df_subset = channel_dataset_df[channel_dataset_df['rx_id'] == grid_name]
        n_paths = channel_df_subset.shape[0]
        [channel_matrix, empty_flag] = compute_channel_matrix(channel_df_subset, n_paths=n_paths, delay_max=delay_max, antenna_rows=M, antenna_cols=N, n_subcarriers=Nc, symbol_duration=Tc, carrier_frequency=f0, v_spacing=0.8*wavelength, h_spacing=0.5*wavelength, path_doppler_shifts=None)
        if empty_flag:
            # tqdm.write("skip")
            continue
        adcpm = compute_adcpm(channel_matrix, antenna_rows=M, antenna_cols=N, n_subcarriers=Nc)
        blockage_flag = channel_df_subset.iloc[0]['blockage_flag']
        position = grid_positions_df.iloc[grid_index][1:].to_numpy(dtype=np.float32)
        
        channel_datawriter.write(channel_matrix)
        position_datawriter.write(position)
        adcpm_datawriter.write(adcpm)
        blockage_flag_datawriter.write(blockage_flag)
        # also write grid_cell_id, grid_cell_location, blockage_flag, 
    channel_datawriter.complete_write(log_file=True, overwrite=True)
    position_datawriter.complete_write(log_file=True)
    adcpm_datawriter.complete_write(log_file=True)
    blockage_flag_datawriter.complete_write(log_file=True)

if __name__ == "__main__":
    print("Job Started")
    main()
    print("Job Completed")