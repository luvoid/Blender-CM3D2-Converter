import re
import struct
import math
import unicodedata
import time
import bpy
import bmesh
import mathutils
from . import common
from . import compat
from .translations.pgettext_functions import *
from . import misc_DOPESHEET_MT_editor_menus


# メインオペレーター
@compat.BlRegister()
class CNV_OT_export_cm3d2_anm(bpy.types.Operator):
    bl_idname = 'export_anim.export_cm3d2_anm'
    bl_label = "CM3D2 Motion (.anm)"
    bl_description = "Allows you to export a pose to a .anm file."
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".anm"
    filter_glob = bpy.props.StringProperty(default="*.anm", options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name="Scale", default=0.2, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="Scale of the .anm at the time of export")
    is_backup = bpy.props.BoolProperty(name="Backup", default=True, description="Will backup overwritten files.")
    version = bpy.props.IntProperty(name="Version", default=1000, min=1000, max=1111, soft_min=1000, soft_max=1111, step=1)

    #is_anm_data_text = bpy.props.BoolProperty(name="From Anm Text", default=False, description="Input data from JSON file")
    items = [
        ('ALL'  , "Bake All Frames"      , "Export every frame as a keyframe (legacy behavior, large file sizes)", 'SEQUENCE' , 1),
        ('KEYED', "Only Export Keyframes", "Only export keyframes and their tangents (for more advance users)"   , 'KEYINGSET', 2),
        ('TEXT' , "From Anm Text JSON"   , "Export data from the JSON in the 'AnmData' text file"                , 'TEXT'     , 3)
    ]
    export_method = bpy.props.EnumProperty(items=items, name="Export Method", default='ALL')

    frame_start = bpy.props.IntProperty(name="Starting Frame", default=0, min=0, max=99999, soft_min=0, soft_max=99999, step=1)
    frame_end = bpy.props.IntProperty(name="Last Frame", default=0, min=0, max=99999, soft_min=0, soft_max=99999, step=1)
    key_frame_count = bpy.props.IntProperty(name="Number of key frames", default=1, min=1, max=99999, soft_min=1, soft_max=99999, step=1)
    time_scale = bpy.props.FloatProperty(name="Playback Speed", default=1.0, min=0.1, max=10.0, soft_min=0.1, soft_max=10.0, step=10, precision=1)
    
    
    
    is_keyframe_clean   = bpy.props.BoolProperty(name="Clean Keyframes"      , default=True )
    
    is_visual_transform = bpy.props.BoolProperty(name="Use Visual Transforms", default=True )
    is_smooth_handle    = bpy.props.BoolProperty(name="Smooth Transitions"   , default=True )

    items = [
        ('ARMATURE', "Armature", "", 'OUTLINER_OB_ARMATURE', 1),
        ('ARMATURE_PROPERTY', "Armature Data", "", 'ARMATURE_DATA', 2),
    ]
    bone_parent_from = bpy.props.EnumProperty(items=items, name="Bone Parent From", default='ARMATURE_PROPERTY')

    is_remove_unkeyed_bone       = bpy.props.BoolProperty(name="Remove Unkeyed Bones"                 , default=False)  
    is_remove_alone_bone         = bpy.props.BoolProperty(name="Remove Loose Bones"                   , default=True )
    is_remove_ik_bone            = bpy.props.BoolProperty(name="Remove IK Bones"                      , default=True )
    is_remove_serial_number_bone = bpy.props.BoolProperty(name="Remove Duplicate Numbers"             , default=True )
    is_remove_japanese_bone      = bpy.props.BoolProperty(name="Remove Japanese Characters from Bones", default=True )

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob and ob.type == 'ARMATURE':
            return True
        return False

    def invoke(self, context, event):
        prefs = common.preferences()

        ob = context.active_object
        arm = ob.data
        action_name = None
        if ob.animation_data and ob.animation_data.action:
            action_name = common.remove_serial_number(ob.animation_data.action.name)

        if prefs.anm_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.anm_default_path, action_name, "anm")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.anm_export_path, action_name, "anm")
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        self.scale = 1.0 / prefs.scale
        self.is_backup = bool(prefs.backup_ext)
        self.key_frame_count = (context.scene.frame_end - context.scene.frame_start) + 1

        if "BoneData:0" in arm:
            self.bone_parent_from = 'ARMATURE_PROPERTY'
        else:
            self.bone_parent_from = 'ARMATURE'

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        self.layout.prop(self, 'scale')

        box = self.layout.box()
        box.prop(self, 'is_backup', icon='FILE_BACKUP')
        box.prop(self, 'version')

        #self.layout.prop(self, 'is_anm_data_text', icon='TEXT')
        box = self.layout.box()
        box.label(text="Export Method")
        box.prop(self, 'export_method', expand=True)

        box = self.layout.box()
        box.enabled = not (self.export_method == 'TEXT')
        box.prop(self, 'time_scale')
        sub_box = box.box()
        sub_box.enabled = (self.export_method == 'ALL')
        row = sub_box.row()
        row.prop(self, 'frame_start')
        row.prop(self, 'frame_end')
        sub_box.prop(self, 'key_frame_count')
        sub_box.prop(self, 'is_keyframe_clean', icon='DISCLOSURE_TRI_DOWN')
        sub_box.prop(self, 'is_smooth_handle', icon='SMOOTHCURVE')

        sub_box = box.box()
        sub_box.label(text="Destination of bone parent information", icon='FILE_PARENT')
        sub_box.prop(self, 'bone_parent_from', icon='FILE_PARENT', expand=True)

        sub_box = box.box()
        sub_box.label(text="Bones to Exclude", icon='X')
        column = sub_box.column(align=True)
        column.prop(self, 'is_remove_unkeyed_bone'      , icon='KEY_DEHLT'              )
        column.prop(self, 'is_remove_alone_bone'        , icon='UNLINKED'               )
        column.prop(self, 'is_remove_ik_bone'           , icon='CONSTRAINT_BONE'        )
        column.prop(self, 'is_remove_serial_number_bone', icon='SEQUENCE'               )
        column.prop(self, 'is_remove_japanese_bone'     , icon=compat.icon('HOLDOUT_ON'))

    def execute(self, context):
        common.preferences().anm_export_path = self.filepath

        try:
            file = common.open_temporary(self.filepath, 'wb', is_backup=self.is_backup)
        except:
            self.report(type={'ERROR'}, message=f_tip_("Failed to open the file. File does not exist or is inaccessible. file={}", self.filepath))
            return {'CANCELLED'}

        try:
            with file:
                if self.export_method == 'TEXT':
                    self.write_animation_from_text(context, file)
                else:
                    self.write_animation(context, file)
        except common.CM3D2ExportException as e:
            self.report(type={'ERROR'}, message=str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

    def get_animation_frames(self, context, fps, pose, bones, bone_parents):
        anm_data_raw = {}
        class KeyFrame:
            def __init__(self, time, value, slope=None):
                self.time = time
                self.value = value
                if slope:
                    self.slope = slope
                elif type(value) == mathutils.Vector:
                    self.slope = mathutils.Vector.Fill(len(value))
                elif type(value) == mathutils.Quaternion:
                    self.slope = mathutils.Quaternion((0,0,0,0))
                else:
                    self.slope = 0

        same_locs = {}
        same_rots = {}
        pre_rots = {}
        for key_frame_index in range(self.key_frame_count):
            if self.key_frame_count == 1:
                frame = 0.0
            else:
                frame = (self.frame_end - self.frame_start) / (self.key_frame_count - 1) * key_frame_index + self.frame_start
            context.scene.frame_set(frame=int(frame), subframe=frame - int(frame))
            if compat.IS_LEGACY:
                context.scene.update()
            else:
                layer = context.view_layer
                layer.update()

            time = frame / fps * (1.0 / self.time_scale)

            for bone in bones:
                if bone.name not in anm_data_raw:
                    anm_data_raw[bone.name] = {"LOC": {}, "ROT": {}}
                    same_locs[bone.name] = []
                    same_rots[bone.name] = []

                pose_bone = pose.bones[bone.name]
                pose_mat = pose_bone.matrix.copy() #ob.convert_space(pose_bone=pose_bone, matrix=pose_bone.matrix, from_space='POSE', to_space='WORLD')
                parent = bone_parents[bone.name]
                if parent:
                    pose_mat = compat.convert_bl_to_cm_bone_rotation(pose_mat)
                    pose_mat = compat.mul(pose.bones[parent.name].matrix.inverted(), pose_mat)
                    pose_mat = compat.convert_bl_to_cm_bone_space(pose_mat)
                else:
                    pose_mat = compat.convert_bl_to_cm_bone_rotation(pose_mat)
                    pose_mat = compat.convert_bl_to_cm_space(pose_mat)

                loc = pose_mat.to_translation() * self.scale
                rot = pose_mat.to_quaternion()

                # This fixes rotations that jump to alternate representations.
                if bone.name in pre_rots:
                    if 5.0 < pre_rots[bone.name].rotation_difference(rot).angle:
                        rot.w, rot.x, rot.y, rot.z = -rot.w, -rot.x, -rot.y, -rot.z
                pre_rots[bone.name] = rot.copy()

                #if parent:
                #    #loc.x, loc.y, loc.z = -loc.y, -loc.x, loc.z
                #    loc = compat.convert_bl_to_cm_bone_space(loc)
                #    
                #    # quat.w, quat.x, quat.y, quat.z = quat.w, -quat.z, quat.x, -quat.y
                #    #rot.w, rot.x, rot.y, rot.z = rot.w, rot.y, rot.x, -rot.z
                #    rot.w, rot.x, rot.y, rot.z = rot.w, rot.y, -rot.z, -rot.x
                #
                #else:
                #    loc.x, loc.y, loc.z = -loc.x, loc.z, -loc.y
                #
                #    fix_quat = mathutils.Euler((0, 0, math.radians(-90)), 'XYZ').to_quaternion()
                #    fix_quat2 = mathutils.Euler((math.radians(-90), 0, 0), 'XYZ').to_quaternion()
                #    rot = compat.mul3(rot, fix_quat, fix_quat2)
                #
                #    rot.w, rot.x, rot.y, rot.z = -rot.y, -rot.z, -rot.x, rot.w
                
                if not self.is_keyframe_clean or key_frame_index == 0 or key_frame_index == self.key_frame_count - 1:
                    anm_data_raw[bone.name]["LOC"][time] = loc.copy()
                    anm_data_raw[bone.name]["ROT"][time] = rot.copy()

                    if self.is_keyframe_clean:
                        same_locs[bone.name].append(KeyFrame(time, loc.copy()))
                        same_rots[bone.name].append(KeyFrame(time, rot.copy()))
                else:
                    def is_mismatch(a, b):
                        return 0.000001 < abs(a - b)

                    a = same_locs[bone.name][-1].value - loc
                    b = same_locs[bone.name][-1].slope
                    if is_mismatch(a.x, b.x) or is_mismatch(a.y, b.y) or is_mismatch(a.z, b.z):
                        if 2 <= len(same_locs[bone.name]):
                            anm_data_raw[bone.name]["LOC"][same_locs[bone.name][-1].time] = same_locs[bone.name][-1].value.copy()
                        anm_data_raw[bone.name]["LOC"][time] = loc.copy()
                        same_locs[bone.name] = [KeyFrame(time, loc.copy(), a.copy())] # update last position and slope
                    else:
                        same_locs[bone.name].append(KeyFrame(time, loc.copy(), b.copy())) # update last position, but not last slope
                    
                    a = same_rots[bone.name][-1].value - rot
                    b = same_rots[bone.name][-1].slope
                    if is_mismatch(a.w, b.w) or is_mismatch(a.x, b.x) or is_mismatch(a.y, b.y) or is_mismatch(a.z, b.z):
                        if 2 <= len(same_rots[bone.name]):
                            anm_data_raw[bone.name]["ROT"][same_rots[bone.name][-1].time] = same_rots[bone.name][-1].value.copy()
                        anm_data_raw[bone.name]["ROT"][time] = rot.copy()
                        same_rots[bone.name] = [KeyFrame(time, rot.copy(), a.copy())] # update last position and slope
                    else:
                        same_rots[bone.name].append(KeyFrame(time, rot.copy(), b.copy())) # update last position, but not last slope
        
        return anm_data_raw

    def get_animation_keyframes(self, context, fps, pose, keyed_bones, fcurves):
        anm_data_raw = {}

        prop_sizes = {'location': 3, 'rotation_quaternion': 4, 'rotation_euler': 3}
        
        #class KeyFrame:
        #    def __init__(self, time, value):
        #        self.time = time
        #        self.value = value
        #same_locs = {}
        #same_rots = {}
        #pre_rots = {}
        
        def _convert_loc(pose_bone, loc):
            loc = mathutils.Vector(loc)
            loc = compat.mul(pose_bone.bone.matrix_local, loc)
            if pose_bone.parent:
                loc = compat.mul(pose_bone.parent.bone.matrix_local.inverted(), loc)
                loc = compat.convert_bl_to_cm_bone_space(loc)
            else:
                loc = compat.convert_bl_to_cm_space(loc)
            return loc * self.scale
        """
        def _convert_quat(pose_bone, quat):
            #quat = mathutils.Quaternion(quat)
            #'''Can't use matrix transforms here as they would mess up interpolation.'''
            #quat = compat.mul(pose_bone.bone.matrix_local.to_quaternion(), quat)
            
            quat_mat = mathutils.Quaternion(quat).to_matrix().to_4x4()
            quat_mat = compat.mul(pose_bone.bone.matrix_local, quat_mat)
            #quat = quat_mat.to_quaternion()
            if pose_bone.parent:
                ## inverse of quat.w, quat.x, quat.y, quat.z = quat.w, -quat.z, quat.x, -quat.y
                #quat.w, quat.x, quat.y, quat.z = quat.w, quat.y, -quat.z, -quat.x
                #quat = compat.mul(pose_bone.parent.bone.matrix_local.to_quaternion().inverted(), quat)
                ##quat = compat.mul(pose_bone.parent.bone.matrix_local.inverted().to_quaternion(), quat)\
                quat_mat = compat.convert_bl_to_cm_bone_rotation(quat_mat)
                quat_mat = compat.mul(pose_bone.parent.bone.matrix_local.inverted(), quat_mat)
                quat_mat = compat.convert_bl_to_cm_bone_space(quat_mat)
                quat = quat_mat.to_quaternion()
            else:
                #fix_quat = mathutils.Euler((0, 0, math.radians(-90)), 'XYZ').to_quaternion()
                #fix_quat2 = mathutils.Euler((math.radians(-90), 0, 0), 'XYZ').to_quaternion()
                #quat = compat.mul3(quat, fix_quat, fix_quat2)
                #
                #quat.w, quat.x, quat.y, quat.z = -quat.y, -quat.z, -quat.x, quat.w
                
                #quat.w, quat.x, quat.y, quat.z = quat.w, quat.y, -quat.z, -quat.x
                #quat = compat.mul(mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z').to_quaternion(), quat)

                quat_mat = compat.convert_bl_to_cm_bone_rotation(quat_mat)
                quat_mat = compat.convert_bl_to_cm_space(quat_mat)
                quat = quat_mat.to_quaternion()
            return quat
        """

        def _convert_quat(pose_bone, quat):
            bone_quat = pose_bone.bone.matrix.to_quaternion()
            quat = mathutils.Quaternion(quat)

            '''Can't use matrix transforms here as they would mess up interpolation.'''
            quat = compat.mul(bone_quat, quat)
            
            if pose_bone.bone.parent:
                #quat.w, quat.x, quat.y, quat.z = quat.w, -quat.z, quat.x, -quat.y
                quat.w, quat.y, quat.x, quat.z = quat.w, -quat.z, quat.y, -quat.x
            else:
                quat = compat.mul(mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z').to_quaternion(), quat)
                quat.w, quat.y, quat.x, quat.z = quat.w, -quat.z, quat.y, -quat.x
            return quat

        for prop, prop_keyed_bones in keyed_bones.items():
            #self.report(type={'INFO'}, message=f_tip_("{prop} {list}", prop=prop, list=prop_keyed_bones))
            for bone_name in prop_keyed_bones:
                if bone_name not in anm_data_raw:
                    anm_data_raw[bone_name] = {}
                    #same_locs[bone_name] = []
                    #same_rots[bone_name] = []
                
                pose_bone = pose.bones[bone_name]
                rna_data_path = 'pose.bones["{bone_name}"].{property}'.format(bone_name=bone_name, property=prop)
                prop_fcurves = [ fcurves.find(rna_data_path, index=axis_index) for axis_index in range(prop_sizes[prop]) ]
                
                # Create missing fcurves, and make existing fcurves CM3D2 compatible.
                for axis_index, fcurve in enumerate(prop_fcurves):
                    if not fcurve:
                        fcurve = fcurves.new(rna_data_path, index=axis_index, action_group=pose_bone.name)
                        prop_fcurves[axis_index] = fcurve
                        self.report(type={'WARNING'}, message=f_tip_("Creating missing FCurve for {path}[{index}]", path=rna_data_path, index=axis_index))
                    else:
                        override = context.copy()
                        override['active_editable_fcurve'] = fcurve
                        bpy.ops.fcurve.convert_to_cm3d2_interpolation(override, only_selected=False, keep_reports=True)
                        for kwargs in misc_DOPESHEET_MT_editor_menus.REPORTS:
                            self.report(**kwargs)
                        misc_DOPESHEET_MT_editor_menus.REPORTS.clear()


                # Create a list by frame, indicating wether or not there is a keyframe at that time for each fcurve
                is_keyframes = {}
                for fcurve in prop_fcurves:
                    for keyframe in fcurve.keyframe_points:
                        frame = keyframe.co[0]
                        if frame not in is_keyframes:
                            is_keyframes[frame] = [False] * prop_sizes[prop]
                        is_keyframes[frame][fcurve.array_index] = True
                
                # Make sure that no keyframe times are missing any components
                for frame, is_axes in is_keyframes.items():
                    for axis_index, is_axis in enumerate(is_axes):
                        if not is_axis:
                            fcurve = prop_fcurves[axis_index]
                            keyframe = fcurve.keyframe_points.insert(
                                frame         = frame                 , 
                                value         = fcurve.evaluate(frame), 
                                options       = {'NEEDED', 'FAST'}                        
                            )
                            self.report(type={'WARNING'}, message=f_tip_("Creating missing keyframe @ frame {frame} for {path}[{index}]", path=rna_data_path, index=axis_index, frame=frame))
                
                for fcurve in prop_fcurves:
                    fcurve.update()
                
                for keyframe_index, frame in enumerate(is_keyframes.keys()):
                    time = frame / fps * (1.0 / self.time_scale)

                    _kf = lambda fcurve: fcurve.keyframe_points[keyframe_index]
                    raw_keyframe = [ _kf(fc).co[1] for fc in prop_fcurves ]                                                                            
                    tangent_in   = [ ( _kf(fc).handle_left [1] - _kf(fc).co[1] ) / ( _kf(fc).handle_left [0] - _kf(fc).co[0] ) * fps for fc in prop_fcurves ]
                    tangent_out  = [ ( _kf(fc).handle_right[1] - _kf(fc).co[1] ) / ( _kf(fc).handle_right[0] - _kf(fc).co[0] ) * fps for fc in prop_fcurves ]
                                                   
                    if prop == 'location':
                        if 'LOC' not in anm_data_raw[bone_name]:
                            anm_data_raw[bone_name]['LOC'    ] = {}
                            anm_data_raw[bone_name]['LOC_IN' ] = {}
                            anm_data_raw[bone_name]['LOC_OUT'] = {}
                        anm_data_raw[bone_name]['LOC'    ][time] = _convert_loc(pose_bone, raw_keyframe).copy()
                        anm_data_raw[bone_name]['LOC_IN' ][time] = _convert_loc(pose_bone, tangent_in  ).copy()
                        anm_data_raw[bone_name]['LOC_OUT'][time] = _convert_loc(pose_bone, tangent_out ).copy()
                    elif prop == 'rotation_quaternion':
                        if 'ROT' not in anm_data_raw[bone_name]:
                            anm_data_raw[bone_name]['ROT'    ] = {}
                            anm_data_raw[bone_name]['ROT_IN' ] = {}
                            anm_data_raw[bone_name]['ROT_OUT'] = {}
                        anm_data_raw[bone_name]['ROT'    ][time] = _convert_quat(pose_bone, raw_keyframe).copy()
                        anm_data_raw[bone_name]['ROT_OUT'][time] = _convert_quat(pose_bone, tangent_out ).copy()
                        anm_data_raw[bone_name]['ROT_IN' ][time] = _convert_quat(pose_bone, tangent_in  ).copy()
                        # - - - Alternative Method - - -
                        #raw_keyframe = mathutils.Quaternion(raw_keyframe)
                        #tangent_in   = mathutils.Quaternion(tangent_in)
                        #tangent_out  = mathutils.Quaternion(tangent_out)
                        #converted_quat = _convert_quat(pose_bone, raw_keyframe).copy()
                        #anm_data_raw[bone_name]['ROT'    ][time] = converted_quat.copy()
                        #anm_data_raw[bone_name]['ROT_IN' ][time] = converted_quat.inverted() @ _convert_quat(pose_bone, raw_keyframe @ tangent_in  )
                        #anm_data_raw[bone_name]['ROT_OUT'][time] = converted_quat.inverted() @ _convert_quat(pose_bone, raw_keyframe @ tangent_out )
        
        return anm_data_raw

    def write_animation(self, context, file):
        ob = context.active_object
        arm = ob.data
        pose = ob.pose
        fps = context.scene.render.fps


        bone_parents = {}
        if self.bone_parent_from == 'ARMATURE_PROPERTY':
            for i in range(9999):
                name = "BoneData:" + str(i)
                if name not in arm:
                    continue
                elems = arm[name].split(",")
                if len(elems) != 5:
                    continue
                if elems[0] in arm.bones:
                    if elems[2] in arm.bones:
                        bone_parents[elems[0]] = arm.bones[elems[2]]
                    else:
                        bone_parents[elems[0]] = None
            for bone in arm.bones:
                if bone.name in bone_parents:
                    continue
                bone_parents[bone.name] = bone.parent
        else:
            for bone in arm.bones:
                bone_parents[bone.name] = bone.parent

        copied_action = None
        if ob.animation_data and ob.animation_data.action:
            copied_action = ob.animation_data.action.copy()
            copied_action.name = ob.animation_data.action.name + "__anm_export"
            fcurves = copied_action.fcurves
            keyed_bones = {'location': [], 'rotation_quaternion': [], 'rotation_euler': []}
            for bone in arm.bones:
                rna_data_stub = 'pose.bones["{bone_name}"]'.format(bone_name=bone.name)
                for prop, axes in [('location', 3), ('rotation_quaternion', 4), ('rotation_euler', 3)]:
                    found_fcurve = False
                    for axis_index in range(0, axes):
                        if fcurves.find(rna_data_stub + '.' + prop, index=axis_index):
                            found_fcurve = True
                            break
                    if found_fcurve:
                        keyed_bones[prop].append(bone.name)

        elif self.export_method == 'KEYED' or self.is_remove_unkeyed_bone:
            raise common.CM3D2ExportException(
                "Active armature has no animation data / action. Please use \"{method}\" with \"{option}\" disabled, or bake keyframes before exporting.".format(
                    method = "Bake All Frames",
                    option = "Remove Unkeyed Bones"
                )
            )




        def is_japanese(string):
            for ch in string:
                name = unicodedata.name(ch)
                if 'CJK UNIFIED' in name or 'HIRAGANA' in name or 'KATAKANA' in name:
                    return True
            return False
        bones = []
        already_bone_names = []
        bones_queue = arm.bones[:]
        while len(bones_queue):
            bone = bones_queue.pop(0)

            if not bone_parents[bone.name]:
                already_bone_names.append(bone.name)
                if self.is_remove_serial_number_bone:
                    if common.has_serial_number(bone.name):
                        continue
                if self.is_remove_japanese_bone:
                    if is_japanese(bone.name):
                        continue
                if self.is_remove_alone_bone and len(bone.children) == 0:
                    continue
                if self.is_remove_unkeyed_bone:
                    is_keyed = False
                    for prop in keyed_bones:
                        if bone.name in keyed_bones[prop]:
                            is_keyed = True
                            break
                    if not is_keyed:
                        continue
                bones.append(bone)
                continue
            elif bone_parents[bone.name].name in already_bone_names:
                already_bone_names.append(bone.name)
                if self.is_remove_serial_number_bone:
                    if common.has_serial_number(bone.name):
                        continue
                if self.is_remove_japanese_bone:
                    if is_japanese(bone.name):
                        continue
                if self.is_remove_ik_bone:
                    bone_name_low = bone.name.lower()
                    if '_ik_' in bone_name_low or bone_name_low.endswith('_nub') or bone.name.endswith('Nub'):
                        continue
                if self.is_remove_unkeyed_bone:
                    is_keyed = False
                    for prop in keyed_bones:
                        if bone.name in keyed_bones[prop]:
                            is_keyed = True
                            break
                    if not is_keyed:
                        continue
                bones.append(bone)
                continue

            bones_queue.append(bone)

        if self.export_method == 'ALL':
            anm_data_raw = self.get_animation_frames(context, fps, pose, bones, bone_parents)
        elif self.export_method == 'KEYED':
            anm_data_raw = self.get_animation_keyframes(context, fps, pose, keyed_bones, fcurves)

        if copied_action:
            context.blend_data.actions.remove(copied_action, do_unlink=True, do_id_user=True, do_ui_user=True)

        anm_data = {}
        for bone_name, channels in anm_data_raw.items():
            anm_data[bone_name] = {100: {}, 101: {}, 102: {}, 103: {}, 104: {}, 105: {}, 106: {}}
            if channels.get('LOC'):
                has_tangents = bool(channels.get('LOC_IN') and channels.get('LOC_OUT'))
                for time, loc in channels["LOC"].items():
                    tangent_in  = channels['LOC_IN' ][time] if has_tangents else mathutils.Vector()
                    tangent_out = channels['LOC_OUT'][time] if has_tangents else mathutils.Vector()
                    anm_data[bone_name][104][time] = (loc.x, tangent_in.x, tangent_out.x)
                    anm_data[bone_name][105][time] = (loc.y, tangent_in.y, tangent_out.y)
                    anm_data[bone_name][106][time] = (loc.z, tangent_in.z, tangent_out.z)
            if channels.get('ROT'):
                has_tangents = bool(channels.get('ROT_IN') and channels.get('ROT_OUT'))
                for time, rot in channels["ROT"].items():
                    tangent_in  = channels['ROT_IN' ][time] if has_tangents else mathutils.Quaternion((0,0,0,0))
                    tangent_out = channels['ROT_OUT'][time] if has_tangents else mathutils.Quaternion((0,0,0,0))
                    anm_data[bone_name][100][time] = (rot.x, tangent_in.x, tangent_out.x)
                    anm_data[bone_name][101][time] = (rot.y, tangent_in.y, tangent_out.y)
                    anm_data[bone_name][102][time] = (rot.z, tangent_in.z, tangent_out.z)
                    anm_data[bone_name][103][time] = (rot.w, tangent_in.w, tangent_out.w)
                                                      
        time_step = 1 / fps * (1.0 / self.time_scale)


        ''' Write data to the file '''

        common.write_str(file, 'CM3D2_ANIM')
        file.write(struct.pack('<i', self.version))

        for bone in bones:
            if not anm_data.get(bone.name):
                continue

            file.write(struct.pack('<?', True))

            bone_names = [bone.name]
            current_bone = bone
            while bone_parents[current_bone.name]:
                bone_names.append(bone_parents[current_bone.name].name)
                current_bone = bone_parents[current_bone.name]

            bone_names.reverse()
            common.write_str(file, "/".join(bone_names))
            
            for channel_id, keyframes in sorted(anm_data[bone.name].items(), key=lambda x: x[0]):
                file.write(struct.pack('<B', channel_id))
                file.write(struct.pack('<i', len(keyframes)))

                keyframes_list = sorted(keyframes.items(), key=lambda x: x[0])
                for i in range(len(keyframes_list)):
                    x = keyframes_list[i][0]
                    y, dydx_in, dydx_out = keyframes_list[i][1]

                    if len(keyframes_list) <= 1:
                        file.write(struct.pack('<f', x))
                        file.write(struct.pack('<f', y))
                        file.write(struct.pack('<2f', 0.0, 0.0))
                        continue

                    file.write(struct.pack('<f', x))
                    file.write(struct.pack('<f', y))

                    if self.is_smooth_handle and self.export_method == 'ALL':
                        if i == 0:
                            prev_x = x - (keyframes_list[i + 1][0] - x)
                            prev_y = y - (keyframes_list[i + 1][1][0] - y)
                            next_x = keyframes_list[i + 1][0]
                            next_y = keyframes_list[i + 1][1][0]
                        elif i == len(keyframes_list) - 1:
                            prev_x = keyframes_list[i - 1][0]
                            prev_y = keyframes_list[i - 1][1][0]
                            next_x = x + (x - keyframes_list[i - 1][0])
                            next_y = y + (y - keyframes_list[i - 1][1][0])
                        else:
                            prev_x = keyframes_list[i - 1][0]
                            prev_y = keyframes_list[i - 1][1][0]
                            next_x = keyframes_list[i + 1][0]
                            next_y = keyframes_list[i + 1][1][0]

                        prev_rad = (prev_y - y) / (prev_x - x)
                        next_rad = (next_y - y) / (next_x - x)
                        join_rad = (prev_rad + next_rad) / 2

                        tan_in  = join_rad if x - prev_x <= time_step * 1.5 else prev_rad
                        tan_out = join_rad if next_x - x <= time_step * 1.5 else next_rad
                        
                        file.write(struct.pack('<2f', tan_in, tan_out))
                        #file.write(struct.pack('<2f', join_rad, join_rad))
                        #file.write(struct.pack('<2f', prev_rad, next_rad))
                    else:
                        file.write(struct.pack('<2f', dydx_in, dydx_out))

        file.write(struct.pack('<?', False))

    def write_animation_from_text(self, context, file):
        txt = context.blend_data.texts.get("AnmData")
        if not txt:
            raise common.CM3D2ExportException("There is no 'AnmData' text file.")

        import json
        anm_data = json.loads(txt.as_string())

        common.write_str(file, 'CM3D2_ANIM')
        file.write(struct.pack('<i', self.version))

        for base_bone_name, bone_data in anm_data.items():
            path = bone_data['path']
            file.write(struct.pack('<?', True))
            common.write_str(file, path)

            for channel_id, channel in bone_data['channels'].items():
                file.write(struct.pack('<B', int(channel_id)))
                channel_data_count = len(channel)
                file.write(struct.pack('<i', channel_data_count))
                for channel_data in channel:
                    frame = channel_data['frame']
                    data = ( channel_data['f0'], channel_data['f1'], channel_data['f2'] )
                    file.write(struct.pack('<f' , frame))
                    file.write(struct.pack('<3f', *data ))

        file.write(struct.pack('<?', False))





# メニューに登録する関数
def menu_func(self, context):
    self.layout.operator(CNV_OT_export_cm3d2_anm.bl_idname, icon_value=common.kiss_icon())
