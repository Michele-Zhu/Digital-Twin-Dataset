# PEP 8 Python Style guide
# Standard library imports

# Third party imports
import numpy as np
from scipy import constants


# Local imports

def db2pow(power_dB):
    return np.power(10, power_dB / 10)


def compute_channel_matrix(propagation_paths_df, n_paths, delay_max, antenna_rows, antenna_cols, n_subcarriers,
                           symbol_duration, carrier_frequency, v_spacing, h_spacing, path_doppler_shifts=None):
    wavelength = constants.c / carrier_frequency

    # Calculate per each path the array response
    dod_elevation_array = np.radians(propagation_paths_df['DoD_elevation_deg'].to_numpy())
    dod_azimuth_array = np.radians(propagation_paths_df['DoD_azimuth_deg'].to_numpy())
    array_response_matrix = np.zeros((antenna_rows * antenna_cols, n_paths), dtype=np.complex128)
    for path_index in range(0, n_paths):
        array_response_el = np.exp(-1j * 2 * np.pi * np.arange(0, antenna_rows) * (v_spacing / wavelength) * np.cos(
            dod_elevation_array[path_index]))
        array_response_az = np.exp(-1j * 2 * np.pi * np.arange(0, antenna_cols) * (h_spacing / wavelength) * np.sin(
            dod_elevation_array[path_index]) * np.cos(dod_azimuth_array[path_index]))
        array_response_matrix[:, path_index] = np.kron(array_response_el, array_response_az)

    power_array = np.sqrt(db2pow(propagation_paths_df['received_power_dBm'].to_numpy() - 30))
    delay_array = propagation_paths_df['delay_sec'].to_numpy()
    # Set to zero the values coming from delays bigger than delay_max
    delay_array = np.array([0 if x > delay_max else x for x in delay_array])

    if np.sum(delay_array) == 0:  # Exit and return None if you all delays are zeros
        empty_flag = True
        return None, empty_flag
    else:
        empty_flag = False
    phase_distance = delay_array * constants.c / wavelength
    if path_doppler_shifts is not None:
        raise NotImplementedError("Not implemented yet")
    else:
        alpha = np.multiply(power_array, np.exp(-1j * 2 * np.pi * phase_distance))

    channel_matrix = np.zeros((antenna_rows * antenna_cols, n_subcarriers), dtype=np.complex128)
    for subcarrier_index in range(0, n_subcarriers):
        channel_path = np.zeros((antenna_rows * antenna_cols, n_paths), dtype=np.complex128)
        for path_index in range(0, n_paths):
            channel_path[:, path_index] = alpha[path_index] * array_response_matrix[:, path_index] * np.exp(
                -1j * 2 * np.pi * delay_array[path_index] * subcarrier_index / symbol_duration)
        # NM x Nc complex matrix
        channel_matrix[:, subcarrier_index] = np.sum(channel_path, axis=1)
    return channel_matrix, empty_flag


def compute_adcpm(channel_matrix, antenna_rows, antenna_cols, n_subcarriers):
    # dft matrices
    V_N = np.mat(1 / np.sqrt(antenna_cols) * np.exp(
        -1j * (2 * np.pi / antenna_cols) * np.arange(0, antenna_cols).reshape(antenna_cols, 1) * np.arange(
            -antenna_cols / 2 + 1, antenna_cols / 2 + 1).reshape(1, antenna_cols)))
    V_M = np.mat(1 / np.sqrt(antenna_rows) * np.exp(
        -1j * (2 * np.pi / antenna_rows) * np.arange(0, antenna_rows).reshape(antenna_rows, 1) * np.arange(
            -antenna_rows / 2 + 1, antenna_rows / 2 + 1).reshape(1, antenna_rows)))
    F = np.mat(1 / np.sqrt(n_subcarriers) * np.exp(
        -1j * (2 * np.pi / n_subcarriers) * np.arange(0, n_subcarriers).reshape(n_subcarriers, 1) * np.arange(0,
                                                                                                              n_subcarriers).reshape(
            1, n_subcarriers)))

    # angle delay channel response matrix(ADCRM)
    G = 1 / np.sqrt(n_subcarriers * antenna_cols * antenna_rows) * np.kron(V_M.getH(),
                                                                           V_N.getH()) * channel_matrix * np.conjugate(
        F)
    P = np.square(np.abs(G))
    return P


