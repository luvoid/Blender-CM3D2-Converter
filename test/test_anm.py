import bpy
from mathutils import Vector, Quaternion

from .blenderunittest import BlenderTestCase
from .profilehelpers import dump_test_stats, Profile, LineProfile

import cm3d2converter

class AnmTestCase(BlenderTestCase):
    
    def assertPoseEqual(self, pose1: bpy.types.Pose, pose2: bpy.types.Pose, *, allow_missing_bones=False, msg=None):
        msg = f" : {msg}" if not msg is None else ""
        
        bpy.context.view_layer.update()
        
        for bone1 in pose1.bones:
            bone1: bpy.types.PoseBone
            bone2: bpy.types.PoseBone = pose2.bones.get(bone1.name)
            if bone2 is None:
                if not allow_missing_bones:
                    raise AssertionError(f"Could not find bone {bone1.name} in {pose2}")
                else:
                    continue
            
            rtol = 1e-1
            atol = 1
            
            self.assertVectorAlmostEqual(bone1.location, bone2.location,
                                         rtol=rtol, atol=atol,
                                         msg=f"pose.bones[\"{bone1.name}\"].location not equal" + msg)
            self.assertQuaternionAlmostEqual(bone1.rotation_quaternion, bone2.rotation_quaternion,
                                             rtol=rtol*3, atol=atol*3,
                                             msg=f"pose.bones[\"{bone1.name}\"].rotation_quaternion not equal" + msg)
            self.assertVectorAlmostEqual(bone1.scale, bone2.scale,
                                         rtol=1e-3, atol=1e-4,
                                         msg=f"pose.bones[\"{bone1.name}\"].scale not equal" + msg)
            
            #loc_diff: Vector = bone2.location - bone1.location
            #rot_diff: Quaternion = bone2.rotation_quaternion - bone1.rotation_quaternion
            #scl_diff: Vector = bone2.scale - bone1.scale
            #
            ## TODO : Use a proper epislon-based floating point precision check
            #self.assertAlmostEqual(loc_diff.magnitude * 0.01, 0, 1, msg=f"loc diff of {bone1.name} is {loc_diff}")
            #self.assertAlmostEqual(rot_diff.magnitude * 0.01, 0, 1, msg=f"rot diff of {bone1.name} is {rot_diff}")
            #self.assertAlmostEqual(scl_diff.magnitude * 0.01, 0, 1, msg=f"scl diff of {bone1.name} is {scl_diff}")

    def assertPoseFramesEqual(self, pose1: bpy.types.Pose, pose2: bpy.types.Pose, start: int, stop: int, *,
                              allow_missing_bones=False, msg=None):
        msg = f" : {msg}" if not msg is None else ""
        
        for frame in range(start, stop):
            bpy.context.scene.frame_set(frame=int(frame))
            bpy.context.view_layer.update()
            self.assertPoseEqual(pose1, pose2, 
                                 allow_missing_bones=allow_missing_bones,
                                 msg=f"@ frame {frame}" + msg)


