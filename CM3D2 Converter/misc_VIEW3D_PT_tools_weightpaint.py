# 「3Dビュー」エリア → 「ウェイトペイント」モード → ツールシェルフ → 「ウェイトツール」パネル
import bpy
import bmesh
import mathutils
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    icon_id = common.kiss_icon()
    box = self.layout.box()
    column = box.column(align=False)
    column.prop(context.active_object.data, 'use_paint_mask_vertex', icon='VERTEXSEL', text="Vertex selection mode")
    column.operator('mesh.selected_mesh_vertex_group_blur', text="Blur the selected part", icon_value=icon_id)
    column.operator('mesh.selected_mesh_vertex_group_calculation', text="Four arithmetic operation", icon_value=icon_id)


@compat.BlRegister()
class CNV_OT_selected_mesh_vertex_group_blur(bpy.types.Operator):
    bl_idname = 'mesh.selected_mesh_vertex_group_blur'
    bl_label = "Blur the vertex group of the selected part"
    bl_description = "Blurs the vertex groups of the selected parts."
    bl_options = {'REGISTER', 'UNDO'}

    items = [
        ('LINER', "Linear", "", 'LINCURVE', 1),
        ('TRIGONOMETRIC', "Trigonometric", "", 'SMOOTHCURVE', 2),
    ]
    smooth_method = bpy.props.EnumProperty(items=items, name="Damping type", default='TRIGONOMETRIC')

    selection_blur_range_multi = bpy.props.FloatProperty(name="Blur Range", default=4.0, min=0.0, max=100.0, soft_min=0.0, soft_max=100.0, step=50, precision=1)
    selection_blur_accuracy = bpy.props.IntProperty(name="Blur Accuracy", default=3, min=0, max=10, soft_min=1, soft_max=10)

    items = [
        ('ALL', "All", "", 'COLLAPSEMENU', 1),
        ('ACTIVE', "Active", "", 'LAYER_ACTIVE', 2),
    ]
    target_vertex_group = bpy.props.EnumProperty(items=items, name="Target vertex groups", default='ALL')
    items = [
        ('NORMAL', "Normal", "", 'BRUSH_BLUR', 1),
        ('ADD', "Add", "", 'BRUSH_DARKEN', 2),
        ('SUB', "Sub", "", 'BRUSH_LIGHTEN', 3),
    ]
    blur_mode = bpy.props.EnumProperty(items=items, name="Blur Mode", default='NORMAL')
    blur_range_multi = bpy.props.FloatProperty(name="Blur Range", default=4.0, min=0.0, max=100.0, soft_min=0.0, soft_max=100.0, step=50, precision=1)
    blur_count = bpy.props.IntProperty(name="Blur Amount", default=1, min=1, max=100, soft_min=1, soft_max=100)
    is_vertex_group_limit_total = bpy.props.BoolProperty(name="Limit total weights.", default=True)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob.type == 'MESH':
            if len(ob.vertex_groups):
                return len(ob.data.vertices) and len(ob.data.edges)
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'smooth_method')

        self.layout.label(text="Blur Selected", icon='UV_SYNC_SELECT')
        self.layout.prop(self, 'selection_blur_range_multi', text="Range | Average of side lengths ×")
        self.layout.prop(self, 'selection_blur_accuracy', text="Accuracy (number of steps)")

        self.layout.label(text="Blur Vertex Group", icon='GROUP_VERTEX')
        self.layout.prop(self, 'target_vertex_group', text="Target Group")
        self.layout.prop(self, 'blur_mode', text="Mode")
        self.layout.prop(self, 'blur_range_multi', text="Range | Average of side lengths ×")
        self.layout.prop(self, 'blur_count', text="Blur Count")
        self.layout.prop(self, 'is_vertex_group_limit_total', icon='IMGDISPLAY')

    def execute(self, context):
        class EmptyClass:
            pass

        ob = context.active_object
        me = ob.data

        pre_mode = ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        pre_selected_objects = context.selected_objects[:]
        for selected_object in pre_selected_objects:
            compat.set_select(selected_object, False)
        compat.set_select(ob, True)

        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')

        selection_ob = context.active_object
        selection_me = selection_ob.data

        for v in selection_me.vertices:
            if v.hide:
                v.hide = False
                compat.set_select(v, False)
        for e in selection_me.edges:
            if e.hide:
                e.hide = False
                compat.set_select(e, False)
        for p in selection_me.polygons:
            if p.hide:
                p.hide = False
                compat.set_select(p, False)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='INVERT')
        if context.tool_settings.mesh_select_mode[0]:
            bpy.ops.mesh.delete(type='VERT')
        elif context.tool_settings.mesh_select_mode[1]:
            bpy.ops.mesh.delete(type='EDGE')
        elif context.tool_settings.mesh_select_mode[2]:
            bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        if 1 <= self.selection_blur_accuracy:
            # quadtriはデフォルトでFalseのため、省略(2.8では代わりにngon=Trueが追加)
            bpy.ops.mesh.subdivide(
                number_cuts=self.selection_blur_accuracy,
                smoothness=0, quadcorner='INNERVERT',
                fractal=0, fractal_along_normal=0, seed=0)
        bpy.ops.object.mode_set(mode='OBJECT')

        selection_kd = mathutils.kdtree.KDTree(len(selection_me.vertices))
        for v in selection_me.vertices:
            selection_kd.insert(v.co, v.index)
        selection_kd.balance()
        common.remove_data([selection_ob, selection_me])

        compat.set_select(ob, True)
        compat.set_active(context, ob)

        bm = bmesh.new()
        bm.from_mesh(me)
        edge_lengths = [e.calc_length() for e in bm.edges]
        bm.free()
        edge_lengths.sort()
        edge_lengths_center_index = int((len(edge_lengths) - 1) * 0.5)
        average_edge_length = edge_lengths[edge_lengths_center_index]
        selection_blur_range = average_edge_length * self.selection_blur_range_multi

        vert_selection_values = [None for v in me.vertices]
        for vert in me.vertices:
            co, index, dist = selection_kd.find(vert.co)
            if dist <= selection_blur_range + 0.00001:
                if 0 < selection_blur_range:
                    if self.smooth_method == 'TRIGONOMETRIC':
                        value = common.trigonometric_smooth(1.0 - (dist / selection_blur_range))
                    else:
                        value = 1.0 - (dist / selection_blur_range)
                    vert_selection_values[vert.index] = value
                else:
                    vert_selection_values[vert.index] = 1.0

        """
        # 頂点カラーで選択状態を確認
        preview_vertex_color = me.vertex_colors.new()
        for loop in me.loops:
            v = vert_selection_values[loop.vertex_index]
            if v != None:
                preview_vertex_color.data[loop.index].color = (v, v, v)
            else:
                preview_vertex_color.data[loop.index].color = (0, 0, 0)
        """

        kd = mathutils.kdtree.KDTree(len(me.vertices))
        # [kd.insert(v.co, v.index) for v in me.vertices]
        for v in me.vertices:
            kd.insert(v.co, v.index)
        kd.balance()

        blur_range = average_edge_length * self.blur_range_multi

        for i in range(self.blur_count):

            pre_vert_weights = [[0.0 for vg in ob.vertex_groups] for v in me.vertices]
            for vert in me.vertices:
                for vge in vert.groups:
                    pre_vert_weights[vert.index][vge.group] = vge.weight

            for vert in me.vertices:
                selection_value = vert_selection_values[vert.index]
                if selection_value is None:
                    continue

                near_infos = []
                total_effect = 0.0
                for co, index, dist in kd.find_range(vert.co, blur_range):
                    ec = EmptyClass()
                    ec.index = index
                    if 0 < blur_range:
                        raw_effect = 1.0 - (dist / blur_range)
                        if self.smooth_method == 'TRIGONOMETRIC':
                            ec.effect = common.trigonometric_smooth(raw_effect)
                        else:
                            ec.effect = raw_effect
                    else:
                        ec.effect = 1.0
                    total_effect += ec.effect
                    near_infos.append(ec)

                new_vert_weight = [0.0 for vg in ob.vertex_groups]
                for ec in near_infos:
                    pre_vert_weight = pre_vert_weights[ec.index]
                    weight_multi = ec.effect / total_effect
                    for vg_index, near_vert_pre_weight_value in enumerate(pre_vert_weight):
                        current_vert_pre_weight_value = pre_vert_weights[vert.index][vg_index]

                        if self.blur_mode == 'NORMAL':
                            send_weight_value = near_vert_pre_weight_value
                        elif self.blur_mode == 'ADD':
                            if current_vert_pre_weight_value < near_vert_pre_weight_value:
                                send_weight_value = near_vert_pre_weight_value
                            else:
                                send_weight_value = current_vert_pre_weight_value
                        elif self.blur_mode == 'SUB':
                            if near_vert_pre_weight_value < current_vert_pre_weight_value:
                                send_weight_value = near_vert_pre_weight_value
                            else:
                                send_weight_value = current_vert_pre_weight_value

                        new_vert_weight[vg_index] += send_weight_value * weight_multi

                for vg in ob.vertex_groups:
                    if self.target_vertex_group == 'ACTIVE' and ob.vertex_groups.active.name != vg.name: continue
                    if vg.lock_weight:
                        continue

                    pre_weight = pre_vert_weights[vert.index][vg.index]
                    new_weight = new_vert_weight[vg.index]
                    result_weight = (pre_weight * (1.0 - selection_value)) + (new_weight * selection_value)

                    if 0.0 < result_weight:
                        vg.add([vert.index], result_weight, 'REPLACE')
                    else:
                        vg.remove([vert.index])

        if self.is_vertex_group_limit_total:
            bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)

        bpy.ops.object.mode_set(mode=pre_mode)
        for selected_object in pre_selected_objects:
            compat.set_select(selected_object, True)
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_selected_mesh_vertex_group_calculation(bpy.types.Operator):
    bl_idname = 'mesh.selected_mesh_vertex_group_calculation'
    bl_label = "Four arithmetic operations on the vertex groups of the selection"
    bl_description = "Applies four arithmetic operations to the vertex groups of selection."
    bl_options = {'REGISTER', 'UNDO'}

    items = [
        ('LINER', "Iinear", "", 'LINCURVE', 1),
        ('TRIGONOMETRIC', "Trigonometric", "", 'SMOOTHCURVE', 2),
    ]
    smooth_method = bpy.props.EnumProperty(items=items, name="Smooth Methid", default='TRIGONOMETRIC')

    selection_blur_range_multi = bpy.props.FloatProperty(name="Blur Range", default=4.0, min=0.0, max=100.0, soft_min=0.0, soft_max=100.0, step=50, precision=1)
    selection_blur_accuracy = bpy.props.IntProperty(name="Blur Accuracy", default=3, min=0, max=10, soft_min=1, soft_max=10)

    items = [
        ('ACTIVE', "Active", "", 'LAYER_ACTIVE', 1),
    ]
    target_vertex_group = bpy.props.EnumProperty(items=items, name="Target Vertex Group", default='ACTIVE')
    items = [
        ('ADD', "Add", "", 'ZOOMIN', 1),
        ('SUB', "Sub", "", 'ZOOMOUT', 2),
        ('MULTI', "Multi", "", 'X', 3),
        ('DIV', "Div", "", 'FULLSCREEN_EXIT', 4),
    ]
    calculation_mode = bpy.props.EnumProperty(items=items, name="Arithmetic operation mode", default='ADD')
    calculation_value = bpy.props.FloatProperty(name="Value", default=1.0, min=-100.0, max=100.0, soft_min=-100.0, soft_max=100.0, step=10, precision=1)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob.type == 'MESH':
            return len(ob.vertex_groups) > 0
        return False

    def draw(self, context):
        self.layout.label(text="Blur the selection of the vertex groups.", icon='UV_SYNC_SELECT')
        self.layout.prop(self, 'smooth_method')
        self.layout.prop(self, 'selection_blur_range_multi', text="Range | Average of side length ×")
        self.layout.prop(self, 'selection_blur_accuracy', text="Accuracy (Steps)")

        self.layout.label(text="Four arithmetic operations", icon='BRUSH_ADD')
        self.layout.prop(self, 'target_vertex_group', text="Target Group")
        self.layout.prop(self, 'calculation_mode', text="Mode")
        self.layout.prop(self, 'calculation_value', text="Value")

        calculation_text = "Expression: Original weight "
        if self.calculation_mode == 'ADD':
            calculation_text += "＋"
        elif self.calculation_mode == 'SUB':
            calculation_text += "－"
        elif self.calculation_mode == 'MULTI':
            calculation_text += "×"
        elif self.calculation_mode == 'DIV':
            calculation_text += "÷"
        calculation_text += " " + str(round(self.calculation_value, 1))
        self.layout.label(text=calculation_text)

    def execute(self, context):
        class EmptyClass:
            pass

        if self.calculation_mode == 'DIV' and self.calculation_value == 0.0:
            self.report(type={'ERROR'}, message="Cannot divide by zero, Aborting.")
            return {'CANCELLED'}

        ob = context.active_object
        me = ob.data

        pre_mode = ob.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        pre_selected_objects = context.selected_objects[:]
        for selected_object in pre_selected_objects:
            compat.set_select(selected_object, False)
        compat.set_select(ob, True)

        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')

        selection_ob = context.active_object
        selection_me = selection_ob.data

        for v in selection_me.vertices:
            if v.hide:
                v.hide = False
                compat.set_select(v, False)
        for e in selection_me.edges:
            if e.hide:
                e.hide = False
                compat.set_select(e, False)
        for p in selection_me.polygons:
            if p.hide:
                p.hide = False
                compat.set_select(p, False)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='INVERT')
        if context.tool_settings.mesh_select_mode[0]:
            bpy.ops.mesh.delete(type='VERT')
        elif context.tool_settings.mesh_select_mode[1]:
            bpy.ops.mesh.delete(type='EDGE')
        elif context.tool_settings.mesh_select_mode[2]:
            bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        if 1 <= self.selection_blur_accuracy:
            bpy.ops.mesh.subdivide(number_cuts=self.selection_blur_accuracy, smoothness=0, quadcorner='INNERVERT', fractal=0, fractal_along_normal=0, seed=0)
        bpy.ops.object.mode_set(mode='OBJECT')

        selection_kd = mathutils.kdtree.KDTree(len(selection_me.vertices))
        [selection_kd.insert(v.co, v.index) for v in selection_me.vertices]
        selection_kd.balance()
        common.remove_data([selection_ob, selection_me])

        compat.set_select(ob, True)
        compat.set_active(context, ob)

        bm = bmesh.new()
        bm.from_mesh(me)
        edge_lengths = [e.calc_length() for e in bm.edges]
        bm.free()
        edge_lengths.sort()
        edge_lengths_center_index = int((len(edge_lengths) - 1) * 0.5)
        average_edge_length = edge_lengths[edge_lengths_center_index]
        selection_blur_range = average_edge_length * self.selection_blur_range_multi

        vert_selection_values = [None for v in me.vertices]
        for vert in me.vertices:
            co, index, dist = selection_kd.find(vert.co)
            if dist <= selection_blur_range + 0.00001:
                if 0 < selection_blur_range:
                    if self.smooth_method == 'TRIGONOMETRIC':
                        value = common.trigonometric_smooth(1.0 - (dist / selection_blur_range))
                    else:
                        value = 1.0 - (dist / selection_blur_range)
                    vert_selection_values[vert.index] = value
                else:
                    vert_selection_values[vert.index] = 1.0

        """
        # 頂点カラーで選択状態を確認
        preview_vertex_color = me.vertex_colors.new()
        for loop in me.loops:
            v = vert_selection_values[loop.vertex_index]
            if v != None:
                preview_vertex_color.data[loop.index].color = (v, v, v)
            else:
                preview_vertex_color.data[loop.index].color = (0, 0, 0)
        """

        for vert in me.vertices:
            effect = vert_selection_values[vert.index]
            if effect is None:
                continue

            pre_vert_weight = 0.0
            for vge in vert.groups:
                if ob.vertex_groups.active.index == vge.group:
                    pre_vert_weight = vge.weight

            if self.calculation_mode == 'ADD':
                new_vert_weight = pre_vert_weight + self.calculation_value
            elif self.calculation_mode == 'SUB':
                new_vert_weight = pre_vert_weight - self.calculation_value
            elif self.calculation_mode == 'MULTI':
                new_vert_weight = pre_vert_weight * self.calculation_value
            elif self.calculation_mode == 'DIV':
                new_vert_weight = pre_vert_weight / self.calculation_value

            if new_vert_weight < 0.0:
                new_vert_weight = 0.0
            elif 1.0 < new_vert_weight:
                new_vert_weight = 1.0

            new_vert_weight = (pre_vert_weight * (1.0 - effect)) + (new_vert_weight * effect)

            if 0.0 < new_vert_weight:
                ob.vertex_groups.active.add([vert.index], new_vert_weight, 'REPLACE')
            else:
                ob.vertex_groups.active.remove([vert.index])

        bpy.ops.object.mode_set(mode=pre_mode)
        for selected_object in pre_selected_objects:
            compat.set_select(selected_object, True)
        return {'FINISHED'}
