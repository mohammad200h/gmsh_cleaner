
import argparse
import pathlib
import gmsh
from typing import List
import os
import meshio
from collections import Counter
from abc import ABC, abstractmethod
import numpy as np
import networkx as nx
import io

class Elements:
  def __init__(self,elementTypes,elementTags,elementNodeTags):
    self.types = elementTypes
    self.tags = elementTags 
    self.nodeTags = elementNodeTags 

class Nodes:
  def __init__(self,indexes,nodes):
    self.indexes = indexes 
    self.nodes = nodes

class Obj:
  def __init__(self,name,entities,elements,nodes):
    self.name = name
    self.elements = elements 
    self.nodes = nodes 
    self.entities = entities

class BaseExtractor(object):
  def __init__(self, input_file_path):
    input_path = pathlib.Path(input_file_path)
    print("input_path:: ",input_path)
    gmsh.open(input_path.as_posix())


  @abstractmethod
  def process(self):
    pass

  @abstractmethod
  def process_joint_object(self,entities):
    pass

  @abstractmethod
  def process_disjoint_object(self,entities):
    pass

  def has_msh_extension(self,filename):
    filename_without_extension, extension = os.path.splitext(filename)
    return filename_without_extension, extension.lower() == '.msh'

  def split_path_and_filename(self,path):
    directory, filename = os.path.split(path)
    return directory + os.sep, filename

  def produce_path(self, path, is_volume = True,is_obj = False) -> str:
    path,filename = self.split_path_and_filename(path)
    filename_without_extension, there_is_an_extension = self.has_msh_extension(filename)

    self.path_without_filename = path
    self.output_filename_without_extension = filename_without_extension

    new_file_name = ""
    if there_is_an_extension:
      new_file_name = filename_without_extension
    else:
      new_file_name = filename

    if is_volume:
      new_file_name +="_vol.msh"
    else:
      if is_obj:
        new_file_name +="_surf.obj"
      else:
        new_file_name +="_surf.msh"

    return  path,filename_without_extension,new_file_name

  def get_num_points(self,node_indexes):
    return len(node_indexes)
  
  def get_nodes(self):
    nodes_index,points,info = gmsh.model.mesh.getNodes()
    return nodes_index,points.reshape(-1,3)

  def get_max_xyz(self,points):
    x = [point[0] for point in points]
    y = [point[1] for point in points]
    z = [point[2] for point in points]

    max_x = max(x)
    max_y = max(y)
    max_z = max(z)

    min_x = min(x)
    min_y = min(y)
    min_z = min(z)

    return (min_x, min_y, min_z, max_x, max_y, max_z)

  def create_adjacency_matrix(self,volume_entities):
    num_vol = len(volume_entities)
    adjacency_matrix = np.zeros((num_vol,num_vol))
    for i,v_e_one in enumerate(volume_entities):
      for j,v_e_two in enumerate(volume_entities):
        if i!=j:
          adjacency_matrix[i,j] = 1 if self.is_there_a_shared_surface(v_e_one,v_e_two) else 0
    return adjacency_matrix

  def create_graph_from_adjacency_matrix(self,adjacency_matrix):
    # Create a graph from the adjacency matrix
    G = nx.from_numpy_array(adjacency_matrix)

    return G

  def get_objects_from_graph(self,G,volume_entities):
    graphs = list(nx.connected_components(G))
    objects = []
    for g in graphs:
      v_entities = [volume_entities[i] for i in g]
      objects.append(v_entities)

    return objects

  def get_maximum_occurrence(self,surfaces_index):
    # https://www.geeksforgeeks.org/python-count-occurrences-element-list/
    d = Counter(surfaces_index)
    max_occurrence = 0
    for s in surfaces_index:
      occ = d[s]
      if occ>max_occurrence:
        max_occurrence = occ

    return max_occurrence

  def get_all_entities(self):
    return gmsh.model.getEntities()

  def get_point_entities(self,entities):
    e_point = []
    for e in entities:
      if e[0]==0:
        e_point.append(e)

    return e_point

  def get_curve_entities(self,entities):
    e_curve = []
    for e in entities:
      if e[0]==1:
        e_curve.append(e)

    return e_curve

  def get_surface_entities(self,entities):
    e_surface = []
    for e in entities:
      if e[0]==2:
        e_surface.append(e)

    return e_surface

  def get_volume_entities(self,entities):
    e_volume = []
    for e in entities:
      if e[0]==3:
        e_volume.append(e)

    return e_volume

  def get_boundary_entities_for_volumes(self,volume_entities):
    e_surface = []

    for e_v in volume_entities:
      e_surface += gmsh.model.getBoundary([e_v])
    return e_surface

  def is_there_a_shared_surface(self,e1,e2):
    entities = [e1,e2]
    e_surface = self.get_boundary_entities_for_volumes(entities)
    surface = []
    for e in e_surface:
      # shared surface will be repeated but one will have opposite sign
      surface.append(abs(e[1]))

    occ = self.get_maximum_occurrence(surface)
   
    if occ>1:
       return True

    return False

  def get_nodes_given_elements_indexes(self,nodes_idx):
    v_nodes_data = self.get_nodes()
    node_indexes,nodes = v_nodes_data

    remapped_nodes = nodes[nodes_idx]

    return remapped_nodes
  
  def get_normals(self,elements,nodes):
    normals = []
    for elem in elements:
      # print(f"elem[0]::{elem[0]-1}")
      n_0 = nodes[elem[0]-1]
      n_1 = nodes[elem[1]-1]
      n_2 = nodes[elem[2]-1]
      # print(f"n_0::{n_0}")
      # print(f"n_1::{n_1}")
      # print(f"n_2::{n_2}")

      edge_one = n_1 - n_0
      edge_two = n_2 - n_0

      normal = np.cross(edge_one, edge_two)

      normal /= np.linalg.norm(normal)
      normals.append(normal)

    return normals
    
  def get_entity_elements(self,entity):
    elem_data = gmsh.model.mesh.getElements(entity[0],entity[1])
    elem_dim,element_index,elem_nodes_index = elem_data
    if elem_dim[0]==2:
      dim = elem_dim[0]+1
    elem_nodes_index = np.array(elem_nodes_index).reshape(-1,dim)
    return dim,element_index,elem_nodes_index

  def combine(self,arrays):
    # Initialize an empty array to store combined arrays
    combined_array = np.empty((0, arrays[0].shape[1]), arrays[0].dtype)

    # Combine arrays
    for array in arrays:
        combined_array = np.vstack((combined_array, array))
    return combined_array

