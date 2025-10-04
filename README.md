# Digital-Twin-Dataset
### This Repository is under contruction
This repository contains the processing used in the paper "Exploiting Age of Information in Network Digital Twins for AI-driven Real-Time Link Blockage Detection". The dataset can be downloaded at the following [link TBD]()

### Contents

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
