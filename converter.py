import meshio

class BaseExtractor(object):
  def __init__(self,mesh,path=""):
    self.mesh = mesh
    self.output_file_path = None

  def process(self):
    self.write41_mesh_format_41()
    self.write41_entity_header()
    self.write41_node_header()
    self.write41_nodes_indices()
    self.write41_nodes()
    self.write41_nodes_header_end()
    self.write41_element_header()
    self.write41_elements()
    self.write41_element_header_end()

  ####utility functions####
  def get_num_points(self):
    points = self.mesh.points
    return len(points)

  def get_max_xyz(self):
    points = self.mesh.points

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

  ####main functions####
  def write41_mesh_format_41(self):
    with open(self.output_file_path, 'w') as f:
      f.write('$MeshFormat\n')
      f.write('4.1 0 8\n')
      f.write('$EndMeshFormat\n')

  def write41_nodes_header_end(self):
    with open(self.output_file_path,'a') as f:
     f.write('$EndNodes\n')

  def write41_nodes_indices(self):
    num_nodes = self.get_num_points()
    with open(self.output_file_path,'a') as f:
       for i in range(num_nodes):
         f.write(f"{i+1}\n")

  def write41_nodes(self):
    nodes = self.mesh.points
    with open(self.output_file_path,'a') as f:
       for node in nodes:
         f.write(f"{node[0]} {node[1]} {node[2]}\n")

  def write41_element_header_end(self):
     with open(self.output_file_path,'a') as f:
      f.write('$EndElements\n')

  #######abstract functions######
  def write41_entity_header(self):
    raise NotImplementedError("Please Implement write41_entity_header")

  def write41_node_header(self):
    raise NotImplementedError("Please Implement write41_node_header")

  def write41_element_header(self):
    raise NotImplementedError("Please Implement write41_element_header")

  def write41_elements(self):
    raise NotImplementedError("Please Implement write41_elements")

class ModelInformation:
  def __init__(self):
    # TODO : print information about model
    pass

class VolumeExtractor(BaseExtractor):
  """
  Takes a file with multiple entities and removes all but volume.
  Mujoco parser only support file with a single Entity
  """
  def __init__(self,mesh,path=""):
    self.mesh = mesh
    self.output_file_path = path+"_volume.msh"

    self.process()


  ####utility functions####
  def get_num_elements(self):
    Elements = None
    for cellblock in self.mesh.cells:
      if cellblock.type == "tetra":
          Elements = cellblock.data
          return len(Elements)
    raise ValueError("There are no elements")

  def get_elements(self):
    Elements = None
    for cellblock in self.mesh.cells:
      if cellblock.type == "tetra":
          Elements = cellblock.data
          return Elements
    raise ValueError("Could not find elements representing a Volume.")

  ####main functions####
  def write41_entity_header(self):
    min_max = self.get_max_xyz()
    with open(self.output_file_path,'a') as f:
      f.write('$Entities\n')
      f.write('0 0 0 1\n')
      f.write('0 ' + str(min_max[0]) + ' ' + str(min_max[1]) + ' ' + str(min_max[2]) + ' ' + str(min_max[3]) + ' ' + str(min_max[4]) + ' ' + str(min_max[5]) + ' 0 0 \n')
      f.write('$EndEntities\n')

  def write41_node_header(self):
    num_nodes = self.get_num_points()
    with open(self.output_file_path,'a') as f:
        f.write('$Nodes\n')
        f.write(f"1 {num_nodes} 1 {num_nodes}\n")
        f.write(f"3 0 0 {num_nodes}\n")



  def write41_element_header(self):
    num_elems = self.get_num_elements()
    with open(self.output_file_path,'a') as f:
     f.write('$Elements\n')
     f.write(f"1 {num_elems} 1 {num_elems}\n")
     f.write(f"3 0 4 {num_elems}\n")

  def write41_elements(self):
     elements = self.get_elements()
     with open(self.output_file_path,'a') as f:
        index = 1
        for element in elements:
          f.write(f"{index} {element[0]+1} {element[1]+1} {element[2]+1} {element[3]+1}\n")
          index += 1

class SurfaceExtractor(BaseExtractor):
  def __init__(self,mesh,path=""):
    self.mesh = mesh
    self.output_file_path = path+"_surface.msh"

    self.process()

  ####utility functions####
  def get_num_elements(self):
    Elements = None
    for cellblock in self.mesh.cells:
      if cellblock.type == "triangle":
          Elements = cellblock.data
          return len(Elements)
    raise ValueError("There are no elements")

  def get_elements(self):
    Elements = None
    for cellblock in self.mesh.cells:
      if cellblock.type == "triangle":
          Elements = cellblock.data
          return Elements
    raise ValueError("Could not find elements representing a surface.")

  def write41_entity_header(self):
    min_max = self.get_max_xyz()
    with open(self.output_file_path,'a') as f:
      f.write('$Entities\n')
      f.write('0 0 1 0\n')
      f.write('0 ' + str(min_max[0]) + ' ' + str(min_max[1]) + ' ' + str(min_max[2]) + ' ' + str(min_max[3]) + ' ' + str(min_max[4]) + ' ' + str(min_max[5]) + ' 0 0 \n')
      f.write('$EndEntities\n')

  def write41_node_header(self):
    num_nodes = self.get_num_points()
    with open(self.output_file_path,'a') as f:
        f.write('$Nodes\n')
        f.write(f"1 {num_nodes} 1 {num_nodes}\n")
        f.write(f"2 0 0 {num_nodes}\n")

  def write41_element_header(self):
    num_elems = self.get_num_elements()
    with open(self.output_file_path,'a') as f:
     f.write('$Elements\n')
     f.write(f"1 {num_elems} 1 {num_elems}\n")
     f.write(f"2 0 2 {num_elems}\n")

  def write41_elements(self):
     elements = self.get_elements()
     with open(self.output_file_path,'a') as f:
        index = 1
        for element in elements:
          f.write(f"{index} {element[0]+1} {element[1]+1} {element[2]+1}\n")
          index += 1

def main():
  #TODO: add arg parser input output


  mesh = meshio.read("hollow_cylinder_binary.msh")

  # produce a file only containing volume
  VolumeExtractor(mesh)

  # produce a file only containing surface
  SurfaceExtractor(mesh)

if __name__ == '__main__':
  main()