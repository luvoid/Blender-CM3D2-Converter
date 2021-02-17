import re
import struct
import math
import unicodedata
import time
import bpy
import bmesh
import mathutils
import os
from . import common
from . import compat


# メインオペレーター
@compat.BlRegister()
class CNV_OT_import_cm3d2_anm(bpy.types.Operator):
    bl_idname = 'import_anim.import_cm3d2_anm'
    bl_label = "CM3D2モーション (.anm)"
    bl_description = "カスタムメイド3D2のanmファイルを読み込みます"
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".anm"
    filter_glob = bpy.props.StringProperty(default="*.anm", options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name="倍率", default=5, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="インポート時のメッシュ等の拡大率です")
    set_frame_rate = bpy.props.BoolProperty(name="Set Framerate", default=True, description="Change the scene's render settings to 60 fps")                                     
    is_loop = bpy.props.BoolProperty(name="Loop", default=True)

    is_anm_data_text = bpy.props.BoolProperty(name="Anm Text", default=True, description="Output Data to a JSON file")
    
    remove_pre_animation = bpy.props.BoolProperty(name="既にあるアニメーションを削除", default=True)
    set_frame = bpy.props.BoolProperty(name="フレーム開始・終了位置を調整", default=True)
    ignore_automatic_bone = bpy.props.BoolProperty(name="Twisterボーンを除外", default=True)

    is_location = bpy.props.BoolProperty(name="位置", default=True)
    is_rotation = bpy.props.BoolProperty(name="回転", default=True)
    is_scale = bpy.props.BoolProperty(name="拡縮", default=False)
    is_tangents = bpy.props.BoolProperty(name="Tangents"      , default=False)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob and ob.type == 'ARMATURE':
            return True
        return False

    def invoke(self, context, event):
        prefs = common.preferences()
        if prefs.anm_default_path:
            self.filepath = common.default_cm3d2_dir(prefs.anm_default_path, None, "anm")
        else:
            self.filepath = common.default_cm3d2_dir(prefs.anm_import_path, None, "anm")
        self.scale = prefs.scale
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        self.layout.prop(self, 'scale')
        self.layout.prop(self, 'set_frame_rate'  , icon=compat.icon('RENDER_ANIMATION'))
        self.layout.prop(self, 'is_loop'         , icon=compat.icon('LOOP_BACK'       ))
        self.layout.prop(self, 'is_anm_data_text', icon=compat.icon('TEXT'            ))

        box = self.layout.box()
        box.prop(self, 'remove_pre_animation', icon='DISCLOSURE_TRI_DOWN')
        box.prop(self, 'set_frame', icon='NEXT_KEYFRAME')
        box.prop(self, 'ignore_automatic_bone', icon='X')

        box = self.layout.box()
        box.label(text="読み込むアニメーション情報")
        column = box.column(align=True)
        column.prop(self, 'is_location', icon=compat.icon('CON_LOCLIKE'))
        column.prop(self, 'is_rotation', icon=compat.icon('CON_ROTLIKE'))
        row = column.row()
        row.prop(self, 'is_scale', icon=compat.icon('CON_SIZELIKE'))
        row.enabled = False
        column.prop(self, 'is_tangents', icon=compat.icon('IPO_BEZIER' ))

    def execute(self, context):
        prefs = common.preferences()
        prefs.anm_import_path = self.filepath
        prefs.scale = self.scale

        try:
            file = open(self.filepath, 'rb')
        except:
            self.report(type={'ERROR'}, message="ファイルを開くのに失敗しました、アクセス不可かファイルが存在しません")
            return {'CANCELLED'}

        # ヘッダー
        ext = common.read_str(file)
        if ext != 'CM3D2_ANIM':
            self.report(type={'ERROR'}, message="これはカスタムメイド3D2のモーションファイルではありません")
            return {'CANCELLED'}
        anm_version = struct.unpack('<i', file.read(4))[0]
        first_channel_id = struct.unpack('<B', file.read(1))[0]
        if first_channel_id != 1:
            self.report(type={'ERROR'}, message="Unexpected first channel id = {id} (should be 1).".format(id=first_channel_id))
            return {'CANCELLED'}


        anm_data = {}
        for anim_data_index in range(9**9):
            path = common.read_str(file)
            
            base_bone_name = path.split('/')[-1]
            if base_bone_name not in anm_data:
                anm_data[base_bone_name] = {'path': path}
                anm_data[base_bone_name]['channels'] = {}

            for channel_index in range(9**9):
                channel_id = struct.unpack('<B', file.read(1))[0]
                channel_id_str = channel_id
                if channel_id <= 1:
                    break
                anm_data[base_bone_name]['channels'][channel_id_str] = []
                channel_data_count = struct.unpack('<i', file.read(4))[0]
                for channel_data_index in range(channel_data_count):
                    frame = struct.unpack('<f', file.read(4))[0]
                    data = struct.unpack('<3f', file.read(4 * 3))

                    anm_data[base_bone_name]['channels'][channel_id_str].append({'frame': frame, 'f0': data[0], 'f1': data[1], 'f2': data[2]})

            if channel_id == 0:
                break
        
        if self.is_anm_data_text:
            if "AnmData" in context.blend_data.texts:
                txt = context.blend_data.texts["AnmData"]
                txt.clear()
            else:
                txt = context.blend_data.texts.new("AnmData")
            import json
            txt.write( json.dumps(anm_data, ensure_ascii=False, indent=2) )

        if self.set_frame_rate:
            context.scene.render.fps = 60
        fps = context.scene.render.fps

        ob = context.active_object
        arm = ob.data
        pose = ob.pose
        base_bone = arm.get('BaseBone')
        if base_bone:
            base_bone = arm.bones.get(base_bone)

        anim = ob.animation_data
        if not anim:
            anim = ob.animation_data_create()
        action = anim.action
        if not action:
            action = context.blend_data.actions.new(os.path.basename(self.filepath))
            anim.action = action
            fcurves = action.fcurves
        else:
            action.name = os.path.basename(self.filepath)
            fcurves = action.fcurves
            if self.remove_pre_animation:
                for fcurve in fcurves:
                    fcurves.remove(fcurve)

        max_frame = 0
        bpy.ops.object.mode_set(mode='OBJECT')
        found_unknown = []
        found_tangents = []
        for bone_name, bone_data in anm_data.items():
            if self.ignore_automatic_bone:
                if re.match(r"Kata_[RL]", bone_name):
                    continue
                if re.match(r"Uppertwist1_[RL]", bone_name):
                    continue
                if re.match(r"momoniku_[RL]", bone_name):
                    continue

            if bone_name not in pose.bones:
                bone_name = common.decode_bone_name(bone_name)
                if bone_name not in pose.bones:
                    continue
            bone = arm.bones[bone_name]
            pose_bone = pose.bones[bone_name]

            loc_fcurves  = None

            locs = {}
            loc_tangents = {}
            quats = {}
            quat_tangents = {}
            for channel_id, channel_data in bone_data['channels'].items():

                if channel_id in [100, 101, 102, 103]:
                    for data in channel_data:
                        frame = data['frame']
                        if frame not in quats:
                            quats[frame] = [None, None, None, None]

                        if channel_id == 103:
                            quats[frame][0] = data['f0']
                        elif channel_id == 100:
                            quats[frame][1] = data['f0']
                        elif channel_id == 101:
                            quats[frame][2] = data['f0']
                        elif channel_id == 102:
                            quats[frame][3] = data['f0']

                        #tangents = (data['f1'], data['f2'])
                        #if (data['f1']**2 + data['f2']**2) ** .5 > 0.01:
                        #    found_tangents.append(tangents)
                        if frame not in quat_tangents:
                            quat_tangents[frame] = {'in': [None, None, None, None], 'out': [None, None, None, None]}

                        if channel_id == 103:
                            quat_tangents[frame]['in' ][0] = data['f1']
                            quat_tangents[frame]['out'][0] = data['f2']
                        elif channel_id == 100:                        
                            quat_tangents[frame]['in' ][1] = data['f1']
                            quat_tangents[frame]['out'][1] = data['f2']
                        elif channel_id == 101:                        
                            quat_tangents[frame]['in' ][2] = data['f1']
                            quat_tangents[frame]['out'][2] = data['f2']
                        elif channel_id == 102:              
                            quat_tangents[frame]['in' ][3] = data['f1']
                            quat_tangents[frame]['out'][3] = data['f2']

                elif channel_id in [104, 105, 106]:
                    for data in channel_data:
                        frame = data['frame']
                        if frame not in locs:
                            locs[frame] = [None, None, None]

                        if channel_id == 104:
                            locs[frame][0] = data['f0']
                        elif channel_id == 105:
                            locs[frame][1] = data['f0']
                        elif channel_id == 106:
                            locs[frame][2] = data['f0']
                        
                        #tangents = (data['f1'], data['f2'])
                        #if (data['f1']**2 + data['f2']**2) ** .5 > 0.05:
                        #    found_tangents.append(tangents)
                        if frame not in loc_tangents:
                            loc_tangents[frame] = {'in': [None, None, None], 'out': [None, None, None]}

                        if channel_id == 104:
                            loc_tangents[frame]['in' ][0] = data['f1']
                            loc_tangents[frame]['out'][0] = data['f2']
                        elif channel_id == 105:                       
                            loc_tangents[frame]['in' ][1] = data['f1']
                            loc_tangents[frame]['out'][1] = data['f2']
                        elif channel_id == 106:                       
                            loc_tangents[frame]['in' ][2] = data['f1']
                            loc_tangents[frame]['out'][2] = data['f2']

                elif channel_id not in found_unknown:
                    found_unknown.append(channel_id)
                    self.report(type={'INFO'}, message="Unknown channel id {num}".format(num=channel_id))

            '''
            for frame, (loc, quat) in enumerate(zip(locs.values(), quats.values())):
                loc  = mathutils.Vector(loc) * self.scale
                quat = mathutils.Quaternion(quat)
            
                loc_mat = mathutils.Matrix.Translation(loc).to_4x4()
                rot_mat = quat.to_matrix().to_4x4()
                mat     = compat.mul(loc_mat, rot_mat)
                
                bone_loc  = bone.head_local.copy()
                bone_quat = bone.matrix.to_quaternion()
            
                if bone.parent:
                    parent = bone.parent
                else:
                    parent = base_bone
                    
                if parent:
                    mat = compat.convert_cm_to_bl_bone_space(mat)
                    mat = compat.mul(parent.matrix_local, mat)
                    mat = compat.convert_cm_to_bl_bone_rotation(mat)
                    pose_mat = bone.convert_local_to_pose(
                        matrix              = mat, 
                        matrix_local        = bone.matrix_local,
                        parent_matrix       = mathutils.Matrix.Identity(4),
                        parent_matrix_local = parent.matrix_local
                    )
                else:
                    mat = compat.convert_cm_to_bl_bone_rotation(mat)
                    mat = compat.convert_cm_to_bl_space(mat)
                    pose_mat = bone.convert_local_to_pose(
                        matrix       = mat, 
                        matrix_local = bone.matrix_local
                    )
            
                if self.is_location:
                    pose_bone.location = pose_mat.to_translation()
                    pose_bone.keyframe_insert('location'           , frame=frame * fps, group=pose_bone.name)
                if self.is_rotation:
                    pose_bone.rotation_quaternion = pose_mat.to_quaternion()
                    pose_bone.keyframe_insert('rotation_quaternion', frame=frame * fps, group=pose_bone.name)
                if max_frame < frame * fps:
                    max_frame = frame * fps
            '''            
            
            def _apply_tangents(fcurves, keyframes, tangents):
                for axis_index, axis_keyframes in enumerate(keyframes):
                    fcurve = fcurves[axis_index]
                    fcurve.update() # make sure automatic handles are calculated
                    axis_keyframes.sort() # make sure list is in order
                    for keyframe_index, frame in enumerate(axis_keyframes):
                        tangent_in  = tangents[frame]['in' ][axis_index]
                        tangent_out = tangents[frame]['out'][axis_index]

                        vec_in   = mathutils.Vector((1, tangent_in  / fps))   
                        vec_out  = mathutils.Vector((1, tangent_out / fps))

                        this_keyframe = fcurve.keyframe_points[keyframe_index  ]
                        next_keyframe = fcurve.keyframe_points[keyframe_index+1] if keyframe_index+1 < len(axis_keyframes) else None
                        last_keyframe = fcurve.keyframe_points[keyframe_index-1] if keyframe_index-1 >= 0                  else None
                        
                        if vec_in.y != vec_out.y:
                            this_keyframe.handle_left_type  = 'FREE'
                            this_keyframe.handle_right_type = 'FREE'
                        else:
                            this_keyframe.handle_left_type  = 'ALIGNED'
                            this_keyframe.handle_right_type = 'ALIGNED'

                        this_co = mathutils.Vector(this_keyframe.co)
                        next_co = mathutils.Vector(next_keyframe.co) if next_keyframe else None
                        last_co = mathutils.Vector(last_keyframe.co) if last_keyframe else None
                        if not next_keyframe:
                            next_keyframe = fcurve.keyframe_points[0]
                            if next_keyframe and next_keyframe != this_keyframe:
                                next_co = mathutils.Vector(next_keyframe.co)
                                next_co.x += max_frame
                        if not last_keyframe:
                            last_keyframe = fcurve.keyframe_points[len(axis_keyframes)-1]
                            if last_keyframe and last_keyframe != this_keyframe:
                                last_co = mathutils.Vector(last_keyframe.co)
                                last_co.x -= max_frame

                        factor = 3
                        dist_in  = (last_co.x - this_co.x) / factor if factor and last_co else None
                        dist_out = (next_co.x - this_co.x) / factor if factor and next_co else None
                        if not dist_in and not dist_out:
                            dist_in  = this_keyframe.handle_left[0]  - this_co.x
                            dist_out = this_keyframe.handle_right[0] - this_co.x
                        elif not dist_in:
                            dist_in  = -dist_out
                        elif not dist_out:
                            dist_out = -dist_in

                        this_keyframe.handle_left  = vec_in  * dist_in  + this_co
                        this_keyframe.handle_right = vec_out * dist_out + this_co


            if self.is_location:
                loc_fcurves = [None, None, None]
                loc_keyframes = [[],[],[]]
                rna_data_path = 'pose.bones["{bone_name}"].location'.format(bone_name=bone.name)
                for axis_index in range(0, 3):
                    new_fcurve = fcurves.find(rna_data_path, index=axis_index)
                    if not new_fcurve:
                        new_fcurve = fcurves.new(rna_data_path, index=axis_index, action_group=pose_bone.name)
                    loc_fcurves[axis_index] = new_fcurve
                
                def _convert_loc(loc) -> mathutils.Vector:
                    loc = mathutils.Vector(loc) * self.scale
                    #bone_loc = bone.head_local.copy()
                    #
                    #if bone.parent:
                    #    #loc.x, loc.y, loc.z = -loc.y, -loc.x, loc.z
                    #
                    #    #co.x, co.y, co.z = -co.y, co.z, co.x
                    #    #loc.x, loc.y, loc.z = loc.z, -loc.x, loc.y
                    #    #mat = mathutils.Matrix(
                    #    #    [( 0,  0,  1,  0), 
                    #    #     (-1,  0,  0,  0), 
                    #    #     ( 0,  1,  0,  0),
                    #    #     ( 0,  0,  0,  1)]
                    #    #)
                    #    #loc = compat.mul(mat, loc)
                    #
                    #    loc = compat.convert_cm_to_bl_bone_space(loc)
                    #
                    #    bone_loc = bone_loc - bone.parent.head_local
                    #    bone_loc.rotate(bone.parent.matrix_local.to_quaternion().inverted())
                    #else:
                    #    #loc.x, loc.y, loc.z = loc.x, loc.z, loc.y
                    #    loc = compat.convert_cm_to_bl_space(loc)
                    #
                    #result_loc = loc - bone_loc
                    if bone.parent:
                        loc = compat.convert_cm_to_bl_bone_space(loc)
                        loc = compat.mul(bone.parent.matrix_local, loc)
                    else:
                        loc = compat.convert_cm_to_bl_space(loc)
                    return compat.mul(bone.matrix_local.inverted(), loc)

                for frame, loc in locs.items():
                    result_loc = _convert_loc(loc)
                    #pose_bone.location = result_loc

                    #pose_bone.keyframe_insert('location', frame=frame * fps, group=pose_bone.name)
                    if max_frame < frame * fps:
                        max_frame = frame * fps
     
                    for fcurve in loc_fcurves:
                        keyframe_type = 'KEYFRAME'
                        tangents = loc_tangents[frame]
                        if tangents:
                            tangents = mathutils.Vector((tangents['in'][fcurve.array_index], tangents['out'][fcurve.array_index]))
                            if tangents.magnitude < 1e-6:
                                keyframe_type = 'JITTER'
                            elif tangents.magnitude > 0.1:
                                keyframe_type = 'EXTREME'

                        keyframe = fcurve.keyframe_points.insert(
                            frame         = frame * fps                   , 
                            value         = result_loc[fcurve.array_index], 
                            options       = {'FAST'}                      , 
                            keyframe_type = keyframe_type
                        )
                        keyframe.type = keyframe_type
                        loc_keyframes[fcurve.array_index].append(frame)

                if self.is_loop:
                    for fcurve in loc_fcurves:
                        new_modifier = fcurve.modifiers.new('CYCLES')

                if self.is_tangents:
                    for frame, tangents in loc_tangents.items():
                        tangent_in  = mathutils.Vector(tangents['in' ]) * self.scale
                        tangent_out = mathutils.Vector(tangents['out']) * self.scale
                        if bone.parent:
                            tangent_in  = compat.convert_cm_to_bl_bone_space(tangent_in )
                            tangent_out = compat.convert_cm_to_bl_bone_space(tangent_out)
                        else:
                            tangent_in  = compat.convert_cm_to_bl_space(tangent_in )
                            tangent_out = compat.convert_cm_to_bl_space(tangent_out)
                        tangents['in' ][:] = tangent_in [:]
                        tangents['out'][:] = tangent_out[:]

                    _apply_tangents(loc_fcurves, loc_keyframes, loc_tangents)
                        
            
            
            if self.is_rotation:
                quat_fcurves = [None, None, None, None]
                quat_keyframes = [[],[],[],[]]
                rna_data_path = 'pose.bones["{bone_name}"].rotation_quaternion'.format(bone_name=pose_bone.name)
                for axis_index in range(0, 4):
                    new_fcurve = fcurves.find(rna_data_path, index=axis_index)
                    if not new_fcurve:
                        new_fcurve = fcurves.new(rna_data_path, index=axis_index, action_group=pose_bone.name)
                    quat_fcurves[axis_index] = new_fcurve


                bone_quat = bone.matrix.to_quaternion()
                def _convert_quat(quat) -> mathutils.Quaternion:
                    quat = mathutils.Quaternion(quat)
                    #orig_quat = quat.copy()
                    '''Can't use matrix transforms here as they would mess up interpolation.'''
                    if bone.parent:
                        quat.w, quat.x, quat.y, quat.z = quat.w, -quat.z, quat.x, -quat.y
                        #quat_mat = compat.convert_cm_to_bl_bone_space(quat.to_matrix().to_4x4())
                        #quat_mat = compat.convert_cm_to_bl_bone_rotation(quat_mat)
                    else:
                        quat.w, quat.x, quat.y, quat.z = quat.w, -quat.z, quat.x, -quat.y
                        quat = compat.mul(mathutils.Matrix.Rotation(math.radians(-90.0), 4, 'Z').to_quaternion(), quat)
                        #quat_mat = compat.convert_cm_to_bl_space(quat.to_matrix().to_4x4())
                        #quat = compat.convert_cm_to_bl_bone_rotation(quat_mat).to_quaternion()
                    quat = compat.mul(bone_quat.inverted(), quat)
                    #quat.make_compatible(orig_quat)
                    return quat
                        
                for frame, quat in quats.items():
                    result_quat = _convert_quat(quat)
                    #pose_bone.rotation_quaternion = result_quat.copy()
            
                    #pose_bone.keyframe_insert('rotation_quaternion', frame=frame * fps, group=pose_bone.name)
                    if max_frame < frame * fps:
                        max_frame = frame * fps
                    
                    for fcurve in quat_fcurves:
                        keyframe_type = 'KEYFRAME'
                        tangents = quat_tangents[frame]
                        if tangents:
                            tangents = mathutils.Vector((tangents['in'][fcurve.array_index], tangents['out'][fcurve.array_index]))
                            if tangents.magnitude < 1e-6:
                                keyframe_type = 'JITTER'
                            elif tangents.magnitude > 0.1:
                                keyframe_type = 'EXTREME'
                        
                        keyframe = fcurve.keyframe_points.insert(
                            frame         = frame * fps                     , 
                            value         = result_quat[fcurve.array_index] , 
                            options       = {'FAST'}                        , 
                            keyframe_type = keyframe_type
                        )
                        keyframe.type = keyframe_type
                        quat_keyframes[fcurve.array_index].append(frame)

                if self.is_loop:
                    for fcurve in quat_fcurves:
                        new_modifier = fcurve.modifiers.new('CYCLES')
                
                if self.is_tangents:
                    for frame, tangents in quat_tangents.items():
                        tangents['in' ][:] = _convert_quat(tangents['in' ])[:]
                        tangents['out'][:] = _convert_quat(tangents['out'])[:]

                    _apply_tangents(quat_fcurves, quat_keyframes, quat_tangents)
                            


        if found_tangents:
            self.report(type={'INFO'}, message="Found the following tangent values:")
            for f1, f2 in found_tangents:
                self.report(type={'INFO'}, message="f1 = {float1}, f2 = {float2}".format(float1=f1, float2=f2))
            self.report(type={'INFO'}, message="Found the above tangent values.")  
            self.report(type={'WARNING'}, message="Found {count} large tangents. Blender animation may not interpolate properly. See log for more info.".format(count=len(found_tangents)))  
        if found_unknown:
            self.report(type={'INFO'}, message="Found the following unknown channel IDs:")
            for channel_id in found_unknown:
                self.report(type={'INFO'}, message="id = {id}".format(id=channel_id))
            self.report(type={'INFO'}, message="Found the above unknown channel IDs.")  
            self.report(type={'WARNING'}, message="Found {count} unknown channel IDs. Blender animation may be missing some keyframes. See log for more info.".format(count=len(found_unknown)))

        if self.set_frame:
            context.scene.frame_start = 0
            context.scene.frame_end = max_frame
            context.scene.frame_set(0)

        return {'FINISHED'}


# メニューに登録する関数
def menu_func(self, context):
    self.layout.operator(CNV_OT_import_cm3d2_anm.bl_idname, icon_value=common.kiss_icon())
