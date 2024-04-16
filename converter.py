
from abc import ABC, abstractmethod
import argparse
from collections import Counter
import io
import os
import pathlib
from typing import List
import gmsh
import matplotlib.pyplot as plt
import meshio
import networkx as nx
import numpy as np


class Elements:

  def __init__(self, element_types, element_tags, element_node_tags):
    self.types = element_types
    self.tags = element_tags
    self.node_tags = element_node_tags


class Nodes:

  def __init__(self, indexes, nodes):
    self.indexes = indexes
    self.nodes = nodes


class Obj:

  def __init__(self, name, entities, elements, nodes,faces_to_flip = None):
    self.name = name
    self.elements = elements
    self.nodes = nodes
    self.entities = entities
    self.faces_to_flip = faces_to_flip


class BaseExtractor(object):

  def __init__(self, input_file_path):
    input_path = pathlib.Path(input_file_path)
    gmsh.open(input_path.as_posix())

  @abstractmethod
  def process(self):
    pass

  @abstractmethod
  def process_joint_object(self, entities):
    pass

  def has_msh_extension(self, filename):
    filename_without_extension, extension = os.path.splitext(filename)
    return filename_without_extension, extension.lower() == ".msh"

  def split_path_and_filename(self, path):
    directory, filename = os.path.split(path)
    return directory + os.sep, filename

  def get_path_info(self, path):
    path, filename = self.split_path_and_filename(path)
    filename_without_extension, _ = self.has_msh_extension(
        filename
    )
    return path, filename_without_extension

  def get_nodes(self):
    nodes_index, points, info = gmsh.model.mesh.getNodes()
    return nodes_index, points.reshape(-1, 3)

  def create_adjacency_matrix(self, volume_entities):
    num_vol = len(volume_entities)
    adjacency_matrix = np.zeros((num_vol, num_vol))
    for i, v_e_one in enumerate(volume_entities):
      for j, v_e_two in enumerate(volume_entities):
        if i != j:
          adjacency_matrix[i, j] = (
              1 if self.is_there_a_shared_surface(v_e_one, v_e_two) else 0
          )
    return adjacency_matrix

  def create_graph_from_adjacency_matrix(self, adjacency_matrix):
    # create a graph from the adjacency matrix
    graph = nx.from_numpy_array(adjacency_matrix)

    return graph

  def get_objects_from_graph(self, graph, volume_entities):
    graphs = list(nx.connected_components(graph))
    objects = []
    for g in graphs:
      v_entities = [volume_entities[i] for i in g]
      objects.append(v_entities)

    return objects

  def get_maximum_occurrence(self, surfaces_index):
    d = Counter(surfaces_index)
    max_occurrence = 0
    for s in surfaces_index:
      occ = d[s]
      if occ > max_occurrence:
        max_occurrence = occ

    return max_occurrence

  def get_all_entities(self):
    return gmsh.model.getEntities()

  def get_curve_entities(self, entities):
    e_curve = []
    for e in entities:
      if e[0] == 1:
        e_curve.append(e)

    return e_curve

  def get_surface_entities(self, entities):
    e_surface = []
    for e in entities:
      if e[0] == 2:
        e_surface.append(e)

    return e_surface

  def get_volume_entities(self, entities):
    e_volume = []
    for e in entities:
      if e[0] == 3:
        e_volume.append(e)

    return e_volume

  def get_boundary_entities_for_volumes(self, volume_entities):
    e_surface = []

    for e_v in volume_entities:
      e_surface += gmsh.model.getBoundary([e_v])
    return e_surface

  def is_there_a_shared_surface(self, entitiy_one, entitiy_two):
    entities = [entitiy_one, entitiy_two]
    e_surface = self.get_boundary_entities_for_volumes(entities)
    surface = []
    for e in e_surface:
      # shared surface will be repeated but one will have opposite sign
      surface.append(abs(e[1]))

    occ = self.get_maximum_occurrence(surface)

    if occ > 1:
      return True

    return False

  def get_nodes_given_elements_indexes(self, nodes_idx):
    v_nodes_data = self.get_nodes()
    node_indexes, nodes = v_nodes_data

    remapped_nodes = nodes[nodes_idx]

    return remapped_nodes

  def flip_face(self,face):
    return face[::-1]


  def get_normal(self,n_0,n_1,n_2):
    edge_one = n_1 - n_0
    edge_two = n_2 - n_0

    normal = np.cross(edge_one, edge_two)
    normal /= np.linalg.norm(normal)
  
    return normal
  
  def get_normals(self, elements, nodes):
    normals = []
  
    for i,elem in enumerate(elements):

      n_0 = nodes[elem[0] - 1]
      n_1 = nodes[elem[1] - 1]
      n_2 = nodes[elem[2] - 1]

      normal = self.get_normal(n_0,n_1,n_2) 

      normals.append(normal)

    
    
    

    return np.array(normals).reshape(-1,3)
  



  def get_entity_elements(self, entity):
    elem_data = gmsh.model.mesh.getElements(entity[0], entity[1])
    elem_dim, element_index, elem_nodes_index = elem_data

    if elem_dim[0] == 2:
      dim = elem_dim[0] + 1
    elem_nodes_index = np.array(elem_nodes_index).reshape(-1, dim)
    return dim, element_index, elem_nodes_index

  def combine(self, arrays):
    # Initialize an empty array to store combined arrays
    combined_array = np.empty((0, arrays[0].shape[1]), arrays[0].dtype)

    # combine arrays
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

    self.path,self.file_name = self.get_path_info(pathlib.Path(output_file_path))

  def process(self):
    entities = self.get_all_entities()
    v_entities = self.get_volume_entities(entities)

    # creating graph of connected volumes
    adjacency_matrix = self.create_adjacency_matrix(v_entities)
    graph = self.create_graph_from_adjacency_matrix(adjacency_matrix)

    objects_per_graph = self.get_objects_from_graph(graph, v_entities)
    there_are_separate_objects = len(objects_per_graph) > 1
    objects = []
    for i, v_entities in enumerate(objects_per_graph):
      prefix = None
      if there_are_separate_objects:
        prefix = i+1
 
      
      obj = self.process_object(v_entities,prefix)
      objects.append(obj)

    for obj in objects:
      self.create_model(obj)

  def process_object(self, v_entities,prefix):

    element_types = {}
    element_tags = {}
    element_node_tags = {}

    for v_entity in v_entities:
      (
          element_types[v_entity],
          element_tags[v_entity],
          element_node_tags[v_entity],
      ) = gmsh.model.mesh.getElements(v_entity[0], v_entity[1])

    v_nodes_data = self.get_nodes()
    node_indexes, nodes = v_nodes_data

    obj = Obj(
        self.file_name + "_vol" + (str(prefix) if prefix !=None else "") ,
        v_entities,
        Elements(element_types, element_tags, element_node_tags),
        Nodes(node_indexes, nodes.flatten().tolist()),
    )
    return obj

  def create_model(self, obj):
    gmsh.model.add(obj.name)
    gmsh.model.addDiscreteEntity(3, 1)
    gmsh.model.mesh.addNodes(3, 1, obj.nodes.indexes, obj.nodes.nodes)

    for e in obj.entities:
      gmsh.model.mesh.addElements(
          3,
          1,
          obj.elements.types[e],
          obj.elements.tags[e],
          obj.elements.node_tags[e],
      )

    gmsh.model.mesh.reclassifyNodes()
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    # gmsh.model.mesh.generate(3)
    gmsh.write(obj.name+".msh")


