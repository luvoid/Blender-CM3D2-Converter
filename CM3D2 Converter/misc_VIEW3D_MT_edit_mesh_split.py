import bpy
import bmesh
from . import common
from . import compat

# メニュー等に項目追加
def menu_func(self, context):
    icon_id = common.kiss_icon()
    self.layout.separator()
    self.layout.label(text="CM3D2", icon_value=icon_id)
    self.layout.operator('mesh.split_sharp')

@compat.BlRegister()
class CNV_OT_split_sharp(bpy.types.Operator):
    bl_idname = 'mesh.split_sharp'
    bl_label = "Split Sharp Edges"
    bl_description = "Split all edges marked as sharp"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'EDIT'

    def execute(self, context):
        ob = context.active_object
        me = ob.data

        bpy.ops.mesh.select_all(action='DESELECT')

        bm = bmesh.from_edit_mesh(me)

        sharp_edges = list()
        for edge in bm.edges:
            if not edge.smooth:
                sharp_edges.append(edge)

        changed = bmesh.ops.split_edges(bm, edges=sharp_edges)
        for edge in changed['edges']:
            edge.select_set(True)
        
        return {'FINISHED'}