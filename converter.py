
import argparse
import pathlib
import gmsh
from typing import List
import os
import meshio
from collections import Counter
from abc import ABC, abstractmethod
import numpy as np


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

  def write41_mesh_format_41(self):
    print(f"write41_mesh_format_41::output_file_path::{self.output_file_path}")
    with self.output_file_path.open('w') as f:
      f.write('$MeshFormat\n')
      f.write('4.1 0 8\n')
      f.write('$EndMeshFormat\n')

  def write41_nodes_header_end(self):
    with self.output_file_path.open('a') as f:
      f.write('$EndNodes\n')

  def write41_nodes_indices(self,num_nodes):
    with self.output_file_path.open('a') as f:
      for i in range(num_nodes):
        f.write(f"{i+1}\n")

  def write41_nodes(self,nodes):

    with self.output_file_path.open('a') as f:
      for node in nodes:
        f.write(f"{node[0]} {node[1]} {node[2]}\n")

  def write41_element_header_end(self):
    with self.output_file_path.open('a') as f:
      f.write('$EndElements\n')

  def write41_elements(self,elem_dim,elem_nodes_index):
     with self.output_file_path.open('a') as f:
      index = 1
      for element in elem_nodes_index:
        elem_str = ""
        for i in range(elem_dim):
          elem_str += " "+str(element[i])
        elem_str = str(index) + elem_str + "\n"
        f.write(elem_str)
        index += 1

  @abstractmethod
  def write41_entity_header(self):
    pass

  @abstractmethod
  def write41_node_header(self):
    pass

  @abstractmethod
  def write41_element_header(self):
    pass



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

  def get_boundary_entities_for_volumes(self,entities):
    e_volumes = self.get_volume_entities(entities)
    e_surface = []

    for e_v in e_volumes:
      e_surface += gmsh.model.getBoundary([e_v])
    return e_surface

  def is_there_a_shared_surface(self,entities):
    e_surface = self.get_boundary_entities_for_volumes(entities)
    surface = []
    for e in e_surface:
      # shared surface will be repeated but one will have opposite sign
      surface.append(abs(e[1]))

    occ = self.get_maximum_occurrence(surface)
    print(f"is_there_a_shared_surface::occ::{occ}")
    if occ>1:
       return True

    return False

  def get_entity_nodes(self,entity):
    #TODO rewrite this using elements nodes_indexes
    #given elements nodes_indexes for entity return nodes
    pass

  def get_entity_elements(self,entity):
    elem_data = gmsh.model.mesh.getElements(entity[0],entity[1])
    elem_dim,element_index,elem_nodes_index = elem_data
    dim = elem_dim[0]
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


    self.process()

  def process(self):
    entities = self.get_all_entities()

    if self.is_disjoint(entities):
      self.process_disjoint_object(entities)
    else:
      self.process_joint_object(entities)

  def process_joint_object(self,entities):
    # volume entities
    v_entities = self.get_volume_entities(entities)
    print(f"process_joint_object::v_entities::{v_entities}")
    # creating a single volume entity
    combined_elem_indexes = []
    combined_elem_nodes_index = []
    elem_dim = None
    for v_entity in v_entities:
      v_elements_data = self.get_entity_elements(v_entity)
      elem_dim,elem_index,elem_nodes_index = v_elements_data


      combined_elem_indexes += elem_index
      combined_elem_nodes_index.append(elem_nodes_index)

    v_nodes_data = self.get_nodes()
    node_indexes,nodes = v_nodes_data
    elements = self.combine(combined_elem_nodes_index)

    min_max = self.get_max_xyz(nodes)
    num_nodes = len(node_indexes)
    num_elems = len(elements)

    self.write41_mesh_format_41()
    self.write41_entity_header(min_max)
    self.write41_node_header(num_nodes)
    self.write41_nodes_indices(num_nodes)
    self.write41_nodes(nodes)
    self.write41_nodes_header_end()
    self.write41_element_header(num_elems)
    self.write41_elements(elem_dim,elements)
    self.write41_element_header_end()

  def process_disjoint_object(self,entities):
    print("process_disjoint_object::called")
    v_entities = self.get_volume_entities(entities)
    for i,v_entity in enumerate(v_entities):
      v_nodes_data = self.get_nodes()
      node_indexes,nodes = v_nodes_data

      v_elements_data = self.get_entity_elements(v_entity)
      elem_dim,elem_index,elem_nodes_index = v_elements_data

      #change_file_name
      file_name = self.output_filename_without_extension + "_vol" + f"{i+1}.msh"
      if self.output_filename_without_extension == "/":
        self.output_file_path = pathlib.Path(file_name)
      else:
        self.output_file_path = pathlib.Path(self.output_filename_without_extension + file_name)


      min_max = self.get_max_xyz(nodes)
      num_nodes = len(node_indexes)
      num_elems = len(elem_nodes_index)

      self.write41_mesh_format_41()
      self.write41_entity_header(min_max)
      self.write41_node_header(num_nodes)
      self.write41_nodes_indices(num_nodes)
      self.write41_nodes(nodes)
      self.write41_nodes_header_end()
      self.write41_element_header(num_elems)
      self.write41_elements(elem_dim,elem_nodes_index)
      self.write41_element_header_end()


  def is_disjoint(self,entities):
    v_entities = self.get_volume_entities(entities)
    if len(v_entities)>1 and not self.is_there_a_shared_surface(entities):
      return True

    return False

  def write41_entity_header(self,min_max):
    with self.output_file_path.open('a') as f:
      f.write('$Entities\n')
      f.write('0 0 0 1\n')
      f.write('0 ' + str(min_max[0]) + ' ' + str(min_max[1]) + ' ' +
              str(min_max[2]) + ' ' + str(min_max[3]) + ' ' + str(min_max[4]) +
              ' ' + str(min_max[5]) + ' 0 0 \n')
      f.write('$EndEntities\n')

  def write41_node_header(self,num_nodes):
    with self.output_file_path.open('a') as f:
      f.write('$Nodes\n')
      f.write(f'1 {num_nodes} 1 {num_nodes}\n')
      f.write(f'3 0 0 {num_nodes}\n')

  def write41_element_header(self,num_elems):

    with self.output_file_path.open('a') as f:
      f.write('$Elements\n')
      f.write(f'1 {num_elems} 1 {num_elems}\n')
      f.write(f'3 0 4 {num_elems}\n')


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

    self.process()

  def process(self):
    entities = self.get_all_entities()

    if self.is_disjoint(entities):
      self.process_disjoint_object(entities)
    else:
      self.process_joint_object(entities)

  def process_joint_object(self,entities):
    # surfaces around the volume entities
    combined_elem_indexes = []
    combined_elem_nodes_index = []
    e_surfaces = self.get_boundary_entities_for_volumes(entities)
    print(f"get_surface_entities::{self.get_surface_entities(entities)}")

    print(f"e_surfaces_boundry::::{e_surfaces}")
    for e_surface in e_surfaces:

      elem_dim,elem_index,elem_nodes_index = self.get_entity_elements(e_surface)
      print(f"elem_dim::{elem_dim}::elem_index::{elem_index}::elem_nodes_index::{elem_nodes_index}")
      combined_elem_indexes += elem_index
      combined_elem_nodes_index.append(elem_nodes_index)

    v_nodes_data = self.get_nodes()
    node_indexes,nodes = v_nodes_data
    elements = self.combine(combined_elem_nodes_index)

    min_max = self.get_max_xyz(nodes)
    num_nodes = len(node_indexes)
    num_elems = len(elements)

    self.write41_mesh_format_41()
    self.write41_entity_header(min_max)
    self.write41_node_header(num_nodes)
    self.write41_nodes_indices(num_nodes)
    self.write41_nodes(nodes)
    self.write41_nodes_header_end()
    self.write41_element_header(num_elems)
    self.write41_elements(elem_dim,elements)
    self.write41_element_header_end()

  def process_disjoint_object(self,entities):
    print(f"process_disjoint_object::called")
    #volume entities
    e_volumes = self.get_volume_entities(entities)
    for i,e_v in enumerate(e_volumes):
      # surfaces around the volume entities
      combined_elem_indexes = []
      combined_elem_nodes_index = []
      e_surfaces = gmsh.model.getBoundary([e_v])

      print(f"e_v:::{e_v} :: e_surfaces_boundry::::{e_surfaces}")
      for e_surface in e_surfaces:

        elem_dim,elem_index,elem_nodes_index = self.get_entity_elements(e_surface)
        print(f"elem_dim::{elem_dim}::elem_index::{elem_index}::elem_nodes_index::{elem_nodes_index}")
        combined_elem_indexes += elem_index
        combined_elem_nodes_index.append(elem_nodes_index)

      #change_file_name
      file_name = self.output_filename_without_extension + "_surf" + f"{i+1}.msh"
      if self.output_filename_without_extension == "/":
        self.output_file_path = pathlib.Path(file_name)
      else:
        self.output_file_path = pathlib.Path(self.output_filename_without_extension + file_name)

      v_nodes_data = self.get_nodes()
      node_indexes,nodes = v_nodes_data
      elements = self.combine(combined_elem_nodes_index)

      min_max = self.get_max_xyz(nodes)
      num_nodes = len(node_indexes)
      num_elems = len(elements)

      self.write41_mesh_format_41()
      self.write41_entity_header(min_max)
      self.write41_node_header(num_nodes)
      self.write41_nodes_indices(num_nodes)
      self.write41_nodes(nodes)
      self.write41_nodes_header_end()
      self.write41_element_header(num_elems)
      self.write41_elements(elem_dim,elements)
      self.write41_element_header_end()


      nodes = None
      elements = None




  def is_disjoint(self,entities):
    v_entities = self.get_volume_entities(entities)
    if len(v_entities)>1 and not self.is_there_a_shared_surface(entities):
      return True

    return False

  def write41_entity_header(self,min_max):
    with open(self.output_file_path, 'a') as f:
      f.write('$Entities\n')
      f.write('0 0 1 0\n')
      f.write(
          '0 '
          + str(min_max[0])
          + ' '
          + str(min_max[1])
          + ' '
          + str(min_max[2])
          + ' '
          + str(min_max[3])
          + ' '
          + str(min_max[4])
          + ' '
          + str(min_max[5])
          + ' 0 0 \n'
      )
      f.write('$EndEntities\n')

  def write41_node_header(self,num_nodes):
    with self.output_file_path.open('a') as f:
      f.write('$Nodes\n')
      f.write(f'1 {num_nodes} 1 {num_nodes}\n')
      f.write(f'2 0 0 {num_nodes}\n')

  def write41_element_header(self,num_elems):
    with self.output_file_path.open('a') as f:
      f.write('$Elements\n')
      f.write(f'1 {num_elems} 1 {num_elems}\n')
      f.write(f'2 0 2 {num_elems}\n')



def main():

  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("-i", "--input", type=str, help="Path to the msh file produced by Gmsh App.")
  parser.add_argument("-o", "--output", type=str, help="Path to the output file.")
  args = parser.parse_args()

  # produce a file only containing volume
  # VolumeExtractor(args.input, args.output)

  # produce a file only containing surface
  SurfaceExtractor(args.input, args.output)

if __name__ == '__main__':
  # Initialize Gmsh
  gmsh.initialize()

  main()

  # Finalize Gmsh
  gmsh.finalize()
