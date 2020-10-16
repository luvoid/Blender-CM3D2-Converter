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

    frame_start = bpy.props.IntProperty(name="Starting Frame", default=0, min=0, max=99999, soft_min=0, soft_max=99999, step=1)
    frame_end = bpy.props.IntProperty(name="Last Frame", default=0, min=0, max=99999, soft_min=0, soft_max=99999, step=1)
    key_frame_count = bpy.props.IntProperty(name="Number of key frames", default=1, min=1, max=99999, soft_min=1, soft_max=99999, step=1)
    time_scale = bpy.props.FloatProperty(name="Playback Speed", default=1.0, min=0.1, max=10.0, soft_min=0.1, soft_max=10.0, step=10, precision=1)
    is_keyframe_clean = bpy.props.BoolProperty(name="Clean Keyframes", default=True)
    is_smooth_handle = bpy.props.BoolProperty(name="Smooth Transitions", default=True)

    items = [
        ('ARMATURE', "Armature", "", 'OUTLINER_OB_ARMATURE', 1),
        ('ARMATURE_PROPERTY', "Armature Data", "", 'ARMATURE_DATA', 2),
    ]
    bone_parent_from = bpy.props.EnumProperty(items=items, name="Bone Parent From", default='ARMATURE_PROPERTY')

    is_remove_alone_bone = bpy.props.BoolProperty(name="Remove Loose Bones", default=True)
    is_remove_ik_bone = bpy.props.BoolProperty(name="Remove IK Bones", default=True)
    is_remove_serial_number_bone = bpy.props.BoolProperty(name="Remove Duplicate Numbers", default=True)
    is_remove_japanese_bone = bpy.props.BoolProperty(name="Remove Japanese Characters from Bones", default=True)

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
            self.filepath = common.default_cm3d2_dir(prefs.anm_export_path, None, "anm")
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end
        self.scale = 1.0 / prefs.scale
        self.is_backup = bool(prefs.backup_ext)
        self.key_frame_count = (context.scene.frame_end - context.scene.frame_start) + 1

        ob = context.active_object
        arm = ob.data
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

        box = self.layout.box()
        sub_box = box.box()
        row = sub_box.row()
        row.prop(self, 'frame_start')
        row.prop(self, 'frame_end')
        sub_box.prop(self, 'key_frame_count')
        sub_box.prop(self, 'time_scale')
        sub_box.prop(self, 'is_keyframe_clean', icon='DISCLOSURE_TRI_DOWN')
        sub_box.prop(self, 'is_smooth_handle', icon='SMOOTHCURVE')

        sub_box = box.box()
        sub_box.label("Destination of bone parent information", icon='FILE_PARENT')
        sub_box.prop(self, 'bone_parent_from', icon='FILE_PARENT', expand=True)

        sub_box = box.box()
        sub_box.label("Bones to Exclude", icon='X')
        column = sub_box.column(align=True)
        column.prop(self, 'is_remove_alone_bone', icon='UNLINKED')
        column.prop(self, 'is_remove_ik_bone', icon='CONSTRAINT_BONE')
        column.prop(self, 'is_remove_serial_number_bone', icon='SEQUENCE')
        column.prop(self, 'is_remove_japanese_bone', icon=compat.icon('HOLDOUT_ON'))

    def execute(self, context):
        common.preferences().anm_export_path = self.filepath

        try:
            file = common.open_temporary(self.filepath, 'wb', is_backup=self.is_backup)
        except:
            self.report(type={'ERROR'}, message="Failed to open this file, possibily inaccessible.")
            return {'CANCELLED'}

        try:
            with file:
                self.write_animation(context, file)
        except common.CM3D2ExportException as e:
            self.report(type={'ERROR'}, message=str(e))
            return {'CANCELLED'}

        return {'FINISHED'}

    def write_animation(self, context, file):
        ob = context.active_object
        arm = ob.data
        pose = ob.pose
        fps = context.scene.render.fps

        common.write_str(file, 'CM3D2_ANIM')
        file.write(struct.pack('<i', self.version))

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
                bones.append(bone)
                continue

            bones_queue.append(bone)

        anm_data_raw = {}

        class KeyFrame:
            def __init__(self, time, value):
                self.time = time
                self.value = value
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

                pose_mat = ob.convert_space(pose_bone=pose_bone, matrix=pose_bone.matrix, from_space='POSE', to_space='WORLD')
                if bone_parents[bone.name]:
                    parent_mat = ob.convert_space(pose_bone=pose.bones[bone_parents[bone.name].name], matrix=pose.bones[bone_parents[bone.name].name].matrix, from_space='POSE', to_space='WORLD')
                    pose_mat = compat.mul(parent_mat.inverted(), pose_mat)

                loc = pose_mat.to_translation() * self.scale
                rot = pose_mat.to_quaternion()

                if bone.name in pre_rots:
                    if 5.0 < pre_rots[bone.name].rotation_difference(rot).angle:
                        rot.w, rot.x, rot.y, rot.z = -rot.w, -rot.x, -rot.y, -rot.z
                pre_rots[bone.name] = rot.copy()

                if bone_parents[bone.name]:
                    loc.x, loc.y, loc.z = -loc.y, -loc.x, loc.z
                    rot.w, rot.x, rot.y, rot.z = rot.w, rot.y, rot.x, -rot.z
                else:
                    loc.x, loc.y, loc.z = -loc.x, loc.z, -loc.y

                    fix_quat = mathutils.Euler((0, 0, math.radians(-90)), 'XYZ').to_quaternion()
                    fix_quat2 = mathutils.Euler((math.radians(-90), 0, 0), 'XYZ').to_quaternion()
                    rot = compat.mul3(rot, fix_quat, fix_quat2)

                    rot.w, rot.x, rot.y, rot.z = -rot.y, -rot.z, -rot.x, rot.w

                if not self.is_keyframe_clean or key_frame_index == 0 or key_frame_index == self.key_frame_count - 1:
                    anm_data_raw[bone.name]["LOC"][time] = loc.copy()
                    anm_data_raw[bone.name]["ROT"][time] = rot.copy()

                    if self.is_keyframe_clean:
                        same_locs[bone.name].append(KeyFrame(time, loc.copy()))
                        same_rots[bone.name].append(KeyFrame(time, rot.copy()))
                else:
                    def is_mismatch(a, b):
                        return 0.000001 < abs(a - b)

                    a, b = loc, same_locs[bone.name][-1].value
                    if is_mismatch(a.x, b.x) or is_mismatch(a.y, b.y) or is_mismatch(a.z, b.z):
                        if 2 <= len(same_locs[bone.name]):
                            anm_data_raw[bone.name]["LOC"][same_locs[bone.name][-1].time] = same_locs[bone.name][-1].value.copy()
                        anm_data_raw[bone.name]["LOC"][time] = loc.copy()
                        same_locs[bone.name] = [KeyFrame(time, loc.copy())]
                    else:
                        same_locs[bone.name].append(KeyFrame(time, loc.copy()))

                    a, b = rot, same_rots[bone.name][-1].value
                    if is_mismatch(a.w, b.w) or is_mismatch(a.x, b.x) or is_mismatch(a.y, b.y) or is_mismatch(a.z, b.z):
                        if 2 <= len(same_rots[bone.name]):
                            anm_data_raw[bone.name]["ROT"][same_rots[bone.name][-1].time] = same_rots[bone.name][-1].value.copy()
                        anm_data_raw[bone.name]["ROT"][time] = rot.copy()
                        same_rots[bone.name] = [KeyFrame(time, rot.copy())]
                    else:
                        same_rots[bone.name].append(KeyFrame(time, rot.copy()))

        anm_data = {}
        for bone_name, channels in anm_data_raw.items():
            anm_data[bone_name] = {100: {}, 101: {}, 102: {}, 103: {}, 104: {}, 105: {}, 106: {}}
            for time, loc in channels["LOC"].items():
                anm_data[bone_name][104][time] = loc.x
                anm_data[bone_name][105][time] = loc.y
                anm_data[bone_name][106][time] = loc.z
            for time, rot in channels["ROT"].items():
                anm_data[bone_name][100][time] = rot.x
                anm_data[bone_name][101][time] = rot.y
                anm_data[bone_name][102][time] = rot.z
                anm_data[bone_name][103][time] = rot.w

        for bone in bones:
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
                    y = keyframes_list[i][1]

                    if len(keyframes_list) <= 1:
                        file.write(struct.pack('<f', x))
                        file.write(struct.pack('<f', y))
                        file.write(struct.pack('<2f', 0.0, 0.0))
                        continue

                    if i == 0:
                        prev_x = x - (keyframes_list[i + 1][0] - x)
                        prev_y = y - (keyframes_list[i + 1][1] - y)
                        next_x = keyframes_list[i + 1][0]
                        next_y = keyframes_list[i + 1][1]
                    elif i == len(keyframes_list) - 1:
                        prev_x = keyframes_list[i - 1][0]
                        prev_y = keyframes_list[i - 1][1]
                        next_x = x + (x - keyframes_list[i - 1][0])
                        next_y = y + (y - keyframes_list[i - 1][1])
                    else:
                        prev_x = keyframes_list[i - 1][0]
                        prev_y = keyframes_list[i - 1][1]
                        next_x = keyframes_list[i + 1][0]
                        next_y = keyframes_list[i + 1][1]

                    prev_rad = (prev_y - y) / (prev_x - x)
                    next_rad = (next_y - y) / (next_x - x)
                    join_rad = (prev_rad + next_rad) / 2

                    file.write(struct.pack('<f', x))
                    file.write(struct.pack('<f', y))

                    if self.is_smooth_handle:
                        file.write(struct.pack('<2f', join_rad, join_rad))
                        # file.write(struct.pack('<2f', prev_rad, next_rad))
                    else:
                        file.write(struct.pack('<2f', 0.0, 0.0))

        file.write(struct.pack('<?', False))


# メニューに登録する関数
def menu_func(self, context):
    self.layout.operator(CNV_OT_export_cm3d2_anm.bl_idname, icon_value=common.kiss_icon())
