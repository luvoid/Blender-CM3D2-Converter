# 「プロパティ」エリア → 「モディファイア」タブ
import os
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


# メニュー等に項目追加
def menu_func(self, context):
    ob = context.active_object
    if ob:
        if ob.type == 'MESH':
            me = ob.data
            if len(ob.modifiers):
                self.layout.operator('object.forced_modifier_apply', icon_value=common.kiss_icon())


@compat.BlRegister()
class CNV_UL_modifier_selector(common.CNV_UL_generic_selector):
    bl_label       = 'CNV_UL_modifier_selector'
    bl_options     = {'DEFAULT_CLOSED'}
    bl_region_type = 'WINDOW'
    bl_space_type  = 'PROPERTIES'

    # Constants (flags)
    # Be careful not to shadow FILTER_ITEM!
    #bitflag_forced_true  = 1 << 0
    #bitflag_forced_false = 1 << 1
    #force_values = False
    #did_force_values = False

    force_values = bpy.props.BoolProperty(
        name="force_values",
        default=False,
        options=set(),
    )

    did_force_values = bpy.props.BoolProperty(
        name="force_values",
        default=False,
        options=set(),
    )

    # This allows us to have mutually exclusive options, which are also all disable-able!
    def _gen_force_values(self, context):
        setattr(self, "force_values", True)
        setattr(self, "did_force_values", False)
        print("SET TRUE force_values =", self.force_values)
    
    def _gen_visible_update(name1, name2):
        def _u(self, context):
            self._gen_force_values(context)
            if (getattr(self, name1)):
                setattr(self, name2, False)
        return _u
    use_filter_viewport_visible = bpy.props.BoolProperty(
        name="Viewport",
        default=False,
        options=set(),
        description="Only enable modifiers visible in viewport",
        update=_gen_visible_update("use_filter_viewport_visible", "use_filter_renderer_visible"),
    )
    use_filter_renderer_visible = bpy.props.BoolProperty(
        name="Renderer",
        default=False,
        options=set(),
        description="Only enable modifiers visible in renderer",
        update=_gen_visible_update("use_filter_renderer_visible", "use_filter_viewport_visible"),
    )
    use_filter_reversed_visible = bpy.props.BoolProperty(
        name="Reverse Visible Filter",
        default=False,
        options=set(),
        description="Reverse the selected visible-in filter",
        update=_gen_force_values
    )


    use_filter_name_reverse = bpy.props.BoolProperty(
        name="Reverse Name",
        default=False,
        options=set(),
        description="Reverse name filtering",
    )

    def _gen_order_update(name1, name2):
        def _u(self, ctxt):
            if (getattr(self, name1)):
                setattr(self, name2, False)
        return _u
    use_order_name = bpy.props.BoolProperty(
        name="Name", default=False, options=set(),
        description="Sort groups by their name (case-insensitive)",
        update=_gen_order_update("use_order_name", "use_order_importance"),
    )
    use_filter_orderby_invert = bpy.props.BoolProperty(
        name="Order by Invert",
        default=False,
        options=set(),
        description="Invert the sort by order"
    )


    def draw_filter(self, context, layout):
        row = layout.row()
        row.label(text="Visible in:")
        subrow = row.row(align=True)
        subrow.prop(self, "use_filter_viewport_visible", toggle=True)
        subrow.prop(self, "use_filter_renderer_visible", toggle=True)
        icon = 'ZOOM_OUT' if self.use_filter_reversed_visible else 'ZOOM_IN'
        icon = compat.icon(icon)
        subrow.prop(self, "use_filter_reversed_visible", text="", icon=icon)

        super(CNV_UL_modifier_selector, self).draw_filter(context, layout)

    def filter_items(self, context, data, propname):
        flt_flags, flt_neworder = super(CNV_UL_modifier_selector, self).filter_items(context, data, propname)
        items = getattr(data, propname)

        if getattr(self, 'did_force_values'):
            setattr(self,'force_values', False)
        setattr(self, 'did_force_values', getattr(self, 'force_values'))

        print("CHECK force_values = ", getattr(self, 'force_values'))

        if self.use_filter_viewport_visible or self.use_filter_renderer_visible or getattr(self, 'force_values'):

            if not self.use_filter_reversed_visible:
                in_flag  = self.bitflag_forced_true 
                out_flag = ~(self.bitflag_forced_false | self.bitflag_soft_filter)
            else:
                in_flag  = self.bitflag_forced_false | self.bitflag_soft_filter
                out_flag = ~self.bitflag_forced_true

            for index, item in enumerate(items):
                if getattr(self, 'force_values'):
                    flt_flags[index] |= self.bitflag_forced_value

                if self.use_filter_viewport_visible and item.filter0:
                    flt_flags[index] |= in_flag
                    flt_flags[index] &= out_flag
                elif self.use_filter_renderer_visible and item.filter1:
                    flt_flags[index] |= in_flag
                    flt_flags[index] &= out_flag
                elif not self.use_filter_viewport_visible and not self.use_filter_renderer_visible:
                    pass
                else:
                    flt_flags[index] |= ~out_flag
                    flt_flags[index] &= ~in_flag

        return flt_flags, flt_neworder


