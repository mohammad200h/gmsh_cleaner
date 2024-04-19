# Copyright 2023 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for gmsh_cleaner.py."""

from absl.testing import absltest
import gmsh
import mujoco
from gmsh_cleaner import (VolumeExtractor,
                          SurfaceExtractor,
                          _get_all_entities
                         )
import numpy as np
import os

class VolumeExtractorTest(absltest.TestCase):

  def test_volume_is_in_file_fail(self) -> None:

    input_path = "surface.msh"
    output_path = "surface_out.msh"
    version = "4.1"

    with self.assertRaisesWithLiteralMatch(
        ValueError, "No volume entities found."
    ):
      gmsh.initialize()
      VolumeExtractor(input_path, output_path, version).process()
      gmsh.finalize()

  def test_generates_correct_number_of_files_for_volume(self) -> None:
    input_path = "two_disjoint_composite_objects.msh"
    output_path = "two_disjoint_composite_objects_out.msh"
    version = "4.1"

    gmsh.initialize()
    VolumeExtractor(input_path, output_path, version).process()
    gmsh.finalize()


    file_count = 0
    files = os.listdir(".")
    for file in files:
        if "two_disjoint_composite_objects_out_vol" in file:
          file_count +=1
    
    self.assertTrue(file_count==2)

  def test_there_is_only_volume_in_generated_file(self) -> None:
    input_path = "two_disjoint_composite_objects.msh"
    output_path = "two_disjoint_composite_objects_out.msh"
    version = "4.1"

    gmsh.initialize()

    VolumeExtractor(input_path, output_path, version).process()


    # Reading generated files.
    for i in range(2):
      file_to_read = "two_disjoint_composite_objects_out_vol"+str(i+1)+".msh"
      gmsh.open(file_to_read)
      entities = _get_all_entities()
      for e in entities:
        self.assertTrue(e[0]==3)
    
    gmsh.finalize()

  def test_there_is_a_single_volume_in_generated_file(self) -> None:
    input_path = "two_disjoint_composite_objects.msh"
    output_path = "two_disjoint_composite_objects_out.msh"
    version = "4.1"

    gmsh.initialize()

    VolumeExtractor(input_path, output_path, version).process()


    # Reading generated files.
    for i in range(2):
      file_to_read = "two_disjoint_composite_objects_out_vol"+str(i+1)+".msh"
      gmsh.open(file_to_read)
      entities = _get_all_entities()
      for e in entities:
        self.assertTrue(e[1]==1)
    
    gmsh.finalize()

  def test_files_can_be_loaded_in_mujoco(self)-> None:
    nflexvert = [363,251]
    nflexelem = [1123,750]
    for i in range(2):
      file_to_read = "two_disjoint_composite_objects_out_vol"+str(i+1)

      XML = (
              "<mujoco>"
              "  <worldbody>"
             f"    <flexcomp name='{file_to_read}' type='gmsh' dim='3' file='{file_to_read}.msh'>"
              "    <edge equality='true'/>"
              "    </flexcomp>"
              "  </worldbody>"
              "</mujoco>"

      )
      model = mujoco.MjModel.from_xml_string(XML) 
      data = mujoco.MjData(model)

      self.assertTrue(model.nflexvert, nflexvert[i])
      self.assertTrue(model.nflexelem, nflexelem[i])
      mujoco.mj_step(model, data)

class SurfaceExtractorTest(absltest.TestCase):
  def test_surface_is_in_file_fail(self) -> None:
    input_path = "surface.msh"
    output_path = "surface_out.msh"
    version = "4.1"

    with self.assertRaisesWithLiteralMatch(
        ValueError, "No volume entities found."
    ):
      gmsh.initialize()
      SurfaceExtractor(input_path, output_path, version).process()
      gmsh.finalize()

  def test_generates_correct_number_of_files_for_surface(self) -> None:
    input_path = "two_disjoint_composite_objects.msh"
    output_path = "two_disjoint_composite_objects_out.msh"
    version = "4.1"

    gmsh.initialize()
    SurfaceExtractor(input_path, output_path, version).process()
    gmsh.finalize()

    file_count = 0
    files = os.listdir(".")
    for file in files:
        print(f"surf::file::{file}")
        if "two_disjoint_composite_objects_out_surf" in file:
          file_count +=1
    
    self.assertTrue(file_count==4)
  
  def test_there_is_only_surface_in_generated_file(self) -> None:
    input_path = "two_disjoint_composite_objects.msh"
    output_path = "two_disjoint_composite_objects_out.msh"
    version = "4.1"

    gmsh.initialize()

    SurfaceExtractor(input_path, output_path, version).process()

    # Reading generated files.
    for i in range(2):
      file_to_read = "two_disjoint_composite_objects_out_surf"+str(i+1)+".msh"
      gmsh.open(file_to_read)
      entities = _get_all_entities()
      for e in entities:
        self.assertTrue(e[0]==2)

  def test_there_is_a_single_surface_in_generated_file(self) -> None:
    input_path = "two_disjoint_composite_objects.msh"
    output_path = "two_disjoint_composite_objects_out.msh"
    version = "4.1"

    gmsh.initialize()

    SurfaceExtractor(input_path, output_path, version).process()
    
    # Reading generated files.
    for i in range(2):
      file_to_read = "two_disjoint_composite_objects_out_surf"+str(i+1)+".msh"
      gmsh.open(file_to_read)
      entities = _get_all_entities()
      for e in entities:
        self.assertTrue(e[1]==1)
  
  def test_files_can_be_loaded_in_mujoco_msh(self)-> None:
    nflexvert = [308,218]
    nflexelem = [612,432]
    for i in range(2):
      file_to_read = "two_disjoint_composite_objects_out_surf"+str(i+1)

      XML = (
              "<mujoco>"
              "  <worldbody>"
             f"    <flexcomp name='{file_to_read}' type='gmsh' dim='2' file='{file_to_read}.msh'>"
              "    <edge equality='true'/>"
              "    </flexcomp>"
              "  </worldbody>"
              "</mujoco>"

      )
      model = mujoco.MjModel.from_xml_string(XML) 
      data = mujoco.MjData(model)

      self.assertTrue(model.nflexvert, nflexvert[i])
      self.assertTrue(model.nflexelem, nflexelem[i])
      mujoco.mj_step(model, data)

  def test_files_can_be_loaded_in_mujoco_obj(self)-> None:
    nflexvert = [308,218]
    nflexelem = [612,432]
    for i in range(2):
      file_to_read = "two_disjoint_composite_objects_out_surf"+str(i+1)

      XML = (
              "<mujoco>"
              "  <worldbody>"
             f"    <flexcomp name='{file_to_read}'  type='mesh'  dim='2' file='{file_to_read}.obj'>"
              "    <edge equality='true'/>"
              "    </flexcomp>"
              "  </worldbody>"
              "</mujoco>"

      )
      model = mujoco.MjModel.from_xml_string(XML) 
      data = mujoco.MjData(model)

      self.assertTrue(model.nflexvert, nflexvert[i])
      self.assertTrue(model.nflexelem, nflexelem[i])
      mujoco.mj_step(model, data)

if __name__ == "__main__":
  absltest.main()
