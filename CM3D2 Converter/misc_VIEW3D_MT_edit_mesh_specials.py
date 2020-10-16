# 「3Dビュー」エリア → メッシュ編集モード → 「W」キー
import bpy
import bmesh
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    icon_id = common.kiss_icon()
    self.layout.separator()
    self.layout.operator('mesh.selected_mesh_vertex_group_blur', icon_value=icon_id)
    self.layout.separator()
    self.layout.operator('mesh.selected_face_sort_front', text="Draw this object first", icon_value=icon_id).is_back = False
    self.layout.operator('mesh.selected_face_sort_front', text="Draw this object further back", icon_value=icon_id).is_back = True


@compat.BlRegister()
class CNV_OT_selected_mesh_sort_front(bpy.types.Operator):
    bl_idname = 'mesh.selected_face_sort_front'
    bl_label = "The drawing order of the selected surface is set to the forefront"
    bl_description = "Rearranges the drawing order of the currently selected face to the front / back"
    bl_options = {'REGISTER', 'UNDO'}

    is_back = bpy.props.BoolProperty(name="Back")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'EDIT'

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        bm.faces.ensure_lookup_table()

        selected_face_indexs = []
        other_face_indexs = []
        for face in bm.faces:
            if face.select:
                selected_face_indexs.append(face.index)
            else:
                other_face_indexs.append(face.index)

        output_face_indexs = []
        if not self.is_back:
            output_face_indexs = other_face_indexs + selected_face_indexs
        else:
            output_face_indexs = selected_face_indexs + other_face_indexs

        for for_index, sorted_index in enumerate(output_face_indexs):
            bm.faces[sorted_index].index = for_index

        bm.faces.sort()
        bmesh.update_edit_mesh(me)
        return {'FINISHED'}
