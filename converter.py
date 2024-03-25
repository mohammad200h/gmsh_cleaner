import pygmsh
import meshio

def get_num_elements(mesh):
   # find tetra cells
    Elements = None
    for cellblock in mesh.cells:
      if cellblock.type == "tetra":
          Elements = cellblock.data
          return len(Elements)

def get_elements(mesh):
   # find tetra cells
    Elements = None
    for cellblock in mesh.cells:
      if cellblock.type == "tetra":
          Elements = cellblock.data
          return Elements

def get_num_points(mesh):
   points = mesh.points
   return len(points)

def get_max_xyz(mesh):
    points = mesh.points

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

def write41Mesh_format_41():
  with open('volume.msh', 'w') as f:
    f.write('$MeshFormat\n')
    f.write('4.1 0 8\n')
    f.write('$EndMeshFormat\n')

def write_entity_header(mesh):
  with open('volume.msh','a') as f:
    f.write('$Entities\n')
    f.write('0 0 0 1\n')
    f.write('0 ' + str(get_max_xyz(mesh)[0]) + ' ' + str(get_max_xyz(mesh)[1]) + ' ' + str(get_max_xyz(mesh)[2]) + ' ' + str(get_max_xyz(mesh)[3]) + ' ' + str(get_max_xyz(mesh)[4]) + ' ' + str(get_max_xyz(mesh)[5]) + ' 0 0 \n')
    f.write('$EndEntities\n')


def wirte41NodeHeader(mesh):
    num_nodes = get_num_points(mesh)
    with open('volume.msh','a') as f:
        f.write('$Nodes\n')
        f.write(f"1 {num_nodes} 1 {num_nodes}\n")
        f.write(f"3 0 0 {num_nodes}\n")
def write41NodesIndices(mesh):
   num_nodes = get_num_points(mesh)
   with open('volume.msh','a') as f:
      for i in range(num_nodes):
        f.write(f"{i+1}\n")
def write41Nodes(mesh):
   nodes = mesh.points
   with open('volume.msh','a') as f:
      for node in nodes:
        f.write(f"{node[0]} {node[1]} {node[2]}\n")

def write41NodesHeaderEnd(mesh):
   with open('volume.msh','a') as f:
    f.write('$EndNodes\n')


def write41ElementHeader(mesh):
   with open('volume.msh','a') as f:
    f.write('$Elements\n')
    f.write(f"1 {get_num_elements(mesh)} 1 {get_num_elements(mesh)}\n")
    f.write(f"3 0 4 {get_num_elements(mesh)}\n")


def wrtie41Elements(mesh):
   elements = get_elements(mesh)
   with open('volume.msh','a') as f:
      index = 1
      for element in elements:
        f.write(f"{index} {element[0]+1} {element[1]+1} {element[2]+1} {element[3]+1}\n")
        index += 1

def write41ElementHeaderEnd(mesh):
   with open('volume.msh','a') as f:
    f.write('$EndElements\n')


def main():
  mesh = meshio.read("hollow_cylinder_binary.msh")

  write41Mesh_format_41()
  write_entity_header(mesh)
  wirte41NodeHeader(mesh)
  write41NodesIndices(mesh)
  write41Nodes(mesh)
  write41NodesHeaderEnd(mesh)
  write41ElementHeader(mesh)
  wrtie41Elements(mesh)
  write41ElementHeaderEnd(mesh)


if __name__ == '__main__':
  main()