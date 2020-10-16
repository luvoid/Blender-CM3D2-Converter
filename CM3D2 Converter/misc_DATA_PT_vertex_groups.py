# 「プロパティ」エリア → 「メッシュデータ」タブ → 「頂点グループ」パネル
import re
import bpy
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    ob = context.active_object
    if not ob or len(ob.vertex_groups) == 0 and ob.type != 'MESH':
        return

    flag = False
    for vertex_group in ob.vertex_groups:
        if not flag and re.search(r'[_ ]([rRlL])[_ ]', vertex_group.name):
            flag = True
        if not flag and vertex_group.name.count('*') == 1:
            if re.search(r'\.([rRlL])$', vertex_group.name):
                flag = True
        if flag:
            col = self.layout.column(align=True)
            col.label(text="Convert names for CM3D2", icon_value=common.kiss_icon())
            row = col.row(align=True)
            row.operator('object.decode_cm3d2_vertex_group_names', icon='BLENDER', text="CM3D2 → Blender")
            row.operator('object.encode_cm3d2_vertex_group_names', icon_value=common.kiss_icon(), text="Blender → CM3D2")
            break


@compat.BlRegister()
class CNV_OT_decode_cm3d2_vertex_group_names(bpy.types.Operator):
    bl_idname = 'object.decode_cm3d2_vertex_group_names'
    bl_label = "Convert Vertex Group Names for Blender"
    bl_description = "Names are converted for use with Blender's mirror functions."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        import re
        ob = context.active_object
        if ob and ob.type == 'MESH':
            if ob.vertex_groups.active:
                for vg in ob.vertex_groups:
                    if re.search(r'[_ ]([rRlL])[_ ]', vg.name):
                        return True
        return False

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        convert_count = 0
        context.window_manager.progress_begin(0, len(ob.vertex_groups))
        for vg_index, vg in enumerate(ob.vertex_groups[:]):
            context.window_manager.progress_update(vg_index)
            vg_name = common.decode_bone_name(vg.name)
            if vg_name != vg.name:
                if vg_name in ob.vertex_groups:
                    target_vg = ob.vertex_groups[vg_name]
                    for vert in me.vertices:
                        try:
                            weight = vg.weight(vert.index)
                        except:
                            weight = 0.0
                        try:
                            target_weight = target_vg.weight(vert.index)
                        except:
                            target_weight = 0.0
                        if 0.0 < weight + target_weight:
                            target_vg.add([vert.index], weight + target_weight, 'REPLACE')
                    ob.vertex_groups.remove(vg)
                else:
                    vg.name = vg_name
                convert_count += 1
        if convert_count == 0:
            self.report(type={'WARNING'}, message="A Name that could not be converted was found. Mission Failed.")
        else:
            self.report(type={'INFO'}, message="Vertex group names were converted for Blender. Mission Accomplished.")
        context.window_manager.progress_end()
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_encode_cm3d2_vertex_group_names(bpy.types.Operator):
    bl_idname = 'object.encode_cm3d2_vertex_group_names'
    bl_label = "Convert vertex group names for CM3D2"
    bl_description = "Converts bone names for CM3D2."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob and ob.type == 'MESH' and ob.vertex_groups.active:
            for vg in ob.vertex_groups:
                if vg.name.count('*') == 1 and re.search(r'\.([rRlL])$', vg.name):
                    return True
        return False

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        convert_count = 0
        context.window_manager.progress_begin(0, len(ob.vertex_groups))
        for vg_index, vg in enumerate(ob.vertex_groups[:]):
            context.window_manager.progress_update(vg_index)
            vg_name = common.encode_bone_name(vg.name)
            if vg_name != vg.name:
                if vg_name in ob.vertex_groups:
                    target_vg = ob.vertex_groups[vg_name]
                    for vert in me.vertices:
                        try:
                            weight = vg.weight(vert.index)
                        except:
                            weight = 0.0

                        try:
                            target_weight = target_vg.weight(vert.index)
                        except:
                            target_weight = 0.0
                        if 0.0 < weight + target_weight:
                            target_vg.add([vert.index], weight + target_weight, 'REPLACE')
                    ob.vertex_groups.remove(vg)
                else:
                    vg.name = vg_name
                convert_count += 1
        if convert_count == 0:
            self.report(type={'WARNING'}, message="A Name that could not be converted was found. Mission Failed.")
        else:
            self.report(type={'INFO'}, message="Names were converted for CM3D2. Mission Accomplished")
        context.window_manager.progress_end()
        return {'FINISHED'}
