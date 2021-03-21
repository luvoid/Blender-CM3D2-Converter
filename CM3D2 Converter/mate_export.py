import bpy
from . import common
from . import compat
from . import cm3d2_data
from .translations.pgettext_functions import *


@compat.BlRegister()
class CNV_OT_export_cm3d2_mate(bpy.types.Operator):
    bl_idname = 'material.export_cm3d2_mate'
    bl_label = "mateとして保存"
    bl_description = "表示しているマテリアルをmateファイルとして保存します"
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".mate"
    filter_glob = bpy.props.StringProperty(default="*.mate", options={'HIDDEN'})

    is_backup = bpy.props.BoolProperty(name="ファイルをバックアップ", default=True, description="ファイルに上書きする場合にバックアップファイルを複製します")

    version = bpy.props.IntProperty(name="ファイルバージョン", default=1000, min=1000, max=1111, soft_min=1000, soft_max=1111, step=1)
    name1 = bpy.props.StringProperty(name="名前1")
    name2 = bpy.props.StringProperty(name="名前2")

    @classmethod
    def poll(cls, context):
        mate = getattr(context, 'material')
        if mate:
            if 'shader1' in mate and 'shader2' in mate:
                return True
        return False

    def invoke(self, context, event):
        prefs = common.preferences()
        mate = context.material
        if prefs.mate_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.mate_default_path, mate.name.lower(), "mate")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.mate_export_path, mate.name.lower(), "mate")
        self.is_backup = bool(prefs.backup_ext)
        self.name1 = common.remove_serial_number(mate.name.lower())
        self.name2 = common.remove_serial_number(mate.name)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        row = self.layout.row()
        row.prop(self, 'is_backup', icon='FILE_BACKUP')
        if not common.preferences().backup_ext:
            row.enabled = False
        self.layout.prop(self, 'version', icon='LINENUMBERS_ON')
        self.layout.prop(self, 'name1', icon='SORTALPHA')
        self.layout.prop(self, 'name2', icon='SORTALPHA')

    def execute(self, context):
        common.preferences().mate_export_path = self.filepath

        try:
            writer = common.open_temporary(self.filepath, 'wb', is_backup=self.is_backup)
        except:
            self.report(type={'ERROR'}, message=f_tip_("ファイルを開くのに失敗しました、アクセス不可かファイルが存在しません。file={}", self.filepath))
            return {'CANCELLED'}

        try:
            with writer:
                mate = context.material
                if compat.IS_LEGACY:
                    mat_data = cm3d2_data.MaterialHandler.parse_mate_old(mate, remove_serial=True)
                else:
                    mat_data = cm3d2_data.MaterialHandler.parse_mate(mate, remove_serial=True)

                mat_data.version = self.version
                mat_data.name1 = self.name1
                mat_data.name2 = self.name2

                mat_data.write(writer)

        except common.CM3D2ExportException as e:
            self.report(type={'ERROR'}, message=str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_export_cm3d2_mate_text(bpy.types.Operator):
    bl_idname = 'text.export_cm3d2_mate_text'
    bl_label = "mateとして保存"
    bl_description = "表示しているテキストデータをmateファイルとして保存します"
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".mate"
    filter_glob = bpy.props.StringProperty(default="*.mate", options={'HIDDEN'})

    is_backup = bpy.props.BoolProperty(name="ファイルをバックアップ", default=True, description="ファイルに上書きする場合にバックアップファイルを複製します")

    version = bpy.props.IntProperty(name="ファイルバージョン", default=1000, min=1000, max=1111, soft_min=1000, soft_max=1111, step=1)
    name1 = bpy.props.StringProperty(name="名前1")
    name2 = bpy.props.StringProperty(name="名前2")

    @classmethod
    def poll(cls, context):
        edit_text = getattr(context, 'edit_text')
        if edit_text:
            data = edit_text.as_string()
            if len(data) < 32:
                return False
            if "\ntex\n" in data or "\ncol\n" in data or "\nf\n" in data:
                return True

        return False

    def invoke(self, context, event):
        txt = context.edit_text
        lines = txt.as_string().split('\n')
        mate_name = lines[1]
        if common.preferences().mate_default_path:
            self.filepath = common.default_cm3d2_dir(common.preferences().mate_default_path, mate_name.lower(), "mate")
        else:
            self.filepath = common.default_cm3d2_dir(common.preferences().mate_export_path, mate_name.lower(), "mate")
        try:
            self.version = int(lines[0])
        except:
            self.version = 1000
        if lines[1] != '***':
            self.name1 = lines[1]
        else:
            self.name1 = lines[2]
        self.name2 = lines[2]
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        row = self.layout.row()
        row.prop(self, 'is_backup', icon='FILE_BACKUP')
        if not common.preferences().backup_ext:
            row.enabled = False
        self.layout.prop(self, 'version', icon='LINENUMBERS_ON')
        self.layout.prop(self, 'name1', icon='SORTALPHA')
        self.layout.prop(self, 'name2', icon='SORTALPHA')

    def execute(self, context):
        common.preferences().mate_export_path = self.filepath

        try:
            text = context.edit_text.as_string()
            mat_data = cm3d2_data.MaterialHandler.parse_text(text)
        except Exception as e:
            self.report(type={'ERROR'}, message='マテリアル情報の貼付けを中止します。' + str(e))
            return {'CANCELLED'}

        try:
            file = common.open_temporary(self.filepath, 'wb', is_backup=self.is_backup)
        except:
            self.report(type={'ERROR'}, message=f_tip_("ファイルを開くのに失敗しました、アクセス不可かファイルが存在しません。file={}", self.filepath))
            return {'CANCELLED'}

        try:
            with file:
                mat_data.write(file, write_header=True)
        except Exception as e:
            self.report(type={'ERROR'}, message="mateファイルの出力に失敗、中止します。 構文を見直して下さい。" + str(e))
            return {'CANCELLED'}

        return {'FINISHED'}


# テキストメニューに項目を登録
def TEXT_MT_text(self, context):
    self.layout.operator(CNV_OT_export_cm3d2_mate_text.bl_idname, icon_value=common.kiss_icon())
