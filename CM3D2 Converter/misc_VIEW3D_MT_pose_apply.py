# 「3Dビュー」エリア → ポーズモード → Ctrl+A (ポーズ → 適用)
import bpy
import mathutils
from . import common
from . import compat


# メニュー等に項目追加
def menu_func(self, context):
    self.layout.separator()
    self.layout.operator('pose.apply_prime_field', icon_value=common.kiss_icon())
    self.layout.operator('pose.copy_prime_field' , icon_value=common.kiss_icon())

@compat.BlRegister()
class CNV_OT_copy_prime_field(bpy.types.Operator):
    bl_idname = 'pose.copy_prime_field'
    bl_label = "Copy Prime Field"
    bl_description = "Copies the visual pose of the selected object to the prime field of the active object"
    bl_options = {'REGISTER', 'UNDO'}

    #is_apply_armature_modifier = bpy.props.BoolProperty(name="Apply Armature Modifier", default=True )
    #is_deform_preserve_volume  = bpy.props.BoolProperty(name="Preserve Volume"        , default=True )
    #is_keep_original           = bpy.props.BoolProperty(name="Keep Original"          , default=True )
    #is_swap_prime_field        = bpy.props.BoolProperty(name="Swap Prime Field"       , default=False)
    #is_bake_drivers            = bpy.props.BoolProperty(name="Bake Drivers"           , default=False, description="Enable keyframing of driven properties, locking sliders and twist bones for final apply")
    
    is_only_selected = bpy.props.BoolProperty(name="Only Selected", default=True )
    is_key_location  = bpy.props.BoolProperty(name="Key Location" , default=True )
    is_key_rotation  = bpy.props.BoolProperty(name="Key Rotation" , default=True )
    is_key_scale     = bpy.props.BoolProperty(name="Key Scale"    , default=True )
    is_apply_prime   = bpy.props.BoolProperty(name="Apply Prime"  , default=False, options={'HIDDEN'})
    


    @classmethod
    def poll(cls, context):
        target_ob, source_ob = common.get_target_and_source_ob(context)
        if target_ob and source_ob:
            return True
        else:
            return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_only_selected')
        self.layout.prop(self, 'is_key_location' )
        self.layout.prop(self, 'is_key_rotation' )
        self.layout.prop(self, 'is_key_scale'    )

    def execute(self, context):
        target_ob, source_ob = common.get_target_and_source_ob(context)
        pose = target_ob.pose
        arm = target_ob.data

        pre_selected_pose_bones = context.selected_pose_bones
        pre_mode = target_ob.mode
        
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.constraints_clear()

        if not target_ob.pose_library:
             bpy.ops.poselib.new()
             poselib = target_ob.pose_library

        consts = []
        bones = pre_selected_pose_bones if self.is_only_selected else pose.bones
        for bone in bones:
            source_bone = source_ob.pose.bones.get(bone.name)
            if source_bone:
                if self.is_key_location or self.is_key_rotation:
                    const = bone.constraints.new('COPY_TRANSFORMS')
                    const.target = source_ob
                    const.subtarget = source_bone.name
                    consts.append(const)
                if self.is_key_scale:
                    const = bone.constraints.new('LIMIT_SCALE')
                    const.owner_space = 'LOCAL'
                    const.use_transform_limit = True
                    const.use_min_x = True
                    const.use_min_y = True
                    const.use_min_z = True
                    const.use_max_x = True
                    const.use_max_y = True
                    const.use_max_z = True
                    const.min_x = source_bone.scale.x
                    const.min_y = source_bone.scale.y
                    const.min_z = source_bone.scale.z
                    if source_ob.data.get("is T Stance"):
                        source_prime_scale = mathutils.Vector(source_bone.get('prime_scale',(1,1,1)))
                        const.min_x *= source_prime_scale.x
                        const.min_y *= source_prime_scale.y
                        const.min_z *= source_prime_scale.x
                    if arm.get("is T Stance"):
                        target_prime_scale = mathutils.Vector(bone.get('prime_scale', (1,1,1)))
                        const.min_x /= target_prime_scale.x
                        const.min_y /= target_prime_scale.y
                        const.min_z /= target_prime_scale.z
                    const.max_x = const.min_x
                    const.max_y = const.min_y
                    const.max_z = const.min_z
                    consts.append(const)

        #if True:
        #    return {'CANCELLED'}

        for i in range(2):
            is_prime_frame = not bool(i % 2) if arm.get("is T Stance") else bool(i % 2)
            pose_name = '__prime_field_pose' if is_prime_frame else '__base_field_pose'
            if self.is_apply_prime:
                is_prime_frame = not is_prime_frame
            
            #if self.is_key_scale and is_prime_frame:
            #    for const in consts:
            #        if const.type == 'LIMIT_SCALE':
            #            const.mute = not is_prime_frame
            #    bpy.ops.pose.visual_transform_apply()
            #    for bone in pose.bones:
            #        bone.keyframe_insert(data_path='scale', frame=i, group=bone.name)
            #    for const in consts:
            #        if const.type == 'LIMIT_SCALE':
            #            const.mute = is_prime_frame
            
            for const in consts:
                const.mute = not is_prime_frame
            if is_prime_frame:
                bpy.ops.pose.visual_transform_apply()
            else:
                bpy.ops.pose.transforms_clear()
            for bone in pose.bones:
                if self.is_key_location:
                    bone.keyframe_insert(data_path='location'           , frame=i, group=bone.name)
                if self.is_key_rotation:
                    bone.keyframe_insert(data_path='rotation_euler'     , frame=i, group=bone.name)
                    bone.keyframe_insert(data_path='rotation_quaternion', frame=i, group=bone.name)
                if self.is_key_scale: # and not is_prime_frame:
                    bone.keyframe_insert(data_path='scale'              , frame=i, group=bone.name)
                bpy.ops.poselib.pose_add(frame=i, name=pose_name)

        bpy.ops.pose.constraints_clear()
        bpy.ops.pose.transforms_clear()
        target_ob.animation_data_clear()

        bpy.ops.pose.select_all(action='DESELECT')
        if pre_selected_pose_bones:
            for bone in pre_selected_pose_bones:
                arm.bones[bone.name].select = True

        if pre_mode: 
            bpy.ops.object.mode_set(mode=pre_mode)
        
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_apply_prime_field(bpy.types.Operator):
    bl_idname = 'pose.apply_prime_field'
    bl_label = "現在のポーズで素体化"
    bl_description = "現在のポーズで衣装をモデリングしやすくする素体を作成します"
    bl_options = {'REGISTER', 'UNDO'}

    is_apply_armature_modifier   = bpy.props.BoolProperty(name="関係するメッシュのアーマチュアを適用", default=True)
    is_preserve_shape_key_values = bpy.props.BoolProperty(name="Preserve Shape Key Values", default=True , description="Ensure shape key values of child mesh objects are not changed")
    is_deform_preserve_volume    = bpy.props.BoolProperty(name="アーマチュア適用は体積を維持", default=True)
    is_keep_original             = bpy.props.BoolProperty(name="Keep Original"            , default=True , description="If the armature is already primed, don't replace the base pose with the current rest pose")
    is_swap_prime_field          = bpy.props.BoolProperty(name="Swap Prime Field"         , default=False)
    #is_bake_drivers              = bpy.props.BoolProperty(name="Bake Drivers"             , default=False, description="Enable keyframing of driven properties, locking sliders and twist bones for final apply")
    
    
    was_t_stance = False

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob and ob.type == 'ARMATURE':
            return True
        return False

    def invoke(self, context, event):
        self.was_t_stance = context.object.data.get('is T Stance')
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_apply_armature_modifier')

        col = self.layout.column()
        col.enabled = self.is_apply_armature_modifier
        col.prop(self , 'is_preserve_shape_key_values')
        col.prop(self , 'is_deform_preserve_volume'   )
        if compat.IS_LEGACY:
            col.prop(prefs, 'custom_normal_blend', icon=compat.icon('SNAP_NORMAL'  ), slider=True)

        self.layout.prop(self, 'is_bake_drivers')
        if self.was_t_stance:
            self.layout.prop(self, 'is_keep_original')

    def execute(self, context):
        ob = context.active_object
        arm = ob.data
        pose = ob.pose
        progress = 0

        pre_selected_objects = context.selected_objects
        pre_selected_pose_bones = context.selected_pose_bones
        pre_mode = ob.mode
        pre_frame = context.scene.frame_current

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        compat.set_select(ob, True)

        if self.is_swap_prime_field:
            #context.scene.frame_set(1)
            bpy.ops.poselib.apply_pose(pose_index=1)
            bpy.context.view_layer.update()

        if self.is_apply_armature_modifier and ob.children:
            override = context.copy()
            context.window_manager.progress_begin(0, len(ob.children)+1)  
            for child in ob.children:
                override['object'], override['active_object'] = child, child
                if child.type == 'MESH' and len(child.modifiers) and bpy.ops.object.forced_modifier_apply.poll(override):
                    for mod in child.modifiers:
                        if mod.type == 'ARMATURE':
                            mod.use_deform_preserve_volume = self.is_deform_preserve_volume
                            if not mod.object == ob:
                                had_armature = False
                            else:
                                had_armature = True
                                old_name                = mod.name                      
                                old_show_expanded       = mod.show_expanded             
                                old_show_in_editmode    = mod.show_in_editmode          
                                old_show_on_cage        = mod.show_on_cage              
                                old_show_render         = mod.show_render               
                                old_show_viewport       = mod.show_viewport             
                                old_use_apply_on_spline = mod.use_apply_on_spline       
                                old_invert_vertex_group = mod.invert_vertex_group       
                                old_use_bone_envelopes  = mod.use_bone_envelopes        
                                #old_use_multi_modifier  = mod.use_multi_modifier        
                                old_use_vertex_groups   = mod.use_vertex_groups         
                                old_vertex_group        = mod.vertex_group        
                    apply_results = bpy.ops.object.forced_modifier_apply(override, apply_viewport_visible=True, is_preserve_shape_key_values=self.is_preserve_shape_key_values, initial_progress=progress)
                    if ('FINISHED' in apply_results) and had_armature:
                        new_mod = child.modifiers.new(name=old_name, type='ARMATURE')
                        new_mod.object              = ob
                        new_mod.use_deform_preserve_volume = self.is_deform_preserve_volume
                        new_mod.show_expanded       = old_show_expanded      
                        new_mod.show_in_editmode    = old_show_in_editmode   
                        new_mod.show_on_cage        = old_show_on_cage       
                        new_mod.show_render         = old_show_render        
                        new_mod.show_viewport       = old_show_viewport      
                        new_mod.use_apply_on_spline = old_use_apply_on_spline
                        new_mod.invert_vertex_group = old_invert_vertex_group
                        new_mod.use_bone_envelopes  = old_use_bone_envelopes 
                        #new_mod.use_multi_modifier  = old_use_multi_modifier 
                        new_mod.use_vertex_groups   = old_use_vertex_groups  
                        new_mod.vertex_group        = old_vertex_group
                
                progress += 1
                context.window_manager.progress_update(progress)

        else:
            context.window_manager.progress_begin(0, 1)  

        temp_ob = ob.copy()
        temp_arm = arm.copy()
        temp_ob.data = temp_arm
        compat.link(context.scene, temp_ob)
        
        compat.set_active(context, ob)
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        for bone in ob.pose.bones:
            prime_scale = mathutils.Vector(bone.get('prime_scale', (1.0,1.0,1.0)))
            bone_scale = bone.scale #bone.matrix.to_scale()
            prime_scale.x *= bone_scale.x
            prime_scale.y *= bone_scale.y
            prime_scale.z *= bone_scale.z
            bone['prime_scale'] = prime_scale
            #bone['_RNA_UI']['prime_scale']['subtype'] = 'XYZ'
        bpy.ops.pose.armature_apply()
        bpy.ops.pose.constraints_clear()
        ob.animation_data_clear()
        
        if arm.get("is T Stance") and self.is_keep_original and not self.is_swap_prime_field:
            anim_data = temp_ob.animation_data
            if anim_data and anim_data.drivers:
                drivers = anim_data.drivers
                for driver in drivers.values():
                    drivers.remove(driver)
            #context.scene.frame_set(1)
            bpy.ops.pose.user_transforms_clear()
            bpy.ops.poselib.apply_pose(pose_index=1)
        else:
            compat.set_active(context, temp_ob)
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.pose.select_all(action='SELECT')
            temp_ob.animation_data_clear()
            bpy.ops.pose.transforms_clear()
            bpy.ops.object.mode_set(mode='OBJECT')
            compat.set_select(temp_ob, False)
        
        if self.is_swap_prime_field and arm.get('is T Stance'):
            arm['is T Stance'] = False
        else:
            arm['is T Stance'] = True

        # CNV_OT_copy_prime_field.execute()
        compat.set_select(temp_ob, True)
        compat.set_active(context, ob)
        bpy.context.view_layer.update()
        response = bpy.ops.pose.copy_prime_field(is_only_selected=False, is_key_location=True, is_key_scale=True, is_apply_prime=(not self.is_swap_prime_field))#is_key_location=self.is_bake_drivers, is_key_scale=self.is_bake_drivers, is_apply_prime=True)

        context.window_manager.progress_end()

        if not 'FINISHED' in response:
            return response

        common.remove_data(temp_arm)
        try:
            common.remove_data(temp_ob)
        except:
            pass
        
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')
        if pre_selected_pose_bones:
            for bone in pre_selected_pose_bones:
                arm.bones[bone.name].select = True

        if pre_selected_objects:
            for o in pre_selected_objects:
                compat.set_select(o, True)
        compat.set_active(context, ob)
        bpy.ops.object.mode_set(mode=pre_mode)

        context.scene.frame_set(pre_frame)



        return {'FINISHED'}