def simulate_awgn(channel_matrix, noise_snr_db=15):
    snr = db2pow(noise_snr_db)
    power_tx = db2pow(23 - 30)  # transmit power of 23 dBm
    pilot = np.random.randn() + 1j * np.random.randn()
    pilot = pilot / np.linalg.norm(pilot) * np.sqrt(power_tx)
    power_rx = np.linalg.norm(channel_matrix * pilot) ** 2
    power_noise = power_rx / snr
    noise = np.random.randn(channel_matrix.shape[0], channel_matrix.shape[1]) + 1j * np.random.randn(
        channel_matrix.shape[0], channel_matrix.shape[1])
    noise = noise / np.linalg.norm(noise) * np.sqrt(power_noise)
    received_signal = channel_matrix * pilot + noise
    channel_uplink_estimate = received_signal / pilot
    return channel_uplink_estimate


class ADCPM_Manager:
    def __init__(self, antenna_rows, antenna_cols, n_subcarriers):
        # compute dft matrices used for adcpm
        self.antenna_rows = antenna_rows
        self.antenna_cols = antenna_cols
        self.n_subcarriers = n_subcarriers
        self.V_N = np.mat(1 / np.sqrt(antenna_cols) * np.exp(
            -1j * (2 * np.pi / antenna_cols) * np.arange(0, antenna_cols).reshape(antenna_cols, 1) * np.arange(
                -antenna_cols / 2 + 1, antenna_cols / 2 + 1).reshape(1, antenna_cols)))
        self.V_M = np.mat(1 / np.sqrt(antenna_rows) * np.exp(
            -1j * (2 * np.pi / antenna_rows) * np.arange(0, antenna_rows).reshape(antenna_rows, 1) * np.arange(
                -antenna_rows / 2 + 1, antenna_rows / 2 + 1).reshape(1, antenna_rows)))
        self.F = np.mat(1 / np.sqrt(n_subcarriers) * np.exp(
            -1j * (2 * np.pi / n_subcarriers) * np.arange(0, n_subcarriers).reshape(n_subcarriers, 1) * np.arange(0,
                                                                                                                  n_subcarriers).reshape(
                1, n_subcarriers)))
        self.F_conj = np.conj(self.F)
        self.G_norm_factor = 1 / np.sqrt(n_subcarriers * antenna_cols * antenna_rows)
        self.dft_kron = np.kron(self.V_M.getH(), self.V_N.getH())

        # parameters used to add noise
        self.power_tx = db2pow(23 - 30)  # TX power in linear
        self.power_tx_sqrt = np.sqrt(self.power_tx)

    def compute_adcpm(self, channel_matrix):
        G = self.G_norm_factor * self.dft_kron * channel_matrix * self.F_conj
        P = np.square(np.abs(G))
        return P

    def simulate_awgn(self, channel_matrix, noise_snr_db=15):
        snr = db2pow(noise_snr_db)
        pilot = np.random.randn() + 1j * np.random.randn()
        pilot = pilot / np.linalg.norm(pilot) * np.sqrt(self.power_tx_sqrt)
        power_rx = np.linalg.norm(channel_matrix * pilot) ** 2
        power_noise = power_rx / snr
        noise = np.random.randn(channel_matrix.shape[0], channel_matrix.shape[1]) + 1j * np.random.randn(
            channel_matrix.shape[0], channel_matrix.shape[1])
        noise = noise / np.linalg.norm(noise) * np.sqrt(power_noise)
        received_signal = channel_matrix * pilot + noise
        channel_uplink_estimate = received_signal / pilot
        return channel_uplink_estimate

    def compute_adcpm_with_noise(self, channel_matrix, noise_snr_db=15):
        channel_uplink_estimate = self.simulate_awgn(channel_matrix, noise_snr_db=noise_snr_db)
        P_estimate = self.compute_adcpm(channel_uplink_estimate)
        return P_estimate