# 「プロパティ」エリア → 「オブジェクト」タブ → 「トランスフォーム」パネル
import bpy
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    self.layout.operator('object.sync_object_transform', icon_value=common.kiss_icon())


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
        target_ob = context.active_object
        for ob in context.selected_objects:
            if target_ob.name != ob.name:
                source_ob = ob
                break

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
