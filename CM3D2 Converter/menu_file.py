import bpy
import math
import mathutils
import struct
from . import common
from . import compat



PROP_OPTS = {'LIBRARY_EDITABLE'}

# New specially handled commands need to have 3 things
#   1) An enum entry in COMMAND_ENUMS (if it is not already in there)
#   2) A class decorated with @CM3D2MenuCommand([enum1, [enum2, [...]]], name="{command_name}" )
#   3) A collection property to hold that class in OBJECT_PG_CM3D2Menu
# The decorators will handle the rest

COMMAND_ENUMS = [
    ('', "Menu Meta", ''),
    ('end'          , "End"                    , "description", 'X'                    ,   0),
    ('name'         , "Menu Name"              , "description", 'FILE_TEXT'            ,   3),
    ('saveitem'     , "Menu Category"          , "description", 'FILE_TEXT'            ,   4),
    ('setumei'      , "Menu Description"       , "description", 'FILE_TEXT'            ,   5),
    ('priority'     , "Priority"               , "description", 'SORT_DESC'            ,   6),
    ('メニューフォルダ'     , "Folder"                 , "description", 'FILE_FOLDER'          ,   7),
    ('icon'         , "Icon"                   , "description", 'FILE_IMAGE'           ,  10),
    ('icons'        , "Icon (Small)"           , "description", 'FILE_IMAGE'           ,  11), # alias of 'icon'
    ('iconl'        , "Icon (Large)"           , "Unused"     , 'BLANK1'               ,  12),
    
    ('', "Item Meta", ''),
    ('ver'          , "Item Version"           , "description", 'FILE_TEXT'            ,  20),
    ('category'     , "Item Category"          , "description", 'SORTALPHA'            ,  21),
    ('catno'        , "Item Category Number"   , "description", 'LINENUMBERS_ON'       ,  22),
    ('アイテム'         , "Item"                   , "description", 'FILE_3D'              ,  30),
    ('アイテム条件'       , "Item Conditions"        , "description", 'SCRIPTPLUGINS'        ,  31),
    ('if'           , "Item If"                , "description", 'FILE_SCRIPT'          ,  32),
    ('アイテムパラメータ'    , "Item Parameters"        , "description", 'SCRIPTPLUGINS'        ,  33),
    ('半脱ぎ'          , "Item Half Off"          , "description", 'LIBRARY_DATA_INDIRECT',  34),
    ('リソース参照'       , "Item Resource Reference", "description", 'LIBRARY_DATA_INDIRECT',  35),  # alias of '半脱ぎ'
    
    ('', "Item Control", ''),
    ('set'          , "Set"                    , "Unused"     , 'BLANK1'               ,  40),
    ('setname'      , "Set Name"               , "Unused"     , 'BLANK1'               ,  41),
    ('setslotitem'  , "Set Slot Item"          , "description", 'FILE_TICK'            ,  42),
    ('additem'      , "Add Item"               , "description", 'ADD'                  ,  43),
    ('unsetitem'    , "Unset Item"             , "description", 'REMOVE'               ,  44),
    ('nofloory'     , "Disable Item Floor"     , "description", 'CON_FLOOR'            ,  45),
    ('maskitem'     , "Mask Item"              , "description", 'MOD_MASK'             ,  46),
    ('delitem'      , "Delete Item"            , "description", 'TRASH'                ,  47),
    ('node消去'       , "Node Hide"              , "description", 'HIDE_ON'              ,  50),
    ('node表示'       , "Node Display"           , "description", 'HIDE_OFF'             ,  51),
    ('パーツnode消去'    , "Parts-Node Hide"        , "description", 'VIS_SEL_01'           ,  52),
    ('パーツnode表示'    , "Parts-Node Display"     , "description", 'VIS_SEL_11'           ,  53),

    ('', "Material Control", ''),
    ('color'        , "Color"                  , "description", 'COLOR'                ,  60),
    ('mancolor'     , "Man Color"              , "description", 'GHOST_ENABLED'        ,  61),
    ('color_set'    , "Color-Set"              , "description", 'GROUP_VCOL'           ,  62),
    ('tex'          , "Texture"                , "description", 'TEXTURE'              ,  70),
    ('テクスチャ変更'      , "Texture Change"         , "description", 'TEXTURE'              ,  71), # alias of 'tex'
    ('テクスチャ乗算'      , "Texture Multiplication" , "description", 'FORCE_TEXTURE'        ,  72),
    ('テクスチャ合成'      , "Texture Composition"    , "description", 'NODE_TEXTURE'         ,  73),
    ('テクスチャセット合成'   , "Texture Set Composition", "description", 'NODE_TEXTURE'         ,  74),
    ('マテリアル変更'      , "Material Change"        , "description", 'MATERIAL'             ,  80),
    ('useredit'     , "Material Properties"    , "description", 'MATERIAL'             ,  81),
    ('shader'       , "Shader"                 , "description", 'SHADING_RENDERED'     ,  90),

    ('', "Maid Control", ''),
    ('prop'         , "Property"               , "description", 'PROPERTIES'           , 100),
    ('アタッチポイントの設定'  , "Attach Point"           , "description", 'HOOK'                 , 110),
    ('blendset'     , "Face Blend-Set"         , "description", 'SHAPEKEY_DATA'        , 120),
    ('paramset'     , "Face Parameter-Set"     , "description", 'OPTIONS'              , 121),
    ('commenttype'  , "Profile Comment Type"   , "description", 'TEXT'                 , 130),
    ('bonemorph'    , "Bone Morph"             , "description", 'CONSTRAINT_BONE'      , 140),
    ('length'       , "Hair Length"            , "description", 'CONSTRAINT_BONE'      , 141),
    ('anime'        , "Animation"              , "description", 'ANIM'                 , 150),
    ('animematerial', "Animation (Material)"   , "description", 'ANIM'                 , 151),
    ('param2'       , "Parameter 2"            , "description", 'CON_TRANSFORM'        , 160),

    ('', "Misc.", ''),
    ('setstr'       , "Set String"             , "Unused"     , 'BLANK1'               , 170),
    ('onclickmenu'  , "onclickmenu"            , "Decorative" , 'NONE'                 , 200),
    ('属性追加'         , "addattribute"           , "Decorative" , 'NONE'                 , 201)                 
]