class SurfaceExtractor(BaseExtractor):

  def __init__(self, input_file_path, output_file_path):
    super().__init__(input_file_path)

    self.path,self.file_name = self.get_path_info(pathlib.Path(output_file_path))

  def process(self):
    entities = self.get_all_entities()
    v_entities = self.get_volume_entities(entities)

    # creating graph of connected volumes
    adjacency_matrix = self.create_adjacency_matrix(v_entities)
    G = self.create_graph_from_adjacency_matrix(adjacency_matrix)

    objects_per_graph = self.get_objects_from_graph(G, v_entities)
    there_are_separate_objects = len(objects_per_graph) > 1

    paths = []
    objects = []
    for i, v_entities in enumerate(objects_per_graph):
      prefix = None
      if there_are_separate_objects:
        prefix = i+1

      obj = self.process_object(v_entities,prefix)
      objects.append(obj)

    for obj in objects:
      self.create_model(obj)

  def process_object(self, volume_entities,prefix):
    # surfaces around the volume entities
    e_surfaces = gmsh.model.getBoundary(volume_entities)

    

    element_types = {}
    element_tags = {}
    element_node_tags = {}

    for e_surface in e_surfaces:
      (
          element_types[e_surface],
          element_tags[e_surface],
          element_node_tags[e_surface],
      ) = gmsh.model.mesh.getElements(e_surface[0], abs(e_surface[1]))

    v_nodes_data = self.get_nodes()
    node_indexes, nodes = v_nodes_data

    obj = Obj(
        self.file_name + "_surf" + (str(prefix) if prefix !=None else "") ,
        e_surfaces,
        Elements(element_types, element_tags, element_node_tags),
        Nodes(node_indexes, nodes.flatten().tolist())
    )
    return obj

  def create_model(self, obj):
    # generating GMSH
    gmsh.model.add(obj.name)
    gmsh.model.addDiscreteEntity(2, 1)
    gmsh.model.mesh.addNodes(2, 1, obj.nodes.indexes, obj.nodes.nodes)

  
    for e in obj.entities:
      elements_node_tags = obj.elements.node_tags[e]
      if e[1]<0:
        elements_node_tags = obj.elements.node_tags[e]
        elements_node_tags = [np.flip(obj.elements.node_tags[e][0])]

      gmsh.model.mesh.addElements(
          2,
          1,
          obj.elements.types[e],
          obj.elements.tags[e],
          elements_node_tags
      )



    


    gmsh.model.mesh.reclassifyNodes()
    gmsh.option.setNumber("Mesh.MshFileVersion", 4.1)
    gmsh.model.mesh.generate(3)
    gmsh.write(obj.name+".msh")

    # generate OBJ
    node_indexes, nodes = self.get_nodes()
    elem_dim, element_index, elem_nodes_index = gmsh.model.mesh.getElements()
    elements = np.array(elem_nodes_index, dtype=np.int32).reshape(-1, 3)

    normals = self.get_normals(elements,nodes)

    out = io.StringIO()

    # nodes
    for node in nodes:
      x, y, z = node
      out.write(f"v {x} {y} {z}\n")

    # normals
    for normal in normals:
      x, y, z = normal
      out.write(f"vn {x} {y} {z}\n")

    # faces
    for idx,face in enumerate(elements):
   
      i,j,k = face
  
      out.write(f"f {i}/{i}/{i} {j}/{j}/{j} {k}/{k}/{k}\n")

    with open(pathlib.Path(obj.name + ".obj"), "w") as f:
      f.write(out.getvalue())


def main():

  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument(
      "-i",
      "--input",
      type=str,
      help="Path to the msh file produced by Gmsh App.",
  )
  parser.add_argument(
      "-o", "--output", type=str, help="Path to the output file."
  )
  args = parser.parse_args()

  # produce files only containing volume
  VolumeExtractor(args.input, args.output).process()

  # produce a files only containing surface
  SurfaceExtractor(args.input, args.output).process()


if __name__ == "__main__":
  # Initialize Gmsh
  gmsh.initialize()

  main()

  # Finalize Gmsh
  gmsh.finalize()
