
from collections import Counter
import gmsh
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt



def get_all_entities():
  return gmsh.model.getEntities()

def get_volume_entities(entities):
  e_volume = []
  for e in entities:
    if e[0]==3:
      e_volume.append(e)
  return e_volume

def get_maximum_occurrence(surfaces_index):
    # https://www.geeksforgeeks.org/python-count-occurrences-element-list/
    d = Counter(surfaces_index)
    max_occurrence = 0
    for s in surfaces_index:
      occ = d[s]
      if occ>max_occurrence:
        max_occurrence = occ

    return max_occurrence

def get_boundary_entities_for_volumes(entities):
  e_surface = []
  for e in entities:
    e_surface += gmsh.model.getBoundary([e])
  return e_surface

def is_there_a_shared_surface(e1,e2):
  entities = [e1,e2]
  e_surface = get_boundary_entities_for_volumes(entities)
  surface = []
  for e in e_surface:
    # shared surface will be repeated but one will have opposite sign
    surface.append(abs(e[1]))
  occ = get_maximum_occurrence(surface)

  if occ>1:
     return True
  return False

def create_adjacency_matrix(volume_entities):
  num_vol = len(volume_entities)
  adjacency_matrix = np.zeros((num_vol,num_vol))
  for i,v_e_one in enumerate(volume_entities):
    for j,v_e_two in enumerate(volume_entities):
      if i!=j:
        adjacency_matrix[i,j] = 1 if is_there_a_shared_surface(v_e_one,v_e_two) else 0
  return adjacency_matrix,volume_entities
      
def create_graph_from_adjacency_matrix(adjacency_matrix):
  # Create a graph from the adjacency matrix
  G = nx.from_numpy_array(adjacency_matrix)

  return G

def get_objects_id(G):
  objects_id =[] 
  graphs = list(nx.connected_components(G))

  for g in graphs:
    obj = [i+1 for i in g]
    objects_id.append(obj)
  num_objs = len(objects_id)

  return num_objs,objects_id

  
def main():
  input_path = "sophisticated.msh"
  gmsh.open(input_path)

  entities   = get_all_entities()
  v_entities = get_volume_entities(entities)

  print(f"v_entities::{v_entities}")

  adjacency_matrix,_ = create_adjacency_matrix(v_entities)
  print("adjacency_matrix:: ",adjacency_matrix)
  G = create_graph_from_adjacency_matrix(adjacency_matrix)

  num_objs,objects_id = get_objects_id(G)
  print(f"num_objs::{num_objs}")
  print(f"objects_id::{objects_id}")


  # You can also visualize the graph
  nx.draw(G, with_labels=True)
  plt.show()

if __name__ == "__main__":
  # Initialize Gmsh
  gmsh.initialize()

  main()

  # Finalize Gmsh
  gmsh.finalize()




  