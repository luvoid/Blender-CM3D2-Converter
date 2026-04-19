import bpy
from pathlib import Path

import cm3d2converter
from .blenderunittest import BlenderTestCase



class ModelTest(BlenderTestCase):
    # override
    @property
    def blend_file_path(self) -> str:
        return str(Path(self.resources_dir) / 'body001_standard.blend')

    def assertMeshEqual(self, mesh1: bpy.types.Mesh, mesh2: bpy.types.Mesh, msg=None):
        msg = f" : {msg}" if not msg is None else ""

        self.assertEqual(len(mesh1.vertices), len(mesh2.vertices), "len(vertices) not equal" + msg)
        for i, (vert1, vert2) in enumerate(zip(mesh1.vertices, mesh2.vertices)):
            vert1: bpy.types.MeshVertex
            vert2: bpy.types.MeshVertex
            self.assertEqual(vert1.co, vert2.co, f"vertices[{i}].co not equal" + msg)
            self.assertEqual(len(vert1.groups), len(vert2.groups),
                             f"len(vertices[{i}].groups) not equal" + msg)
            for j, (group1, group2) in enumerate(zip(vert1.groups, vert2.groups)):
                group1: bpy.types.VertexGroupElement
                group2: bpy.types.VertexGroupElement
                self.assertEqual(group1.group, group2.group,
                                 f"vertices[{i}].groups[{j}].group not equal" + msg)
                self.assertEqual(group1.weight, group2.weight,
                                 f"vertices[{i}].groups[{j}].weight not equal" + msg)

        self.assertEqual(len(mesh1.loops), len(mesh2.loops), "len(loops) not equal" + msg)
        mesh1.calc_normals_split()
        mesh2.calc_normals_split()
        for i, (loop1, loop2) in enumerate(zip(mesh1.loops, mesh2.loops)):
            loop1: bpy.types.MeshLoop
            loop2: bpy.types.MeshLoop
            self.assertEqual(loop1.vertex_index, loop2.vertex_index,
                             msg=f"loops[{i}].vertex_index not equal" + msg)
            self.assertVectorAlmostEqual(loop1.normal, loop2.normal, atol=5e-4,
                                         msg=f"loops[{i}].normal not equal" + msg)

        self.assertEqual(len(mesh1.shape_keys.key_blocks), len(mesh2.shape_keys.key_blocks),
                         "len(shape_keys.key_blocks) not equal" + msg)
        for i, (shape_key1, shape_key2) in enumerate(zip(mesh1.shape_keys.key_blocks, mesh2.shape_keys.key_blocks)):
            shape_key1: bpy.types.ShapeKey
            shape_key2: bpy.types.ShapeKey
            self.assertEqual(shape_key1.name, shape_key2.name,
                             f"shape_keys.key_blocks[{i}].name not equal" + msg)
            for j, (data1, data2) in enumerate(zip(shape_key1.data, shape_key2.data)):
                data1: bpy.types.ShapeKeyPoint
                data2: bpy.types.ShapeKeyPoint
                self.assertVectorAlmostEqual(
                    data1.co, data2.co, rtol=2e-4,  # XXX `rtol=2e-4` is higher than I would like it to be
                    msg=f"shape_keys.key_blocks[\"{shape_key1.name}\"].data[{j}].co not equal" + msg
                )

        self.assertEqual(len(mesh1.vertex_colors), len(mesh2.vertex_colors),
                         "len(vertex_colors) not equal" + msg)
        for i, (colors1, colors2) in enumerate(zip(mesh1.vertex_colors, mesh2.vertex_colors)):
            colors1: bpy.types.MeshLoopColorLayer
            colors2: bpy.types.MeshLoopColorLayer
            self.assertEqual(colors1.name, colors2.name, f"vertex_colors[{i}].name not equal" + msg)
            for j, (color1, color2) in enumerate(zip(colors1.data, colors2.data)):
                color1: bpy.types.MeshLoopColor
                color2: bpy.types.MeshLoopColor
                self.assertEqual(color1.color, color2.color,
                                 f"vertex_colors[\"{colors1.name}\"].data[{j}].color not equal" + msg)

    def assertArmatureEqual(self, armature1: bpy.types.Armature, armature2: bpy.types.Armature, msg=None):
        msg = f" : {msg}" if not msg is None else ""

        self.assertEqual(len(armature1.bones), len(armature2.bones), "len(bones) not equal" + msg)
        for i, (bone1, bone2) in enumerate(zip(armature1.bones, armature2.bones)):
            bone1: bpy.types.Bone
            bone2: bpy.types.Bone
            self.assertEqual(bone1.name, bone2.name, f"bones[{i}].name not equal" + msg)
            self.assertEqual(bone1.head, bone2.head,
                             f"bones[\"{bone1.name}\"].head not equal" + msg)
            self.assertEqual(bone1.tail, bone2.tail,
                             f"bones[\"{bone1.name}\"].tail not equal" + msg)
            self.assertEqual(bone1.matrix, bone2.matrix,
                             f"bones[\"{bone1.name}\"].matrix not equal" + msg)
            parent1 = bone1.parent and bone1.parent.name
            parent2 = bone2.parent and bone2.parent.name
            self.assertEqual(parent1, parent2, f"bones[\"{bone1.name}\"].parent not equal" + msg)

    def test_model_import(self):
        bpy.ops.import_mesh.import_cm3d2_model(filepath=f'{self.resources_dir}/body001.model')

        standard_armature_object = bpy.data.objects.get('body001_standard.armature')
        standard_mesh_object = bpy.data.objects.get('body001_standard')

        imported_armature_object = bpy.data.objects.get('body001.armature')
        imported_mesh_object = bpy.data.objects.get('body001')

        self.assertMeshEqual(standard_mesh_object.data, imported_mesh_object.data)
        self.assertArmatureEqual(standard_armature_object.data, imported_armature_object.data)
        for material_slot1, material_slot2 in zip(standard_mesh_object.material_slots,
                                                  imported_mesh_object.material_slots):
            material_slot1: bpy.types.MaterialSlot
            material_slot2: bpy.types.MaterialSlot
            self.assertEqual(material_slot1.name, material_slot2.name.removesuffix(".001"))

    def test_model_export(self):
        bpy.ops.import_mesh.import_cm3d2_model(filepath=f'{self.resources_dir}/body001.model')

        body001_mesh_object: bpy.types.Object = bpy.data.objects.get('body001')
        self.activate_object(body001_mesh_object)

        bpy.ops.export_mesh.export_cm3d2_model(
            filepath=f'{self.output_dir}/{self._testMethodName}.model')

    def test_model_recursive(self):
        bpy.ops.import_mesh.import_cm3d2_model(filepath=f'{self.resources_dir}/body001.model')

        in_file = f'{self.resources_dir}/body001.model'
        out_file_0 = f'{self.output_dir}/{self._testMethodName}_0.model'
        out_file_1 = f'{self.output_dir}/{self._testMethodName}_1.model'
        out_file_2 = f'{self.output_dir}/{self._testMethodName}_2.model'

        bpy.ops.import_mesh.import_cm3d2_model(filepath=in_file)
        bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file_0)
        bpy.ops.import_mesh.import_cm3d2_model(filepath=out_file_0)
        repeats = 10
        for _ in range(repeats):
            bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file_1)
            bpy.ops.import_mesh.import_cm3d2_model(filepath=out_file_1)
        bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file_2)

        with open(in_file, 'rb') as reader:
            expected_data = reader.read()
        with open(out_file_0, 'rb') as reader:
            actual_data_0 = reader.read()
        with open(out_file_1, 'rb') as reader:
            actual_data_1 = reader.read()
        with open(out_file_2, 'rb') as reader:
            actual_data_2 = reader.read()
        print(len(expected_data))
        print(len(actual_data_0))
        print(len(actual_data_1))
        print(len(actual_data_2))

        # Check the loss
        first_mesh = bpy.data.meshes.get('body001')
        last_mesh = bpy.data.meshes.get(f'body001.{repeats+2:03}')
        self.assertMeshEqual(first_mesh, last_mesh)

        first_armature = bpy.data.armatures.get('body001.armature')
        last_armature = bpy.data.armatures.get(f'body001.armature.{repeats+2:03}')
        self.assertArmatureEqual(first_armature, last_armature)

    def test_normalize_weights(self):
        mesh_object = bpy.data.objects.get('body001_standard')
        self.activate_object(mesh_object)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.vertex_group_remove(all=True)
        bpy.ops.object.vertex_group_add()
        vertex_group = mesh_object.vertex_groups.new(name='Bip01')
        mesh_object.vertex_groups.active = vertex_group
        bpy.context.scene.tool_settings.vertex_group_weight = 0.5
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode='OBJECT')

        out_file_0 = f'{self.output_dir}/{self._testMethodName}_0.model'
        out_file_1 = f'{self.output_dir}/{self._testMethodName}_1.model'

        self.activate_object(mesh_object)
        bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file_0, is_normalize_weight=False)
        bpy.ops.import_mesh.import_cm3d2_model(filepath=out_file_0)
        halfweight_mesh_object = bpy.context.object
        self.assertEqual(0.5, halfweight_mesh_object.vertex_groups.active.weight(0),
                         "Weights were normalized when is_normalize_weight=False")

        self.activate_object(mesh_object)
        bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file_1, is_normalize_weight=True)
        bpy.ops.import_mesh.import_cm3d2_model(filepath=out_file_1)
        fullweight_mesh_object = bpy.context.object
        self.assertEqual(1, fullweight_mesh_object.vertex_groups.active.weight(0),
                         "Weights were not normalized when is_normalize_weight=True")


