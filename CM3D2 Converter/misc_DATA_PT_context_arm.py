# 「プロパティ」エリア → 「アーマチュアデータ」タブ
import re
import struct
import math
import unicodedata
import time
import bpy
import bmesh
import mathutils
import os
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    import re
    ob = context.active_object
    if not ob: return
    if ob.type != 'ARMATURE': return

    arm = ob.data
    is_boxed = False

    bone_data_count = 0
    if 'BoneData:0' in arm and 'LocalBoneData:0' in arm:
        for key in arm.keys():
            if re.search(r'^(Local)?BoneData:\d+$', key):
                bone_data_count += 1
    enabled_clipboard = False
    clipboard = context.window_manager.clipboard
    if 'BoneData:' in clipboard and 'LocalBoneData:' in clipboard:
        enabled_clipboard = True
    if bone_data_count or enabled_clipboard:
        if not is_boxed:
            box = self.layout.box()
            box.label(text="For CM3D2", icon_value=common.kiss_icon())
            is_boxed = True

        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="Bone Data", icon='CONSTRAINT_BONE')
        sub_row = row.row()
        sub_row.alignment = 'RIGHT'
        if bone_data_count:
            sub_row.label(text=str(bone_data_count), icon='CHECKBOX_HLT')
        else:
            sub_row.label(text="0", icon='CHECKBOX_DEHLT')
        row = col.row(align=True)
        row.operator('object.copy_armature_bone_data_property', icon='COPYDOWN', text="Copy")
        row.operator('object.paste_armature_bone_data_property', icon='PASTEDOWN', text="Paste")
        row.operator('object.remove_armature_bone_data_property', icon='X', text="")

    flag = False
    for bone in arm.bones:
        if not flag and re.search(r'[_ ]([rRlL])[_ ]', bone.name):
            flag = True
        if not flag and bone.name.count('*') == 1:
            if re.search(r'\.([rRlL])$', bone.name):
                flag = True
        if flag:
            if not is_boxed:
                box = self.layout.box()
                box.label(text="For CM3D2", icon_value=common.kiss_icon())
                is_boxed = True

            col = box.column(align=True)
            col.label(text="Convert Bone Names", icon='SORTALPHA')
            row = col.row(align=True)
            row.operator('armature.decode_cm3d2_bone_names', text="CM3D2 → Blender", icon='BLENDER')
            row.operator('armature.encode_cm3d2_bone_names', text="Blender → CM3D2", icon_value=common.kiss_icon())
            break

    if 'is T Stance' in arm:
        if not is_boxed:
            box = self.layout.box()
            box.label(text="For CM3D2", icon_value=common.kiss_icon())
            is_boxed = True

        col = box.column(align=True)
        col.label(text="Pause", icon='POSE_HLT')
        row = col.row(align=True)

        sub_row = row.row(align=True)
        op = sub_row.operator('wm.context_set_int', icon='ARMATURE_DATA', text="Original")
        op.data_path, op.value = 'scene.frame_current', 1
        if context.scene.frame_current % 2:
            sub_row.enabled = False

        sub_row = row.row(align=True)
        op = sub_row.operator('wm.context_set_int', icon='POSE_DATA', text="Pose data")
        op.data_path, op.value = 'scene.frame_current', 0
        if not context.scene.frame_current % 2:
            sub_row.enabled = False


