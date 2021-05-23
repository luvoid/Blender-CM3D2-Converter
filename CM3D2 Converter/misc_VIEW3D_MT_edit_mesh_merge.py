# XXX : This file is not used
import bpy
import bmesh
from . import common
from . import compat

# メニュー等に項目追加
def menu_func(self, context):
    icon_id = common.kiss_icon()
    self.layout.separator()
    self.layout.label(text="CM3D2", icon_value=icon_id)
    self.layout.operator('mesh.remove_and_mark_doubles')

@compat.BlRegister()
class CNV_OT_remove_and_mark_doubles(bpy.types.Operator):
    bl_idname = 'mesh.remove_and_mark_doubles'
    bl_label = "Remove and Mark Doubles"
    bl_description = "Remove doubles while marking merged geometry as seams and/or sharp edges"
    bl_options = {'REGISTER', 'UNDO'}

    threshold        = bpy.props.FloatProperty(name="Merge Distance", default=0.0001, description="Maximum distance between elements to merge")
    normal_threshold = bpy.props.FloatProperty(name="Normal Angle"  , default=0.0000, description="Maximum angle between element's normals to mark sharp")
    use_unselected   = bpy.props.FloatProperty(name="Unselected"    , default=False , description="Merge selected to other unselected vertices")
    mark_seams       = bpy.props.FloatProperty(name="Mark Seams"    , default=True  , description="Mark seams")
    mark_sharp       = bpy.props.FloatProperty(name="Mark Sharp"    , default=True  , description="Mark sharp")
    mark_freestyle   = bpy.props.FloatProperty(name="Mark Freestyle", default=True  , description="Mark freestyle")
    
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == 'MESH' and ob.mode == 'EDIT'

    def execute(self, context):
        ob = context.active_object
        me = ob.data

        #bpy.ops.mesh.select_all(action='DESELECT')

        bm = bmesh.from_edit_mesh(me)

        selected_verts = bm.verts if len(bm.select_history) <= 0 else set( filter(lambda v : v.select, bm.verts) )
        search_verts   = bm.verts if self.use_unselected         else selected_verts  

        targetmap = bmesh.ops.find_doubles(bm, verts=search_verts, dist=self.threshold,
            keep_verts=selected_verts if use_unselected else None)['targetmap']
        
        print(targetmap)
        return {'FINISHED'}

        comparison_data = list(hash(repr(v['co']) + " " + repr(v['normal'])) for v in vertex_data)
        comparison_counter = Counter(comparison_data)
        comparison_data = list((comparison_counter[h] > 1) for h in comparison_data)
        del comparison_counter

        selected_edges = bm.edges if len(bm.select_history) <= 0 else set( filter(lambda e : e.verts[0].select or e.verts[1].select, bm.edges) )
        for edge in bm.edges:
            if edge.is_boundary:
                
                

        changed = bmesh.ops.split_edges(bm, edges=sharp_edges)
        for edge in changed['edges']:
            edge.select_set(True)

        # メッシュ整頓
        pre_mesh_select_mode = context.tool_settings.mesh_select_mode[:]
        if self.is_sharp:
            context.tool_settings.mesh_select_mode = (False, True, False)
            bpy.ops.object.mode_set(mode='EDIT')
        
            bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True, use_multi_face=False, use_non_contiguous=False, use_verts=False)
            bpy.ops.mesh.mark_sharp(use_verts=False)
        
            bpy.ops.object.mode_set(mode='OBJECT')
            context.tool_settings.mesh_select_mode = pre_mesh_select_mode
        if self.is_remove_doubles:
            pre_mesh_select_mode = context.tool_settings.mesh_select_mode[:]
            context.tool_settings.mesh_select_mode = (True, False, False)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
        
            for is_comparison, vert in zip(comparison_data, me.vertices):
                if is_comparison:
                    vert.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.remove_doubles(threshold=0.000001)
        
            if self.is_sharp:
                context.tool_settings.mesh_select_mode = (False, True, False)
                bpy.ops.mesh.select_non_manifold(extend=False, use_wire=True, use_boundary=True, use_multi_face=False, use_non_contiguous=False, use_verts=False)
                bpy.ops.mesh.mark_sharp(use_verts=False)
        
            bpy.ops.object.mode_set(mode='OBJECT')
        context.tool_settings.mesh_select_mode = pre_mesh_select_mode
        if self.is_seam:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.select_all(action='SELECT')
            bpy.ops.uv.seams_from_islands()

        
        
        return {'FINISHED'}