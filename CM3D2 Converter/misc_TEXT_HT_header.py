# 「テキストエディター」エリア → ヘッダー
import bpy
from . import common
from . import compat
from .translations.pgettext_functions import *


# メニュー等に項目追加
def menu_func(self, context):
    texts = bpy.data.texts
    text_keys = texts.keys()
    self.layout.label(text="For CM3D2:", icon_value=common.kiss_icon())
    row = self.layout.row(align=True)
    if 'BoneData' in text_keys:
        txt = bpy.data.texts['BoneData']
        line_count = 0
        for line in txt.as_string().split('\n'):
            if line:
                line_count += 1
        row.operator('text.show_text', icon='ARMATURE_DATA', text=f_iface_("BoneData ({})", line_count, msgctxt='Operator')).name = 'BoneData'
    if 'LocalBoneData' in text_keys:
        txt = bpy.data.texts['LocalBoneData']
        line_count = 0
        for line in txt.as_string().split('\n'):
            if line:
                line_count += 1
        row.operator('text.show_text', icon='BONE_DATA', text=f_iface_("LocalBoneData ({})", line_count, msgctxt='Operator')).name = 'LocalBoneData'
    if 'BoneData' in text_keys and 'LocalBoneData' in text_keys:
        if 'BoneData' in texts:
            if 'BaseBone' not in texts['BoneData']:
                texts['BoneData']['BaseBone'] = ""
            row.prop(texts['BoneData'], '["BaseBone"]', text="")
        row.operator('text.copy_text_bone_data', icon='COPYDOWN', text="")
        row.operator('text.paste_text_bone_data', icon='PASTEDOWN', text="")
    if "Material:0" in text_keys:
        self.layout.label(text="", icon='MATERIAL_DATA')
        row = self.layout.row(align=True)
        pass_count = 0
        for i in range(99):
            name = "Material:" + str(i)
            if name in text_keys:
                sub_row = row.row(align=True)
                sub_row.scale_x = 0.75
                sub_row.operator('text.show_text', text=str(i)).name = name
            else:
                pass_count += 1
            if 9 < pass_count:
                break
        if "Material:0" in text_keys:
            row.operator('text.remove_all_material_texts', icon='X', text="")


@compat.BlRegister()
class CNV_OT_show_text(bpy.types.Operator):
    bl_idname = 'text.show_text'
    bl_label = "Display Text"
    bl_description = "Displays the specified text in this area"
    bl_options = {'REGISTER', 'UNDO'}

    name = bpy.props.StringProperty(name="Text name")

    @classmethod
    def poll(cls, context):
        return hasattr(context.space_data, 'text')

    def execute(self, context):
        context.space_data.text = bpy.data.texts[self.name]
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_copy_text_bone_data(bpy.types.Operator):
    bl_idname = 'text.copy_text_bone_data'
    bl_label = "Copy the Bone Data in the text"
    bl_description = "Bone data is copied to clipboard so it can be pasted in the custom properties."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        texts = context.blend_data.texts
        return 'BoneData' in texts and 'LocalBoneData' in texts

    def execute(self, context):
        output_text = ""
        if 'BaseBone' in context.blend_data.texts['BoneData']:
            output_text += "BaseBone:" + context.blend_data.texts['BoneData']['BaseBone'] + "\n"
        for line in context.blend_data.texts['BoneData'].as_string().split('\n'):
            if not line:
                continue
            output_text += "BoneData:" + line + "\n"
        for line in context.blend_data.texts['LocalBoneData'].as_string().split('\n'):
            if not line:
                continue
            output_text += "LocalBoneData:" + line + "\n"
        context.window_manager.clipboard = output_text
        self.report(type={'INFO'}, message="Bonedata was copied, mission accomplished")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_paste_text_bone_data(bpy.types.Operator):
    bl_idname = 'text.paste_text_bone_data'
    bl_label = "Paste Bone Data"
    bl_description = "Paste Bone Data from clipboard into text editor."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        clipboard = context.window_manager.clipboard
        return "BoneData:" in clipboard and "LocalBoneData:" in clipboard

    def execute(self, context):
        if "BoneData" in context.blend_data.texts:
            bone_data_text = context.blend_data.texts["BoneData"]
            bone_data_text.clear()
        else:
            bone_data_text = context.blend_data.texts.new("BoneData")
        if "LocalBoneData" in context.blend_data.texts:
            local_bone_data_text = context.blend_data.texts["LocalBoneData"]
            local_bone_data_text.clear()
        else:
            local_bone_data_text = context.blend_data.texts.new("LocalBoneData")

        clipboard = context.window_manager.clipboard
        for line in clipboard.split("\n"):
            if line.startswith('BaseBone:'):
                info = line[9:]  # len('BaseData:') == 9
                bone_data_text['BaseBone'] = info
                local_bone_data_text['BaseBone'] = info
                continue
            if line.startswith('BoneData:'):
                if line.count(',') >= 4:
                    bone_data_text.write(line[9:] + "\n")  # len('BoneData:') == 9
                continue
            if line.startswith('LocalBoneData:'):
                if line.count(',') == 1:
                    local_bone_data_text.write(line[14:] + "\n")  # len('LocalBoneData:') == 14
        bone_data_text.current_line_index = 0
        local_bone_data_text.current_line_index = 0
        self.report(type={'INFO'}, message="Bone Data was pasted, mission accomplished.")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_remove_all_material_texts(bpy.types.Operator):
    bl_idname = 'text.remove_all_material_texts'
    bl_label = "Delete all .mate data"
    bl_description = "Removes .mate data in the text editor"
    bl_options = {'REGISTER', 'UNDO'}

    is_keep_used_material = bpy.props.BoolProperty(name="Keep Used Materials", default=True)

    @classmethod
    def poll(cls, context):
        return "Material:0" in context.blend_data.texts

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_keep_used_material')

    def execute(self, context):
        remove_texts = []
        pass_count = 0
        for i in range(9999):
            name = "Material:" + str(i)
            if name in context.blend_data.texts:
                remove_texts.append(context.blend_data.texts[name])
            else:
                pass_count += 1
            if 10 < pass_count:
                break
        if self.is_keep_used_material:
            ob = context.active_object
            if ob:
                remove_texts = remove_texts[len(ob.material_slots):]
        for txt in remove_texts:
            context.blend_data.texts.remove(txt)
        return {'FINISHED'}
