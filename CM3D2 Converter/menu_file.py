import bpy
import math
import mathutils
import struct
from . import common
from . import compat



PROP_OPTS = {'LIBRARY_EDITABLE'}

# New specially handled commands need to have 4 things
#   1) An enum entry in COMMAND_ENUMS
#   2) A class decorated with @CM3D2MenuCommand
#   3) A collection property to hold that class in CNV_PG_CM3D2MenuFileData
#   4) An entry in the CNV_PG_CM3D2MenuFileData.command_type_collections dictionary
#       key   = step 2's class.bl_idname
#       value = attribute name of step 2's collection property

COMMAND_ENUMS = {
    ('アタッチポイントの設定', "Attach Point", "description", 'NONE', 27),
    ('prop', "Property", "description", 'NONE', 30)
}

COMMAND_TYPE_LIST = dict()

def get_command_enum_name(enum, enum_items=COMMAND_ENUMS):
    for enum_info in enum_items:
        if enum_info[0] == enum:
            return enum_info[1]
    return enum

# Decorator for CM3D2 Menu Command Classes
class CM3D2MenuCommand():
    def __init__(self, *args, name="{command_name}"):
        self.name_template = name
        self.command_enums = set()
        for command in args:
            for enum_info in COMMAND_ENUMS:
                if enum_info[0] == command:
                    self.command_enums.add(enum_info)
                    break
            continue
    
    def __call__(self, cls):
        cls.name_template = self.name_template
        cls.command_enums = self.command_enums
        # Associate the class with its command in COMMAND_CLASSES
        for enum in cls.command_enums:
            COMMAND_TYPE_LIST[enum[0]] = cls

        # define command property
        if len(cls.command_enums) > 0:
            cls.command = bpy.props.EnumProperty(
                items   = cls.command_enums,
                name    = "Command",
                options = PROP_OPTS,
                default = next(iter(cls.command_enums))[0],
                description = "The command of this menu file command-chunk"
            )
        else:
            cls.command = bpy.props.StringProperty(
                name    = "Command",
                options = PROP_OPTS,
                default = "command",
                description = "The command of this menu file command-chunk"
            )

        attributes = dir(cls)
        cls.name_format_attributes = set()
        for attr in attributes:
            if "{"+attr+"}" in cls.name_template:
                cls.name_format_attributes.add(attr)

        def format_name(self):
            params = { attr : getattr(self, attr) for attr in cls.name_format_attributes }
            if len(cls.command_enums) > 0:
                params['command_name'] = get_command_enum_name(self.command, enum_items=cls.command_enums)
            else:
                params['command_name'] = self.command
            return cls.name_template.format(**params)
        
        cls.format_name = format_name
        
        # define name property
        cls.name = bpy.props.StringProperty(
            name    = "Name"                 ,
            options = {'HIDDEN', 'SKIP_SAVE'},
            get     = cls.format_name
        )

        # add catch and rethrow for functions
        def catch_throw_wrap(func, gerund, catch_type, throw_type=None):
            throw_type = throw_type or catch_type
            prefix = "Error {gerund} {bl_idname}: ".format(gerund=gerund, bl_idname=cls.bl_idname) + "{message}"
            def _f(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except catch_type as e:
                    raise throw_type(prefix.format(e.args[0]))
            return _f

        cls.parse_list = catch_throw_wrap(cls.parse_list, "parsing", ValueError)
        cls.pack_into  = catch_throw_wrap(cls.pack_into , "packing", ValueError)

        return cls



''' Sub-Classes '''

@compat.BlRegister()
class CNV_PG_CM3D2AnyTypePointer(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2AnyTypePointer'

    collection_rna : bpy.props.StringProperty(options={'HIDDEN'})
    prop_index     : bpy.props.IntProperty   (options={'HIDDEN'})

    def dereference(self, data):
        return getattr(data, self.collection_rna)[self.prop_index]


@compat.BlRegister()
class CNV_PG_CM3D2String(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2String'

    # Really the value should be saved, not the name, but template_list() doesn't like that so they're switched.
    def _s(self, value):
        self.name = value

    #name: bpy.props.StringProperty(name="Name", options=PROP_OPTS, get=lambda self : self.value)
    name  : bpy.props.StringProperty(name="Name", default="string", options={'HIDDEN'})
    value : bpy.props.StringProperty(name="Slot Name", options={'SKIP_SAVE'}, set=_s, get=lambda self: self.name)




''' Menu File Command Classes '''

@compat.BlRegister()
@CM3D2MenuCommand('アタッチポイントの設定', name="{command_name} : {slot_name}")
class CNV_PG_CM3D2AttachPoint(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2AttachPoint'
    '''
    アタッチポイントの設定
      ├ slot_name （呼び出し名）
      ├ location.x（座標）
      ├ location.y（座標）
      ├ location.z（座標）
      ├ rotation.x（軸回転角度）[範囲:0±180°]
      ├ rotation.y（軸回転角度）[範囲:0±180°]
      └ rotation.z（軸回転角度）[範囲:0±180°]
    '''
    slot_name = bpy.props.StringProperty     (name="Slot Name", default="Attach Point", description="Name of the slot to define the attatchment point for" , options=PROP_OPTS)
    location  = bpy.props.FloatVectorProperty(name="Location" , default=(0, 0, 0)     , description="Location of the attatchment relative to the base bone", options=PROP_OPTS, subtype=compat.subtype('TRANSLATION'))
    rotation  = bpy.props.FloatVectorProperty(name="Rotation" , default=(0, 0, 0)     , description="Rotation of the attatchment relative to the base bone", options=PROP_OPTS, subtype=compat.subtype('EULER'      ))

    def parse_list(self, string_list):
        self.command = string_list[0]
        self.slot_name  = string_list[1]
        self.location.x = float(string_list[2])
        self.location.y = float(string_list[3])
        self.location.z = float(string_list[4])
        self.rotation.x = float(string_list[5]) * math.pi/180
        self.rotation.y = float(string_list[6]) * math.pi/180
        self.rotation.z = float(string_list[7]) * math.pi/180
    
    def pack_into(self, buffer):
        buffer = buffer + struct.pack('<B', 1 + 1 + 3 + 3)
        buffer = common.pack_str(buffer, self.command   )
        buffer = common.pack_str(buffer, self.slot_name )
        buffer = common.pack_str(buffer, str(self.location.x)              )
        buffer = common.pack_str(buffer, str(self.location.y)              )
        buffer = common.pack_str(buffer, str(self.location.z)              )
        buffer = common.pack_str(buffer, str(self.rotation.x * 180/math.pi))
        buffer = common.pack_str(buffer, str(self.rotation.y * 180/math.pi))
        buffer = common.pack_str(buffer, str(self.rotation.z * 180/math.pi))

    def draw(self, context, layout):
        layout.label(text=self.name)
        col = layout.column()
        col.label(text=self.command, translate=False)
        col.prop(self, 'slot_name')
        col.prop(self, 'location' )
        col.prop(self, 'rotation' )


@compat.BlRegister()
@CM3D2MenuCommand('prop', name="{command_name} : {prop_name} = {value}")
class CNV_PG_CM3D2PropertyValue(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2PropertyValue'
    '''
    prop
      ├ prop_name
      └ value
    '''
    prop_name = bpy.props.StringProperty(name="Property Name" , default="prop name", description="Name of the property to set on load" , options=PROP_OPTS)
    value     = bpy.props.FloatProperty (name="Property Value", default=50         , description="Value of the property to set on load", options=PROP_OPTS)
    
    def parse_list(self, string_list):
        self.command    = string_list[0]
        self.prop_name  = string_list[1]
        self.value      = float(string_list[2])
    
    def pack_into(self, buffer):
        buffer = buffer + struct.pack('<B', 1 + 1 + 1)
        buffer = common.pack_str(buffer, self.command    )
        buffer = common.pack_str(buffer, self.prop_name  )
        buffer = common.pack_str(buffer, str(self.value) )

    def draw(self, context, layout):
        layout.label(text=self.name)
        col = layout.column()
        col.label(text=self.command, translate=False)
        col.prop(self, 'prop_name')
        col.prop(self, 'value'    )


@compat.BlRegister()
@CM3D2MenuCommand(name="{command_name}")
class CNV_PG_CM3D2MiscCommand(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2MiscCommand'
    '''
    command
      ├ child_0
      ├ child_1
      ├ child_2
      ├ ...
      ├ child_n-1
      └ child_n
    '''
    params = bpy.props.CollectionProperty(name="Parameters", options=PROP_OPTS, type=CNV_PG_CM3D2String)
    
    active_param_index = bpy.props.IntProperty(options={'HIDDEN'})

    def parse_list(self, string_list):
        self.command = string_list[0]
        for param in string_list[1:]:
            new_param = self.params.add()
            new_param.value = param
            new_param.name  = param

    def pack_into(self, buffer):
        buffer = buffer + struct.pack('<B', 1 + len(self.params))
        buffer = common.pack_str(buffer, self.command)
        for param in self.params:
            buffer = common.pack_str(buffer, param.value)
        return buffer
    
    def draw(self, context, layout):
        layout.prop(self, 'command', text='')
        layout.template_list('UI_UL_list', 'OBJECT_UL_cm3d2_menu_children', self, 'params', self, 'active_param_index')




''' Menu File Data Class '''

@compat.BlRegister()
class CNV_PG_CM3D2MenuFileData(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2MenuFileData'

    version     : bpy.props.IntProperty   (name="Version"    , options=PROP_OPTS, min=0, step=100    )
    path        : bpy.props.StringProperty(name="Path"       , options=PROP_OPTS, subtype='FILE_PATH')
    name        : bpy.props.StringProperty(name="Name"       , options=PROP_OPTS)
    category    : bpy.props.StringProperty(name="Category"   , options=PROP_OPTS)
    description : bpy.props.StringProperty(name="Description", options=PROP_OPTS)
                                                                       
    attach_points   : bpy.props.CollectionProperty(type=CNV_PG_CM3D2AttachPoint  , options={'HIDDEN'})
    property_values : bpy.props.CollectionProperty(type=CNV_PG_CM3D2PropertyValue, options={'HIDDEN'})
    misc_commands   : bpy.props.CollectionProperty(type=CNV_PG_CM3D2MiscCommand  , options={'HIDDEN'})

    commands : bpy.props.CollectionProperty(name="Commands", type=CNV_PG_CM3D2AnyTypePointer, options=PROP_OPTS)
    active_command : bpy.props.IntProperty(name="Active command", options=PROP_OPTS)

    command_type_collections = {
        'CM3D2AttachPoint'   : 'attach_points'  ,
        'CM3D2PropertyValue' : 'property_values'
    }

    def get_active_command(self):
        command_pointer = self.commands[self.active_command]
        return command_pointer.dereference(self)

    def parse_list(self, string_list):
        command = string_list[0]
        command_type = COMMAND_TYPE_LIST.get(command)
        collection_rna = 'misc_commands'
        if command_type:
            collection_rna = self.command_type_collections.get(command_type.bl_idname)
        collection = getattr(self, collection_rna)
        prop = collection.add()
        prop.parse_list(string_list)
        prop.command = command
        pointer = self.commands.add()
        pointer.collection_rna = collection_rna
        pointer.prop_index = len(collection) - 1

    def unpack_from_file(self, file):
        if common.read_str(file) != 'CM3D2_MENU':
            raise IOError("Not a valid CM3D2 .menu file.")

        self.version      = struct.unpack('<i', file.read(4))[0]
        self.path         = common.read_str(file)
        self.name         = common.read_str(file)
        self.category     = common.read_str(file)
        self.description  = common.read_str(file)
        
        struct.unpack('<i', file.read(4))[0]
        string_list = []
        string_list_length = struct.unpack('<B', file.read(1))[0]
        while string_list_length > 0:
            string_list.clear()

            for i in range(string_list_length):
                string_list.append(common.read_str(file))
            
            try:
                self.parse_list(string_list)
            except ValueError as e:
                print(e)
            
            chunk = file.read(1)
            if len(chunk) == 0:
                break
            string_list_length = struct.unpack('<B', chunk)[0]
    
    def pack_into_file(self, file):
        common.write_str(file, 'CM3D2_MENU')

        file.write(struct.pack('<i', self.version    ))
        common.write_str(file,       self.path       )
        common.write_str(file,       self.name       )
        common.write_str(file,       self.category   )
        common.write_str(file,       self.description)
                    
        buffer = bytearray()
        for command_pointer in self.commands:
            buffer = command_pointer.dereference(self).pack_into(buffer)
        buffer = buffer + struct.pack('<B', 0x00)
        
        file.write(struct.pack('<i', len(buffer)))
        file.write(bytes(buffer))

    def clear(self):
        self.property_unset('version'    )
        self.property_unset('path'       )
        self.property_unset('name'       )
        self.property_unset('category'   )
        self.property_unset('description')
        
        for prop in self.command_type_collections.values():
            self.property_unset(prop)

        self.property_unset('misc_commands')

        self.property_unset('commands'      )
        self.property_unset('active_command')




''' Menu File Panel Classes '''

@compat.BlRegister()
class OBJECT_UL_cm3d2_menu_command_list(bpy.types.UIList):
    bl_label       = 'OBJECT_UL_cm3d2_menu_command_list'
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
                layout.label(text=command_prop.name, icon_value=icon)
            else:
                layout.label(text="", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


@compat.BlRegister()
class OBJECT_PT_cm3d2_menu_file(bpy.types.Panel):
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = 'object'
    bl_label       = 'CM3D2 Menu File'
    bl_idname      = 'OBJECT_PT_cm3d2_menu_file'

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
        row.operator('object.import_cm3d2_menu_file', text="Import Menu File", icon=compat.icon('IMPORT'))
        row.operator('object.export_cm3d2_menu_file', text="Export Menu File", icon=compat.icon('EXPORT'))

        menu_file_data = ob.cm3d2_menu_file_data
        
        col = self.layout.column()
        col.prop(menu_file_data, 'version'    )
        col.prop(menu_file_data, 'path'       )
        col.prop(menu_file_data, 'name'       )
        col.prop(menu_file_data, 'category'   )
        col.prop(menu_file_data, 'description')

        collection = menu_file_data.commands #getattr(menu_file_data, collection_rna)
        col = self.layout.column(align=True)
        #col.box().label(text=menu_file_data.bl_rna.properties[collection_rna].name)
        if len(collection) > 0:
            col.template_list('OBJECT_UL_cm3d2_menu_command_list', '',
                menu_file_data, 'commands'      ,
                menu_file_data, 'active_command',
            )
        # TODO create add/remove buttons here
        if len(collection) > 0:
            box = col.box()
            box.use_property_split = True
            active_item = collection[menu_file_data.active_command]
            active_item.dereference(menu_file_data).draw(context, box)




''' Operators '''

@compat.BlRegister()
class CNV_OT_import_cm3d2_menu_file(bpy.types.Operator):
    bl_idname      = 'object.import_cm3d2_menu_file'
    bl_label       = "Import Menu File"
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
        if prefs.model_import_path:
            self.filepath = prefs.model_import_path
        else:
            self.filepath = prefs.model_default_path

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        ob = context.object
        try:
            file = open(self.filepath, 'rb')
            ob.cm3d2_menu_file_data.clear()
            ob.cm3d2_menu_file_data.unpack_from_file(file)
        except IOError as e:
            self.report(type={'ERROR'}, message=e.args[0])
            return {'CANCELLED'}
        return {'FINISHED'}
        

@compat.BlRegister()
class CNV_OT_export_cm3d2_menu_file(bpy.types.Operator):
    bl_idname      = 'object.export_cm3d2_menu_file'
    bl_label       = "Export Menu File"
    bl_description = "Writes a CM3D2 Menu to a .menu file"
    bl_options     = {'REGISTER', 'UNDO'}

    filepath     = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = '.menu'
    filter_glob  = bpy.props.StringProperty(default='*.menu', options={'HIDDEN'})

    is_backup = bpy.props.BoolProperty(name="Backup", default=True, description="Will backup overwritten files.")

    @classmethod
    def poll(cls, context):
        ob = context.object
        if ob and len(ob.cm3d2_menu_file_data.commands):
            return True
        return False

    def invoke(self, context, event):  # type: (bpy.types.Context, Any) -> set
        prefs = common.preferences()
        if prefs.model_import_path:
            self.filepath = prefs.model_import_path
        else:
            self.filepath = prefs.model_default_path

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        box = self.layout.box()
        box.prop(self, 'is_backup', icon='FILE_BACKUP')

    def execute(self, context):
        ob = context.object
        try:
            file = common.open_temporary(self.filepath, 'wb', is_backup=self.is_backup)
            ob.cm3d2_menu_file_data.pack_into_file(file)
        except IOError as e:
            self.report(type={'ERROR'}, message=e.args[0])
            return {'CANCELLED'}
        self.report(type={'INFO'}, message="Successfully exported to .menu file")
        return {'FINISHED'}
        

