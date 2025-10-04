# PEP8 Python Style Import
# Standard library imports
import sys
import os
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
    random_blockage_flag = False # If true randomly remove the LoS path, i.e., models a random probability of the LoS path being blocked by some non-modelled object
    random_blockage_probability = 0.2  # random blockage probability, randomly set delete the LoS path 

    data_path = Path("data/ray_tracing/28_GHz/DEIB_PARKED/i2v_vehicular_dynamic/VEH_d300s_st0.1s_vSE15_vHA15_vTR10_vBU5/RT_sI2V_c2.8E+10_d5_p1.0E+06_iTTTT_l20")
    channel_path = data_path / "channel_dataset/channel_dataset.csv"
    vehicle_traffic_path = data_path / "vehicular_traffic/sumo_vehicular_traffic_dataset.csv"

    output_path = Path("data/space_frequency_dataset")
    if random_blockage_flag:
      output_foldername = "Nc_{}_{}x{}".format(Nc, M, N) + "_vehicular" + "_random_blockage_probability{}_".format(random_blockage_probability) 
    else:
      output_foldername = "Nc_{}_{}x{}".format(Nc, M, N) + "_vehicular"
    output_folder_path = output_path/ output_foldername
    output_folder_path.mkdir(exist_ok=True, parents=True)
    # print(data_path)
    # print(data_path.is_dir())

    # import data
    channel_dataset_df = pd.read_csv(channel_path)
    vehicle_positions_df = pd.read_csv(vehicle_traffic_path)

    channel_datawriter = MemmapManager(output_folder_path/"channel_data.npy", dtype=np.complex128, mode='w+', grow_size=10, shape=(1, N*M, Nc), overwrite=True)
    sionna_position_datawriter = MemmapManager(output_folder_path/"sionna_positions.npy", dtype=np.float32, mode='w+', grow_size=10, shape=(1, 3), overwrite=True)
    gcs_position_datawriter = MemmapManager(output_folder_path/"gcs_positions.npy", dtype=np.float32, mode='w+', grow_size=10, shape=(1, 2), overwrite=True)
    utm_position_datawriter = MemmapManager(output_folder_path/"utm_positions.npy", dtype=np.float32, mode='w+', grow_size=10, shape=(1, 2), overwrite=True)

    time_step_datawriter = MemmapManager(output_folder_path/"time_steps.npy", dtype=np.int16, mode='w+', shape=(1,), overwrite=True)
    vehicle_id_datawriter = MemmapManager(output_folder_path/"vehicles_id.npy", dtype='<U16', mode='w+', shape=(1,), overwrite=True)
    blockage_flag_datawriter = MemmapManager(output_folder_path/"blockage_flags.npy", dtype=bool, mode='w+', grow_size=10, shape=(1,), overwrite=True)

    time_step_channel_dataset = np.unique(channel_dataset_df.time_step.to_numpy())
    for time_step in tqdm(time_step_channel_dataset):
        channel_dataset_time_step = channel_dataset_df[channel_dataset_df['time_step'] == time_step]
        vehicles_in_time_step_list = channel_dataset_time_step.rx_id.drop_duplicates().to_list()
        for vehicle_id in vehicles_in_time_step_list:
            channel_dataset_subset = channel_dataset_time_step[channel_dataset_time_step['rx_id'] == vehicle_id]
            n_paths = channel_dataset_subset.shape[0]
            # Blockage info 
            blockage_flag = channel_dataset_subset.iloc[0]['blockage_flag']
            # Randomly delete the LoS path if the blockage_flag is 0
            if (random_blockage_flag and not blockage_flag and np.random.uniform(0, 1) < random_blockage_probability and n_paths > 1):
                # delete the LoS path
                channel_dataset_subset = channel_dataset_subset[channel_dataset_subset['interactions_num'] != 0]
                channel_dataset_subset['blockage_flag'] = True # Artifially set the blockage flag to True
                blockage_flag = channel_dataset_subset.iloc[0]['blockage_flag']
                n_paths = n_paths - 1
                if n_paths == 0:
                    raise ValueError("No paths present, please check the data.")

            [channel_matrix, empty_flag] = compute_channel_matrix(channel_dataset_subset, n_paths=n_paths, delay_max=delay_max, antenna_rows=M, antenna_cols=N, n_subcarriers=Nc, symbol_duration=Tc, carrier_frequency=f0, v_spacing=0.8*wavelength, h_spacing=0.5*wavelength, path_doppler_shifts=None)
            if empty_flag:
                continue

            # Sionna position
            interaction_position_list = channel_dataset_subset.iloc[0]['interaction_positions_list']
            interaction_position_list = interaction_position_list.replace("[", "").replace("]", "").replace("\n", "").split()
            sionna_position = np.array([interaction_position_list[-3], interaction_position_list[-2], interaction_position_list[-1]], dtype=np.float32)
            # gcs and utm positions
            vehicle_time_step = vehicle_positions_df[vehicle_positions_df['time_step'] == time_step]
            vehicle_time_step = vehicle_time_step[vehicle_time_step['vehicle_id'] == vehicle_id]
            gcs_position = np.array([vehicle_time_step['latitude'].values[0], vehicle_time_step['longitude'].values[0]], dtype=np.float32)
            utm_position = np.array([vehicle_time_step['utm_x'].values[0], vehicle_time_step['utm_y'].values[0]], dtype=np.float32)

            channel_datawriter.write(channel_matrix)
            sionna_position_datawriter.write(sionna_position)
            gcs_position_datawriter.write(gcs_position)
            utm_position_datawriter.write(utm_position)
            time_step_datawriter.write(time_step)
            vehicle_id_datawriter.write(np.array(vehicle_id, dtype='<U16'))
            blockage_flag_datawriter.write(blockage_flag)

    channel_datawriter.complete_write(log_file=True, overwrite=True)
    sionna_position_datawriter.complete_write(log_file=True)
    gcs_position_datawriter.complete_write(log_file=True)
    utm_position_datawriter.complete_write(log_file=True)
    time_step_datawriter.complete_write(log_file=True)
    vehicle_id_datawriter.complete_write(log_file=True)
    blockage_flag_datawriter.complete_write(log_file=True)


if __name__ == "__main__":
    print("Job Starting")
    main()
    print("Job Completed.")