class ModelInformation:
  def __init__(self):
    # TODO : print information about model
    pass

class VolumeExtractor(BaseExtractor):
  def __init__(self, input_file_path, output_file_path):
    super().__init__(input_file_path)

    path_info = self.produce_path(pathlib.Path(output_file_path))
    self.path_without_filename = path_info[0]
    self.output_filename_without_extension = path_info[1]
    self.new_file_name = path_info[2]
    if self.path_without_filename == "/":
      self.output_file_path = pathlib.Path(self.new_file_name)
    else:
      self.output_file_path = pathlib.Path(self.path_without_filename + self.new_file_name)


  def process(self):
    entities = self.get_all_entities()
    v_entities = self.get_volume_entities(entities)

    # creating graph of connected volumes
    adjacency_matrix = self.create_adjacency_matrix(v_entities)
    G = self.create_graph_from_adjacency_matrix(adjacency_matrix)

    objects_per_graph = self.get_objects_from_graph(G,v_entities)

    objects = []
    for i,v_entities in enumerate(objects_per_graph):
      if len(objects_per_graph)>0:
        file_name = self.output_filename_without_extension + "_vol" + f"{i+1}.msh"
      else:
        file_name = self.output_filename_without_extension + "_vol.msh"
      
      if self.output_filename_without_extension == "/":
        self.output_file_path = pathlib.Path(file_name)
      else:
        self.output_file_path = pathlib.Path(self.output_filename_without_extension 
                                             + file_name
        )
      
      obj = self.process_object(v_entities,file_name)
      objects.append(obj)

    for obj in objects:
      self.create_model(obj)

  def process_object(self,v_entities,file_name):
    
    # creating a single volume entity
    elementTypes = {}
    elementTags = {}
    elementNodeTags = {}

    for v_entity in v_entities:
      elementTypes[v_entity],elementTags[v_entity],elementNodeTags[v_entity]=gmsh.model.mesh.getElements(v_entity[0],v_entity[1])


    v_nodes_data = self.get_nodes()
    node_indexes,nodes = v_nodes_data
    
    obj = Obj(
              file_name,
              v_entities,
              Elements(elementTypes,elementTags,elementNodeTags),
              Nodes(node_indexes,nodes.flatten().tolist())
          )
    return obj

  def create_model(self,obj):
    gmsh.model.add(obj.name)
    gmsh.model.addDiscreteEntity(3,1)
    gmsh.model.mesh.addNodes(3,1,obj.nodes.indexes,obj.nodes.nodes)
    
    for e in obj.entities:
      gmsh.model.mesh.addElements(3, 1, obj.elements.types[e], obj.elements.tags[e],
                                  obj.elements.nodeTags[e])

    gmsh.model.mesh.reclassifyNodes()
    gmsh.option.setNumber("Mesh.MshFileVersion",4.1)
    # gmsh.model.mesh.generate(3)
    gmsh.write(obj.name)

