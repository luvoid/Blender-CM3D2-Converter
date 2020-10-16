# 「3Dビュー」エリア → 追加(Shift+A) → CM3D2
import os
import bpy
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    self.layout.separator()
    self.layout.menu('MISC_INFO_MT_add_cm3d2', icon_value=common.kiss_icon())


# サブメニュー
@compat.BlRegister()
class misc_INFO_MT_add_cm3d2(bpy.types.Menu):
    bl_idname = 'MISC_INFO_MT_add_cm3d2'
    bl_label = "CM3D2"

    def draw(self, context):
        self.layout.operator('wm.append_cm3d2_figure', text="body001", icon_value=common.kiss_icon()).object_name = "body001.body"
        self.layout.separator()
        self.layout.operator('wm.append_cm3d2_figure', text="乳袋防止素体", icon=compat.icon('PIVOT_INDIVIDUAL')).object_name = "乳袋防止素体"
        self.layout.separator()
        self.layout.operator('wm.append_cm3d2_figure', text="Tスタンス素体", icon='MOD_ARMATURE').object_name = "Tスタンス素体"
        self.layout.operator('wm.append_cm3d2_figure', text="Tスタンス素体 足のみ", icon='SOUND').object_name = "Tスタンス素体 足のみ"
        self.layout.operator('wm.append_cm3d2_figure', text="Tスタンス素体 手のみ", icon='OUTLINER_DATA_ARMATURE').object_name = "Tスタンス素体 手のみ"
        self.layout.separator()
        self.layout.operator('wm.append_cm3d2_figure', text="anm出力用リグ", icon='OUTLINER_OB_ARMATURE').object_name = "anm出力用リグ・身体メッシュ"
        self.layout.operator('wm.append_cm3d2_figure', text="anm出力用リグ(男)", icon='ARMATURE_DATA').object_name = "anm出力用リグ(男)・身体メッシュ"


@compat.BlRegister()
class CNV_OT_append_cm3d2_figure(bpy.types.Operator):
    bl_idname = 'wm.append_cm3d2_figure'
    bl_label = "CM3D2用の素体をインポート"
    bl_description = "CM3D2関係の素体を現在のシーンにインポートします"
    bl_options = {'REGISTER', 'UNDO'}

    object_name = bpy.props.StringProperty(name="素体名")

    def execute(self, context):
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
        if bpy.ops.object.select_all.poll():
            bpy.ops.object.select_all(action='DESELECT')

        blend_path = os.path.join(os.path.dirname(__file__), "append_data.blend")
        with context.blend_data.libraries.load(blend_path) as (data_from, data_to):
            data_to.objects = [self.object_name]

        ob = data_to.objects[0]
        compat.link(context.scene, ob)
        compat.set_active(context, ob)
        compat.set_select(ob, True)

        for mod in ob.modifiers:
            if mod.type == 'ARMATURE':
                compat.link(context.scene, mod.object)
                compat.set_select(mod.object, True)

        return {'FINISHED'}
