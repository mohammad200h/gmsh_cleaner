# Getting Started
This package was meade to create compatible gmsh files for mujoco. Apps like [GMSH](https://gmsh.info/) can be used to view and create volume meshes. As part of the process multiple entities are created. It tends to create a volume mesh from surface mesh and store both in a single file.  gmsh_cleanr takes generated file as input and create two files one for surface as well as one for volume.

In addition if more that one volume file is stored in a single file; gmsh cleaner will create a file for each volume.

Here is a [tutorial](https://www.youtube.com/watch?v=RlZ6hPIo9F8) on how to create a volume mesh.


# Installation
Simply install the package using pip

```
pip install .
```

# Use Case

```
 gmsh_cleaner -v <GMSH version: 4.1 | 2.2> -b <boolean:  binary | ASCII  >  -i <input file> -o <outfile>
```

# Demo
First let's create a mesh from stl file using GMSH APP.

<video src="https://github.com/mohammad200h/gmsh_cleaner/edit/main/media/creating_volume_mesh.mp4" controls width="600"></video>


Now let's clean the file and create separate surface and volume mesh.

<video src="https://github.com/mohammad200h/gmsh_cleaner/edit/main//media/cleaning.mp4" controls width="600"></video>



# Relevant Mujoco github issues:

[#2342](https://github.com/google-deepmind/mujoco/issues/2342#issuecomment-2587066593): Unjustifid Error Thrown "XML Error: Error: Node tags must be sequential"
[#1543](https://github.com/google-deepmind/mujoco/issues/1543#event-14086492635) [#1492](https://github.com/google-deepmind/mujoco/issues/1492#event-14086474326): Unable to Build an XML file that reads in a binary MSH file?
[#1724](https://github.com/google-deepmind/mujoco/issues/1724): Using gmsh files in MuJoCo - XML Error: Error: Node tags must be sequential