class SurfaceExtractor(BaseExtractor):
  def __init__(self, input_file_path, output_file_path):
    super().__init__(input_file_path)

    path_info = self.produce_path(pathlib.Path(output_file_path),is_volume = False)
    self.path_without_filename = path_info[0]
    self.output_filename_without_extension = path_info[1]
    self.new_file_name = path_info[2]
    if self.path_without_filename == "/":
      self.output_file_path = pathlib.Path(self.new_file_name)
    else:
      self.output_file_path = pathlib.Path(self.path_without_filename + self.new_file_name)

  def process(self):
    entities = self.get_all_entities()
    v_entities = self.get_volume_entities(entities)

    # creating graph of connected volumes
    adjacency_matrix = self.create_adjacency_matrix(v_entities)
    G = self.create_graph_from_adjacency_matrix(adjacency_matrix)

    objects_per_graph = self.get_objects_from_graph(G,v_entities)


    paths = []
    objects = []
    for i,v_entities in enumerate(objects_per_graph):
      file_name = ""
      if len(objects_per_graph)>0:
        file_name = self.output_filename_without_extension + "_surf" + f"{i+1}.msh"
      else:
        file_name = self.output_filename_without_extension + "_surf.msh"
      
      if self.output_filename_without_extension == "/":
        self.output_file_path = pathlib.Path(file_name)
      else:
        print(f"self.output_filename_without_extension:: {self.output_filename_without_extension}")
        print(f"file_name:: {file_name}")
        self.output_file_path = pathlib.Path(
                                file_name
        )
      paths.append(self.output_file_path)
      obj = self.process_object(v_entities,file_name)
      objects.append(obj)

    for obj in objects:
      self.create_model(obj)

    return paths

  def process_object(self,volume_entities,file_name):
    # surfaces around the volume entities
    e_surfaces = gmsh.model.getBoundary(volume_entities)
    e_surfaces =  [(e[0],abs(e[1])) for e in e_surfaces]

    elementTypes = {}
    elementTags = {}
    elementNodeTags = {}


    for e_surface in e_surfaces:
      elementTypes[e_surface],elementTags[e_surface],elementNodeTags[e_surface]=gmsh.model.mesh.getElements(e_surface[0],e_surface[1])
      
    v_nodes_data = self.get_nodes()
    node_indexes,nodes = v_nodes_data
 


    obj = Obj(
              file_name,
              e_surfaces,
              Elements(elementTypes,elementTags,elementNodeTags),
              Nodes(node_indexes,nodes.flatten().tolist())
          )
    return obj

  def create_model(self,obj):
    # generating GMSH
    gmsh.model.add(obj.name)
    gmsh.model.addDiscreteEntity(2,1)
    gmsh.model.mesh.addNodes(2,1,obj.nodes.indexes,obj.nodes.nodes)
    
    for e in obj.entities:
      gmsh.model.mesh.addElements(2, 1, obj.elements.types[e], obj.elements.tags[e],
                                  obj.elements.nodeTags[e])

    gmsh.model.mesh.reclassifyNodes()
    gmsh.option.setNumber("Mesh.MshFileVersion",4.1)
    gmsh.model.mesh.generate(3)
    gmsh.write(obj.name)

    # generate OBJ
    node_indexes,nodes = self.get_nodes()
    elem_dim,element_index,elem_nodes_index = gmsh.model.mesh.getElements()
    elements = np.array(elem_nodes_index,dtype=np.int32).reshape(-1,3)

    # print(f"num nodes::{nodes.shape}")
    # print(f"num elements::{elements.shape}")


    normals = np.array(self.get_normals(elements,nodes)).reshape(-1,3)

    # print(f"normals::{normals}")

    out = io.StringIO()

    # nodes 
    for node in nodes:
      x,y,z = node
      out.write(f"v {x} {y} {z}\n")

    # normals
    for normal in normals:
      x,y,z = normal  
      out.write(f"vn {x} {y} {z}\n")

    #faces
    for face in elements:
      i,j,k = face 
      out.write(f"f {i}/{i}/{i} {j}/{j}/{j} {k}/{k}/{k}\n")
    
    with open(pathlib.Path(obj.name+".obj"), "w") as f:
      f.write(out.getvalue())

  
def main():

  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("-i", "--input", type=str, help="Path to the msh file produced by Gmsh App.")
  parser.add_argument("-o", "--output", type=str, help="Path to the output file.")
  args = parser.parse_args()

  # produce files only containing volume
  VolumeExtractor(args.input, args.output).process()

  # produce a files only containing surface
  paths = SurfaceExtractor(args.input, args.output).process()


if __name__ == '__main__':
  # Initialize Gmsh
  gmsh.initialize()
  # gmsh.initialize(argv=["","-bin"])

  main()

  # Finalize Gmsh
  gmsh.finalize()
