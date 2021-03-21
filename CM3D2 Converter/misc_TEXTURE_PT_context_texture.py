# 「プロパティ」エリア → 「テクスチャ」タブ
import os
import bpy
import bmesh
import mathutils
from . import common
from . import compat
from . import cm3d2_data
from .translations.pgettext_functions import *

LAYOUT_FACTOR = 0.3


# メニュー等に項目追加
def menu_func(self, context):
    ob = context.active_object
    if ob is None or compat.IS_LEGACY is False:
        return
    try:
        tex_slot = context.texture_slot
        tex = context.texture
        mate = ob.active_material
        mate['shader1']
        mate['shader2']
    except:
        return
    if not tex_slot:
        return

    if tex_slot.use:
        slot_type = 'tex'
    else:
        slot_type = 'col' if tex_slot.use_rgb_to_intensity else 'f'

    base_name = common.remove_serial_number(tex.name)

    box = self.layout.box()
    box.label(text="For CM3D2", icon_value=common.kiss_icon())
    split = compat.layout_split(box, factor=1 / 3)
    split.label(text="Setting type:")
    row = split.row()

    if slot_type == 'tex':
        row.label(text="Texture", icon='TEXTURE')
    elif slot_type == 'col':
        row.label(text="Color", icon='COLOR')
    elif slot_type == 'f':
        row.label(text="Value", icon='ARROW_LEFTRIGHT')

    check_row = row.row(align=True)

    check_row.prop(tex_slot, 'use', text="")
    sub_row = check_row.row()
    sub_row.prop(tex_slot, 'use_rgb_to_intensity', text="")
    if tex_slot.use:
        sub_row.enabled = False

    box.prop(tex, 'name', icon='SORTALPHA', text="Setting Value Name")

    if slot_type == "tex":
        if tex.type == 'IMAGE':
            img = tex.image
            if img:
                if img.source == 'FILE':
                    common.setup_image_name(img)

                    sub_box = box.box()
                    row = compat.layout_split(sub_box, factor=1 / 3, align=True)
                    row.label(text="Texture name:")
                    row.template_ID(tex, 'image', open='image.open')
                    if 'cm3d2_path' not in img:
                        img['cm3d2_path'] = common.get_tex_cm3d2path(img.filepath)
                    sub_box.prop(img, '["cm3d2_path"]', text="Game Directory")

                    if base_name == "_ToonRamp":
                        sub_box.menu('TEXTURE_MT_context_texture_ToonRamp', icon='NLA')
                    elif base_name == "_ShadowRateToon":
                        sub_box.menu('TEXTURE_MT_context_texture_ShadowRateToon', icon='NLA')
                    elif base_name == "_OutlineToonRamp":
                        sub_box.menu('TEXTURE_MT_context_texture_OutlineToonRamp', icon='NLA')

                    split = compat.layout_split(sub_box, factor=1 / 3, align=True)
                    split.label(text="Offset:")
                    row = split.row(align=True)
                    row.prop(tex_slot, 'color', index=0, text="")
                    row.prop(tex_slot, 'color', index=1, text="")

                    split = compat.layout_split(sub_box, factor=1 / 3, align=True)
                    split.label(text="Enlargement/Reduction:")
                    row = split.row(align=True)
                    row.prop(tex_slot, 'color', index=2, text="")
                    row.prop(tex_slot, 'diffuse_color_factor', text="")

                    row = sub_box.row()
                    row.operator('image.show_image', text="Image to UV/Image Editor", icon='ZOOM_IN').image_name = img.name
                    if len(img.pixels):
                        row.operator('image.quick_export_cm3d2_tex', text="Save as .tex", icon='FILESEL').node_name = tex.name
                    else:
                        row.operator('image.replace_cm3d2_tex', icon='BORDERMOVE')

    elif slot_type == "col":
        sub_box = box.box()

        # row = compat.layout_split(sub_box, factor=0.7, align=True)
        row = sub_box.row(align=True)
        row.prop(tex_slot, 'color', text="")
        row.operator('texture.auto_set_color_value', icon='AUTO', text="Auto")
        row.operator('texture.set_color_value_old', text="", icon=compat.icon('SHADING_SOLID')).color = [0, 0, 0] + [tex_slot.diffuse_color_factor]
        row.operator('texture.set_color_value_old', text="", icon=compat.icon('MESH_CIRCLE')).color = [1, 1, 1] + [tex_slot.diffuse_color_factor]

        row = sub_box.row(align=True)
        row.operator('texture.set_color_value_old', text="", icon='TRIA_LEFT').color = list(tex_slot.color) + [0]
        row.prop(tex_slot, 'diffuse_color_factor', icon='IMAGE_RGB_ALPHA', text="Alpha", slider=True)
        row.operator('texture.set_color_value_old', text="", icon='TRIA_RIGHT').color = list(tex_slot.color) + [1]

    elif slot_type == "f":
        sub_box = box.box()
        row = sub_box.row(align=True)
        row.prop(tex_slot, 'diffuse_color_factor', icon='ARROW_LEFTRIGHT', text="Value")

        data_path = 'texture_slot.diffuse_color_factor'
        if base_name == '_Shininess':
            row.menu('TEXTURE_MT_context_texture_values_normal', icon='DOWNARROW_HLT', text="")

            row = sub_box.row(align=True)
            row.operator('texture.set_color_value_old', text="0.0", icon='MESH_CIRCLE').color = list(tex_slot.color) + [0.0]
            row.operator('texture.set_color_value_old', text="0.25").color = list(tex_slot.color) + [0.25]
            row.operator('texture.set_color_value_old', text="0.5").color = list(tex_slot.color) + [0.5]
            row.operator('texture.set_color_value_old', text="0.75").color = list(tex_slot.color) + [0.75]
            row.operator('texture.set_color_value_old', text="1.0", icon=compat.icon('NODE_MATERIAL')).color = list(tex_slot.color) + [1.0]

        elif base_name == '_OutlineWidth':
            row.menu('TEXTURE_MT_context_texture_values_OutlineWidth', icon='DOWNARROW_HLT', text="")

            row = sub_box.row(align=True)
            row.operator('texture.set_color_value_old', text="0.001", icon='MATSPHERE').color = list(tex_slot.color) + [0.001]
            row.operator('texture.set_color_value_old', text="0.0015").color = list(tex_slot.color) + [0.0015]
            row.operator('texture.set_color_value_old', text="0.002", icon='ANTIALIASED').color = list(tex_slot.color) + [0.002]

            split = compat.layout_split(sub_box, factor=0.3)
            split.label(text=" Exact Value: ")
            split.label(text=str(tex_slot.diffuse_color_factor))

        elif base_name == '_RimPower':
            row.menu('TEXTURE_MT_context_texture_values_RimPower', icon='DOWNARROW_HLT', text="")

            row = sub_box.row(align=True)
            row.operator('texture.set_color_value_old', text="1", icon='BRUSH_TEXFILL').color = list(tex_slot.color) + [1]
            row.operator('texture.set_color_value_old', text="10").color = list(tex_slot.color) + [10]
            row.operator('texture.set_color_value_old', text="20").color = list(tex_slot.color) + [20]
            row.operator('texture.set_color_value_old', text="30", icon=compat.icon('SHADING_RENDERED')).color = list(tex_slot.color) + [30]

        elif base_name == '_RimShift':
            row.menu('TEXTURE_MT_context_texture_values_normal', icon='DOWNARROW_HLT', text="")

            row = sub_box.row(align=True)
            row.operator('texture.set_color_value_old', text="0.0", icon='FULLSCREEN_EXIT').color = list(tex_slot.color) + [0.0]
            row.operator('texture.set_color_value_old', text="0.25").color = list(tex_slot.color) + [0.25]
            row.operator('texture.set_color_value_old', text="0.5").color = list(tex_slot.color) + [0.5]
            row.operator('texture.set_color_value_old', text="0.75").color = list(tex_slot.color) + [0.75]
            row.operator('texture.set_color_value_old', text="1.0", icon='FULLSCREEN_ENTER').color = list(tex_slot.color) + [1.0]

        elif base_name == '_ZTest':
            row.menu('TEXTURE_MT_context_texture_values_ZTest', icon='DOWNARROW_HLT', text="")
            col = sub_box.column(align=True)
            row = col.row(align=True)
            row.operator('texture.set_color_value_old', text="Disabled").color = list(tex_slot.color) + [0]
            row.operator('texture.set_color_value_old', text="Never").color = list(tex_slot.color) + [1]
            row.operator('texture.set_color_value_old', text="Less ").color = list(tex_slot.color) + [2]
            row.operator('texture.set_color_value_old', text="Equal").color = list(tex_slot.color) + [3]
            row.operator('texture.set_color_value_old', text="LessEqual").color = list(tex_slot.color) + [4]
            row = col.row(align=True)
            row.operator('texture.set_color_value_old', text="Greater").color = list(tex_slot.color) + [5]
            row.operator('texture.set_color_value_old', text="NotEqual").color = list(tex_slot.color) + [6]
            row.operator('texture.set_color_value_old', text="GreaterEqual").color = list(tex_slot.color) + [7]
            row.operator('texture.set_color_value_old', text="Always").color = list(tex_slot.color) + [8]

        elif base_name == '_ZTest2':
            row = sub_box.row(align=True)
            row.operator('texture.set_color_value_old', text="0").color = list(tex_slot.color) + [0]
            row.operator('texture.set_color_value_old', text="1").color = list(tex_slot.color) + [1]

        elif base_name == '_ZTest2Alpha':
            row.menu('TEXTURE_MT_context_texture_values_ZTest2Alpha', icon='DOWNARROW_HLT', text="")
            row = sub_box.row(align=True)
            row.operator('texture.set_color_value_old', text="0").color = list(tex_slot.color) + [0]
            row.operator('texture.set_color_value_old', text="0.8").color = list(tex_slot.color) + [0.8]
            row.operator('texture.set_color_value_old', text="1").color = list(tex_slot.color) + [1]

    box.operator('texture.sync_tex_color_ramps', icon='LINKED')

    description = cm3d2_data.PROP_DESC.get(base_name, '')
    if description != '':
        sub_box = box.box()
        col = sub_box.column(align=True)
        col.label(text="Description", icon='TEXT')
        for line in description:
            col.label(text=line)


