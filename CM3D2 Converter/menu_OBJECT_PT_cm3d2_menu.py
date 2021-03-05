import bpy
import math
import mathutils
import struct
from . import common
from . import compat
from . import menu_file

''' CM3D2 Menu / Object Panel Classes '''

@compat.BlRegister()
class CM3D2MENU_UL_command_list(bpy.types.UIList):
    bl_idname      = 'CM3D2MENU_UL_command_list'
    bl_options     = {'DEFAULT_CLOSED'}
    bl_region_type = 'WINDOW'
    bl_space_type  = 'PROPERTIES'
    # The draw_item function is called for each item of the collection that is visible in the list.
    #   data is the RNA object containing the collection,
    #   item is the current drawn item of the collection,
    #   icon is the "computed" icon for the item (as an integer, because some objects like materials or textures
    #   have custom icons ID, which are not available as enum items).
    #   active_data is the RNA object containing the active property for the collection (i.e. integer pointing to the
    #   active item of the collection).
    #   active_propname is the name of the active property (use 'getattr(active_data, active_propname)').
    #   index is index of the current item in the collection.
    #   flt_flag is the result of the filtering process for this item.
    #   Note: as index and flt_flag are optional arguments, you do not have to use/declare them here if you don't
    #         need them.
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        command_prop = item.dereference(data)
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # You should always start your row layout by a label (icon + text), or a non-embossed text field,
            # this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
            # We use icon_value of label, as our given icon is an integer value, not an enum ID.
            # Note "data" names should never be translated!
            if command_prop:
                command_enum_info = menu_file.get_command_enum_info(command_prop.command)
                icon = 'NONE'
                if command_enum_info:
                    icon = compat.icon(command_enum_info[3])
                layout.label(text=command_prop.name, icon=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


@compat.BlRegister()
class OBJECT_PT_cm3d2_menu(bpy.types.Panel):
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = 'object'
    bl_label       = 'CM3D2 Menu'
    bl_idname      = 'OBJECT_PT_cm3d2_menu'

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and ob.type == 'ARMATURE':
            return True
        return False

    def draw(self, context):
        ob = context.object

        if not ob or ob.type != 'ARMATURE':
            return

        row = self.layout.row(align=True)
        row.operator('cm3d2menu.import', text="Import CM3D2 Menu File", icon=compat.icon('IMPORT'))
        row.operator('cm3d2menu.export', text="Export CM3D2 Menu File", icon=compat.icon('EXPORT'))

        cm3d2_menu = ob.cm3d2_menu
        active_command = cm3d2_menu.get_active_command()
        
        col = self.layout.column()
        col.prop(cm3d2_menu, 'version'    , translate=False)
        col.prop(cm3d2_menu, 'path'       , translate=False)
        col.prop(cm3d2_menu, 'name'       , translate=False)
        col.prop(cm3d2_menu, 'category'   , translate=False)
        col.prop(cm3d2_menu, 'description', translate=False, expand=True)

        row = self.layout.row()
        row.template_list('CM3D2MENU_UL_command_list', '',
            cm3d2_menu, 'commands'    ,
            cm3d2_menu, 'active_index',
        )
        sub_col = row.column(align=True)
        sub_col.operator('cm3d2menu.command_add'   , icon='ADD'   , text="")
        sub_col.operator('cm3d2menu.command_remove', icon='REMOVE', text="")
        #sub_col.separator()
        #sub_col.menu("OBJECT_MT_cm3d2_menu_context_menu", icon='DOWNARROW_HLT', text="")
        if active_command:
            sub_col.separator()
            sub_col.operator("cm3d2menu.command_move", icon='TRIA_UP'  , text="").direction = 'UP'  
            sub_col.operator("cm3d2menu.command_move", icon='TRIA_DOWN', text="").direction = 'DOWN'
        
        if active_command:
            box = self.layout.box()
            if not compat.IS_LEGACY:
                box.use_property_split = True
            cm3d2_menu.get_active_command().draw(context, box)




''' CM3D2 Menu Operators '''

@compat.BlRegister()
class CM3D2MENU_OT_import(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.import'
    bl_label       = "Import CM3D2 Menu File"
    bl_description = "Open a .menu file"
    bl_options     = {'REGISTER', 'UNDO'}

    filepath     = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = '.menu'
    filter_glob  = bpy.props.StringProperty(default='*.menu', options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and ob.type == 'ARMATURE':
            return True
        return False

    def invoke(self, context, event):  # type: (bpy.types.Context, Any) -> set
        prefs = common.preferences()
        if prefs.menu_import_path:
            self.filepath = prefs.menu_import_path
        else:
            self.filepath = prefs.menu_default_path

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        ob = context.object
        try:
            file = open(self.filepath, 'rb')
            ob.cm3d2_menu.clear()
            ob.cm3d2_menu.unpack_from_file(file)
        except IOError as e:
            self.report(type={'ERROR'}, message=e.args[0])
            return {'CANCELLED'}
        return {'FINISHED'}
        

@compat.BlRegister()
class CM3D2MENU_OT_export(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.export'
    bl_label       = "Export CM3D2 Menu File"
    bl_description = "Writes the active CM3D2Menu to a .menu file"
    bl_options     = {'REGISTER', 'UNDO'}

    filepath     = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = '.menu'
    filter_glob  = bpy.props.StringProperty(default='*.menu', options={'HIDDEN'})

    is_backup = bpy.props.BoolProperty(name="Backup", default=True, description="Will backup overwritten files.")

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and len(ob.cm3d2_menu.commands):
            return True
        return False

    def invoke(self, context, event):  # type: (bpy.types.Context, Any) -> set
        prefs = common.preferences()
        if prefs.menu_import_path:
            self.filepath = prefs.menu_import_path
        else:
            self.filepath = prefs.menu_default_path

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        box = self.layout.box()
        box.prop(self, 'is_backup', icon='FILE_BACKUP')

    def execute(self, context):
        ob = context.object
        try:
            file = common.open_temporary(self.filepath, 'wb', is_backup=self.is_backup)
            ob.cm3d2_menu.pack_into_file(file)
        except IOError as e:
            self.report(type={'ERROR'}, message=e.args[0])
            return {'CANCELLED'}
        self.report(type={'INFO'}, message="Successfully exported to .menu file")
        return {'FINISHED'}


@compat.BlRegister()
class CM3D2MENU_OT_command_add(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.command_add'
    bl_label       = "Add Command"
    bl_description = "Adds a new CM3D2MenuCommand to the active CM3D2Menu"
    bl_options     = {'REGISTER', 'UNDO'}

    command_type_enums = menu_file.COMMAND_ENUMS.copy()
    command_type_enums.append( ('NONE', 'Custom', 'Some other manually entered miscillaneous command', 'GREASEPENCIL', -1) )
    type = bpy.props.EnumProperty(items=command_type_enums, name="Type", default='NONE')
    
    string = bpy.props.StringProperty(name="String", default="newcommand")

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob:
            return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        self.layout.prop(self, 'type')
        if self.type == 'NONE':
            self.layout.prop(self, 'string')
    
    def execute(self, context):
        ob = context.object
        cm3d2_menu = ob.cm3d2_menu
        if self.type != 'NONE':
            self.string = self.type

        cm3d2_menu.new_command(self.string)
        cm3d2_menu.active_index = len(cm3d2_menu.commands) - 1

        return {'FINISHED'}


@compat.BlRegister()
class CM3D2MENU_OT_command_remove(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.command_remove'
    bl_label       = "Remove Command"
    bl_description = "Removes the active CM3D2MenuCommand from the active CM3D2Menu"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and len(ob.cm3d2_menu.commands) - ob.cm3d2_menu.active_index > 0:
            return True
        return False

    def execute(self, context):
        ob = context.object
        cm3d2_menu = ob.cm3d2_menu
        cm3d2_menu.remove_command(cm3d2_menu.active_index)
        if cm3d2_menu.active_index >= len(cm3d2_menu.commands):
            cm3d2_menu.active_index = len(cm3d2_menu.commands) - 1

        return {'FINISHED'}


@compat.BlRegister()
class CM3D2MENU_OT_command_move(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.command_move'
    bl_label       = "Move Command"
    bl_description = "Moves the active CM3D2MenuCommand up/down in the list"
    bl_options     = {'REGISTER', 'UNDO'}

    items = [
        ('UP'  , "Up"  , "Move the active CM3D2MenuCommand up in the list"  ),
        ('DOWN', "Down", "Move the active CM3D2MenuCommand down in the list"),
    ]
    direction = bpy.props.EnumProperty(items=items, name="Direction")

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and len(ob.cm3d2_menu.commands) - ob.cm3d2_menu.active_index > 0:
            return True
        return False

    def execute(self, context):
        ob = context.object
        cm3d2_menu = ob.cm3d2_menu

        new_index = cm3d2_menu.active_index - 1 if self.direction == 'UP' else cm3d2_menu.active_index + 1
        if new_index >= len(cm3d2_menu.commands):
            new_index = len(cm3d2_menu.commands) - 1
        elif new_index < 0:
            new_index = 0

        cm3d2_menu.move_command(cm3d2_menu.active_index, new_index)
        cm3d2_menu.active_index = new_index

        return {'FINISHED'}




''' CM3D2 Menu Command Operators '''

# For menu_file.CM3D2MENU_PG_AttachPointCommand

@compat.BlRegister()
class CM3D2MENU_OT_align_selected_to_attach_point(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.align_selected_to_attach_point'
    bl_label       = "Align Selected to Attach Point"
    bl_description = "Align other selected objects to the active object's active CM3D2 attach point"
    bl_options     = {'REGISTER', 'UNDO'}

    scale = bpy.props.FloatProperty(name="Scale", default=5, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="The amount by which the mesh is scaled when imported. Recommended that you use the same when at the time of export.")

    @classmethod
    def poll(cls, context):
        ob = context.object
        arm_ob = None
        if ob.type == 'ARMATURE':
            arm_ob = ob
        else:
            arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent

        if arm_ob and arm_ob.type == 'ARMATURE':
            active_command = ob.cm3d2_menu.get_active_command()
            if type(active_command) != menu_file.CM3D2MENU_PG_AttachPointCommand:
                return False
        
        selection = None
        try:
            selection = context.selected_editable_objects
        except:
            return False

        if not selection or len(selection) < 1:
            return False

        for selected in selection:
            if selected != arm_ob and selected != ob:
                return True

        return False

    def invoke(self, context, event):
        self.scale = common.preferences().scale
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'scale')

    def execute(self, context):
        ob = context.object
        if ob.type == 'ARMATURE':
            arm_ob = ob
        else:
            arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent
        selection = context.selected_editable_objects
        
        attach_point = ob.cm3d2_menu.get_active_command()
        attach_mat = attach_point.rotation.to_matrix().to_4x4()
        attach_mat.translation = attach_point.location.copy() * self.scale

        attach_basis = compat.convert_cm_to_bl_space(attach_mat)
        attach_basis = compat.convert_cm_to_bl_bone_rotation(attach_basis)

        for selected in selection:
            if selected == arm_ob or selected == ob:
                continue
            const = selected.constraints.get("CM3D2 Attachment")
            if not const:
                const = selected.constraints.new("CHILD_OF")
                const.name = "CM3D2 Attachment"
            const.target = arm_ob
            selected.matrix_basis = attach_basis
    
        return {'FINISHED'}


@compat.BlRegister()
class CM3D2MENU_OT_align_attach_point_to_selected(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.align_attach_point_to_selected'
    bl_label       = "Align Attach Point to Selected"
    bl_description = "Align the active CM3D2Menu's active attach point to the first other selected object"
    bl_options     = {'REGISTER', 'UNDO'}

    scale = bpy.props.FloatProperty(name="Scale", default=5, min=0.1, max=100, soft_min=0.1, soft_max=100, step=100, precision=1, description="The amount by which the mesh is scaled when imported. Recommended that you use the same when at the time of export.")

    @classmethod
    def poll(cls, context):
        ob = context.object
        arm_ob = None
        if ob.type == 'ARMATURE':
            arm_ob = ob
        else:
            arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent

        if arm_ob and arm_ob.type == 'ARMATURE':
            active_command = ob.cm3d2_menu.get_active_command()
            if type(active_command) != menu_file.CM3D2MENU_PG_AttachPointCommand:
                return False
        
        selection = None
        try:
            selection = context.selected_objects
        except:
            return False

        if not selection or len(selection) < 1:
            return False

        for selected in selection:
            if selected != arm_ob and selected != ob:
                return True

        return False

    def invoke(self, context, event):
        self.scale = common.preferences().scale
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'scale')

    def execute(self, context):
        ob = context.object
        if ob.type == 'ARMATURE':
            arm_ob = ob
        else:
            arm_ob = ob.find_armature()
        if (not arm_ob) and (ob.parent and ob.parent.type == 'ARMATURE'):
            arm_ob = ob.parent
        selection = context.selected_objects
        
        attach_point = ob.cm3d2_menu.get_active_command()


        for selected in selection:
            if selected == arm_ob or selected == ob:
                continue
            mat = compat.mul(arm_ob.matrix_world.inverted(), selected.matrix_world)
            mat = compat.convert_bl_to_cm_space(mat)
            mat = compat.convert_bl_to_cm_bone_rotation(mat)

            attach_point.location = mat.translation * (1/self.scale)
            attach_point.rotation = mat.to_euler()
    
        return {'FINISHED'}



# For menu_file.CM3D2MENU_PG_MiscCommand

@compat.BlRegister()
class CM3D2MENU_OT_param_add(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.param_add'
    bl_label       = "Add Parameter"
    bl_description = "Adds a new CM3D2MenuParam to the active CM3D2MenuCommand"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and ob.cm3d2_menu:
            misc_command = ob.cm3d2_menu.get_active_command()
            if type(misc_command) == menu_file.CM3D2MENU_PG_MiscCommand:
                return True
        return False
   
    def execute(self, context):
        ob = context.object
        cm3d2_menu = ob.cm3d2_menu
        misc_command = ob.cm3d2_menu.get_active_command()
        misc_command.new_param()
        misc_command.active_index = len(misc_command.params) - 1

        return {'FINISHED'}


@compat.BlRegister()
class CM3D2MENU_OT_param_remove(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.param_remove'
    bl_label       = "Remove Parameter"
    bl_description = "Removes the active CM3D2MenuParam from the active CM3D2MenuCommand"
    bl_options     = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob or not ob.cm3d2_menu:
            return False

        misc_command = ob.cm3d2_menu.get_active_command()
        if type(misc_command) != menu_file.CM3D2MENU_PG_MiscCommand:
            return False
        
        if len(misc_command.params) - misc_command.active_index <= 0:
            return False
            
        return True

    def execute(self, context):
        ob = context.object
        cm3d2_menu = ob.cm3d2_menu
        misc_command = ob.cm3d2_menu.get_active_command()
        misc_command.remove_param(misc_command.active_index)
        if misc_command.active_index >= len(misc_command.params):
            misc_command.active_index = len(misc_command.params) - 1

        return {'FINISHED'}


@compat.BlRegister()
class CM3D2MENU_OT_param_move(bpy.types.Operator):
    bl_idname      = 'cm3d2menu.param_move'
    bl_label       = "Move Parameter"
    bl_description = "Moves the active CM3D2MenuParameter up/down in the list"
    bl_options     = {'REGISTER', 'UNDO'}

    items = [
        ('UP'  , "Up"  , "Move the active CM3D2MenuCommand up in the list"  ),
        ('DOWN', "Down", "Move the active CM3D2MenuCommand down in the list"),
    ]
    direction = bpy.props.EnumProperty(items=items, name="Direction")

    @classmethod
    def poll(cls, context):
        ob = context.object
        if not ob or not ob.cm3d2_menu:
            return False

        misc_command = ob.cm3d2_menu.get_active_command()
        if type(misc_command) != menu_file.CM3D2MENU_PG_MiscCommand:
            return False
        
        if len(misc_command.params) - misc_command.active_index <= 0:
            return False

        return True

    def execute(self, context):
        ob = context.object
        cm3d2_menu = ob.cm3d2_menu
        misc_command = ob.cm3d2_menu.get_active_command()

        new_index = misc_command.active_index - 1 if self.direction == 'UP' else misc_command.active_index + 1
        if new_index >= len(misc_command.params):
            new_index = len(misc_command.params) - 1
        elif new_index < 0:
            new_index = 0

        misc_command.move_param(misc_command.active_index, new_index)
        misc_command.active_index = new_index

        return {'FINISHED'}


