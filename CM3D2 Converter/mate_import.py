import os
import re
import struct
import shutil
import bpy
from . import common
from . import compat
from . import cm3d2_data
from .translations.pgettext_functions import *


@compat.BlRegister()
class CNV_OT_import_cm3d2_mate(bpy.types.Operator):
    bl_idname = 'material.import_cm3d2_mate'
    bl_label = "Import Mate"
    bl_description = "Open a .mate file as a material."
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".mate"
    filter_glob = bpy.props.StringProperty(default="*.mate", options={'HIDDEN'})

    is_decorate = bpy.props.BoolProperty(name="Decorate the material according to its type", default=True)
    is_replace_cm3d2_tex = bpy.props.BoolProperty(name="Find textures", default=True, description="Will search for the textures.")

    @classmethod
    def poll(cls, context):
        if hasattr(context, 'material_slot'):
            if hasattr(context, 'material'):
                return True
        return False

    def invoke(self, context, event):
        prefs = common.preferences()
        if prefs.mate_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.mate_default_path, None, "mate")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.mate_import_path, None, "mate")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        prefs = common.preferences()
        if compat.IS_LEGACY:
            self.layout.prop(self, 'is_decorate', icon=compat.icon('SHADING_TEXTURE'))
        self.layout.prop(prefs, 'is_replace_cm3d2_tex', icon='BORDERMOVE')

    def execute(self, context):
        prefs = common.preferences()
        prefs.mate_import_path = self.filepath

        try:
            file = open(self.filepath, 'rb')
        except:
            self.report(type={'ERROR'}, message=f_tip_("Failed to open the file. File does not exist or is inaccessible. file={}", self.filepath))
            return {'CANCELLED'}

        try:
            with file:
                mat_data = cm3d2_data.MaterialHandler.read(file)

        except Exception as e:
            self.report(type={'ERROR'}, message="This is not a .mate file for CM3D2。" + str(e))
            return {'CANCELLED'}

        if not context.material_slot:
            bpy.ops.object.material_slot_add()
        root, ext = os.path.splitext(os.path.basename(self.filepath))
        mate = context.blend_data.materials.new(name=mat_data.name)
        context.material_slot.material = mate
        common.setup_material(mate)

        if compat.IS_LEGACY:
            cm3d2_data.MaterialHandler.apply_to_old(context, mate, mat_data, prefs.is_replace_cm3d2_tex, self.is_decorate, prefs.mate_unread_same_value)
        else:
            cm3d2_data.MaterialHandler.apply_to(context, mate, mat_data, prefs.is_replace_cm3d2_tex)

        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_import_cm3d2_mate_text(bpy.types.Operator):
    bl_idname = 'text.import_cm3d2_mate_text'
    bl_label = "Import a mate"
    bl_description = "Open a mate file in the text editor as text"
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".mate"
    filter_glob = bpy.props.StringProperty(default="*.mate", options={'HIDDEN'})

    is_overwrite = bpy.props.BoolProperty(name="Overwrites current text in the text editor.", default=False)

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        prefs = common.preferences()
        if prefs.mate_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.mate_default_path, None, "mate")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.mate_import_path, None, "mate")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        self.layout.prop(self, 'is_overwrite', icon='SAVE_COPY')

    def execute(self, context):
        prefs = common.preferences()
        prefs.mate_import_path = self.filepath

        edit_text = None
        if self.is_overwrite:
            edit_text = getattr(context, 'edit_text')
            if not edit_text:
                self.report(type={'ERROR'}, message="Text data could not be overwritten")
                return {'CANCELLED'}
            edit_text.clear()

        try:
            file = open(self.filepath, 'rb')
        except:
            self.report(type={'ERROR'}, message=f_tip_("Failed to open the file. File does not exist or is inaccessible. file={}", self.filepath))
            return {'CANCELLED'}

        try:
            with file:
                mat_data = cm3d2_data.MaterialHandler.read(file)

        except Exception as e:
            self.report(type={'ERROR'}, message="Failed to import the file." + str(e))
            return {'CANCELLED'}

        if not context.material_slot:
            bpy.ops.object.material_slot_add()
        root, ext = os.path.splitext(os.path.basename(self.filepath))
        mate = context.blend_data.materials.new(name=mat_data.name)
        context.material_slot.material = mate
        common.setup_material(mate)

        if compat.IS_LEGACY:
            cm3d2_data.MaterialHandler.apply_to_old(context, mate, mat_data, prefs.is_replace_cm3d2_tex, self.is_decorate, prefs.mate_unread_same_value)
        else:
            cm3d2_data.MaterialHandler.apply_to(context, mate, mat_data, prefs.is_replace_cm3d2_tex)

        if not edit_text:
            edit_text = context.blend_data.texts.new(os.path.basename(mat_data.name))
            context.area.type = 'TEXT_EDITOR'
            context.space_data.text = edit_text

        edit_text.write(mat_data.to_text())
        edit_text.current_line_index = 0
        return {'FINISHED'}


# テキストメニューに項目を登録
def TEXT_MT_text(self, context):
    self.layout.separator()
    self.layout.operator(CNV_OT_import_cm3d2_mate_text.bl_idname, icon_value=common.kiss_icon())