COMMAND_TYPE_LIST = dict() # filled by the CM3D2MenuCommand decorator

def get_command_enum_info(enum_string, enum_items=COMMAND_ENUMS):
    if enum_string == '':
        return None
    for enum_info in enum_items:
        if enum_info[0] == enum_string:
            return enum_info
    return None

def get_command_enum_name(enum_string, enum_items=COMMAND_ENUMS):
    if enum_string == '':
        return ''
    for enum_info in enum_items:
        if enum_info[0] == enum_string:
            return enum_info[1]
    return enum_string




''' CM3D2 Menu Sub-Classes '''

@compat.BlRegister()
class CM3D2MENU_PG_CommandPointer(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2MenuCommandPointer'

    collection_name  = bpy.props.StringProperty(options={'HIDDEN'})
    prop_index       = bpy.props.IntProperty   (options={'HIDDEN'})

    def dereference(self, data):
        return getattr(data, self.collection_name)[self.prop_index]


@compat.BlRegister()
class MISCCOMMAND_PG_Param(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2MenuParam'

    # Really the value should be saved, not the name, but template_list() doesn't like that so they're switched.
    def _s(self, value):
        self.name = value

    #name = bpy.props.StringProperty(name="Name", options=PROP_OPTS, get=lambda self : self.value)
    name   = bpy.props.StringProperty(name="Name", default="param", options={'HIDDEN'})
    value  = bpy.props.StringProperty(name="Slot Name", options={'SKIP_SAVE'}, default="param", set=_s, get=lambda self: self.name)




''' Decorator for CM3D2 Menu Command Classes '''
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

        cls.index = bpy.props.IntProperty(name="Index", options=PROP_OPTS)
        #cls.initalized = bpy.props.BoolProperty(name="Index", options={'SKIP_SAVE'}, default=False)

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
                params['command_name'] = get_command_enum_name(self.command)
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




''' CM3D2 Menu Command Classes '''

@compat.BlRegister()
@CM3D2MenuCommand('アタッチポイントの設定', name="{command_name} : {point_name}")
class CM3D2MENU_PG_AttachPointCommand(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2MenuAttachPointCommand'
    '''
    アタッチポイントの設定
      ├ point_name（呼び出し名）
      ├ location.x（座標）
      ├ location.y（座標）
      ├ location.z（座標）
      ├ rotation.x（軸回転角度）[範囲:0±180°]
      ├ rotation.y（軸回転角度）[範囲:0±180°]
      └ rotation.z（軸回転角度）[範囲:0±180°]
    '''
    point_name = bpy.props.StringProperty     (name="Point Name", default="Attach Point", description="Name of the slot to define the attatchment point for" , options=PROP_OPTS)
    location   = bpy.props.FloatVectorProperty(name="Location"  , default=(0, 0, 0)     , description="Location of the attatchment relative to the base bone", options=PROP_OPTS, subtype=compat.subtype('TRANSLATION'))
    rotation   = bpy.props.FloatVectorProperty(name="Rotation"  , default=(0, 0, 0)     , description="Rotation of the attatchment relative to the base bone", options=PROP_OPTS, subtype=compat.subtype('EULER'      ))

    def parse_list(self, string_list):
        self.command = string_list[0]
        self.point_name  = string_list[1]
        self.location.x = float(string_list[2])
        self.location.y = float(string_list[3])
        self.location.z = float(string_list[4])
        self.rotation.x = float(string_list[5]) * math.pi/180
        self.rotation.y = float(string_list[6]) * math.pi/180
        self.rotation.z = float(string_list[7]) * math.pi/180
    
    def pack_into(self, buffer):
        buffer = buffer + struct.pack('<B', 1 + 1 + 3 + 3)
        buffer = common.pack_str(buffer, self.command   )
        buffer = common.pack_str(buffer, self.point_name)
        buffer = common.pack_str(buffer, str(self.location.x)              )
        buffer = common.pack_str(buffer, str(self.location.y)              )
        buffer = common.pack_str(buffer, str(self.location.z)              )
        buffer = common.pack_str(buffer, str(self.rotation.x * 180/math.pi))
        buffer = common.pack_str(buffer, str(self.rotation.y * 180/math.pi))
        buffer = common.pack_str(buffer, str(self.rotation.z * 180/math.pi))

    def draw(self, context, layout):
        layout.label(text=self.name)

        col = layout.column()
        col.alignment = 'RIGHT'
        col.prop(self, 'command', translate=False)
        col.label(text=self.command + "     ", translate=False)

        col = layout.column()
        col.prop(self, 'point_name')
        col.prop(self, 'location'  )
        col.prop(self, 'rotation'  )
        
        col = layout.column(align=True)
        col.operator('cm3d2menu.align_selected_to_attach_point', icon=compat.icon('OBJECT_ORIGIN')    )
        col.operator('cm3d2menu.align_attach_point_to_selected', icon=compat.icon('ORIENTATION_LOCAL'))


@compat.BlRegister()
@CM3D2MenuCommand('prop', name="{command_name} : {prop_name} = {value}")
class CM3D2MENU_PG_PropertyCommand(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2PropertyMenuCommand'
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
        col = layout.column()
        col.alignment = 'RIGHT'
        col.prop(self, 'command', translate=False)
        col.label(text=self.command + "     ", translate=False)

        col = layout.column()
        col.label(text=self.command, translate=False)
        col.prop(self, 'prop_name')
        col.prop(self, 'value'    )


@compat.BlRegister()
@CM3D2MenuCommand(name="{command_name}")
class CM3D2MENU_PG_MiscCommand(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2MenuMiscCommand'
    '''
    command
      ├ child_0
      ├ child_1
      ├ child_2
      ├ ...
      ├ child_n-1
      └ child_n
    '''
    params = bpy.props.CollectionProperty(name="Parameters", options=PROP_OPTS, type=MISCCOMMAND_PG_Param)
    
    active_index = bpy.props.IntProperty(options={'HIDDEN'})

    search = bpy.props.BoolProperty(name="Search", default=False, description="Search for suggestions", options=PROP_OPTS)

    def new_param(self):
        new_param = self.params.add()
        new_param.value = "newparam"
        return new_param

    def remove_param(self, index: int):
        return self.params.remove(index)

    def move_param(self, old_index, new_index):
        return self.params.move(old_index, new_index)

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
        enum_info = get_command_enum_info(self.command)
        if enum_info:
            layout.label(text=enum_info[1], icon=enum_info[3])

        row = layout.row(align=True)
        if not compat.IS_LEGACY:
            row.use_property_split = False
        if self.search:
            search_data = bpy.ops.cm3d2menu.command_add.get_rna_type().properties.get('type')
            row.prop_search(self, 'command', search_data, 'enum_items', text="", translate=True, icon='VIEWZOOM')
        else:
            row.prop(self, 'command', text="")
        row.prop(self, 'search', text='', icon='ZOOM_OUT' if self.search else 'VIEWZOOM')
        
        
        row = layout.row()
        row.template_list('UI_UL_list', 'CM3D2MENU_UL_misc_command_children',
            self, 'params'      ,
            self, 'active_index',
            rows    = 3,
            maxrows = 8,
        )
        sub_col = row.column(align=True)
        sub_col.operator('cm3d2menu.param_add'   , icon='ADD'   , text="")
        sub_col.operator('cm3d2menu.param_remove', icon='REMOVE', text="")
        #sub_col.separator()
        #sub_col.menu("OBJECT_MT_cm3d2_menu_context_menu", icon='DOWNARROW_HLT', text="")
        if self.active_index < len(self.params):
            sub_col.separator()
            sub_col.operator("cm3d2menu.param_move", icon='TRIA_UP'  , text="").direction = 'UP'  
            sub_col.operator("cm3d2menu.param_move", icon='TRIA_DOWN', text="").direction = 'DOWN'




''' CM3D2 Menu Class '''

# This generates OBJECT_PG_CM3D2Menu.command_type_collections
def generate_command_type_collections(cls):
    prop_example = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    cls.command_type_collections = {}

    for prop_name in dir(cls):
        if prop_name == "commands":
            continue

        prop = getattr(cls, prop_name)
        if type(prop) != type(prop_example):
            continue
        if len(prop)  != len(prop_example) :
            continue
        if prop[0]    != prop_example[0]   :
            continue
        
        command_class = prop[1]["type"]
        if command_class == CM3D2MENU_PG_CommandPointer:
            continue

        cls.command_type_collections[command_class.bl_idname] = prop_name
        #print(cls.bl_idname+".command_type_collections[\""+prop_name+"\"]", "=", prop)
    
    return cls

@compat.BlRegister()
@generate_command_type_collections
class OBJECT_PG_CM3D2Menu(bpy.types.PropertyGroup):
    bl_idname = 'CM3D2Menu'

    version     = bpy.props.IntProperty   (name="Version"    , options=PROP_OPTS, min=0, step=100    )
    path        = bpy.props.StringProperty(name="Path"       , options=PROP_OPTS, subtype='FILE_PATH')
    name        = bpy.props.StringProperty(name="Name"       , options=PROP_OPTS)
    category    = bpy.props.StringProperty(name="Category"   , options=PROP_OPTS)
    description = bpy.props.StringProperty(name="Description", options=PROP_OPTS)
                                                                       
    attach_point_commands = bpy.props.CollectionProperty(type=CM3D2MENU_PG_AttachPointCommand, options={'HIDDEN'})
    property_commands     = bpy.props.CollectionProperty(type=CM3D2MENU_PG_PropertyCommand   , options={'HIDDEN'})
    misc_commands         = bpy.props.CollectionProperty(type=CM3D2MENU_PG_MiscCommand       , options={'HIDDEN'})

    commands = bpy.props.CollectionProperty(name="Commands", type=CM3D2MENU_PG_CommandPointer, options=PROP_OPTS)
    active_index = bpy.props.IntProperty(name="Active Command Index", options=PROP_OPTS)
    
    # NOTE : This dictionary is generated by @generate_command_type_collections
    #command_type_collections = {
    #    'CM3D2MenuAttachPointCommand'   : 'attach_point_commands',
    #    'CM3D2MenuPropertyCommand'      : 'property_commands'    ,
    #    ...
    #    for all Collection Properties (except 'commands')
    #}

    updated = bpy.props.BoolProperty(options={'HIDDEN', 'SKIP_SAVE'}, default=False)
    def update(self):
        for index, command_pointer in enumerate(self.commands):
            command = command_pointer.dereference(self)
            command.index = index
        updated = True

    def get_active_command(self):
        if self.active_index >= len(self.commands):
            self.active_index = len(self.commands) - 1
        command_pointer = self.commands[self.active_index]
        return command_pointer.dereference(self)

    def new_command(self, command: str):
        command_type = COMMAND_TYPE_LIST.get(command)
        collection_name = 'misc_commands'
        if command_type:
            collection_name = self.command_type_collections.get(command_type.bl_idname) or collection_name
        
        collection = getattr(self, collection_name)
        new_command = collection.add()
        new_command.command = command
        
        new_pointer = self.commands.add()
        new_pointer.collection_name = collection_name
        new_pointer.prop_index = len(collection) - 1

        new_command.index = len(self.commands) - 1

        return new_command

    def remove_command(self, index: int):
        command_pointer = self.commands[index]
        command = command_pointer.dereference(self)
        
        collection_name = self.command_type_collections.get(command.bl_idname) or 'misc_commands'
        collection = getattr(self, collection_name)

        prop_index = command_pointer.prop_index
        self.commands.remove(index)
        self.update()
        collection.remove(prop_index)

        for i, c in enumerate(collection):
            self.commands[c.index].prop_index = i

    def move_command(self, old_index, new_index, update=True):
        self.commands.move(old_index, new_index)
        self.updated = False
        if update:
            self.update()

    def parse_list(self, string_list):
        command = string_list[0]
        new_command = self.new_command(command)
        new_command.parse_list(string_list)

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
            
            # Check for end of file
            chunk = file.read(1)
            if len(chunk) == 0:
                break
            string_list_length = struct.unpack('<B', chunk)[0]

        self.update()
    
    def pack_into_file(self, file):
        self.update()

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

        self.property_unset('commands'    )
        self.property_unset('active_index')

        self.property_unset('updated')




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
                command_enum_info = get_command_enum_info(command_prop.command)
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

    command_type_enums = COMMAND_ENUMS.copy()
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

# For CM3D2MENU_PG_AttachPointCommand

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
            if type(active_command) != CM3D2MENU_PG_AttachPointCommand:
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
            if type(active_command) != CM3D2MENU_PG_AttachPointCommand:
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



# For CM3D2MENU_PG_MiscCommand

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
            if type(misc_command) == CM3D2MENU_PG_MiscCommand:
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
        if type(misc_command) != CM3D2MENU_PG_MiscCommand:
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
        if type(misc_command) != CM3D2MENU_PG_MiscCommand:
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