# _ToonRamp設定メニュー
@compat.BlRegister(only_legacy=True)
class TEXTURE_MT_context_texture_ToonRamp(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_ToonRamp'
    bl_label = "_ToonRamp Config"

    def draw(self, context):
        l = self.layout
        cmd = 'texture.set_default_toon_textures'
        for toon_tex in cm3d2_data.TOON_TEXES:
            icon = 'LAYER_ACTIVE' if 'Shadow' not in toon_tex else 'LAYER_USED'
            l.operator(cmd, text=toon_tex, icon=icon).name = toon_tex


# _ShadowRateToon設定メニュー
@compat.BlRegister(only_legacy=True)
class TEXTURE_MT_context_texture_ShadowRateToon(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_ShadowRateToon'
    bl_label = "_ShadowRateToon Configuration"

    def draw(self, context):
        l = self.layout
        cmd = 'texture.set_default_toon_textures'
        for toon_tex in cm3d2_data.TOON_TEXES:
            icon = 'LAYER_ACTIVE' if 'Shadow' not in toon_tex else 'LAYER_USED'
            l.operator(cmd, text=toon_tex, icon=icon).name = toon_tex


# _OutlineToonRamp設定メニュー
@compat.BlRegister(only_legacy=True)
class TEXTURE_MT_context_texture_OutlineToonRamp(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_OutlineToonRamp'
    bl_label = "_OutlineToonRamp Config"

    def draw(self, context):
        l = self.layout
        cmd = 'texture.set_default_toon_textures'
        for toon_tex in cm3d2_data.TOON_TEXES:
            icon = 'LAYER_ACTIVE' if 'Shadow' not in toon_tex else 'LAYER_USED'
            l.operator(cmd, text=toon_tex, icon=icon).name = toon_tex


# 0.0～1.0までの値設定メニュー
@compat.BlRegister()
class TEXTURE_MT_context_texture_values_normal(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_values_normal'
    bl_label = "Value list"

    def draw(self, context):
        tex_slot = context.texture_slot
        for i in range(11):
            value = round(i * 0.1, 1)
            icon = 'LAYER_USED' if i % 2 else 'LAYER_ACTIVE'
            self.layout.operator('texture.set_color_value_old', text=str(value), icon=icon).color = list(tex_slot.color) + [value]


# _OutlineWidth用の値設定メニュー
@compat.BlRegister()
class TEXTURE_MT_context_texture_values_OutlineWidth(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_values_OutlineWidth'
    bl_label = "Value list"

    def draw(self, context):
        tex_slot = context.texture_slot
        for i in range(16):
            value = round(i * 0.0002, 4)
            icon = 'LAYER_USED' if i % 2 else 'LAYER_ACTIVE'
            self.layout.operator('texture.set_color_value_old', text=str(value), icon=icon).color = list(tex_slot.color) + [value]


# _RimPower用の値設定メニュー
@compat.BlRegister()
class TEXTURE_MT_context_texture_values_RimPower(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_values_RimPower'
    bl_label = "Value list"

    def draw(self, context):
        tex_slot = context.texture_slot
        for i in range(16):
            value = round(i * 2, 0)
            icon = 'LAYER_USED' if i % 2 else 'LAYER_ACTIVE'
            if value == 0:
                icon = 'ERROR'
            self.layout.operator('texture.set_color_value_old', text=str(value), icon=icon).color = list(tex_slot.color) + [value]


# _ZTest用の値設定メニュー
@compat.BlRegister(only_legacy=True)
class TEXTURE_MT_context_texture_values_ZTest_old(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_values_ZTest'
    bl_label = "List of Values"

    def draw(self, context):
        tex_slot = context.texture_slot
        for i in range(9):
            value = round(i, 0)
            self.layout.operator('texture.set_color_value_old', text=str(value)).color = list(tex_slot.color) + [value]


# _ZTest用の値設定メニュー
@compat.BlRegister(only_latest=True)
class TEXTURE_MT_context_texture_values_ZTest(bpy.types.Menu):
    bl_idname = 'TEXTURE_MT_context_texture_values_ZTest'
    bl_label = "Values"

    node_name = bpy.props.StringProperty(name='NodeName')

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            mate = ob.active_material
            if mate:
                return mate.use_nodes
        return False

    def draw(self, context):
        ob = context.active_object
        mate = ob.active_material
        if mate.use_nodes:
            mate.node_tree.nodes.get()
        tex_slot = context.texture_slot
        for i in range(9):
            value = round(i, 0)
            opr = self.layout.operator('texture.set_value', text=str(value))
            opr.node_name, opr.color = node_name, list(tex_slot.color) + [value]


@compat.BlRegister()
class CNV_OT_show_image(bpy.types.Operator):
    bl_idname = 'image.show_image'
    bl_label = "Open Image in UV/Image Editor"
    bl_description = "Displays the specified image in the UV/ Image Editor"
    bl_options = {'REGISTER', 'UNDO'}

    image_name = bpy.props.StringProperty(name="Image name")

    def execute(self, context):
        if self.image_name in context.blend_data.images:
            img = context.blend_data.images[self.image_name]
        else:
            self.report(type={'ERROR'}, message="Cannot find the file specified")
            return {'CANCELLED'}

        area = common.get_request_area(context, 'IMAGE_EDITOR')
        if area:
            common.set_area_space_attr(area, 'image', img)
        else:
            self.report(type={'ERROR'}, message="Area to view the image as not found")
            return {'CANCELLED'}
        return {'FINISHED'}


@compat.BlRegister(only_legacy=True)
class CNV_OT_replace_cm3d2_tex_old(bpy.types.Operator):
    bl_idname = 'image.replace_cm3d2_tex'
    bl_label = "Find texture"
    bl_description = "looks for textures in the search paths specified in the Converter Settings."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        tex = getattr(context, 'texture')
        if tex:
            return hasattr(tex, 'image')
        return False

    def execute(self, context):
        tex = context.texture
        img = tex.image
        if not common.replace_cm3d2_tex(img, reload_path=True):
            self.report(type={'ERROR'}, message="Could not be located")
            return {'CANCELLED'}
        tex.image_user.use_auto_refresh = True
        return {'FINISHED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_replace_cm3d2_tex(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'image.replace_cm3d2_tex'
    bl_label = "Find Texture(New)"
    bl_description = "looks for textures in the search paths specified in the Converter Settings"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mate = context.material
        return mate and mate.use_nodes
        # ob = bpy.context.active_object
        # if ob:
        #   mate = ob.active_material
        #   if mate:
        #       return mate.use_nodes
        # return False

    def execute(self, context):
        node = self.get_node(context)
        if node and node.type == 'TEX_IMAGE':
            img = node.image
            if img and common.replace_cm3d2_tex(img, reload_path=True):
                self.report(type={'INFO'}, message=f_tip_("Loaded texture file. file={}", img.filepath))
                node.image_user.use_auto_refresh = True
                return {'FINISHED'}
            else:
                msg = f_tip_("Could not find texture file. file=%s", img.filepath) if img else f_tip_("The image is not set")
                self.report(type={'ERROR'}, message=msg)
        else:
            self.report(type={'ERROR'}, message="Skipped because the texture node was not found")
        return {'CANCELLED'}


@compat.BlRegister()
class CNV_OT_sync_tex_color_ramps(bpy.types.Operator):
    bl_idname = 'texture.sync_tex_color_ramps'
    bl_label = "Sync Textures to Colors and Values."
    bl_description = "Applies Textures according to Color changes. (Example: Changing the RimColor)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if getattr(context, 'material'):
            return True

        return getattr(context, 'texture_slot') and getattr(context, 'texture')

    def execute(self, context):
        for mate in context.blend_data.materials:
            if 'shader1' in mate and 'shader2' in mate:
                for slot in mate.texture_slots:
                    if slot:
                        common.set_texture_color(slot)
        return {'FINISHED'}


@compat.BlRegister(only_legacy=True)
class CNV_OT_set_default_toon_textures_old(bpy.types.Operator):
    bl_idname = 'texture.set_default_toon_textures'
    bl_label = "Select the toon"
    bl_description = "Select the default toon texture."
    bl_options = {'REGISTER', 'UNDO'}

    name = bpy.props.StringProperty(name="Texture Name")
    # dir = bpy.props.StringProperty(name="Path", default="Assets\\texture\\texture\\toon\\")

    @classmethod
    def poll(cls, context):
        tex = getattr(context, 'texture')
        if hasattr(context, 'texture_slot') and tex:
            name = common.remove_serial_number(tex.name)
            return name in ["_ToonRamp", "_ShadowRateToon", "_OutlineToonRamp"]
        return False

    def execute(self, context):
        img = context.texture.image
        img.name = self.name

        dirname = os.path.dirname(bpy.path.abspath(img.filepath))
        png_path = os.path.join(dirname, self.name + ".png")
        tex_path = os.path.join(dirname, self.name + ".tex")
        if not os.path.exists(png_path):
            if os.path.exists(tex_path):
                tex_data = common.load_cm3d2tex(tex_path)
                if tex_data is None:
                    return {'CANCELLED'}
                tex_format = tex_data[1]
                if not (tex_format == 3 or tex_format == 5):
                    return {'CANCELLED'}
                with open(png_path, 'wb') as png_file:
                    png_file.write(tex_data[-1])
        img.filepath = png_path
        img.reload()

        if 'cm3d2_path' not in img:
            img['cm3d2_path'] = common.get_tex_cm3d2path(img.filepath)
        return {'FINISHED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_set_default_toon_textures(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'texture.set_default_toon_textures'
    bl_label = "Select Toon"
    bl_description = "You can select the default toon texture to be loaded."
    bl_options = {'REGISTER', 'UNDO'}

    tex_name = bpy.props.StringProperty(name="Texture Name")

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            mate = ob.active_material
            if mate and mate.use_nodes:
                return True

        return False

    def execute(self, context):
        node = self.get_node(context)
        if node is None:
            self.report(type={'ERROR'}, message=f_tip_("Target node '{}' not found", self.node_name))
            return {'CANCELLED'}

        texpathes = common.get_texpath_dict()
        texpath = texpathes.get(self.tex_name.lower())
        if texpath is None:
            if node.image is None:
                node.image = context.blend_data.images.new(self.tex_name, 128, 128)
                node.image.source = 'FILE'
            # 見つからない場合でも、テクスチャ名、ファイルパスに変更を反映
            node.image.name = self.tex_name
            node.image.filepath = self.tex_name + ".png"
        else:

            if node.image is None:
                node.image = bpy.data.images.load(texpath)
                node.image.source = 'FILE'
            else:
                node.image.filepath = texpath
                node.image.reload()

        node.image['cm3d2_path'] = common.get_tex_cm3d2path(node.image.filepath)
        self.report(type={'INFO'}, message=f_tip_("The texture of node '{}' was reset. filepath={}", self.node_name, node.image.filepath))
        return {'FINISHED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_reload_textures(bpy.types.Operator):
    bl_idname = 'texture.reload_textures'
    bl_label = "Reload Image"
    bl_description = "Reread from actual file path settting"
    bl_options = {'REGISTER', 'UNDO'}

    tex_name = bpy.props.StringProperty(name="Texture Name")

    @classmethod
    def poll(cls, context):
        return len(context.blend_data.images) > 0

    def execute(self, context):
        image = context.blend_data.images.get(self.tex_name)
        if image:
            image.reload()
            return {'FINISHED'}

        self.report(type={'ERROR'}, message=f_tip_("Target image '{}' not found", self.tex_name))
        return {'CANCELLED'}


@compat.BlRegister(only_legacy=True)
class CNV_OT_auto_set_color_value_old(bpy.types.Operator):
    bl_idname = 'texture.auto_set_color_value'
    bl_label = "Automatically set the Color setting Value"
    bl_description = "Color settings are set automatically with the Colors in the Texture"
    bl_options = {'REGISTER', 'UNDO'}

    is_all = bpy.props.BoolProperty(name="All", default=True)
    saturation_multi = bpy.props.FloatProperty(name="Saturation Multiplication", default=2.2, min=0, max=5, soft_min=0, soft_max=5, step=10, precision=2)
    value_multi = bpy.props.FloatProperty(name="Mulitplication of Lightness value", default=0.3, min=0, max=5, soft_min=0, soft_max=5, step=10, precision=2)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if not ob or ob.type != 'MESH':
            return False

        mate = ob.active_material
        if not mate:
            return False

        me = ob.data
        for slot in mate.texture_slots:
            if not slot:
                continue
            tex = slot.texture
            name = common.remove_serial_number(tex.name)
            if name == '_MainTex':
                img = tex.image
                if img and len(img.pixels):
                    break
                if me.uv_textures.active:
                    if me.uv_textures.active.data[0].image:
                        if len(me.uv_textures.active.data[0].image.pixels):
                            break
        else:
            return False

        tex = getattr(context, 'texture')
        slot = getattr(context, 'texture_slot')
        if slot and tex:
            name = common.remove_serial_number(tex.name)
            if name in ['_ShadowColor', '_RimColor', '_OutlineColor']:
                return True
        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_all', icon='ACTION')
        row = self.layout.row()
        row.label(text="", icon=compat.icon('SHADING_RENDERED'))
        row.prop(self, 'saturation_multi')
        row = self.layout.row()
        row.label(text="", icon='SOLID')
        row.prop(self, 'value_multi')

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        mate = ob.active_material
        active_slot = context.texture_slot
        active_tex = context.texture
        tex_name = common.remove_serial_number(active_tex.name)

        target_slots = []
        if self.is_all:
            for slot in mate.texture_slots:
                if not slot:
                    continue
                name = common.remove_serial_number(slot.texture.name)
                if name in ['_ShadowColor', '_RimColor', '_OutlineColor']:
                    target_slots.append(slot)
        else:
            target_slots.append(active_slot)

        for slot in mate.texture_slots:
            if not slot:
                continue
            name = common.remove_serial_number(slot.texture.name)
            if name == '_MainTex':
                img = slot.texture.image
                if img:
                    if len(img.pixels):
                        break
        else:
            img = me.uv_textures.active.data[0].image

        sample_count = 10
        img_width, img_height, img_channel = img.size[0], img.size[1], img.channels

        bm = bmesh.new()
        bm.from_mesh(me)
        uv_lay = bm.loops.layers.uv.active
        uvs = [l[uv_lay].uv[:] for f in bm.faces if f.material_index == ob.active_material_index for l in f.loops]
        bm.free()

        average_color = mathutils.Color([0, 0, 0])
        seek_interval = len(uvs) / sample_count
        for sample_index in range(sample_count):

            uv_index = int(seek_interval * sample_index)
            x, y = uvs[uv_index]
            x, y = int(x * img_width), int(y * img_height)

            pixel_index = ((y * img_width) + x) * img_channel
            color = mathutils.Color(img.pixels[pixel_index: pixel_index + 3])

            average_color += color
        average_color /= sample_count
        average_color.s *= self.saturation_multi
        average_color.v *= self.value_multi

        for slot in target_slots:
            slot.color = average_color[:3]
            common.set_texture_color(slot)

        return {'FINISHED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_auto_set_color_value(bpy.types.Operator):
    bl_idname = 'texture.auto_set_color_value'
    bl_label = "Automatically set colors"
    bl_description = "Set color-related setting values ​​automatically from texture color information"
    bl_options = {'REGISTER', 'UNDO'}

    is_all = bpy.props.BoolProperty(name="All", default=True)
    saturation_multi = bpy.props.FloatProperty(name="Saturation Multiplier", default=2.2, min=0, max=5, soft_min=0, soft_max=5, step=10, precision=2)
    value_multi = bpy.props.FloatProperty(name="Brightness Multiplier", default=0.3, min=0, max=5, soft_min=0, soft_max=5, step=10, precision=2)
    node_name = bpy.props.StringProperty(name='NodeName')

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if not ob or ob.type != 'MESH':
            return False

        mate = ob.active_material
        if not mate or mate.use_nodes is False:
            return False

        tex_node = mate.node_tree.nodes.get('_MainTex')
        # if tex_node is None:  # serial_numberが入っているケースを考慮する場合
        #   for node in mate.node_tree.nodes:
        #       if node.name.startswith('_MainTex.'):
        #           name = common.remove_serial_number(node.name)
        #           if name == '_MainTex':
        #               tex_node = node
        #               break
        if tex_node is None:
            return False

        img = tex_node.image
        return img and len(img.pixels)

        # found = False
        # if img and len(img.pixels):
        #   found = True
        # else:
        #   layer = me.uv_layers.active
        #   if layer and len(layer.data):
        #       # TODO imageはアクセスできないため、代替がないか確認
        #       if layer.data[0].image:
        #           if len(layer.data[0].image.pixels):
        #               found = True
        # return found

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'is_all', icon='ACTION')
        row = self.layout.row()
        row.label(text="", icon=compat.icon('SHADING_RENDERED'))
        row.prop(self, 'saturation_multi')
        row = self.layout.row()
        row.label(text="", icon=compat.icon('SHADING_SOLID'))
        row.prop(self, 'value_multi')

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        mate = ob.active_material
        # active_slot = context.texture_slot
        # active_tex = context.texture
        # tex_name = common.remove_serial_number(active_tex.name)

        target_slots = []
        if self.is_all:
            for node in mate.node_tree.nodes:
                node_name = common.remove_serial_number(node.name)
                if node_name in ['_ShadowColor', '_RimColor', '_OutlineColor']:
                    target_slots.append(node)
        else:
            target_slots.append(mate.node_tree.nodes)

        main_node = mate.node_tree.nodes.get('_MainTex')
        if main_node is None:
            for node in mate.node_tree.nodes:
                if node.type == 'TEX_IMAGE':
                    name = common.remove_serial_number(node.name)
                    if name == '_MainTex':
                        main_node = node
                        break
        img = None
        if main_node:
            img = main_node.image

        if img is None or len(img.pixels) == 0:
            layer = me.uv_layers.active
            if len(layer.data) > 0:
                img = layer.data[0].image

        if img is None or len(img.pixels) == 0:
            return {'CANCELLED'}

        sample_count = 10
        img_width, img_height, img_channel = img.size[0], img.size[1], img.channels

        bm = bmesh.new()
        try:
            bm.from_mesh(me)
            uv_lay = bm.loops.layers.uv.active
            uvs = [l[uv_lay].uv[:] for f in bm.faces if f.material_index == ob.active_material_index for l in f.loops]
        finally:
            bm.free()

        avg_color = mathutils.Color([0, 0, 0])
        seek_interval = len(uvs) / sample_count
        for sample_index in range(sample_count):
            uv_index = int(seek_interval * sample_index)
            x, y = uvs[uv_index]
            x, y = int(x * img_width), int(y * img_height)

            pixel_index = ((y * img_width) + x) * img_channel
            color = mathutils.Color(img.pixels[pixel_index:pixel_index + 3])

            avg_color += color
        avg_color /= sample_count
        avg_color.s *= self.saturation_multi
        avg_color.v *= self.value_multi

        for slot in target_slots:
            slot.outputs[0].default_value = (avg_color[0], avg_color[1], avg_color[2], 1.0)

        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_quick_export_cm3d2_tex(bpy.types.Operator):
    bl_idname = 'image.quick_export_cm3d2_tex'
    bl_label = "Save as Tex"
    bl_description = "Save the texture image as tex in the same folder"
    bl_options = {'REGISTER'}

    node_name = bpy.props.StringProperty(name="NodeName")

    def execute(self, context):
        img = compat.get_tex_image(context, self.node_name)
        if img is None or len(img.pixels) == 0:
            self.report(type={'ERROR'}, message=f_tip_("Failed to get image of '{}'", self.node_name))
            return {'CANCELLED'}

        override = context.copy()
        override['edit_image'] = img

        filepath = os.path.splitext(bpy.path.abspath(img.filepath))[0] + ".tex"
        if 'cm3d2_path' in img:
            path = img['cm3d2_path']
        else:
            path = common.get_tex_cm3d2path(img.filepath)
            img['cm3d2_path'] = path

        # 既存のファイルがあればそこから、バージョンとサイズを取得
        version = '1000'
        uv_rects = None
        if os.path.exists(filepath):
            tex_data = common.load_cm3d2tex(filepath, skip_data=True)
            if tex_data:
                version = str(tex_data[0])
                uv_rects = tex_data[2]
        bpy.types.Scene.MyUVRects = uv_rects
        bpy.ops.image.export_cm3d2_tex(override, filepath=filepath, path=path, version=version)

        self.report(type={'INFO'}, message="Saved as .tex in the same folder" + filepath)
        return {'FINISHED'}


@compat.BlRegister(only_legacy=True)
class CNV_OT_set_color_value_old(bpy.types.Operator):
    bl_idname = 'texture.set_color_value_old'
    bl_label = "Set Color Settings"
    bl_description = "Set the color type setting value"
    bl_options = {'REGISTER', 'UNDO'}

    color = bpy.props.FloatVectorProperty(name="Color", default=(0, 0, 0, 0), subtype='COLOR', size=4)

    @classmethod
    def poll(cls, context):
        if hasattr(context, 'texture_slot') and hasattr(context, 'texture'):
            return True
        return False

    def execute(self, context):
        slot = context.texture_slot
        slot.color = self.color[:3]
        slot.diffuse_color_factor = self.color[3]
        common.set_texture_color(slot)
        return {'FINISHED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_set_color_value(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'texture.set_color_value'
    bl_label = "Set the Color setting Value"
    bl_description = "Set the Color type of setting Value"
    bl_options = {'REGISTER', 'UNDO'}

    color = bpy.props.FloatVectorProperty(name="Color", default=(0, 0, 0, 0), subtype='COLOR', size=4)

    @classmethod
    def poll(cls, context):
        mate = context.material
        return mate and mate.use_nodes

    def execute(self, context):
        node = self.get_node(context)
        if node is None:
            return {'CANCELLED'}

        node.outputs[0].default_value = self.color
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_set_value(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'texture.set_value'
    bl_label = "Set Float Value"
    bl_description = "Set the value of a float type"
    bl_options = {'REGISTER', 'UNDO'}

    value = bpy.props.FloatProperty(name='value')

    @classmethod
    def poll(cls, context):
        if compat.IS_LEGACY:
            if getattr(context, 'texture_slot') and getattr(context, 'texture'):
                return True
        else:
            mate = context.material
            return mate and mate.use_nodes
        return False

    def execute(self, context):
        if compat.IS_LEGACY:
            slot = context.texture_slot
            slot.color = self.color[:3]
            slot.diffuse_color_factor = self.color[3]
            common.set_texture_color(slot)
        else:
            node = self.get_node(context)
            if node is None:  # or node.type != 'VALUE':
                return {'CANCELLED'}
            node.outputs[0].default_value = self.value

        return {'FINISHED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_texture_reset_offset(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'texture.reset_offset'
    bl_label = "Reset Texture Offset"
    bl_description = "Set initial value of texture offset(0, 0)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = self.get_node(context)
        if node and node.type == 'TEX_IMAGE':
            node.texture_mapping.translation[0] = 0
            node.texture_mapping.translation[1] = 0
            return {'FINISHED'}

        return {'CANCELLED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_texture_reset_scale(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'texture.reset_scale'
    bl_label = "Reset Texture Scale"
    bl_description = "Set the intial value (1,1) for the texture scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = self.get_node(context)
        if node and node.type == 'TEX_IMAGE':
            node.texture_mapping.scale[0] = 1
            node.texture_mapping.scale[1] = 1
            return {'FINISHED'}

        return {'CANCELLED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_set_cm3d2path(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'texture.set_cm3d2path'
    bl_label = "Set CM3d2 Path"
    bl_description = "Automatically set the game directory from which to grab textures."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = self.get_node(context)
        if node and node.type == 'TEX_IMAGE':
            img = node.image
            img['cm3d2_path'] = common.get_tex_cm3d2path(img.filepath)
            return {'FINISHED'}
        return {'CANCELLED'}


@compat.BlRegister(only_latest=True)
class CNV_OT_setup_image_name(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'texture.setup_image_name'
    bl_label = "Exclude extensions from image names"
    bl_description = "Allows you to write texture names in the materials without including the extension"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        node = self.get_node(context)
        if node and node.type == 'TEX_IMAGE':
            img = node.image
            common.setup_image_name(img)
            return {'FINISHED'}
        return {'CANCELLED'}


# Toon設定メニュー
class ToonSelectMenuBase():
    bl_label = "toon tex Choice"

    def draw(self, context):
        layout = self.layout
        cmd = 'texture.set_default_toon_textures'
        for toon_tex in cm3d2_data.TOON_TEXES:
            icon = 'LAYER_ACTIVE' if 'Shadow' not in toon_tex else 'LAYER_USED'
            opr = layout.operator(cmd, text=toon_tex, icon=icon)
            opr.node_name, opr.tex_name = self.node_name(), toon_tex

    def node_name(self):
        pass


@compat.BlRegister(only_latest=True)
class TEXTURE_MT_texture_ToonRamp(bpy.types.Menu, ToonSelectMenuBase):
    bl_idname = 'TEXTURE_MT_texture_ToonRamp'

    def node_name(self):
        return '_ToonRamp'


@compat.BlRegister(only_latest=True)
class TEXTURE_MT_texture_ShadowRateToon(bpy.types.Menu, ToonSelectMenuBase):
    bl_idname = 'TEXTURE_MT_texture_ShadowRateToon'

    def node_name(self):
        return '_ShadowRateToon'


@compat.BlRegister(only_latest=True)
class TEXTURE_MT_texture_OutlineToonRamp(bpy.types.Menu, ToonSelectMenuBase):
    bl_idname = 'TEXTURE_MT_texture_OutlineToonRamp'

    def node_name(self):
        return '_OutlineToonRamp'
