import bpy
import bmesh
import math
import mathutils
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    row = self.layout.row()
    row.operator('anim.convert_to_cm3d2_interpolation', icon_value=common.kiss_icon())


def check_fcurve_has_selected_keyframe(fcurve: bpy.types.FCurve) -> bool:
        for keyframe in fcurve.keyframe_points:
            if keyframe.select_control_point or keyframe.select_left_handle or keyframe.select_right_handle:
                return True
        return False

REPORTS = []

@compat.BlRegister()
class CNV_OT_FCURVE_convert_to_cm3d2_interpolation(bpy.types.Operator):
    bl_idname = 'fcurve.convert_to_cm3d2_interpolation'
    bl_label = "Convert to CM3D2 Interpolation"
    bl_description = "Convert keyframes to be compatible with CM3D2 Interpolation"
    bl_options = {'REGISTER', 'UNDO'}

    only_selected = bpy.props.BoolProperty(name="Only Selected", default=True)
    keep_reports  = bpy.props.BoolProperty(name="Keep Reports",  default=False, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        fcurve = context.active_editable_fcurve
        return fcurve
    
    def invoke(self, context, event):
        fcurve = context.active_editable_fcurve
        self.only_selected = check_fcurve_has_selected_keyframe(fcurve)
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        self.layout.prop(self, 'only_selected')

    def do_report(self, **kwargs):
        if self.keep_reports:
            REPORTS.append(kwargs)
        else:
            self.report(**kwargs)

    @staticmethod
    def get_slope_vector(from_keyframe: bpy.types.Keyframe, to_keyframe: bpy.types.Keyframe, interpolation=None, backwards=None):
        if not to_keyframe:
            interpolation = 'BEZIER'
        else:
            if backwards == None:
                # Figure out which keyframe is in charge of controlling the slope
                backwards = to_keyframe.co[0] < from_keyframe.co[0]
            master_keyframe = to_keyframe if backwards else from_keyframe
            interpolation = interpolation or master_keyframe.interpolation
        
        if   interpolation == 'BEZIER':
            if backwards:
                slope_vec = mathutils.Vector(from_keyframe.handle_left ) - mathutils.Vector(from_keyframe.co)
            else:
                slope_vec = mathutils.Vector(from_keyframe.handle_right) - mathutils.Vector(from_keyframe.co)
        elif interpolation == 'LINEAR':
            slope_vec = mathutils.Vector(to_keyframe.co) - mathutils.Vector(from_keyframe.co)
        elif interpolation == 'CONSTANT':
            if backwards:
                slope_vec = mathutils.Vector(to_keyframe.co) - mathutils.Vector(from_keyframe.co)
                slope_vec.x /= 3
            else:
                slope_vec = mathutils.Vector( (1, 0) )
        elif interpolation == 'CONSTANT':
            if backwards:
                slope_vec = mathutils.Vector(to_keyframe.co) - mathutils.Vector(from_keyframe.co)
                slope_vec.x /= 3
            else:
                slope_vec = mathutils.Vector( (1, 0) )
        elif interpolation == 'CONSTANT':
            if backwards:
                slope_vec = mathutils.Vector(to_keyframe.co) - mathutils.Vector(from_keyframe.co)
                slope_vec.x /= 3
            else:
                slope_vec = mathutils.Vector( (1, 0) )
        elif interpolation in {'SINE', 'QUAD', 'CUBIC', 'QUART', 'QUINT'}:#, 'EXPO', 'CIRC'}: # Easing by strength
            easing = 'EASE_IN' if master_keyframe.easing == 'AUTO' else master_keyframe.easing
            if (   (                  easing == 'EASE_IN_OUT' )
                or (not backwards and easing == 'EASE_IN'     )
                or (    backwards and easing == 'EASE_OUT'    )
            ):
                slope_vec = mathutils.Vector( (1, 0) )
            else:
                slope_vec = mathutils.Vector(to_keyframe.co) - mathutils.Vector(from_keyframe.co)
                
                strength = dict()
                strength['SINE']  = math.sin( (1/3) * math.pi/2 )
                strength['QUAD']  = strength['SINE']  ** (1/2)
                strength['CUBIC'] = strength['QUAD']  ** (1/3)
                strength['QUART'] = strength['CUBIC'] ** (1/4)
                strength['QUINT'] = strength['QUART'] ** (1/5)
                #strength['EXPO']  = strength['QUINT'] ** (1/math.e)
                #strength['CIRC']  = strength['EXPO']  ** (1/math.pi)
                
                slope_vec.y *= strength[interpolation]

                slope_vec.x /= 3
        elif interpolation == 'BACK': # Dynamic easing
            easing = 'EASE_IN' if master_keyframe.easing == 'AUTO' else master_keyframe.easing
            if (   (                  easing == 'EASE_IN_OUT' )
                or (not backwards and easing == 'EASE_IN'     )
                or (    backwards and easing == 'EASE_OUT'    )
            ):
                slope_vec = mathutils.Vector( (1, 0) )
            else:
                slope_vec = mathutils.Vector(to_keyframe.co) - mathutils.Vector(from_keyframe.co)
                # y = a + b(x - x_0) + c(x - x_0)^2 + d(x - x_0)^3
                # dx = x_3 - x_0
                # dy = y_3 - y_0
                # y(x_0) = y_0 = a

                # d = B+1
                # c = -B

                # y_3 = y_0 + b(dx) - B(dx)^2 + (B+1)dx^3
                # y_3 - y_0 + B(dx)^2 - (B+1)dx^3 = b(dx)
                # dy/dx + B(dx) - (B+1)dx^2 = b
                # dy/dx + B(dx - dx^2) - dx^2  = b

                # y_2 = (1/3)dx(c*dx+2b) + a
                # y_2 = (1/3)dx((-B)*dx+2b) + y_0

                # y_2 = (1/3)dx(c*dx) + y_0
                dydx = slope_vec.y / slope_vec.x
                b = dydx + master_keyframe.back * (slope_vec.x - slope_vec.x**2) - slope_vec.x**2
                #slope_vec.y = (1/3) * slope_vec.x * ( -master_keyframe.back * slope_vec.x + 2 * b)
                #slope_vec.y = (1/3) * slope_vec.x * ( -master_keyframe.back * slope_vec.x )
                slope_vec.y = master_keyframe.back/3 + slope_vec.y
                slope_vec.x /= 3

                # d = 2.70158
                # .33(-1.70158)
            
        else:
            slope_vec = mathutils.Vector( (0, 0) )
        
        if slope_vec.x != 0:
            slope_vec *= 1 / slope_vec.x

        return slope_vec
        

    def execute(self, context):
        factor = 3

        fcurve = context.active_editable_fcurve
        fcurve.update()
        
        this_interpolation = None
        last_interpolation = None

        found_unsupported = set()

        for keyframe_index in range(len(fcurve.keyframe_points)):
            this_keyframe = fcurve.keyframe_points[keyframe_index  ]
            next_keyframe = fcurve.keyframe_points[keyframe_index+1] if keyframe_index+1 < len(fcurve.keyframe_points) else None
            last_keyframe = fcurve.keyframe_points[keyframe_index-1] if keyframe_index-1 >= 0                          else None

            last_interpolation = this_interpolation
            this_interpolation = this_keyframe.interpolation

            apply_in  = bool(
                ( last_keyframe and last_keyframe.interpolation == 'BEZIER' and this_keyframe.select_left_handle ) 
                or this_keyframe.select_control_point
                or not self.only_selected
            )
            apply_out = bool(
                ( this_interpolation == 'BEZIER' and this_keyframe.select_right_handle )
                or this_keyframe.select_control_point 
                or not self.only_selected
            )

            #print(keyframe_index, this_keyframe.select_left_handle, this_keyframe.select_right_handle, this_keyframe.select_control_point, self.only_selected, " | ", apply_in, apply_out)
            if not apply_in and not apply_out:
                continue

            this_co = mathutils.Vector(this_keyframe.co)
            next_co = mathutils.Vector(next_keyframe.co) if next_keyframe else None
            last_co = mathutils.Vector(last_keyframe.co) if last_keyframe else None

            vec_in  = self.get_slope_vector(this_keyframe, last_keyframe, last_interpolation, backwards=True )
            vec_out = self.get_slope_vector(this_keyframe, next_keyframe, this_interpolation, backwards=False)
            if vec_in.x  == 0:
                apply_in = False
                found_unsupported.add(last_interpolation)
            if vec_out.x == 0:
                apply_out = False
                found_unsupported.add(this_interpolation)
            elif apply_out:
                if this_keyframe.interpolation != 'BEZIER':
                    this_keyframe.interpolation = 'BEZIER'
                    if next_keyframe:
                        next_keyframe.select_left_handle = True


            if vec_in.y != vec_out.y: #and not (this_keyframe.handle_left_type == 'ALIGNED' and this_keyframe.handle_right_type == 'ALIGNED'):
                handle_type = 'FREE'
            else:
                handle_type = 'ALIGNED'

            dist_in  = (last_co.x - this_co.x) / factor if last_co else this_keyframe.handle_left [0] - this_co.x
            dist_out = (next_co.x - this_co.x) / factor if next_co else this_keyframe.handle_right[0] - this_co.x
            
            if apply_in:
                this_keyframe.handle_left_type  = handle_type
                this_keyframe.handle_left       = vec_in  * dist_in  + this_co
            if apply_out:
                this_keyframe.handle_right_type = handle_type
                this_keyframe.handle_right      = vec_out * dist_out + this_co

        
        if found_unsupported:
            for interpolation_type in found_unsupported:
                self.do_report(type={'INFO'}, message="'{interpolation}' interpolation not convertable".format(interpolation=interpolation_type))
            self.do_report(type={'WARNING'}, message="Found {count} unsupported interpolation type(s) in {id_data}'s FCurve {fcurve_path}[{fcurve_index}]. See log for more info.".format(
                count        = len(found_unsupported),
                id_data      = fcurve.id_data.name   ,
                fcurve_path  = fcurve.data_path      ,
                fcurve_index = fcurve.array_index    )
            )

        return {'FINISHED'}

@compat.BlRegister()
class CNV_OT_ANIM_convert_to_cm3d2_interpolation(bpy.types.Operator):
    bl_idname = 'anim.convert_to_cm3d2_interpolation'
    bl_label = "Convert to CM3D2 Interpolation"
    bl_description = "Convert keyframes to be compatible with CM3D2 Interpolation"
    bl_options = {'REGISTER', 'UNDO'}

    only_selected = bpy.props.BoolProperty(name="Only Selected", default=True)
    items = [
        ('FCURVES'  , "FCurves"  , "", 'FCURVE'  , 1),
        ('KEYFRAMES', "KeyFrames", "", 'KEYFRAME', 2),
    ]
    selection_type = bpy.props.EnumProperty(items=items, name="Selection Type", default='FCURVES')

    @classmethod
    def poll(cls, context):
        fcurves = context.editable_fcurves
        if not fcurves:
            return False
        return len(fcurves) > 0
    
    def invoke(self, context, event):
        fcurves = context.selected_editable_fcurves
        if not fcurves:
            fcurves = context.editable_fcurves
            self.only_selected = False
        if fcurves:
            self.selection_type = 'FCURVES'
            for fcurve in fcurves:
                if check_fcurve_has_selected_keyframe(fcurve):
                    self.selection_type = 'KEYFRAMES'
                    break
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        row = self.layout.row(align=True)
        row.alignment = 'LEFT'
        row.prop(self, 'only_selected')
        column = row.column(align=True)
        column.alignment = 'LEFT'
        column.enabled = self.only_selected
        column.prop(self, 'selection_type', text='')
        

    def execute(self, context):
        if self.selection_type == 'FCURVES' and self.only_selected:
            fcurves = context.selected_editable_fcurves
        else:
            fcurves = context.editable_fcurves

        if self.selection_type == 'KEYFRAMES':
            used_fcurves = []
            for fcurve in fcurves:
                if check_fcurve_has_selected_keyframe(fcurve):
                    print(fcurve)
                    used_fcurves.append(fcurve)
            fcurves = used_fcurves

        context.window_manager.progress_begin(0, len(fcurves))
        for fcurve_index, fcurve in enumerate(fcurves):
            override = context.copy()
            override['active_editable_fcurve'] = fcurve
            bpy.ops.fcurve.convert_to_cm3d2_interpolation(override, 'EXEC_REGION_WIN', only_selected=self.only_selected, keep_reports=True)
            for kwargs in REPORTS:
                self.report(**kwargs)
            REPORTS.clear()
            #has_reports = bpy.ops.fcurve.convert_to_cm3d2_interpolation.has_reports
            context.window_manager.progress_update(fcurve_index)
        return {'FINISHED'}
