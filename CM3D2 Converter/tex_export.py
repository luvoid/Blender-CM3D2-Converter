import bpy
import os
import struct
from . import common
from . import compat
from .translations.pgettext_functions import *


@compat.BlRegister()
class CNV_OT_export_cm3d2_tex(bpy.types.Operator):
    bl_idname = 'image.export_cm3d2_tex'
    bl_label = "texファイルを保存"
    bl_description = "CM3D2で使用されるテクスチャファイル(.tex)として保存します"
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".tex"
    filter_glob = bpy.props.StringProperty(default="*.tex", options={'HIDDEN'})

    is_backup = bpy.props.BoolProperty(name="ファイルをバックアップ", default=True, description="ファイルに上書きする場合にバックアップファイルを複製します")

    version = bpy.props.EnumProperty(
        name="ファイルバージョン",
        items=[
            ('1011', '1011', 'COM3D2 1.13 or later', 'NONE', 0),
            ('1010', '1010', 'CM3D2 1.49 ～ or COM3D2', 'NONE', 1),
            ('1000', '1000', '旧フォーマット', 'NONE', 2),
        ], default='1010')
    path = bpy.props.StringProperty(name="パス", default=common.BASE_PATH_TEX + "/*.png")

    @classmethod
    def poll(cls, context):
        if hasattr(context, 'edit_image'):
            img = context.edit_image
            if img and (len(img.pixels) or img.source == 'VIEWER'):
                return True
        return False

    def invoke(self, context, event):
        prefs = common.preferences()
        img = context.edit_image
        if img.filepath:
            prefs.tex_export_path = bpy.path.abspath(img.filepath)
        if prefs.tex_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.tex_default_path, common.remove_serial_number(img.name), "tex")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.tex_export_path, common.remove_serial_number(img.name), "tex")
        self.is_backup = bool(prefs.backup_ext)
        self.path = img.get('cm3d2_path')
        if self.path is None:
            self.path = common.get_tex_cm3d2path(self.filepath)
            img['cm3d2_path'] = self.path

        if 'tex Name' in img:
            self.filepath = os.path.join(os.path.dirname(self.filepath), img['tex Name'])
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        row = self.layout.row()
        row.prop(self, 'is_backup', icon='FILE_BACKUP')
        if not common.preferences().backup_ext:
            row.enabled = False
        self.layout.prop(self, 'version', icon='LINENUMBERS_ON')
        self.layout.prop(self, 'path', icon='ANIM')

    def execute(self, context):
        common.preferences().tex_export_path = self.filepath

        try:
            with common.open_temporary(self.filepath, 'wb', is_backup=self.is_backup) as file:
                version_num = int(self.version)
                self.write_texture(context, file, version_num)
            self.report(type={'INFO'}, message="texファイルを出力しました。" + self.filepath)

        except common.CM3D2ExportException as e:
            self.report(type={'ERROR'}, message=str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report(type={'ERROR'}, message=f_tip_("texファイルの出力に失敗しました。{}", str(e)))
            return {'CANCELLED'}

        return {'FINISHED'}

    def write_texture(self, context, file, version):
        # とりあえずpngで保存
        img = context.edit_image
        if img.source != 'VIEWER':
            temp_path = self.filepath + ".temp.png"
        else:
            temp_path = os.path.splitext(self.filepath)[0] + ".png"
        pre_filepath = bpy.path.abspath(img.filepath)
        pre_source = img.source
        override = context.copy()
        override['edit_image'] = img
        try:
            save_as_render = True if pre_source == 'VIEWER' else False
            copy = True if pre_source == 'VIEWER' else False
            bpy.ops.image.save_as(override, save_as_render=save_as_render, copy=copy, filepath=temp_path, relative_path=True, show_multiview=False, use_multiview=False)
            is_remove = True
        except:
            temp_path = bpy.path.abspath(img.filepath)
            if os.path.exists(temp_path):
                is_remove = False
            else:
                raise common.CM3D2ExportException("PNGファイルの取得に失敗しました")
        if pre_source != 'VIEWER':
            img.filepath = pre_filepath
            img.source = pre_source

        # pngバイナリを全て読み込み
        with open(temp_path, 'rb') as temp_file:
            temp_data = temp_file.read()
        # 一時ファイルを削除
        if is_remove:
            os.remove(temp_path)

        # 本命ファイルに書き込み
        common.write_str(file, 'CM3D2_TEX')
        file.write(struct.pack('<i', version))
        common.write_str(file, self.path)
        if version >= 1010:
            if version >= 1011:
                uv_rects = bpy.types.Scene.MyUVRects if hasattr(bpy.types.Scene, 'MyUVRects') else None
                num_rects = len(uv_rects) if uv_rects else 0
                file.write(struct.pack('<i', num_rects))
                if num_rects > 0:
                    for uv_rect in uv_rects:
                        file.write( struct.pack('<4f', uv_rect[0], uv_rect[1], uv_rect[2], uv_rect[3]) )

            width, height = img.size
            file.write(struct.pack('<i', width))
            file.write(struct.pack('<i', height))
            file.write(struct.pack('<i', 5))  # tex_format TODO ダイアログで指定
        file.write(struct.pack('<i', len(temp_data)))
        file.write(temp_data)


# メニューを登録する関数
def menu_func(self, context):
    self.layout.operator(CNV_OT_export_cm3d2_tex.bl_idname, icon_value=common.kiss_icon())
