import os
import math
import struct
import time
import traceback
import bpy
import bpy_extras
import bmesh
import mathutils
from collections import Counter
from . import common
from . import compat
from . import cm3d2_data
from .translations.pgettext_functions import *
from .misc_OBJECT_PT_transform import CNV_OT_align_to_cm3d2_base_bone


# メインオペレーター
@compat.BlRegister()
#@bpy_extras.io_utils.orientation_helper(axis_forward='-Z', axis_up='Y')
class CNV_OT_import_cm3d2_model(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname = 'import_mesh.import_cm3d2_model'
    bl_label = "CM3D2 Model (.model)"
    bl_description = "Imports a model from the game CM3D2"
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".model"
    filter_glob = bpy.props.StringProperty(default="*.model", options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name="Scale", default=5, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="The amount by which the mesh is scaled when imported. Recommended that you use the same when at the time of export.")

    is_mesh = bpy.props.BoolProperty(name="Load Mesh", default=True, description="Leaving this on will load in the mesh.")
    is_remove_doubles = bpy.props.BoolProperty(name="Remove Doubles", default=True, description="Doubles will be removed in both the uv and the mesh at the time of import.")
    is_seam  = bpy.props.BoolProperty(name="Mark Seams", default=True, description="This will mark the UV seams on your mesh.")
    is_sharp = bpy.props.BoolProperty(name="Mark Sharp", default=True, description="This will mark removed doubles on your mesh as sharp (or all free edges if not removing doubles).")

    is_convert_bone_weight_names = bpy.props.BoolProperty(name="Convert Bone Weight Names to Blender", default=False, description="This will convert bone and vertex group names for use with blender mirroring.")
    is_vertex_group_sort = bpy.props.BoolProperty(name="Sort Vertex Groups", default=True, description="This will sort your vertex groups so they are easier to work with.")
    is_remove_empty_vertex_group = bpy.props.BoolProperty(name="Remove Empty Vertex Groups", default=True, description="Will remove any empty vertex groups to which no vertices are assigned to it.")

    reload_tex_cache = bpy.props.BoolProperty(name="Reconstruct texture cache", default=False, description="Reconfigure cache when looking for tex files")
    is_decorate = bpy.props.BoolProperty(name="Decorate Material", default=True)
    is_mate_data_text = bpy.props.BoolProperty(name="Export Mate Data to text editor.", default=True, description="Material information will be placed into the text editor.")

    is_armature = bpy.props.BoolProperty(name="Load Armature", default=True, description="Loads in the armature that comes with the model.")
    is_armature_clean = bpy.props.BoolProperty(name="Clean Armature", default=False, description="Will delete any unneeded bones.")
    is_custom_bones = bpy.props.BoolProperty(name="Use Custom Bones", default=False, description="Use the currently selected object for custom bone shapes.")
    is_use_local_bones = bpy.props.BoolProperty(name="Use Local Bones", default=True, description="Use the Local Bone Data for orientation (more accurate)")

    is_bone_data_text = bpy.props.BoolProperty(name="Text", default=True, description="Read Bone data from the text")
    is_bone_data_obj_property = bpy.props.BoolProperty(name="Object Property", default=True, description="Will retrieve the bonedata from the object's properties")
    is_bone_data_arm_property = bpy.props.BoolProperty(name="Armature Properties", default=True, description="Will retrieve the bonedata from the armature's properties")
    texpath_dict = None

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        prefs = common.preferences()
        if prefs.model_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.model_default_path, None, "model")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.model_import_path, None, "model")
        self.scale = prefs.scale
        self.is_convert_bone_weight_names = prefs.is_convert_bone_weight_names
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        prefs = common.preferences()
        self.layout.prop(self, 'scale')

        box = self.layout.box()
        box.prop(self, 'is_mesh', icon='MESH_DATA')

        sub_box = box.box()
        sub_box.enabled = self.is_mesh
        sub_box.label(text="Mesh")
        sub_box.prop(self, 'is_remove_doubles', icon='STICKY_UVS_VERT')
        sub_box.prop(self, 'is_seam' , icon='KEY_DEHLT')
        sub_box.prop(self, 'is_sharp', icon='KEY_DEHLT')

        sub_box = box.box()
        sub_box.enabled = self.is_mesh
        sub_box.label(text="Vertex Group")
        sub_box.prop(self, 'is_vertex_group_sort', icon='SORTALPHA')
        sub_box.prop(self, 'is_remove_empty_vertex_group', icon='DISCLOSURE_TRI_DOWN')
        sub_box.prop(self, 'is_convert_bone_weight_names', icon='BLENDER')

        sub_box = box.box()
        sub_box.enabled = self.is_mesh
        sub_box.label(text="Material")
        sub_box.prop(prefs, 'is_replace_cm3d2_tex', icon='BORDERMOVE')
        sub_box.prop(self, 'reload_tex_cache', icon='FILE_REFRESH')
        if compat.IS_LEGACY:
            sub_box.prop(self, 'is_decorate', icon=compat.icon('SHADING_TEXTURE'))
        sub_box.prop(self, 'is_mate_data_text', icon='TEXT')

        box = self.layout.box()
        box.prop(self, 'is_armature', icon='ARMATURE_DATA')
        
        sub_box = box.box()
        sub_box.enabled = self.is_armature
        sub_box.label(text="Armature")
        sub_box.prop(self , 'is_use_local_bones'          , icon=compat.icon('GROUP_BONE'), text="Use Local Bone Data"            )
        sub_box.prop(self , 'is_armature_clean'           , icon=compat.icon('X'         )                                        )
        sub_box.prop(self , 'is_convert_bone_weight_names', icon=compat.icon('BLENDER'   ), text="Convert Bone Names for Blender.")
        sub_box.prop(prefs, 'show_bone_in_front'          , icon=compat.icon('HIDE_OFF'  ), text="Show Bones in Front"            )
        row = sub_box.row()
        row.prop    (self , 'is_custom_bones'             , icon=compat.icon('BONE_DATA' ), text="Use Selected as Bone Shape"     )
        row.enabled = bool(context.object)
        
        box = self.layout.box()
        box.label(text="Bone Data Destination")
        box.prop(self, 'is_bone_data_text', icon='TEXT')
        box.prop(self, 'is_bone_data_obj_property', icon='OBJECT_DATA')
        box.prop(self, 'is_bone_data_arm_property', icon='ARMATURE_DATA')

    def execute(self, context):
        start_time = time.time()

        prefs = common.preferences()
        prefs.model_import_path = self.filepath
        prefs.scale = self.scale
        context.window_manager.progress_begin(0, 10)
        context.window_manager.progress_update(0)

        custom_bone_ob = context.active_object
        if not custom_bone_ob:
            self.is_custom_bones = False

        #global_matrix = bpy_extras.io_utils.axis_conversion(from_forward=self.axis_forward, from_up=self.axis_up).to_4x4()

        try:
            reader = open(self.filepath, 'rb')
        except:
            self.report(type={'ERROR'}, message=f_tip_("Failed to open the file. File does not exist or is inaccessible. file={}", self.filepath))
            return {'CANCELLED'}

        self.texpath_dict = common.get_texpath_dict(reload=self.reload_tex_cache)

        with reader:
            # ヘッダー
            ext = None
            try: # luvoid : utf-8 decoding could possibly throw an error here
                ext = common.read_str(reader)
            except:
                ext = False
            if ext != 'CM3D2_MESH':
                self.report(type={'ERROR'}, message="This is not a CM3D2 Model File.")
                return {'CANCELLED'}
            model_ver = struct.unpack('<i', reader.read(4))[0]
            self.report(type={'INFO'}, message=f_tip_("Model Version = {version}", version=model_ver))
            context.window_manager.progress_update(0.1)

            try:
                # 名前群を取得
                model_name1 = common.read_str(reader)
                model_name2 = common.read_str(reader)
                context.window_manager.progress_update(0.2)

                # ボーン情報読み込み
                bone_data = []
                bone_count = struct.unpack('<i', reader.read(4))[0]
                for i in range(bone_count):
                    name = common.read_str(reader)
                    unknown = struct.unpack('<B', reader.read(1))[0]
                    bone_data.append({'name': name, 'unknown': unknown})

                for i in range(bone_count):
                    parent_index = struct.unpack('<i', reader.read(4))[0]
                    parent_name = None
                    if parent_index != -1:
                        parent_name = bone_data[parent_index]['name']
                    bone_data[i]['parent_index'] = parent_index
                    bone_data[i]['parent_name'] = parent_name

                for i in range(bone_count):
                    x, y, z = struct.unpack('<3f', reader.read(3*4))
                    bone_data[i]['co'] = mathutils.Vector((x, y, z))

                    x, y, z = struct.unpack('<3f', reader.read(3*4))
                    w = struct.unpack('<f', reader.read(4))[0]
                    bone_data[i]['rot'] = mathutils.Quaternion((w, x, y, z))
                    if model_ver >= 2001:
                        use_scale = struct.unpack('<B', reader.read(1))[0]
                        if use_scale:
                            print(bone_data[i]['name'],"has scale data!")
                            scale_x, scale_y, scale_z = struct.unpack('<3f', reader.read(3*4))
                            bone_data[i]['scale'] = [scale_x, scale_y, scale_z]

                context.window_manager.progress_update(0.3)

                print(f_("Reading vertex, mesh, and local bone count at 0x{num:02X}", num=reader.tell()))
                vertex_count, mesh_count, local_bone_count = struct.unpack('<3i', reader.read(3*4))

                # ローカルボーン情報読み込み
                local_bone_data = []
                for i in range(local_bone_count):
                    local_bone_data.append({'name': common.read_str(reader)})

                for i in range(local_bone_count):
                    row0 = struct.unpack('<4f', reader.read(4 * 4))
                    row1 = struct.unpack('<4f', reader.read(4 * 4))
                    row2 = struct.unpack('<4f', reader.read(4 * 4))
                    row3 = struct.unpack('<4f', reader.read(4 * 4))
                    local_bone_data[i]['matrix'] = mathutils.Matrix([row0, row1, row2, row3])
                context.window_manager.progress_update(0.4)

                # 頂点情報読み込み
                vertex_data = []
                print(f_("Reading vertex data at 0x{num:02X}", num=reader.tell()))
                extra_uv_uses = [False] * 7
                if model_ver >= 2102: # CR Edit Mode
                    extra_uv_uses = struct.unpack('<7?', reader.read(7))
                    print(f_("extra_uv_uses = {boollist}", boollist=extra_uv_uses))
                for i in range(vertex_count):
                    co = struct.unpack('<3f', reader.read(3 * 4))
                    no = struct.unpack('<3f', reader.read(3 * 4))
                    uv = struct.unpack('<2f', reader.read(2 * 4))
                    extra_uvs = [] # CR Edit
                    for i, used in enumerate(extra_uv_uses):
                        if used:
                            extra_uvs.append(struct.unpack('<2f', reader.read(2 * 4)))
                    vertex_data.append({'co': co, 'normal': no, 'uv': uv, 'extra_uvs': extra_uvs})
                if self.is_remove_doubles:
                    comparison_data = list(hash(repr(v['co']) + " " + repr(v['normal'])) for v in vertex_data)
                    comparison_counter = Counter(comparison_data)
                    comparison_data = list((comparison_counter[h] > 1) for h in comparison_data)
                    del comparison_counter
                print(f_("Reading unknown count at 0x{num:02X}", num=reader.tell()))
                unknown_count = struct.unpack('<i', reader.read(4))[0]
                for i in range(unknown_count):
                    struct.unpack('<4f', reader.read(4 * 4))
                for i in range(vertex_count):
                    indexes = struct.unpack('<4H', reader.read(4 * 2))
                    values = struct.unpack('<4f', reader.read(4 * 4))
                    vertex_data[i]['weights'] = list({
                            'index': index,
                            'value': value,
                            'name': local_bone_data[index]['name'],
                        } for index, value in zip(indexes, values))
                context.window_manager.progress_update(0.5)
                # 面情報読み込み
                face_data = []
                for i in range(mesh_count):
                    face_count = int(struct.unpack('<i', reader.read(4))[0] / 3)
                    datum = [tuple(reversed(struct.unpack('<3H', reader.read(3 * 2)))) for j in range(face_count)]
                    face_data.append(datum)
                context.window_manager.progress_update(0.6)

                # マテリアル情報読み込み
                # TODO MaterialHandlerに変更
                material_data = []
                material_count = struct.unpack('<i', reader.read(4))[0]
                for i in range(material_count):
                    print(f_("mate count: {num} of {count} @ 0x{pos:02X}", num=i, count=material_count, pos=reader.tell()))
                    data = cm3d2_data.MaterialHandler.read(reader, read_header=False, version=model_ver)
                    data.name1 = data.name.lower()
                    material_data.append(data)
                    
                    # name1 = common.read_str(reader)
                    # name2 = common.read_str(reader)
                    # name3 = common.read_str(reader)
                    # data_list = []
                    # material_data.append({'name1': name1, 'name2': name2, 'name3': name3, 'data': data_list})
                    # while True:
                    #     data_type = common.read_str(reader)
                    #     if data_type == 'tex':
                    #         data_item = {'type': data_type}
                    #         data_list.append(data_item)
                    #         data_item['name'] = common.read_str(reader)
                    #         data_item['type2'] = common.read_str(reader)
                    #         if data_item['type2'] == 'tex2d':
                    #             data_item['name2'] = common.read_str(reader)
                    #             data_item['path'] = common.read_str(reader)
                    #             data_item['tex_map'] = struct.unpack('<4f', reader.read(4*4))
                    #     elif data_type == 'col':
                    #         name = common.read_str(reader)
                    #         col = struct.unpack('<4f', reader.read(4*4))
                    #         data_list.append({'type': data_type, 'name': name, 'color': col})
                    #     elif data_type == 'f':
                    #         name = common.read_str(reader)
                    #         fval = struct.unpack('<f', reader.read(4))[0]
                    #         data_list.append({'type': data_type, 'name': name, 'float': fval})
                    #     else:
                    #         break

                context.window_manager.progress_update(0.8)

                # その他情報読み込み
                misc_data = []
                while True:
                    #print(f_("Reading data_type at 0x{num:02X}", num=reader.tell()))
                    data_type = common.read_str(reader)
                    if data_type == 'morph':
                        misc_item = {'type': data_type}
                        misc_data.append(misc_item)
                        misc_item['name'] = common.read_str(reader)
                        misc_item['data'] = data_list = []
                        morph_vert_count = struct.unpack('<i', reader.read(4))[0]
                        morph_extra_uvs = False
                        if model_ver >= 2102: # CR Edit Mode
                            morph_extra_uvs = struct.unpack('<?', reader.read(1))[0]
                            misc_item['uvs'] = []
                            print(f_("{morph}.morph_extra_uvs @ 0x{pos:02X} = {bool}", morph=misc_item['name'], bool=morph_extra_uvs, pos=reader.tell()-1))
                        for i in range(morph_vert_count):
                            index = struct.unpack('<H', reader.read(2))[0]
                            co = mathutils.Vector(struct.unpack('<3f', reader.read(3 * 4)))
                            normal = struct.unpack('<3f', reader.read(3 * 4))
                            extra_uvs = () # CR Edit
                            if morph_extra_uvs:
                                extra_uvs = struct.unpack('<4f', reader.read(4 * 4))
                            data_list.append({'index': index, 'co': co, 'normal': normal, 'color': extra_uvs})
                    else:
                        break
            
            except UnicodeDecodeError as e:
                msg = [
                    f_tip_("Error reading file at byte 0x{num:02X}", num=reader.tell()-len(e.object)) + "\n",
                    str(e) + "\n",
                    *traceback.format_tb(e.__traceback__)
                ]
                self.report(type={'ERROR'}, message="".join(reversed(msg))[0:-1])
                print("".join(msg))
                return {'CANCELLED'}
            
            except struct.error as e:
                msg = [
                    f_tip_("Error reading file at byte 0x{num:02X}", num=reader.tell()) + "\n",
                    str(e) + "\n",
                    *traceback.format_tb(e.__traceback__)
                ]
                self.report(type={'ERROR'}, message="".join(reversed(msg))[0:-1])
                print("".join(msg))
                return {'CANCELLED'}

            except common.CM3D2ImportException as e:
                msg = [
                    f_tip_("Error reading file at byte 0x{num:02X}", num=reader.tell()) + "\n",
                    str(e) + "\n",
                    *traceback.format_tb(e.__traceback__)
                ]
                self.report(type={'ERROR'}, message="".join(reversed(msg))[0:-1])
                print("".join(msg))
                return {'CANCELLED'}

        context.window_manager.progress_update(1)

        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass
        bpy.ops.object.select_all(action='DESELECT')

        # アーマチュア作成
        if self.is_armature:
            arm    = bpy.data.armatures.new(model_name1 + ".armature")
            arm_ob = bpy.data.objects.new  (model_name1 + ".armature", arm)
            compat.link(bpy.context.scene, arm_ob)
            compat.set_select(arm_ob, True)
            compat.set_active(context, arm_ob)

            arm.show_names              = prefs.show_bone_names        
            arm.show_axes               = prefs.show_bone_axes         
            arm.show_bone_custom_shapes = prefs.show_bone_custom_shapes
            arm.show_group_colors       = prefs.show_bone_group_colors
            if compat.IS_LEGACY:
                arm_ob.show_x_ray = prefs.show_bone_in_front
            else:
                arm_ob.show_in_front = prefs.show_bone_in_front     

            bpy.ops.object.mode_set(mode='EDIT')

            is_odd_scale_bone = False

            # 基幹ボーンのみ作成
            child_data = []
            for data in bone_data:
                if not data['parent_name']:
                    bone = arm.edit_bones.new(common.decode_bone_name(data['name'], self.is_convert_bone_weight_names))
                    bone.head, bone.tail = (0, 0, 0), (0, 1, 0)
                    bone.use_deform = False

                    #co.x, co.y, co.z = -co.x, co.z, -co.y
                    #rot = compat.mul(rot, mathutils.Quaternion((0, 0, 1), math.radians(90)))
                    #rot.w, rot.x, rot.y, rot.z = -rot.w, -rot.x, rot.z, -rot.y
                    
                    #co  = data['co' ].copy()
                    #rot = data['rot'].copy()
                    #co.x, co.y, co.z = -co.x, -co.z, co.y
                    #rot.w, rot.x, rot.y, rot.z = -rot.w, -rot.x, -rot.z, rot.y
                    ##rot = compat.mul(rot, mathutils.Quaternion((0, 0, 1), math.radians(-90)))
                    #rot = compat.convert_cm_to_bl_bone_rotation(rot)
                    #mat = compat.mul(mathutils.Matrix.Translation(co), rot.to_matrix().to_4x4())
                    
                    co_mat  = mathutils.Matrix.Translation(data['co'].copy() * self.scale)
                    rot     = mathutils.Quaternion(data['rot'].copy())
                    #rot     = compat.convert_cm_to_bl_bone_rotation(rot)
                    rot_mat = rot.to_matrix().to_4x4()
                    #rot_mat = compat.convert_cm_to_bl_bone_rotation(rot_mat)
                    mat = compat.mul(co_mat, rot_mat)
                    mat = compat.convert_cm_to_bl_bone_rotation(mat)
                    mat = compat.convert_cm_to_bl_space(mat)
                    #mat = compat.mul(mat, compat.CM_TO_BL_LOCAL_BONE_MAT4)
                    
                    
                    #fix_mat_scale = mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
                    #fix_mat_before = mathutils.Euler((math.radians(90), 0, 0), 'XYZ').to_matrix().to_4x4()
                    #fix_mat_after = mathutils.Euler((0, 0, math.radians(90)), 'XYZ').to_matrix().to_4x4()

                    #compat.set_bone_matrix(bone, compat.mul4(fix_mat_scale, fix_mat_before, mat, fix_mat_after))
                    compat.set_bone_matrix(bone, mat)


                    bone["UnknownFlag"] = 1 if data['unknown'] else 0
                    if 'scale' in data:
                        bone['cm3d2_bone_scale'] = data['scale']
                        scale = mathutils.Vector(data['scale'])
                        if ( scale - mathutils.Vector((1,1,1)) ).length > 1e-5:
                            is_odd_scale_bone = True
                            self.report(type={'WARNING'}, message=f_tip_("Bone '{bone_name}' has odd scale '{bone_scale}' (odd by {bone_diff})", bone_name=bone.name, bone_scale=scale, bone_diff=( scale - mathutils.Vector((1,1,1)) ).length))
                        scale *= self.scale * 0.01
                        scale = compat.convert_cm_to_bl_bone_rotation(scale)
                        bone.bbone_x = scale.x
                        bone.bbone_z = scale.z
                        #look = bone.tail - bone.head
                        #look *= scale.y
                        #bone.tail = look + bone.head
                else:
                    child_data.append(data)
            context.window_manager.progress_update(1.333)

            # 子ボーンを追加していく
            while len(child_data):
                data = child_data.pop(0)
                parent = arm.edit_bones.get(common.decode_bone_name(data['parent_name'], self.is_convert_bone_weight_names))
                if parent:
                    bone = arm.edit_bones.new(common.decode_bone_name(data['name'], self.is_convert_bone_weight_names))
                    bone.parent = parent
                    bone.head, bone.tail = (0, 0, 0), (0, 1, 0)
                    bone.use_deform = False

                    #parent_mats = []
                    #current_bone = bone
                    #while current_bone:
                    #    for b in bone_data:
                    #        if common.decode_bone_name(b['name'], self.is_convert_bone_weight_names) == current_bone.name:
                    #            local_co  = b['co' ].copy()
                    #            local_rot = b['rot'].copy()
                    #            break
                    #
                    #    local_co_mat  = mathutils.Matrix.Translation(local_co)
                    #    local_rot_mat = local_rot.to_matrix().to_4x4()        
                    #    parent_mats.append(compat.mul(local_co_mat, local_rot_mat))
                    #
                    #    current_bone = current_bone.parent
                    #parent_mats.reverse()
                    #
                    #mat = mathutils.Matrix()
                    #for local_mat in parent_mats:
                    #    mat = compat.mul(mat, local_mat)
                    #mat *= self.scale
                    #mat = compat.convert_cm_to_bl_space(mat)
                    #mat = compat.convert_cm_to_bl_bone_rotation(mat)
                     
                    #parent_mat    = compat.mul(
                    #    mathutils.Matrix.Translation(parent.matrix.to_translation()),
                    #    parent.matrix.to_quaternion().to_matrix().to_4x4()
                    #)

                    parent_mat = parent.matrix
                    
                    local_co      = data['co' ].copy() * self.scale
                    local_rot     = data['rot'].copy()
                    #local_rot     = compat.convert_cm_to_bl_bone_rotation(rot)
                    local_co_mat  = mathutils.Matrix.Translation(local_co)
                    local_rot_mat = local_rot.to_matrix().to_4x4()
                    local_mat     = compat.mul(local_co_mat, local_rot_mat)
                    local_mat     = compat.convert_cm_to_bl_bone_space(local_mat)
                    #local_mat     = compat.mul(local_mat, mathutils.Matrix.Diagonal((1,1,1)).to_4x4())
                    mat = compat.mul(parent_mat, local_mat)
                    mat = compat.convert_cm_to_bl_bone_rotation(mat)

                    
                    #co_mat        = compat.mul( parent.matrix.inverted(), compat.convert_cm_to_bl_local_bone_mat4(local_co_mat) )
                    #rot_mat       = compat.mul( local_rot_mat, compat.CM_TO_BL_LOCAL_BONE_MAT4 )
                    #mat           = compat.ul(co_mat, rot_mat)
                    #local_mat = compat.mul(local_co_mat, local_rot_mat)
                    #local_mat *= self.scale
                    #mat = compat.mul( parent.matrix, compat.convert_cm_to_bl_local_bone(local_mat) )
                    #mat *= self.scale

                    #mat *= self.scale

                    #co.x, co.y, co.z = -co.y, co.z, co.x
                    #rot.w, rot.x, rot.y, rot.z = rot.w, rot.y, -rot.z, -rot.x

                    #co  = data['co' ].copy() * self.scale
                    #rot = data['rot'].copy()
                    #co.x, co.y, co.z = co.z, -co.x, co.y
                    ##co = compat.convert_cm_to_bl_local_bone(co)
                    ##rot.w, rot.x, rot.y, rot.z = rot.w, -rot.z, rot.x, -rot.y 
                    ##rot.w, rot.x, rot.y, rot.z = rot.w, -rot.z, rot.x, -rot.y
                    #local_mat = compat.mul(mathutils.Matrix.Translation(co), rot.to_matrix().to_4x4())
                    #mat = compat.mul( parent.matrix, local_mat )
                    ##mat *= self.scale

                    #fix_mat_scale = mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
                    #fix_mat_before = mathutils.Euler((math.radians(90), 0, 0), 'XYZ').to_matrix().to_4x4()
                    #fix_mat_after = mathutils.Euler((0, 0, math.radians(90)), 'XYZ').to_matrix().to_4x4()

                    #compat.set_bone_matrix(bone, compat.mul4(fix_mat_scale, fix_mat_before, mat, fix_mat_after))
                    compat.set_bone_matrix(bone, mat)
                    
                    bone["UnknownFlag"] = 1 if data['unknown'] else 0
                    if 'scale' in data:
                        bone['cm3d2_bone_scale'] = data['scale']
                        scale = mathutils.Vector(data['scale'])
                        if ( scale - mathutils.Vector((1,1,1)) ).length > 1e-5:
                            is_odd_scale_bone = True
                            self.report(type={'WARNING'}, message=f_tip_("Bone '{bone_name}' has odd scale '{bone_scale}' (odd by {bone_diff})", bone_name=bone.name, bone_scale=scale, bone_diff=( scale - mathutils.Vector((1,1,1)) ).length))
                        scale *= self.scale * 0.01
                        bone.bbone_x = scale.x
                        bone.bbone_z = scale.z
                        bone.bbone_segments = scale.y
                        #look = bone.tail - bone.head
                        #look *= scale.y
                        #bone.tail = look + bone.head
                else:
                    child_data.append(data)
            context.window_manager.progress_update(1.666)
            
            # Configure bones in local bone data
            is_local_bones_corrupt = False
            for data in local_bone_data:
                bone = arm.edit_bones.get(common.decode_bone_name(data['name'], self.is_convert_bone_weight_names))
                bone.use_deform = True
                if self.is_use_local_bones:
                    mat = mathutils.Matrix(data['matrix'])
                    
                    mat.transpose()
                    mat.translation *= -self.scale
                    mat.translation = compat.mul(mat.to_3x3().inverted(), mat.translation)
                    pos = mat.translation.copy()
                    
                    mat.transpose()
                    mat.translation = pos
                    #mat.row[3] = (0.0, 0.0, 0.0, 1.0)
                    mat = compat.convert_cm_to_bl_bone_rotation(mat)
                    mat = compat.mul(mathutils.Matrix.Scale(-1, 4, (1, 0, 0)), mat)
                
                    # The matrices from the local bone data are more precise rotations, but make sure they aren't corrupted
                    old_pos, old_rot, old_scale = bone.matrix.decompose()
                    compat.set_bone_matrix(bone, mat)
                    new_pos, new_rot, new_scale = bone.matrix.decompose()
                    dif_pos = (new_pos-old_pos).length/self.scale
                    dif_rot = old_rot.rotation_difference(new_rot)
                    if dif_pos > 0.1 or dif_rot.w < .9:
                        print(dif_pos,  dif_rot)
                        is_local_bones_corrupt = True
                        #self.report(type={'WARNING'}, message="Found potentially corrupt local bone data, please re-import with \"Use Local Bone Data\" disabled.")
            
            # ボーン整頓
            for bone in arm.edit_bones:
                if bone.get('cm3d2_bone_scale'):
                    continue
                if len(bone.children) == 0:
                    if bone.parent:
                        pass
                    else:
                        bone.length = 0.2 * self.scale
                elif len(bone.children) == 1:
                    co = bone.children[0].head - bone.head
                    bone.length = co.length
                elif len(bone.children) >= 2:
                    if bone.parent:
                        max_len = 0.0
                        for child_bone in bone.children:
                            co = child_bone.head - bone.head
                            if max_len < co.length:
                                max_len = co.length
                        bone.length = max_len
                    else:
                        bone.length = 0.2 * self.scale
            for bone in arm.edit_bones:
                if bone.get('cm3d2_bone_scale'):
                    continue
                if len(bone.children) == 0:
                    if bone.parent:
                        bone.length = bone.parent.length * 0.5

            # 一部ボーン削除
            if self.is_armature_clean:
                for bone in arm.edit_bones:
                    for b in local_bone_data:
                        name = common.decode_bone_name(b['name'], self.is_convert_bone_weight_names)
                        if bone.name == name:
                            break
                    else:
                        arm.edit_bones.remove(bone)

            arm.layers[16] = True
            compat.set_display_type(arm, prefs.bone_display_type)
            bpy.ops.armature.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            if self.is_custom_bones:
                print("Set custom bones")
                for pose_bone in arm_ob.pose.bones:
                    pose_bone.custom_shape = custom_bone_ob
        context.window_manager.progress_update(2)

        if self.is_mesh:
            # メッシュ作成
            me = context.blend_data.meshes.new(model_name1)
            verts, faces = [], []
            for data in vertex_data:
                #co = list(data['co'][:])
                #co[0] = -co[0]
                #co[0] *= self.scale
                #co[1] *= self.scale
                #co[2] *= self.scale
                co = compat.convert_cm_to_bl_space( mathutils.Vector(data['co']) * self.scale )
                #co = mathutils.Vector(data['co']) * self.scale
                verts.append(co)
            context.window_manager.progress_update(2.25)
            for data in face_data:
                faces.extend(data)
            context.window_manager.progress_update(2.5)
            me.from_pydata(verts, [], faces)
            # オブジェクト化
            ob = context.blend_data.objects.new(model_name1, me)
            ob.rotation_mode = 'QUATERNION'
            compat.link(context.scene, ob)
            compat.set_select(ob, True)
            compat.set_active(context, ob)
            bpy.ops.object.shade_smooth()
            context.window_manager.progress_update(2.75)
            # オブジェクト変形
            CNV_OT_align_to_cm3d2_base_bone.from_bone_data(ob=ob, bone_data=bone_data, base_bone_name=model_name2, scale=self.scale)
            context.window_manager.progress_update(3)

            # 頂点グループ作成
            for data in local_bone_data:
                ob.vertex_groups.new(name=common.decode_bone_name(data['name'], self.is_convert_bone_weight_names))
            context.window_manager.progress_update(3.333)
            for vert_index, data in enumerate(vertex_data):
                for weight in data['weights']:
                    if 0.0 < weight['value']:
                        vertex_group = ob.vertex_groups[common.decode_bone_name(weight['name'], self.is_convert_bone_weight_names)]
                        vertex_group.add([vert_index], weight['value'], 'REPLACE')
            context.window_manager.progress_update(3.666)
            if self.is_vertex_group_sort:
                bpy.ops.object.vertex_group_sort(sort_type='NAME')
            if self.is_remove_empty_vertex_group:
                for vg in ob.vertex_groups[:]:
                    for vert in me.vertices:
                        for group in vert.groups:
                            if group.group == vg.index:
                                if 0.0 < group.weight:
                                    break
                        else:
                            continue
                        break
                    else:
                        ob.vertex_groups.remove(vg)
            ob.vertex_groups.active_index = 0
            context.window_manager.progress_update(4)

            # UV作成
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.loops.layers.uv.new(f_data_("MainUV"))
            vert_loops = {}
            for i, used in enumerate(extra_uv_uses):    
                if used:
                    bm.loops.layers.uv.new(f_data_("ExtraUV{num}", num=i))
            for face in bm.faces:
                for loop in face.loops:
                    vert_loops.setdefault(loop.vert.index, []).append(loop.index)
                    loop[bm.loops.layers.uv[0]].uv = vertex_data[loop.vert.index]['uv']
                    for extra_uv_index, extra_uv in enumerate(vertex_data[loop.vert.index]['extra_uvs']):
                        loop[bm.loops.layers.uv[extra_uv_index+1]].uv = extra_uv
            bm.to_mesh(me)
            bm.free()
            context.window_manager.progress_update(5)

            # Custom Split Normals
            #normals_color = me.vertex_colors.new(name=f"Basis_normals", do_init=False) or me.vertex_colors[-1]
            #for vert_index, vert in enumerate(vertex_data):
            #    no = compat.convert_cm_to_bl_space( mathutils.Vector(vert['normal']) ) #mathutils.Vector(vert['normal']) * mathutils.Vector((-1,1,1)) #
            #    no.normalize()
            #    print(no)
            #    for loop_index in vert_loops[vert_index]:
            #        #normals[loop_index] = no
            #        normals_color.data[loop_index].color = ( # convert from range(-1, 1) to range(0, 1)
            #            *no, #*(no * 0.5 + mathutils.Vector([0.5]*3)),
            #            1,
            #        )
            #me.normals_split_custom_set(normals)
            me.normals_split_custom_set_from_vertices(
                tuple(
                    compat.convert_cm_to_bl_space( mathutils.Vector(vert['normal']) )
                    for vert in vertex_data
                )
            )
            me.use_auto_smooth = True


            # モーフ追加
            morph_count = 0
            for data in misc_data:
                if data['type'] == 'morph':
                    if morph_count == 0:
                        bpy.ops.object.shape_key_add(from_mix=False)
                        me.shape_keys.name = model_name1
                    shape_key = ob.shape_key_add(name=data['name'], from_mix=False)
                    normals_color = me.vertex_colors.new(name=f"{data['name']}_normals", do_init=False) or me.vertex_colors[-1]
                    if len(data['data']) and data['data'][0]['color']:
                        unknown_color = me.vertex_colors.new(name=f"{data['name']}_unknown", do_init=False) or me.vertex_colors[-1]
                    for vert in data['data']:
                        vert_index = vert['index']
                        co = compat.convert_cm_to_bl_space( mathutils.Vector(vert['co']) * self.scale )
                        shape_key.data[vert_index].co = shape_key.data[vert_index].co + co
                        for loop_index in vert_loops[vert_index]:
                            normals_color.data[loop_index].color = ( # convert from range(-1, 1) to range(0, 1)
                                vert['normal'][0] * 0.5 + 0.5,
                                vert['normal'][1] * 0.5 + 0.5,
                                vert['normal'][2] * 0.5 + 0.5,
                                1,
                            )
                            if vert['color']:
                                unknown_color.data[loop_index].color = ( # convert from range(-1, 1) to range(0, 1)
                                    vert['color'][0] * 0.5 * vert['color'][3] + 0.5,
                                    vert['color'][1] * 0.5 * vert['color'][3] + 0.5,
                                    vert['color'][2] * 0.5 * vert['color'][3] + 0.5,
                                    1,
                                )

                    # XXX Morph custom-normal data is lost
                    morph_count += 1
            context.window_manager.progress_update(6)

            # マテリアル追加
            progress_count_total = 0.0
            for data in material_data:
                progress_count_total += 1 #len(data['data'])
            self.progress_plus_value = 1.0 / (progress_count_total if progress_count_total > 0.0 else 1.0)
            self.progress_count = 6.0

            face_seek = 0
            mates_set = set()
            override = context.copy()
            override['object'] = ob
            prefs = common.preferences()
            for index, data in enumerate(material_data):
                print(f_("material count: {num} of {count}", num=index, count=material_count))
                if prefs.mate_unread_same_value and data.name in mates_set:
                    continue
                mates_set.add(data.name)
                #common.preferences().mate_unread_same_value
                bpy.ops.object.material_slot_add(override)
                mate = context.blend_data.materials.new(data.name)#['name1'])
                #mate['shader1'] = data['name2']
                #mate['shader2'] = data['name3']

                ob.material_slots[-1].material = mate
                # 面にマテリアル割り当て
                for i in range(face_seek, face_seek + len(face_data[index])):
                    me.polygons[i].material_index = index
                face_seek += len(face_data[index])

                # テクスチャ追加
                if compat.IS_LEGACY:
                    #self.create_mateprop_old(context, me, texes_set, mate, index, data)
                    cm3d2_data.MaterialHandler.apply_to_old(override, mate, data)
                    common.decorate_material(mate, self.is_decorate, me, index)
                else:
                    #self.create_mateprop(context, me, texes_set, mate, index, data)
                    cm3d2_data.MaterialHandler.apply_to(override, mate, data)
                    common.decorate_material(mate, self.is_decorate, me, index)
                common.setup_material(mate)

            ob.active_material_index = 0
            context.window_manager.progress_update(7)

            # メッシュ整頓
            pre_mesh_select_mode = context.tool_settings.mesh_select_mode[:]
            #if self.is_sharp:
            #    context.tool_settings.mesh_select_mode = (False, True, False)
            #    bpy.ops.object.mode_set(mode='EDIT')
            #
            #    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True, use_multi_face=False, use_non_contiguous=False, use_verts=False)
            #    bpy.ops.mesh.mark_sharp(use_verts=False)
            #
            #    bpy.ops.object.mode_set(mode='OBJECT')
            #    context.tool_settings.mesh_select_mode = pre_mesh_select_mode
            if self.is_remove_doubles:
                pre_mesh_select_mode = context.tool_settings.mesh_select_mode[:]
                context.tool_settings.mesh_select_mode = (True, False, False)
                bpy.ops.object.mode_set(mode='EDIT')
                if not self.is_sharp:
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.object.mode_set(mode='OBJECT')

                    for is_comparison, vert in zip(comparison_data, me.vertices):
                        if is_comparison:
                            vert.select = True
                    bpy.ops.object.mode_set(mode='EDIT')
                else:
                    bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles(threshold=0.000001, use_sharp_edge_from_normals=self.is_sharp)
                
                #if self.is_sharp:
                #    context.tool_settings.mesh_select_mode = (False, True, False)
                #    bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True, use_multi_face=False, use_non_contiguous=False, use_verts=False)
                #    bpy.ops.mesh.mark_sharp(use_verts=False)
                
                bpy.ops.object.mode_set(mode='OBJECT')
            context.tool_settings.mesh_select_mode = pre_mesh_select_mode
            if self.is_seam:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.select_all(action='SELECT')
                bpy.ops.uv.seams_from_islands()
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            if self.is_armature:
                mod = ob.modifiers.new("Armature", 'ARMATURE')
                mod.object = arm_ob
                compat.set_active(context, arm_ob)
                bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
                compat.set_active(context, ob)
        context.window_manager.progress_update(8)

        # マテリアル情報のテキスト埋め込み
        if self.is_mate_data_text:
            for index, data in enumerate(material_data):
                txt_name = "Material:" + str(index)
                if txt_name in context.blend_data.texts:
                    txt = context.blend_data.texts[txt_name]
                    txt.clear()
                else:
                    txt = context.blend_data.texts.new(txt_name)
                txt.write(data.to_text())
                
                # txt.write("1000" + "\n")
                # txt.write(data['name1'].lower() + "\n")
                # txt.write(data['name1'] + "\n")
                # txt.write(data['name2'] + "\n")
                # txt.write(data['name3'] + "\n")
                # txt.write("\n")
                # for tex_data in data['data']:
                #     txt.write(tex_data['type'] + "\n")
                #     if tex_data['type'] == 'tex':
                #         txt.write("\t" + tex_data['name'] + "\n")
                #         txt.write("\t" + tex_data['type2'] + "\n")
                #         if tex_data['type2'] == 'tex2d':
                #             txt.write("\t" + tex_data['name2'] + "\n")
                #             txt.write("\t" + tex_data['path'] + "\n")
                #             map_list = tex_data['tex_map']
                #             tex_map = " ".join([str(map_list[0]), str(map_list[1]), str(map_list[2]), str(map_list[3])])
                #             txt.write("\t" + tex_map + "\n")
                #     elif tex_data['type'] == 'col':
                #         txt.write("\t" + tex_data['name'] + "\n")
                #         col = " ".join([str(tex_data['color'][0]), str(tex_data['color'][1]), str(tex_data['color'][2]), str(tex_data['color'][3])])
                #         txt.write("\t" + col + "\n")
                #     elif tex_data['type'] == 'f':
                #         txt.write("\t" + tex_data['name'] + "\n")
                #         txt.write("\t" + str(tex_data['float']) + "\n")
                # txt.current_line_index = 0
        context.window_manager.progress_update(9)

        # ボーン情報のテキスト埋め込み
        if self.is_bone_data_text:
            if "BoneData" in context.blend_data.texts:
                txt = context.blend_data.texts["BoneData"]
                txt.clear()
            else:
                txt = context.blend_data.texts.new("BoneData")
        for i, data in enumerate(bone_data):
            s = ",".join([data['name'], str(data['unknown']), ""])
            parent_index = data['parent_index']
            if -1 < parent_index:
                s += bone_data[parent_index]['name'] + ","
            else:
                s += "None" + ","
            s += " ".join([str(data['co'][0]), str(data['co'][1]), str(data['co'][2])]) + ","
            s += " ".join([str(data['rot'][0]), str(data['rot'][1]), str(data['rot'][2]), str(data['rot'][3])])
            if model_ver >= 2001:
                if 'scale' in data:
                    s += ",1," + " ".join(map(str, data['scale']))
                else:
                    s += ",0"

            if self.is_bone_data_text:
                txt.write(s + "\n")
            if self.is_mesh and self.is_bone_data_obj_property:
                ob["BoneData:" + str(i)] = s
            if self.is_armature and self.is_bone_data_arm_property:
                arm["BoneData:" + str(i)] = s
        if self.is_bone_data_text:
            txt['BaseBone'] = model_name2
            txt.current_line_index = 0
        context.window_manager.progress_update(10)

        # ローカルボーン情報のテキスト埋め込み
        if self.is_bone_data_text:
            if "LocalBoneData" in context.blend_data.texts:
                txt = context.blend_data.texts["LocalBoneData"]
                txt.clear()
            else:
                txt = context.blend_data.texts.new("LocalBoneData")
        for i, data in enumerate(local_bone_data):
            s = data['name'] + ","

            mat_list = list(data['matrix'][0])
            mat_list.extend(list(data['matrix'][1]))
            mat_list.extend(list(data['matrix'][2]))
            mat_list.extend(list(data['matrix'][3]))
            for j, f in enumerate(mat_list):
                mat_list[j] = str(f)
            s += " ".join(mat_list)

            if self.is_bone_data_text:
                txt.write(s + "\n")
            if self.is_mesh and self.is_bone_data_obj_property:
                ob["LocalBoneData:" + str(i)] = s
            if self.is_armature and self.is_bone_data_arm_property:
                arm["LocalBoneData:" + str(i)] = s
        if self.is_bone_data_text:
            txt['BaseBone'] = model_name2
            txt.current_line_index = 0

        if self.is_mesh and self.is_bone_data_obj_property:
            ob['BaseBone'] = model_name2
            if model_ver >= 1000:
                ob['ModelVersion'] = model_ver
        if self.is_armature and self.is_bone_data_arm_property:
            arm['BaseBone'] = model_name2
            if model_ver >= 1000:
                arm['ModelVersion'] = model_ver
        context.window_manager.progress_end()

        require_time = time.time() - start_time
        filesize = os.path.getsize(self.filepath)
        filesize_str = "バイト"
        if 1024 * 1024 < filesize:
            filesize = filesize / (1024 * 1024.0)
            filesize_str = "MB"
        elif 1024 < filesize:
            filesize = filesize / 1024.0
            filesize_str = "KB"
        self.report(type={'INFO'}, message=f_tip_("Model was imported successfully ({} {} / {:.2f} sec)", filesize, filesize_str, require_time))
        
        if is_odd_scale_bone:
            self.report(type={'WARNING'}, message="Found bone with a scale not equal to 1.")
        if is_local_bones_corrupt:
            self.report(type={'ERROR'}, message="Found potentially corrupt local bone data, please re-import with \"Use Local Bone Data\" disabled.")
        return {'FINISHED'}

    def create_mateprop_old(self, context, me, tex_set, mate, mate_idx, data: list):
        # create_matepropとの違いは、slot_indexの有無、nodeの接続・配置処理のみ

        prefs = common.preferences()
        # テクスチャ追加
        slot_index = 0
        for tex_data in data['data']:
            if prefs.mate_unread_same_value:
                if tex_data['name'] in tex_set:
                    continue
                tex_set.add(tex_data['name'])

            node_name = tex_data['name']
            if tex_data['type'] == 'tex':
                path = tex_data['path']
                tex_map_data = tex_data['tex_map']
                common.create_tex(context, mate, node_name, tex_data['name2'], path, path, tex_map_data, prefs.is_replace_cm3d2_tex, slot_index)

            elif tex_data['type'] == 'col':
                col = tex_data['color']
                common.create_col(context, mate, node_name, col, slot_index)

            elif tex_data['type'] == 'f':
                f = tex_data['float']
                common.create_f(context, mate, node_name, f, slot_index)

            slot_index += 1

            self.progress(context)

    def create_mateprop(self, context, me, tex_set, mate, mate_idx, data: list):
        if mate.use_nodes is False:
            mate.use_nodes = True

        nodes = mate.node_tree.nodes
        prefs = common.preferences()

        for prop_data in data['data']:
            if prefs.mate_unread_same_value:
                if prop_data['name'] in tex_set:
                    continue
                tex_set.add(prop_data['name'])

            if prop_data['type'] == 'tex':  # テクスチャ追加
                prop_name = prop_data['name']
                if prop_data['type2'] == 'tex2d':
                    tex_name = prop_data['name2']
                    cm3d2path = prop_data['path']
                    tex_map = prop_data['tex_map']
                    tex = common.create_tex(context, mate, prop_name, tex_name, cm3d2path, cm3d2path, tex_map)

                    if prop_data['type2'] == 'tex2d':
                        mapping = prop_data['tex_map']
                        tex_map = tex.texture_mapping
                        tex_map.translation[0] = mapping[0]
                        tex_map.translation[1] = mapping[1]
                        tex_map.scale[0] = mapping[2]
                        tex_map.scale[1] = mapping[3]

                        # ファイルの実体を割り当て
                        if prefs.is_replace_cm3d2_tex:
                            img = tex.image
                            # col = mate.node_tree.nodes.new(type='ShaderNodeAttribute')
                            # tex.image = bpy.data.images.load("C:\\path\\to\\im.jpg")
                            replaced = common.replace_cm3d2_tex(img, self.texpath_dict, reload_path=False)
                            if compat.IS_LEGACY and replaced and prop_name == '_MainTex':
                                for face in me.polygons:
                                    if face.material_index == mate_idx:
                                        me.uv_textures.active.data[face.index].image = img
                else:
                    common.create_tex(context, mate, prop_name)

            elif prop_data['type'] == 'col':
                col = nodes.new(type='ShaderNodeRGB')
                col.name = col.label = prop_data['name']
                # val.type = 'RGB'
                col.outputs[0].default_value = prop_data['color'][:4]

                # mate.node_tree.links.new(bsdf.inputs['xxx'], val.outputs['Color'])
                # mate.node_tree.nodes.active = col

                # slot = mate.texture_slots.create(tex_index)
                # mate.use_textures[tex_index] = False
                # slot.diffuse_color_factor = tex_data['color'][3]
                # slot.use_rgb_to_intensity = True
                # tex = context.blend_data.textures.new(tex_data['name'], 'BLEND')
                # slot.texture = tex

            elif prop_data['type'] == 'f':
                val = nodes.new(type='ShaderNodeValue')
                val.name = prop_data['name']
                val.label = prop_data['name']
                # val.type = 'VALUE'
                # mate.node_tree.links.new(bsdf.inputs['xxx'], val.outputs['Value'])

                val.outputs[0].default_value = prop_data['float']

            self.progress(context)

        cm3d2_data.align_nodes(mate)

    def progress(self, context):
        self.progress_count += self.progress_plus_value
        context.window_manager.progress_update(self.progress_count)


# メニューを登録する関数
def menu_func(self, context):
    self.layout.operator(CNV_OT_import_cm3d2_model.bl_idname, icon_value=common.kiss_icon())