class Dress379Test(BlenderTestCase):
    def test_model_import_dress379(self):
        """Historically caused KeyError in model_import.write_vertex_colors caused by loose vertices."""
        in_file = f'{self.resources_dir}/Dress379_wear.model'
        bpy.ops.import_mesh.import_cm3d2_model(filepath=in_file)


class DuplicateMaterialsTest(BlenderTestCase):
    """Material slots can be lost / deleted when importing a model 
    containing materials with the same name"""
    
    def test_duplicate_materials_import(self):
        """Test that all materials are imported"""
        in_file = f'{self.resources_dir}/duplicate_materials.model'
        bpy.ops.import_mesh.import_cm3d2_model(filepath=in_file)
        
        # This model has exactly three materials
        self.assertEqual(len(bpy.context.object.material_slots), 3, 
                         "Not all materials were imported")
        
    def test_duplicate_materials_recursive(self):
        """Test that all materials are present after importing and exporting
        then importing again"""
        in_file = f'{self.resources_dir}/duplicate_materials.model'
        out_file = f'{self.output_dir}/{self._testMethodName}.model'
        
        bpy.ops.import_mesh.import_cm3d2_model(filepath=in_file)
        bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file)
        bpy.ops.import_mesh.import_cm3d2_model(filepath=out_file)
        
        # This model has exactly three materials
        self.assertEqual(len(bpy.context.object.material_slots), 3, 
                         "Not all materials were imported")
        
    def test_duplicate_material_names_preserved(self):
        """Test that the names of the materials are preserved after repeated
        import and exports"""
        in_file = f'{self.resources_dir}/duplicate_materials.model'
        out_file_0 = f'{self.output_dir}/{self._testMethodName}_0.model'
        out_file_1 = f'{self.output_dir}/{self._testMethodName}_1.model'
        
        bpy.ops.import_mesh.import_cm3d2_model(filepath=in_file)
        for ms in bpy.context.object.material_slots.values():
            ms: bpy.types.MaterialSlot
            ms.material = bpy.data.materials['cube_material']
        expected_names = [cm3d2converter.common.remove_serial_number(k) 
                          for k in bpy.context.object.material_slots.keys()]
        
        bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file_0)
        bpy.ops.import_mesh.import_cm3d2_model(filepath=out_file_0)
        imported_names = [cm3d2converter.common.remove_serial_number(k) 
                          for k in bpy.context.object.material_slots.keys()]
        self.assertListEqual(expected_names, imported_names,
                             "Material names were changed after first export / import")
            
        bpy.ops.export_mesh.export_cm3d2_model(filepath=out_file_1)
        bpy.ops.import_mesh.import_cm3d2_model(filepath=out_file_1)
        imported_names = [cm3d2converter.common.remove_serial_number(k) 
                          for k in bpy.context.object.material_slots.keys()]
        self.assertListEqual(expected_names, imported_names,
                             "Material names were changed after first export / import")
        print(imported_names)
        
        
        
        
