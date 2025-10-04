# Digital-Twin-Dataset
### This Repository is under contruction
This repository contains the processing used in the paper "Exploiting Age of Information in Network Digital Twins for AI-driven Real-Time Link Blockage Detection". The dataset can be downloaded at the following [link TBD]()

### Contents
- Scenario
  - Considered urban scenario
- Simulation
  - lore ius
## Scenario
### Considered urban scenario
The reference simulation scenario is the urban environment surrounding the Department of Electronics, Information and Bioengineering (DEIB) of Politecnico di Milano. A detailed 2.5D representation of the scenario has been provided by the *Laboratorio di simulazione urbana Fausto Curti* of the Department of Architecture and Urban Studies of Politecnico di Milano. The considered area of interest is represented in the "map_image.png" file.

### Parked Vehicles
Based on the above-described buildings scenario, we added a set of parked vehicle mehses along the streets in order to enhance the fidelity with respect to the corresponding real setting. We performed this step by considering a set of satellite images of the scenario and identifying the areas where parked vehicles are usually present. Three vehicle types have been considered for parked vehicles: sedan, hatchback, and truck. Their realizations as specific vehicle meshes are discussed in the Vehicle meshes section above.

### Selected Vehicle Meshes
The selection of the vehicle meshes is critical, as their level of detail can highly impact the fidelity of the raytracing simulation. We gathered a set of detailed and varied vehicle meshes from the open source [CARLA](https://carla.org) automotive simulator:
- Tesla Model 3 (sedan);
- Citroën C3 (hatchback);
- Mercedes Sprinter (truck);
- Mitsubishi Fusorosa (bus).

Considering a right-handed orthogonal reference frame XYZ, the vehicle’s length is assumed to be disposed along the negative y-axis, the vehicle’s width is along the x-axis, and the vehicle’s height is assumed to be along the z-axis. The vehicle meshes are assumed to be referred with respect to the middle of their front bumper (the highest y-coordinate of the mesh is 0 and the mesh is symmetric with respect to the YZ plane), and they are assumed to lie on the ground (z = 0 for the touching points of the wheels with the ground).

### Radio-Materials assignment
Referring to the ITU Recommendation [ITU-R P.2040-3](https://www.itu.int/rec/R-REC-P.2040/en), for the buildings’ meshes, we consider the ITU Concrete material.

Currently, the following radio materials have been considered for the vehicles' component meshes:
- body -> perfect electric conductor (PEC);
- glasses -> ITU glass;
- lights -> ITU glass;
- rims -> PEC;
- wheels -> PEC.

## Simulation Configuration

### Tx/Rx Configuration
The transmitter is a single base station with an isotropic radiation pattern positioned on the roof of the DEIB building.

According to the simulation mode, the receivers are defined in the following ways:
- for **grid simulations**, the static receivers are disposed on an orthogonal grid with given resolution and at a specific height;
- for **vehicular simulations**, the receivers are positioned in the scenario according to the data provided by SUMO vehicular traffic simulation.

### Reference Coordinate Systems
We consider a global coordinate system (GCS) with a Cartesian standard basis x', y', z'. In the considered setting, x' is oriented east, y' is oriented towards north, and z' is outgoing from the ground plane. This system is centered approximately in the center of the considered area of interest. Height, represented by the z-coordinate, is intended with respect to the ground.

`In the following, we will refer to the point coordinates in the scenario referred to the described GCS as local to distinguish them from the geographical coordinates (e.g., UTM or lon/lat) of the original map.`

Considering an arbitrary unit norm vector v'=(x, y, z). The Direction of Arrival (DoA) and Direction of Departure (DoD) elevation $\theta$ and azimuth $\phi$ angles are determined as:

$\theta=arccos(z),$
$\phi=arctan(y, x),$

where $arctan(y, x)$ is the two-argument inverse tangent function.

## Simulation Parameters
### NVIDIA Sionna Simulation Parameters
To simulate the mmWave wireless channel in Sionna, the following parameters are considered:
- **simulation type**: Infrastructure to Vehicle (I2V) or Vehicle to Vehicle (V2V); for this project purposes, only I2V communication is considered;
- **simulation mode**: grid simulation, static vehicular simulation, dynamic vehicular simulation;
- **carrier frequency**: carrier frequency used for simulation;
- **max paths depth**: max paths depth in terms of number of interactions with the environment;
- **sampled paths num**: number of sampled paths, referring to the 'fibonacci' method in Sionna; exponential notation has been used;
- **interaction types**: types of enabled interactions with the environment (among LOS, refraction, diffraction and scattering);
- **saved paths limi**t: max. number of saved paths for each grid point;
- **grid resolution**: spatial resolution of the receivers grid in terms of horizontal and vertical distance (in meters) between two contiguous grid points (in grid-based simulations);
- **grid_height**: height of the simulation grid (in grid-based simulations).

### SUMO simulation parameters
For each vehicle type, we consider the following SUMO simulation parameters:
- **vehicles per minute**: density of vehicles in the simulation, where the density is defined as the average number of vehicles per minute per lane km;
- **fringe factor**: the higher its value, the more likely vehicles are to be generated at the network fringe w.r.t. inner nodes; we set this value to 1E10, in order to generate vehicles only at the network fringe and, therefore, to prevent discontinuities in the SUMO simulation (e.g., vehicles abruptly appearing at inner nodes).
### Dataset Generation
In this section, we provide the details related to the structure of the generated vehicular traffic and
ray tracing datasets as well as on the directory structure used to save them during simulation.

According to the simulation type, the datasets are archived in different subdirectories of the main
output directory:
- `vehicular_traffic` contains the vehicular traffic data generated by SUMO;
- `channel_dataset` contains the ray tracing datasets generated using NVIDIA Sionna RT. 

### Grid Raytracing Datasets
The dataset directory name has the following format, summarizing the simulation parameters used in NVIDIA Sionna for simulation:
```
RT_s{sim_type}_c{carrier_frequency}_d{max_depth}_p{paths_num}_i{interaction_types}_l{paths_lim}_gr{grid_res}_h{grid_height}
E.g., “RT_sI2V_c2.8E+10_d5_p1.0E+05_iTTTT_l30_gr5.0x5.0”.
```
Each dataset directory contains two subdirectories:
- `channel_dataset`, it contains the following files, where the `.pkl` version is serialized within a Pandas DataFrame as Pickle file:
  - `grid_channel_dataset_gr{grid_res}.csv`, where *grid_res* expresses the grid resolution in meters; it contains the channel parameters data generated using Sionna in CSV format;
  - `grid_channel_dataset_gr{grid_res}.yml`, presents the Sionna simulation parameters in YAML format;
  - `grid_positions_grd{grid_res}.csv`, contains the grid points positions for the point ids within the channel dataset in CSV format; unreachable points (i.e., the ones for which no raytracing paths have been generated) have been filtered out;
  - `bs_position.csv`, contains the base station position in CSV format.
- `plots`, containing images representing the top-view of the grid points filtered after the Sionna simulation and, therefore, present in the dataset.

### Vehicular Raytracing Datasets
In this simulation, both vehicular traffic and raytracing are considered. The dataset subfolder structure is organized into two levels, where the first is related to the SUMO vehicular traffic simulation, and the second to the NVIDIA Sionna simulation parameters:
```
<sumo_parameterized_subdir>/<sionna_parameterized_subdir>
```
The `<sumo_parameterized_subdir>` has the following form:
```
VEH_d{duration_sec}s_st{sim_step_duration_sec}s_v{vehicle_type_1}{vehicle_density_1}_...v{vehicle_type_N}{vehicle_density_N}
E.g., “VEH_d300s_st0.1s_vSE15_vHA15_vTR10_vBU5”
```
The `<sionna_parameterized_subdir>` has the following form:
```
RT_s{sim_type}_c{carrier_frequency}_d{max_depth}_p{paths_num}_i{interaction_types}_l{paths_lim}
E.g., “RT_sI2V_c2.8E+10_d5_p1.0E+06_iTTTT_l20”
```
Each dataset directory contains two subdirectories:
- `channel_dataset`, containing the channel data and simulation parameters information, where the `.pkl` version is serialized within a Pandas DataFrame as Pickle file:
  - `channel_dataset.yml`, which contains the Sionna simulation parameters in YAML format;
  - `channel_dataset.csv`, which contains the channel raytracing data generated using Sionna in CSV format;
  - `bs_position.csv`, which contains the base station position in CSV format;
- `vehicular_traffic`, containing a copy of the SUMO vehicular traffic simulation data; in particular, it contains the following files:
 - `sumo_vehicular_traffic_dataset.csv`, contains the SUMO simulation data in CSV format.

## Dataset Columns Descriptions
### Channel Dataset
- Column 1 - Time step
- Column 2 - Transmitter type (only base station, for the considered I2V communication scenarios)
- Column 3 - Transmitter ID
- Column 4 - Receiver type (grid point or vehicle)
- Column 5 - Receiver ID
- Column 6 - Ray index (sequential identifier for a propagation path)
- Column 7 - Interactions number (number of interactions of the path with the environment)
- Column 8 - Received power [dBm]
- Column 9 - Phase [degrees] (between -180° and 180°)
- Column 10 - Delay [sec]
- Column 11 - DoA azimuth [degrees] (between -180° and 180°)
- Column 12 - DoA elevation [degrees] (between 0 and 180)
- Column 13 - DoD azimuth [degrees] (between -180° and 180°)
- Column 14 - DoD elevation [degrees] (between 0 and 180)
- Column 15 - List of interaction types (0: LoS; 1 : Reflected; 2 : Diffracted; 3 : Scattered)
- Column 16 - List of interactions' positions (x-coordinate [m], y-coordinate [m] and height [m])
- Column 17 - List of interactions' velocities (x-coordinate [m/s], y-coordinate [m/s] and zcoordinate [m/s])
- Column 18 - Blockage flag (true if the LoS path is not present for the point, false otherwise)

### Vehicular Traffic Dataset
- Column 1 - Time step (incremental integer; starting from 0)
- Column 2 - Elapsed time in seconds (time step * simulation step duration)
- Column 3 - Vehicle ID
- Column 4 - Vehicle type
- Column 5 - Longitude (w.r.t. the vehicle front bumper)
- Column 6 - Latitude (w.r.t. the vehicle front bumper)
- Column 7 - UTM x-coordinate (w.r.t. the vehicle front bumper)
- Column 8 - UTM y-coordinate (w.r.t. the vehicle front bumper)
- Column 9 - UTM zone
- Column 10 - UTM character
- Column 11 - Local x-coordinate (w.r.t. the vehicle front bumper)
- Column 12 - Local y-coordinate (w.r.t. the vehicle front bumper)
- Column 13 - Speed (m/s)
- Column 14 - Vehicle heading (0-360 deg; 0° towards North; increasing clockwise)
- Column 15 - SUMO Road ID
- Column 16 - SUMO Lane index
