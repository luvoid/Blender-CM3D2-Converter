import bpy
import math
import mathutils
import struct
from . import common
from . import compat
from .translations.pgettext_functions import *



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
            prefix = f_tip_("Error {gerund} {bl_idname}: ", gerund=gerund, bl_idname=cls.bl_idname) + "{message}"
            def _f(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except catch_type as e:
                    raise throw_type(prefix.format(message=e.args[0]))
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

        return buffer

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

        return buffer

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
        command_class = None
        if type(prop) != type(prop_example):
            continue
        if "len" in dir(prop):
            if len(prop)  != len(prop_example) :
                continue
            if prop[0]    != prop_example[0]   :
                continue
            command_class = prop[1]["type"]

        # Fix for Blender 2.93
        elif "keywords" in dir(prop): 
            if len(prop.keywords)  != len(prop_example.keywords) :
                continue
            command_class = prop.keywords["type"]
        else:
            continue

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
    active_index = bpy.props.IntProperty(name="Active Command Index", options=PROP_OPTS, default=0)
    
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
        if len(self.commands) <= self.active_index:
            return None
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

        if self.active_index >= len(self.commands):
            self.active_index = len(self.commands) - 1

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


# Pannel & operators in ./CM3D2 Converter/menu_OBJECT_PT_cm3d2_menu.py
from . import menu_OBJECT_PT_cm3d2_menu

# メニューを登録する関数
def import_menu_func(self, context):
    self.layout.operator(menu_OBJECT_PT_cm3d2_menu.CM3D2MENU_OT_import.bl_idname, text="CM3D2 Menu (.menu)", icon_value=common.kiss_icon())

# メニューを登録する関数
def export_menu_func(self, context):
    self.layout.operator(menu_OBJECT_PT_cm3d2_menu.CM3D2MENU_OT_export.bl_idname, text="CM3D2 Menu (.menu)", icon_value=common.kiss_icon())