@compat.BlRegister()
class CNV_OT_decode_cm3d2_bone_names(bpy.types.Operator):
    bl_idname = 'armature.decode_cm3d2_bone_names'
    bl_label = " Decode CM3D2 bone names→Blender bones names"
    bl_description = "Bone names are converted to Blender bone names for mirror functions."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        import re
        ob = context.active_object
        if ob:
            if ob.type == 'ARMATURE':
                arm = ob.data
                for bone in arm.bones:
                    if re.search(r'[_ ]([rRlL])[_ ]', bone.name):
                        return True
        return False

    def execute(self, context):
        ob = context.active_object
        arm = ob.data
        convert_count = 0
        for bone in arm.bones:
            bone_name = common.decode_bone_name(bone.name)
            if bone_name != bone.name:
                bone.name = bone_name
                convert_count += 1
        if convert_count == 0:
            self.report(type={'WARNING'}, message="No convertible names were found. Aborting.")
        else:
            self.report(type={'INFO'}, message="Bones names were converted for Blender. Mission Accomplished.")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_encode_cm3d2_bone_names(bpy.types.Operator):
    bl_idname = 'armature.encode_cm3d2_bone_names'
    bl_label = "Blender bone names→CM3D2 bone names"
    bl_description = "blender bone names are reverted back to CM3D2 bone names."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        import re
        ob = context.active_object
        if ob:
            if ob.type == 'ARMATURE':
                arm = ob.data
                for bone in arm.bones:
                    if bone.name.count('*') == 1 and re.search(r'\.([rRlL])$', bone.name):
                        return True
        return False

    def execute(self, context):
        ob = context.active_object
        arm = ob.data
        convert_count = 0
        for bone in arm.bones:
            bone_name = common.encode_bone_name(bone.name)
            if bone_name != bone.name:
                bone.name = bone_name
                convert_count += 1
        if convert_count == 0:
            self.report(type={'WARNING'}, message="A name that cannot be converted was found, Mission failed")
        else:
            self.report(type={'INFO'}, message="Bone names were converted back to CM3D2 Format. Mission Accomplished.")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_copy_armature_bone_data_property(bpy.types.Operator):
    bl_idname = 'object.copy_armature_bone_data_property'
    bl_label = "Copy the bone Data"
    bl_description = "Copy the bone Data in the armature custom properties to the clipboard."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if ob.type == 'ARMATURE':
                arm = ob.data
                if 'BoneData:0' in arm and 'LocalBoneData:0' in arm:
                    return True
        return False

    def execute(self, context):
        output_text = ""
        ob = context.active_object.data
        pass_count = 0
        if 'BaseBone' in ob:
            output_text += "BaseBone:" + ob['BaseBone'] + "\n"
        for i in range(99999):
            name = "BoneData:" + str(i)
            if name in ob:
                output_text += "BoneData:" + ob[name] + "\n"
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        pass_count = 0
        for i in range(99999):
            name = "LocalBoneData:" + str(i)
            if name in ob:
                output_text += "LocalBoneData:" + ob[name] + "\n"
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        context.window_manager.clipboard = output_text
        self.report(type={'INFO'}, message="Bone Data was copied, mission accomplished.")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_paste_armature_bone_data_property(bpy.types.Operator):
    bl_idname = 'object.paste_armature_bone_data_property'
    bl_label = "Paste Bone Data"
    bl_description = "Bone Data is pasted into the Armature custom properties. NOTE: this wil replace any Data in the custom properties."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if ob.type == 'ARMATURE':
                clipboard = context.window_manager.clipboard
                if 'BoneData:' in clipboard and 'LocalBoneData:' in clipboard:
                    return True
        return False

    def execute(self, context):
        ob = context.active_object.data
        pass_count = 0
        for i in range(99999):
            name = "BoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        pass_count = 0
        for i in range(99999):
            name = "LocalBoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        bone_data_count = 0
        local_bone_data_count = 0
        for line in context.window_manager.clipboard.split("\n"):
            if line.startswith('BaseBone:'):
                ob['BaseBone'] = line[9:]  # len('BaseData:') == 9
                continue

            if line.startswith('BoneData:'):
                if line.count(',') >= 4:
                    name = "BoneData:" + str(bone_data_count)
                    ob[name] = line[9:]  # len('BoneData:') == 9
                    bone_data_count += 1
                continue

            if line.startswith('LocalBoneData:'):
                if line.count(',') == 1:
                    name = "LocalBoneData:" + str(local_bone_data_count)
                    ob[name] = line[14:]  # len('LocalBoneData:') == 14
                    local_bone_data_count += 1

        self.report(type={'INFO'}, message="Bone Data was pasted, mission accomplished")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_remove_armature_bone_data_property(bpy.types.Operator):
    bl_idname = 'object.remove_armature_bone_data_property'
    bl_label = "Remove Bone Data"
    bl_description = "Removes all Bone Data from the armature's custom properties."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if ob.type == 'ARMATURE':
                arm = ob.data
                if 'BoneData:0' in arm and 'LocalBoneData:0' in arm:
                    return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="Removes all bone Data from the armature's custom properties.", icon='CANCEL')

    def execute(self, context):
        ob = context.active_object.data
        pass_count = 0
        if 'BaseBone' in ob:
            del ob['BaseBone']
        for i in range(99999):
            name = "BoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        pass_count = 0
        for i in range(99999):
            name = "LocalBoneData:" + str(i)
            if name in ob:
                del ob[name]
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        self.report(type={'INFO'}, message="Bone data was removed, mission accomplished")
        return {'FINISHED'}