class AnmTest(AnmTestCase):
    def test_anm_import(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=f'{self.resources_dir}/tpose.anm')

    def test_anm_export(self):
        tpose_object: bpy.types.Object = bpy.data.objects.get('Tスタンス素体.armature')
        self.activate_object(tpose_object)

        bpy.ops.export_anim.export_cm3d2_anm(
            filepath=f'{self.output_dir}/{self._testMethodName}.anm',
            is_backup=False
        )

    def test_anm_recursive(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/tpose.anm'
        out_file_0 = f'{self.output_dir}/{self._testMethodName}_0.anm'
        out_file_1 = f'{self.output_dir}/{self._testMethodName}_1.anm'
        out_file_2 = f'{self.output_dir}/{self._testMethodName}_2.anm'

        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_0)

        bpy.ops.object.duplicate()
        body001_armature_copy: bpy.types.Object = bpy.data.objects.get('body001.body.armature.001')
        self.activate_object(body001_armature_copy)

        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_0)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_1)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_1)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_2)

        with open(in_file, 'rb') as reader:
            expected_data = reader.read()
        with open(out_file_0, 'rb') as reader:
            actual_data_0 = reader.read()
        with open(out_file_1, 'rb') as reader:
            actual_data_1 = reader.read()
        with open(out_file_2, 'rb') as reader:
            actual_data_2 = reader.read()
        print(len(expected_data))
        print(len(actual_data_0))
        print(len(actual_data_1))
        print(len(actual_data_2))

        # Check the loss
        pose: bpy.types.Pose = body001_armature_object.pose
        pose_copy: bpy.types.Pose = body001_armature_copy.pose
        self.assertPoseEqual(pose, pose_copy, allow_missing_bones=True)

    def testprofile_anm_import(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/dance_cm3d21_pole_001_fa_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d2_001_zoukin.anm'
        in_file = f'{self.resources_dir}/tpose.anm'

        #with ProfileLog(self.test_anm_recursive.__name__):
        lineprof = LineProfile()
        lineprof.add_module(cm3d2converter.anm_import)
        prof = Profile()
        lineprof.enable()
        prof.enable()

        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)

        prof.disable()

        dump_test_stats(self, prof, lineprof)

    def testprofile_anm_export(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/dance_cm3d_001_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d21_pole_001_fa_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d2_001_zoukin.anm'
        in_file = f'{self.resources_dir}/tpose.anm'
        out_file = f'{self.output_dir}/{self._testMethodName}.anm'


        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)

        #with ProfileLog(self.test_anm_recursive.__name__):
        lineprof = LineProfile()
        lineprof.add_module(cm3d2converter.anm_export)
        prof = Profile()
        lineprof.enable()
        prof.enable()

        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file)

        dump_test_stats(self, prof, lineprof)

    def testprofile_anm_export_with_warmup(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        in_file = f'{self.resources_dir}/dance_cm3d_001_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d21_pole_001_fa_f1.anm'
        in_file = f'{self.resources_dir}/dance_cm3d2_001_zoukin.anm'
        in_file = f'{self.resources_dir}/tpose.anm'
        out_file = f'{self.output_dir}/{self._testMethodName}.anm'


        bpy.ops.import_anim.import_cm3d2_anm(filepath=in_file)
        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file)

        #with ProfileLog(self.test_anm_recursive.__name__):
        lineprof = LineProfile()
        lineprof.add_module(cm3d2converter.anm_export)
        prof = Profile()
        lineprof.enable()
        prof.enable()

        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file)

        dump_test_stats(self, prof, lineprof)

    def test_exanm(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)

        bpy.ops.object.duplicate()
        body001_armature_copy: bpy.types.Object = bpy.data.objects.get('body001.body.armature.001')

        out_file_0 = f'{self.output_dir}/{self._testMethodName}.ex.anm'

        self.activate_object(body001_armature_object)
        pose: bpy.types.Pose = body001_armature_object.pose
        neck: bpy.types.PoseBone = pose.bones.get('Bip01 Neck')
        neck.scale = Vector((1, 10, 20))
        print(neck.scale)

        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file_0, is_scale=True)

        self.activate_object(body001_armature_copy)
        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file_0)

        # Check the loss
        pose: bpy.types.Pose = body001_armature_object.pose
        pose_copy: bpy.types.Pose = body001_armature_copy.pose
        for bone in pose.bones:
            bone: bpy.types.PoseBone
            bone_copy: bpy.types.PoseBone = pose_copy.bones.get(bone.name)
            if bone_copy is None:
                print(f"Could not find bone {bone.name} in copied armature")
                continue
            loc_expected = bone.location
            loc_actual   = bone_copy.location
            rot_expected = bone.rotation_quaternion
            rot_actual   = bone_copy.rotation_quaternion
            scl_expected = bone.scale
            scl_actual   = bone_copy.scale

            loc_diff: Vector = loc_actual - loc_expected
            rot_diff: Quaternion = rot_actual - rot_expected
            scl_diff: Vector = scl_actual - scl_expected

            # TODO : Use a proper epislon-based floating point precision check
            self.assertAlmostEqual(loc_diff.magnitude * 0.01, 0, 1, msg=f"loc of {bone.name} expected {loc_expected}, got {loc_actual}")
            self.assertAlmostEqual(rot_diff.magnitude * 0.01, 0, 1, msg=f"rot of {bone.name} expected {rot_expected}, got {rot_actual}")
            self.assertAlmostEqual(scl_diff.magnitude * 0.01, 0, 1, msg=f"scl of {bone.name} expected {scl_expected}, got {scl_actual}")


