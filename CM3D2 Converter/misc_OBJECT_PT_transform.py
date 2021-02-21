# 「プロパティ」エリア → 「オブジェクト」タブ → 「トランスフォーム」パネル
import bpy
import bmesh
import mathutils
from . import common
from . import compat
from .model_export import CNV_OT_export_cm3d2_model


# メニュー等に項目追加
def menu_func(self, context):
    self.layout.operator('object.sync_object_transform', icon_value=common.kiss_icon())
    self.layout.operator('object.align_to_base_bone'   , icon_value=common.kiss_icon())


@compat.BlRegister()
class CNV_OT_sync_object_transform(bpy.types.Operator):
    bl_idname = 'object.sync_object_transform'
    bl_label = "Copy Origin Position"
    bl_description = "The previously selected item's origin is copied onto the active object."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obs = context.selected_objects
        return len(obs) == 2

    def execute(self, context):
        #target_ob = context.active_object
        #for ob in context.selected_objects:
        #    if target_ob.name != ob.name:
        #        source_ob = ob
        #        break
        target_ob, source_ob = common.get_target_and_source_object(context)

        if compat.IS_LEGACY:
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            target_space = space
                            break

            pre_cursor_location = target_space.cursor_location[:]
            try:
                target_space.cursor_location = source_ob.location[:]

                compat.set_select(source_ob, False)
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                compat.set_select(source_ob, True)

            finally:
                target_space.cursor_location = pre_cursor_location[:]
        else:
            pre_cursor_loc = context.scene.cursor.location[:]
            try:
                context.scene.cursor.location = source_ob.location[:]

                compat.set_select(source_ob, False)
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                compat.set_select(source_ob, True)

            finally:
                context.scene.cursor.location = pre_cursor_loc[:]
        return {'FINISHED'}