@compat.BlRegister()
class CNV_OT_forced_modifier_apply(bpy.types.Operator):
    bl_idname = 'object.forced_modifier_apply'
    bl_label = "モディファイア強制適用"
    bl_description = "シェイプキーのあるメッシュのモディファイアでも強制的に適用します"
    bl_options = {'REGISTER', 'UNDO'}
    
    is_preserve_shape_key_values = bpy.props.BoolProperty(name="Preserve Shape Key Values", default=True , description="Ensure shape key values are not changed")

    #is_applies = bpy.props.BoolVectorProperty(name="適用するモディファイア", size=32, options={'SKIP_SAVE'})
    is_applies = bpy.props.CollectionProperty(type=common.CNV_SelectorItem)
    active_modifier = bpy.props.IntProperty(name="Active Modifier")

    apply_viewport_visible = bpy.props.BoolProperty(name="Apply Viewport-Visible Modifiers", default=False)
    apply_renderer_visible = bpy.props.BoolProperty(name="Apply Renderer-Visible Modifiers", default=False)

    initial_progress = bpy.props.FloatProperty(name="Progress", default=-1, options={'HIDDEN', 'SKIP_SAVE'})
    
    
    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return len(ob.modifiers)

    def invoke(self, context, event):
        ob = context.active_object
        if len(ob.modifiers) == 0:
            return {'CANCELLED'}

        for index, mod in enumerate(ob.modifiers):
            #if index >= 32: # luvoid : can only apply 32 modifiers at once.
            #    self.report(type={'WARNING'}, message="Can only apply the first 32 modifiers at once.")
            #    break
            icon = 'MOD_%s' % mod.type.replace('DECIMATE','DECIM').replace('SOFT_BODY','SOFT').replace('PARTICLE_SYSTEM','PARTICLES').replace('_SPLIT','SPLIT').replace('_PROJECT','PROJECT').replace('_DEFORM','DEFORM').replace('_SIMULATION','SIM').replace('_EDIT','').replace('_MIX','').replace('_PROXIMITY','').replace('_PAINT','PAINT')
            icon = compat.icon(icon)
            
            new_prop = None
            if index < len(self.is_applies):
                new_prop = self.is_applies[index]
            else:
                new_prop = self.is_applies.add()
            
            if new_prop.name == mod.name and new_prop.icon == icon:
                # It's probably the same one, ignore it
                pass
            else:
                new_prop.name      = mod.name
                new_prop.index     = index
                new_prop.value     = mod.show_viewport
                new_prop.preferred = new_prop.value
                new_prop.icon      = icon
                new_prop.filter0   = mod.show_viewport
                new_prop.filter1   = mod.show_render

        while len(self.is_applies) > len(ob.modifiers):
            self.is_applies.remove(len(self.is_applies)-1)

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        prefs = common.preferences()
        if compat.IS_LEGACY:
            self.layout.prop(prefs, 'custom_normal_blend'         , icon=compat.icon('SNAP_NORMAL'  ), slider=True)
        self.layout.prop(self , 'is_preserve_shape_key_values', icon=compat.icon('SHAPEKEY_DATA'), slider=True)
        self.layout.label(text="適用するモディファイア")
        ob = context.active_object

        #for index, mod in enumerate(ob.modifiers):
        #    if index >= 32: # luvoid : can only apply 32 modifiers at once.
        #        break
        #    icon = 'MOD_%s' % mod.type.replace('DECIMATE','DECIM').replace('SOFT_BODY','SOFT').replace('PARTICLE_SYSTEM','PARTICLES').replace('_SPLIT','SPLIT').replace('_PROJECT','PROJECT').replace('_DEFORM','DEFORM').replace('_SIMULATION','SIM').replace('_EDIT','').replace('_MIX','').replace('_PROXIMITY','').replace('_PAINT','PAINT')
        #    try:
        #        self.layout.prop(self, 'is_applies', text=mod.name, index=index, icon=icon)
        #    except:
        #        self.layout.prop(self, 'is_applies', text=mod.name, index=index, icon='MODIFIER')
        
        self.layout.template_list("CNV_UL_modifier_selector", "", self, "is_applies", self, "active_modifier")
        self.layout.label(text="Show filters", icon='FILE_PARENT')

    def execute(self, context):
        ob = context.object

        did_start_progress = False
        if self.initial_progress == -1:
            progress_start = 0
            context.window_manager.progress_begin(0, 1)
            did_start_progress = True
        else:
            progress_start = self.initial_progress

        if self.apply_viewport_visible or self.apply_renderer_visible:
            for index, mod in enumerate(ob.modifiers):
                new_prop = None
                if index < len(self.is_applies):
                    new_prop = self.is_applies[index]
                else:
                    new_prop = self.is_applies.add()
                
                new_prop.name      = mod.name
                new_prop.index     = index
                new_prop.value     = (self.apply_viewport_visible and mod.show_viewport) or (self.apply_renderer_visible and mod.show_render)

        # 対象が一つも無い場合はキャンセル扱いとする
        is_any = False
        for item in self.is_applies:
            if item.value:
                is_any = True
                break
        if not is_any:
            self.report(type={'INFO'}, message="適用対象のモディファイアがないため、キャンセルします")
            context.window_manager.progress_update(progress_start + 1)
            if did_start_progress:
                context.window_manager.progress_end()
            return {'CANCELLED'}

        custom_normal_blend = common.preferences().custom_normal_blend
        bpy.ops.object.mode_set(mode='OBJECT')

        me = ob.data
        is_shaped = bool(me.shape_keys)

        pre_selected_objects = context.selected_objects[:]
        pre_mode = ob.mode

        arm_ob = None
        if compat.IS_LEGACY:
            for mod in ob.modifiers:
                if mod.type == "ARMATURE":
                    arm_ob = mod.object

        progress = 0
        progress_count = 1
        progress_count += 2 if arm_ob else 0
        progress_count += len(me.shape_keys.key_blocks) * 3 if is_shaped else 0

        if is_shaped:
            pre_active_shape_key_index = ob.active_shape_key_index
            pre_relative_keys          = [None] * len(me.shape_keys.key_blocks)
            pre_shape_key_values       = [0]    * len(me.shape_keys.key_blocks)
            shape_names                = [""]   * len(me.shape_keys.key_blocks)
            shape_deforms              = [None] * len(me.shape_keys.key_blocks)
            for shape_index, shape in enumerate(me.shape_keys.key_blocks):
                pre_relative_keys   [shape_index] = shape.relative_key.name
                pre_shape_key_values[shape_index] = shape.value
                shape_names         [shape_index] = shape.name
                shape_deforms       [shape_index] = [shape.data[v.index].co.copy() for v in me.vertices]
                
                progress += 1
                context.window_manager.progress_update(progress_start + progress / progress_count)

            ob.active_shape_key_index = len(me.shape_keys.key_blocks) - 1
            for i in me.shape_keys.key_blocks[:]:
                ob.shape_key_remove(ob.active_shape_key)
            
            new_shape_deforms = []
            for shape_index, deforms in enumerate(shape_deforms):
                temp_ob = ob.copy()
                temp_me = me.copy()
                temp_ob.data = temp_me
                compat.link(context.scene, temp_ob)
                try:
                    for vert in temp_me.vertices:
                        vert.co = deforms[vert.index].copy()

                    override = context.copy()
                    override['object'] = temp_ob
                    for index, mod in enumerate(temp_ob.modifiers):
                        if self.is_applies[index].value:
                            try:
                                bpy.ops.object.modifier_apply(override, modifier=mod.name)
                            except:
                                temp_ob.modifiers.remove(mod)

                    new_shape_deforms.append([v.co.copy() for v in temp_me.vertices])
                except Exception as e:
                    #ob.modifiers.remove(mod)
                    self.report(type={'WARNING'}, message=f_tip_("Could not apply '{}' modifier \"{}\" to shapekey {}", mod.type, mod.name, shape_index))
                    print(f_("Error applying '{type}' modifier \"{name}\":\n\t", type=mod.type, name=mod.name), e)
                finally:
                    common.remove_data(temp_ob)
                    common.remove_data(temp_me)

                    progress += 1
                    context.window_manager.progress_update(progress_start + progress / progress_count)

        if ob.active_shape_key_index != 0:
            ob.active_shape_key_index = 0
            me.update()

        copy_modifiers = ob.modifiers[:]
        mod_count = len(copy_modifiers)
        mod_progress = 0
        override = context.copy()
        override['object'] = ob
        for index, mod in enumerate(copy_modifiers):
            #if index >= 32: # luvoid : can only apply 32 modifiers at once.
            #    break
            if self.is_applies[index].value and (mod.type != 'ARMATURE' or not compat.IS_LEGACY):
                if mod.type == 'MIRROR' and mod.use_mirror_vertex_groups:
                    if bpy.ops.object.decode_cm3d2_vertex_group_names.poll():
                        self.report(type={'WARNING'}, message="Vertex groups are not in blender naming style. Mirror modifier results may not be as expected")
                    for vg in ob.vertex_groups[:]:
                        replace_list = ((r'\.L$', ".R"), (r'\.R$', ".L"), (r'\.l$', ".r"), (r'\.r$', ".l"), (r'_L$', "_R"), (r'_R$', "_L"), (r'_l$', "_r"), (r'_r$', "_l"))
                        for before, after in replace_list:
                            mirrored_name = re.sub(before, after, vg.name)
                            if mirrored_name not in ob.vertex_groups:
                                ob.vertex_groups.new(override, name=mirrored_name)
                try:
                    bpy.ops.object.modifier_apply(override, modifier=mod.name)
                except Exception as e:
                    #ob.modifiers.remove(mod)
                    self.report(type={'ERROR', 'WARNING'}, message=f_tip_("Could not apply '{type}' modifier \"{name}\"", type=mod.type, name=mod.name))
                    print(f_("Error applying '{type}' modifier \"{name}\":\n\t", type=mod.type, name=mod.name), e)
            
            mod_progress += 1 if (mod.type != 'ARMATURE' or not compat.IS_LEGACY) else 0
            context.window_manager.progress_update( progress_start + (progress + mod_progress / mod_count) / progress_count )

        # Calculate custom normals for armature modifiers in legacy blender
        if arm_ob:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.object.mode_set(mode='OBJECT')

            arm = arm_ob.data
            arm_pose = arm_ob.pose

            pose_quats = {}
            for bone in arm.bones:
                pose_bone = arm_pose.bones[bone.name]

                bone_quat = bone.matrix_local.to_quaternion()
                pose_quat = pose_bone.matrix.to_quaternion()
                result_quat = compat.mul(pose_quat, bone_quat.inverted())

                pose_quats[bone.name] = result_quat.copy()

            custom_normals = []
            for loop in me.loops:
                vert = me.vertices[loop.vertex_index]
                no = vert.normal.copy()

                total_weight = 0.0
                for vge in vert.groups:
                    vg = ob.vertex_groups[vge.group]
                    try:
                        pose_quats[vg.name]
                    except KeyError:
                        continue
                    total_weight += vge.weight

                total_quat = mathutils.Quaternion()
                if total_weight != 0.0:
                    for vge in vert.groups:
                        vg = ob.vertex_groups[vge.group]
                        try:
                            total_quat = total_quat.slerp(pose_quats[vg.name], vge.weight / total_weight)
                        except KeyError:
                            pass
                
                no.rotate(total_quat)
                custom_normals.append(no)

            progress += 1
            context.window_manager.progress_update(progress_start + progress / progress_count)

        override = context.copy()
        override['object'] = ob
        for index, mod in enumerate(copy_modifiers):
            #if index >= 32: # luvoid : can only apply 32 modifiers at once.
            #    break
            if self.is_applies[index].value and (mod.type == 'ARMATURE' and compat.IS_LEGACY):
                try:
                    bpy.ops.object.modifier_apply(override, modifier=mod.name)
                except Exception as e:
                    #ob.modifiers.remove(mod)
                    self.report(type={'ERROR', 'WARNING'}, message=f_tip_("Could not apply '{mod_type}' modifier \"{mod_name}\"", mod_type=mod.type, mod_name=mod.name) )
                    print(f_("Could not apply '{mod_type}' modifier \"{mod_name}\":\n\t", mod_type=mod.type, mod_name=mod.name), e)
            
            mod_progress += 1 if (mod.type == 'ARMATURE' and compat.IS_LEGACY) else 0
            context.window_manager.progress_update( progress_start + (progress + mod_progress / mod_count) / progress_count )

        progress += 1
        context.window_manager.progress_update(progress_start + progress / progress_count)

        compat.set_active(context, ob)

        if is_shaped:
            for deforms in new_shape_deforms:
                if len(me.vertices) != len(deforms):
                    self.report(type={'ERROR'}, message="ミラー等が原因で頂点数が変わっているためシェイプキーを格納できません、中止するのでCtrl+Z等で元に戻し修正してください。")
                    context.window_manager.progress_update(progress_start + 1)
                    if did_start_progress:
                        context.window_manager.progress_end()
                    return {'FINISHED', 'CANCELLED'}

            for shape_index, deforms in enumerate(new_shape_deforms):
                bpy.ops.object.shape_key_add(context.copy(), from_mix=False)
                shape = ob.active_shape_key
                shape.name = shape_names[shape_index]

                for vert in me.vertices:
                    shape.data[vert.index].co = deforms[vert.index].copy()

                progress += 1
                context.window_manager.progress_update(progress_start + progress / progress_count)

            for shape_index, shape in enumerate(me.shape_keys.key_blocks):
                shape.relative_key = me.shape_keys.key_blocks[pre_relative_keys[shape_index]]
                if self.is_preserve_shape_key_values:
                    shape.value = pre_shape_key_values[shape_index]

            ob.active_shape_key_index = pre_active_shape_key_index

        for temp_ob in pre_selected_objects:
            compat.set_select(temp_ob, True)
        bpy.ops.object.mode_set(mode=pre_mode)

        if arm_ob:
            for i, loop in enumerate(me.loops):
                vert = me.vertices[loop.vertex_index]
                no = vert.normal.copy()

                try:
                    custom_rot = mathutils.Vector((0.0, 0.0, 1.0)).rotation_difference(custom_normals[i])
                except:
                    continue
                original_rot = mathutils.Vector((0.0, 0.0, 1.0)).rotation_difference(no)
                output_rot = original_rot.slerp(custom_rot, custom_normal_blend)

                output_no = mathutils.Vector((0.0, 0.0, 1.0))
                output_no.rotate(output_rot)

                custom_normals[i] = output_no
            me.use_auto_smooth = True
            me.normals_split_custom_set(custom_normals)

            progress += 1
            context.window_manager.progress_update(progress_start + progress / progress_count)

        context.window_manager.progress_update(progress_start + 1)
        if did_start_progress:
            context.window_manager.progress_end()
        return {'FINISHED'}