class LongAnmTest(AnmTestCase):
    def test_long_anm(self):
        """There may be a bug where exporting an animation with 
        many frames will cause Blender to freeze
        """
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)
        
        bpy.ops.export_anim.export_cm3d2_anm(
            filepath=f'{self.output_dir}/{self._testMethodName}.anm',
            is_backup=False,
            frame_start=1,
            frame_end=4000,
        )
        
    def testprofile_long_anm(self):
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)
        
        lineprof = LineProfile()
        lineprof.add_module(cm3d2converter.anm_export)
        prof = Profile()
        lineprof.enable()
        prof.enable()
        
        bpy.ops.export_anim.export_cm3d2_anm(
            filepath=f'{self.output_dir}/{self._testMethodName}.anm',
            is_backup=False,
            frame_start=1,
            frame_end=7200,
        )
        
        dump_test_stats(self, prof, lineprof)


class HotdogAnmTest(AnmTestCase):
    # override
    @property
    def blend_file_path(self) -> str:
        return f'{self.resources_dir}/hotdog.blend'
    
    def test_hotdog_export(self):
        hotdog_armature_object: bpy.types.Object = bpy.data.objects.get('hotdog 아마튜어')
        self.activate_object(hotdog_armature_object)

        bpy.ops.export_anim.export_cm3d2_anm(filepath=f'{self.output_dir}/{self._testMethodName}.ex.anm', 
                                             is_scale=True)

    def test_hotdog_reimport(self):
        hotdog_armature_object: bpy.types.Object = bpy.data.objects.get('hotdog 아마튜어')
        self.activate_object(hotdog_armature_object)

        out_file = f'{self.output_dir}/{self._testMethodName}.ex.anm'

        bpy.ops.export_anim.export_cm3d2_anm(filepath=out_file, is_scale=True)
        
        self.activate_object(hotdog_armature_object)
        bpy.ops.object.duplicate()
        copy_armature_object = bpy.context.active_object
        
        bpy.ops.import_anim.import_cm3d2_anm(filepath=out_file, is_scale=True)
        
        self.assertPoseFramesEqual(hotdog_armature_object.pose, copy_armature_object.pose,
                                   bpy.context.scene.frame_start, bpy.context.scene.frame_end)


class VanillaAnmTest(AnmTestCase):
    """If not exporting with any extended anm features, it should be
    importable into the game without COM3D2.ExtendedAnm.Plugin.dll
    """
    
    def test_vanilla_anm_no_scale(self):
        """Make sure there are no channels with scale keys"""
        body001_armature_object: bpy.types.Object = bpy.data.objects.get('body001.body.armature')
        self.activate_object(body001_armature_object)
        
        out_file = f'{self.output_dir}/{self._testMethodName}.anm'
        
        bpy.ops.export_anim.export_cm3d2_anm(
            filepath=out_file,
            is_backup=False,
            frame_start=1,
            frame_end=4000,
            is_scale=False,
        )
        
        from CM3D2.Serialization.Files import Anm
        from cm3d2converter import fileutil
        
        with open(out_file, 'rb') as anm_file: 
            anm = fileutil.deserialize_from_file(Anm, anm_file)
        
        for track in anm.tracks:
            for channel in track.channels:
                channel: Anm.Channel
                self.assertNotEqual(channel.channelId, Anm.ChannelIdType.ExLocalScaleX)
                self.assertNotEqual(channel.channelId, Anm.ChannelIdType.ExLocalScaleY)
                self.assertNotEqual(channel.channelId, Anm.ChannelIdType.ExLocalScaleZ)
        
        
        
        
        