@compat.BlRegister()
class CNV_OT_align_to_base_bone(bpy.types.Operator):
    bl_idname = 'object.align_to_base_bone'
    bl_label = "Align to Base Bone"
    bl_description = "Align the object to it's armature's base bone"
    bl_options = {'REGISTER', 'UNDO'}

    scale           : bpy.props.FloatProperty(name="Scale"        , default=   5, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="The amount by which the mesh is scaled when imported. Recommended that you use the same when at the time of export.")
    is_preserve_mesh: bpy.props.BoolProperty (name="Preserve Mesh", default=True, description="Align object transform, then fix mesh transform so it remains in place.")

    items = [
        ('ARMATURE'         , "Armature"     , "", 'OUTLINER_OB_ARMATURE', 1),
        ('TEXT'             , "Text"         , "", 'FILE_TEXT'           , 2),
        ('OBJECT_PROPERTY'  , "Object Data"  , "", 'OBJECT_DATAMODE'     , 3),
        ('ARMATURE_PROPERTY', "Armature Data", "", 'ARMATURE_DATA'       , 4),
    ]
    bone_info_mode = bpy.props.EnumProperty(items=items, name="Bone Data Source", default='OBJECT_PROPERTY', description="This will decide from where the Bone Data is gathered from.")


    @staticmethod
    def find_base_bone(ob: bpy.types.Object):
        arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent
        
        base_bone_name = None
        if arm_ob:
            base_bone_name = arm_ob.data.get('BaseBone')
        if not base_bone_name:
            base_bone_name = ob.data.get('BaseBone')
        if not base_bone_name:
            # TODO : Check for base bone in object name
            # See model_export.CNV_OT_export_cm3d2_model.export() "BoneData情報読み込み"
            pass
        
        return base_bone_name


    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob: 
            return False
        return cls.find_base_bone(ob) != None


    def invoke(self, context, event):
        ob = context.object

        # model名とか
        #ob_names = common.remove_serial_number(ob.name, self.is_arrange_name).split('.')
        #self.model_name = ob_names[0]
        #self.base_bone_name = ob_names[1] if len(ob_names) >= 2  else 'Auto'

        # ボーン情報元のデフォルトオプションを取得
        if "BoneData" in context.blend_data.texts:
            self.bone_info_mode = 'TEXT'
        if "BoneData:0" in ob:
            self.bone_info_mode = 'OBJECT_PROPERTY'
        arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent
        if arm_ob:
            if arm_ob.type == 'ARMATURE':
                self.bone_info_mode = 'ARMATURE_PROPERTY'

        self.scale = common.preferences().scale
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        ob = context.object
        arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent

        def _prop_enum_row(layout, data, prop, value, enabled=True):
            row = layout.row(align=True)
            name = row.enum_item_name(data, prop, value)
            icon = row.enum_item_icon(data, prop, value)
            row.prop_enum(data, prop, value, text=name)
            row.enabled = enabled
            return row
        
        self.layout.prop(self, 'scale')
        self.layout.prop(self, 'is_preserve_mesh', icon=compat.icon('MESH_DATA'))

        col = self.layout.column(align=True)
        col.label(text="Bone Data Source", icon='BONE_DATA')
        _prop_enum_row(col, self, 'bone_info_mode', 'ARMATURE'         , enabled=bool(arm_ob                                ))
        _prop_enum_row(col, self, 'bone_info_mode', 'TEXT'             , enabled=bool("BoneData" in context.blend_data.texts))
        _prop_enum_row(col, self, 'bone_info_mode', 'OBJECT_PROPERTY'  , enabled=bool("BoneData:0" in ob                    ))
        _prop_enum_row(col, self, 'bone_info_mode', 'ARMATURE_PROPERTY', enabled=bool(arm_ob and "BoneData:0" in arm_ob.data))

    @staticmethod
    def from_bone_data(ob: bpy.types.Object, bone_data, base_bone_name, scale=5):
        for bone in bone_data:
            if bone['name'] == base_bone_name:
                #co = bone['co'].copy()
                #co.x, co.y, co.z = -co.x, -co.z, co.y
                #co *= self.scale
                #ob.location = co
                #
                #rot = bone['rot'].copy()
                #eul = mathutils.Euler((math.radians(90), 0, 0), 'XYZ')
                #rot.rotate(eul)
                #ob.rotation_mode = 'QUATERNION'
                #ob.rotation_quaternion = rot

                parent_mats = []
                current_bone = bone
                while current_bone:
                    local_co_mat  = mathutils.Matrix.Translation(mathutils.Vector(current_bone['co']) * scale)
                    local_rot_mat = mathutils.Quaternion(current_bone['rot']).to_matrix().to_4x4()        
                    parent_mats.append(compat.mul(local_co_mat, local_rot_mat))
                    if current_bone.get('parent_name'):
                        for b in bone_data:
                            if b['name'] == current_bone['parent_name']:
                                current_bone = b
                                break
                    elif current_bone.get('parent_index', -1) != -1 :
                        current_bone = bone_data[current_bone['parent_index']]
                    else:
                        current_bone = None

                parent_mats.reverse()
                mat = mathutils.Matrix()
                for local_mat in parent_mats:
                    mat = compat.mul(mat, local_mat)

                mat = compat.convert_cm_to_bl_space(mat)
                mat = compat.convert_cm_to_bl_local_space(mat)
                ob.matrix_basis = mat
                break


    @staticmethod
    def from_armature(ob: bpy.types.Object, arm: bpy.types.Armature, base_bone_name):
        base_bone = arm.bones.get(base_bone_name)
        mat = base_bone.matrix_local.copy()
        mat = compat.convert_bl_to_cm_bone_rotation(mat)
        mat = compat.convert_cm_to_bl_local_space(mat)
        ob.matrix_basis = mat


    def execute(self, context):
        ob = context.object
        arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent
        
        base_bone_name = None
        bone_data = None
        if self.bone_info_mode == 'ARMATURE':
            #bone_data = CNV_OT_export_cm3d2_model.armature_bone_data_parser(context, arm_ob)
            base_bone_name = arm_ob.data['BaseBone']
        if self.bone_info_mode == 'TEXT':
            bone_data_text = context.blend_data.texts["BoneData"]
            if 'BaseBone' in bone_data_text:
                base_bone_name = bone_data_text['BaseBone']
            bone_data = CNV_OT_export_cm3d2_model.bone_data_parser(l.body for l in bone_data_text.lines)
        elif self.bone_info_mode in ['OBJECT_PROPERTY', 'ARMATURE_PROPERTY']:
            target = ob if self.bone_info_mode == 'OBJECT_PROPERTY' else arm_ob.data
            if 'BaseBone' in target:
                base_bone_name = target['BaseBone']
            bone_data = CNV_OT_export_cm3d2_model.bone_data_parser(CNV_OT_export_cm3d2_model.indexed_data_generator(target, prefix="BoneData:"))
        
        old_basis = ob.matrix_basis.copy()
        if bone_data:
            self.from_bone_data(ob, bone_data, base_bone_name, self.scale)
        else:
            self.from_armature(ob, arm_ob.data, base_bone_name)

        if self.is_preserve_mesh:
            new_basis = ob.matrix_basis.copy()
            ob.matrix_basis = compat.mul(new_basis.inverted(), old_basis)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
            ob.matrix_basis = new_basis


        return {'FINISHED'}



