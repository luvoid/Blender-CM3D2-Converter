# 「プロパティ」エリア → 「オブジェクト」タブ
import re
import bpy
import mathutils
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    ob = context.object
    if not ob or ob.type != 'MESH':
        return

    bone_data_count = 0
    if 'BoneData:0' in ob and 'LocalBoneData:0' in ob:
        for key in ob.keys():
            if re.search(r'^(Local)?BoneData:\d+$', key):
                bone_data_count += 1
    enabled_clipboard = False
    clipboard = context.window_manager.clipboard
    if 'BoneData:' in clipboard and 'LocalBoneData:' in clipboard:
        enabled_clipboard = True

    if bone_data_count or enabled_clipboard:
        col = self.layout.column(align=True)
        row = col.row(align=True)
        row.label(text="CM3D2 Bone Data", icon_value=common.kiss_icon())
        sub_row = row.row()
        sub_row.alignment = 'RIGHT'
        if 'BoneData:0' in ob and 'LocalBoneData:0' in ob:
            bone_data_count = 0
            for key in ob.keys():
                if re.search(r'^(Local)?BoneData:\d+$', key):
                    bone_data_count += 1
            sub_row.label(text=str(bone_data_count), icon='CHECKBOX_HLT')
        else:
            sub_row.label(text="0", icon='CHECKBOX_DEHLT')
        row = col.row(align=True)
        row.operator('object.copy_object_bone_data_property', icon='COPYDOWN', text="Copy")
        row.operator('object.paste_object_bone_data_property', icon='PASTEDOWN', text="Paste")
        row.operator('object.remove_object_bone_data_property', icon='X', text="")

@compat.BlRegister()
class CNV_OT_copy_object_bone_data_property(bpy.types.Operator):
    bl_idname = 'object.copy_object_bone_data_property'
    bl_label = "Copy the Bone Data from the object's custom properties"
    bl_description = "Copies the bone Data in the object's custom properties to the clipboard."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if 'BoneData:0' in ob and 'LocalBoneData:0' in ob:
                return True
        return False

    def execute(self, context):
        output_text = ""
        ob = context.active_object
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
        self.report(type={'INFO'}, message="Bone Data was copied to the clipboard.")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_paste_object_bone_data_property(bpy.types.Operator):
    bl_idname = 'object.paste_object_bone_data_property'
    bl_label = "Paste Bone Data"
    bl_description = "Paste Bone Data from the clipboard into the object's custom properties. NOTE:Any data in custom properties will be replaced."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            clipboard = context.window_manager.clipboard
            if 'BoneData:' in clipboard and 'LocalBoneData:' in clipboard:
                return True
        return False

    def execute(self, context):
        ob = context.active_object
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
        self.report(type={'INFO'}, message="Data was pasted, mission accomplished")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_remove_object_bone_data_property(bpy.types.Operator):
    bl_idname = 'object.remove_object_bone_data_property'
    bl_label = "Remove the bone Data"
    bl_description = "Remove all bone Data for the custom properties"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if 'BoneData:0' in ob and 'LocalBoneData:0' in ob:
                return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text="Remove all bone Data form the custom properties?", icon='CANCEL')

    def execute(self, context):
        ob = context.active_object
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
        self.report(type={'INFO'}, message="Bone Data was removed. Mission Accomplished.")
        return {'FINISHED'}

