# 「プロパティ」エリア → 「マテリアル」タブ
import os
import re
import sys
import time
import bpy
import bmesh
import mathutils
from . import common
from . import compat
from . import cm3d2_data
from .translations.pgettext_functions import *


# メニュー等に項目追加 (for 2.7x or less)
def menu_func(self, context):
    if compat.IS_LEGACY is False:
        return

    # ModelVersionでCOM3D2のmodelか判断
    model_ver = bpy.context.active_object.get("ModelVersion")
    is_com_mode = model_ver and model_ver >= 2000

    mate = context.material
    if not mate:
        col = self.layout.column(align=True)
        if is_com_mode:
            col.operator('material.new_com3d2', icon_value=common.kiss_icon())
        else:
            col.operator('material.new_cm3d2', icon_value=common.kiss_icon())
            col.operator('material.new_com3d2', icon='ERROR')
        row = col.row(align=True)
        row.operator('material.import_cm3d2_mate', icon='FILE_FOLDER', text="mateから")
        opr = row.operator('material.paste_material', icon='PASTEDOWN', text="クリップボードから")
        opr.is_decorate, opr.is_create = True, True
    else:
        if 'shader1' in mate and 'shader2' in mate:
            box = self.layout.box()
            # row = box.split(percentage=0.3)
            row = compat.layout_split(box, factor=0.5)
            row.label(text="CM3D2用", icon_value=common.kiss_icon())
            sub_row = row.row(align=True)
            sub_row.operator('material.export_cm3d2_mate', icon='FILE_FOLDER', text="mateへ")
            sub_row.operator('material.copy_material', icon='COPYDOWN', text="コピー")
            sub_row.operator('material.paste_material', icon='PASTEDOWN', text="貼付け")

            icon = 'ERROR'
            shader1 = mate['shader1']
            shader_prop = cm3d2_data.Handler.get_shader_prop(shader1)
            type_name = shader_prop.get('type_name')
            icon = shader_prop.get('icon')

            row = compat.layout_split(box, factor=0.333333333333333333333)
            row.label(text="種類:")
            row.label(text=type_name, icon=icon)
            box.prop(mate, 'name', icon='SORTALPHA', text="マテリアル名")
            box.prop(mate, '["shader1"]', icon='MATERIAL', text="シェーダー1")
            box.prop(mate, '["shader2"]', icon=compat.icon('SHADING_RENDERED'), text="シェーダー2")

            box.operator('material.decorate_material', icon=compat.icon('SHADING_TEXTURE'))

            if 'CM3D2 Texture Expand' not in mate:
                mate['CM3D2 Texture Expand'] = True
            box = self.layout.box()
            if mate.get('CM3D2 Texture Expand', False):
                row = box.row()
                row.alignment = 'LEFT'
                op = row.operator('wm.context_set_int', icon='DOWNARROW_HLT', text="", emboss=False)
                op.data_path, op.value, op.relative = 'material["CM3D2 Texture Expand"]', 0, False
                row.label(text="簡易テクスチャ情報", icon_value=common.kiss_icon())

                if compat.IS_LEGACY:
                    for slot in mate.texture_slots:
                        if not slot or not slot.texture:
                            continue
                        tex = slot.texture
                        name = common.remove_serial_number(tex.name).replace("_", "") + " "

                        if slot.use:
                            node_type = 'tex'
                        else:
                            node_type = 'col' if slot.use_rgb_to_intensity else 'f'

                        if node_type == 'tex':
                            row = box.row(align=True)
                            sub_row = compat.layout_split(row, factor=0.333333333333333333333, align=True)
                            sub_row.label(text=name, icon_value=sub_row.icon(tex))
                            img = getattr(text, 'image')
                            if img:
                                sub_row.template_ID(tex, 'image')
                            row.operator('material.quick_texture_show', text="", icon='RIGHTARROW').texture_name = tex.name
                        elif node_type == 'col':
                            row = box.row(align=True)
                            sub_row = compat.layout_split(row, factor=0.333333333333333333333, align=True)
                            sub_row.label(text=name, icon_value=sub_row.icon(tex))
                            sub_row.prop(slot, 'color', text="")
                            sub_row.prop(slot, 'diffuse_color_factor', icon='IMAGE_RGB_ALPHA', text="透明度", slider=True)
                            row.operator('material.quick_texture_show', text="", icon='RIGHTARROW').texture_name = tex.name
                        elif node_type == 'f':
                            row = box.row(align=True)
                            sub_row = compat.layout_split(row, factor=0.333333333333333333333, align=True)
                            sub_row.label(text=name, icon_value=sub_row.icon(tex))
                            sub_row.prop(slot, 'diffuse_color_factor', icon='ARROW_LEFTRIGHT', text="値")
                            row.operator('material.quick_texture_show', text="", icon='RIGHTARROW').texture_name = tex.name

                    box.operator('texture.sync_tex_color_ramps', icon='LINKED')

            else:
                row = box.row()
                row.alignment = 'LEFT'
                op = row.operator('wm.context_set_int', icon='RIGHTARROW', text="", emboss=False)
                op.data_path, op.value, op.relative = 'material["CM3D2 Texture Expand"]', 1, False
                row.label(text="簡易テクスチャ情報", icon_value=common.kiss_icon())

        else:
            if is_com_mode:
                self.layout.operator('material.new_com3d2', text="COM3D2用に変更", icon_value=common.kiss_icon())
            else:
                self.layout.operator('material.new_com3d2', text="COM3D2用に変更", icon_value=common.kiss_icon())
                self.layout.operator('material.new_cm3d2', text="CM3D2用に変更", icon_value=common.kiss_icon())


@compat.BlRegister(only_latest=True)
class MATERIAL_PT_cm3d2_properties(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_label = 'CM3D2'
    bl_idname = 'MATERIAL_PT_cm3d2_properties'

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        ob = context.active_object
        # ModelVersionでCOM3D2のmodelか判断
        model_ver = ob.get('ModelVersion')
        is_com_mode = model_ver and model_ver >= 2000

        mate = context.material
        if not mate:
            col = self.layout.column(align=True)
            if is_com_mode:
                col.operator('material.new_com3d2', icon_value=common.kiss_icon())
            else:
                col.operator('material.new_cm3d2', icon_value=common.kiss_icon())
                col.operator('material.new_com3d2', icon='ERROR')
            row = col.row(align=True)
            row.operator('material.import_cm3d2_mate', icon='FILE_FOLDER', text="mateから")
            opr = row.operator('material.paste_material', icon='PASTEDOWN', text="クリップボードから")
            opr.is_decorate, opr.is_create, opr.use_dialog = True, True, False

        else:
            if 'shader1' in mate and 'shader2' in mate:
                box = self.layout#.box()
                # row = box.split(percentage=0.3)
                #row = compat.layout_split(box, factor=0.5)
                row = self.layout.column()
                row.label(text="CM3D2用", icon_value=common.kiss_icon())
                sub_row = row.row(align=True)
                sub_row.operator('material.export_cm3d2_mate', icon='FILE_FOLDER', text="mateへ")
                sub_row.operator('material.copy_material', icon='COPYDOWN', text="コピー")
                opr = sub_row.operator('material.paste_material', icon='PASTEDOWN', text="貼付け")
                opr.use_dialog = True
                opr.is_create = False

                shader1 = mate['shader1']
                shader_prop = cm3d2_data.Handler.get_shader_prop(shader1)
                type_name = shader_prop.get('type_name', '不明')
                icon = shader_prop.get('icon', 'ERROR')

                row = compat.layout_split(box, factor=1 / 3)
                row.label(text="種類:")
                row.label(text=type_name, icon=icon)
                box.prop(mate, 'name', icon='SORTALPHA', text="マテリアル名")
                box.prop(mate, '["shader1"]', icon='MATERIAL', text="シェーダー1")
                box.prop(mate, '["shader2"]', icon=compat.icon('SHADING_RENDERED'), text="シェーダー2")

                # For LEGACY
                # box.operator('material.decorate_material', icon=compat.icon('SHADING_TEXTURE'))
                if 'CM3D2 Texture Expand' not in mate:
                    box.operator('material.setup_mate_expand', text="フラグセットアップ")
                    return

                box = self.layout.box()
                if mate['CM3D2 Texture Expand']:
                    if mate.use_nodes is False:
                        box.operator('material.setup_mate_expand', text="フラグセットアップ")
                        return

                    row = box.row()
                    row.alignment = 'LEFT'
                    op = row.operator('wm.context_set_int', icon='DOWNARROW_HLT', text="", emboss=False)
                    op.data_path, op.value, op.relative = 'material["CM3D2 Texture Expand"]', 0, False
                    row.label(text="マテリアルプロパティ", icon_value=common.kiss_icon())

                    # ノード名はシリアル番号がついていない想定とする
                    tex_list, col_list, f_list = [], [], []
                    nodes = mate.node_tree.nodes
                    for node_name in shader_prop['tex_list']:
                        node = nodes.get(node_name)
                        if node and node.type == 'TEX_IMAGE':
                            tex_list.append(node)

                    for node_name in shader_prop['col_list']:
                        node = nodes.get(node_name)
                        if node and node.type == 'RGB':
                            col_list.append(node)

                    for node_name in shader_prop['f_list']:
                        node = nodes.get(node_name)
                        if node and node.type == 'VALUE':
                            f_list.append(node)

                    for node in tex_list:
                        tex = node.image
                        if tex:
                            name = common.remove_serial_number(tex.name).replace("_", "") + " "

                            row = box.row(align=True)
                            sub_row = compat.layout_split(row, factor=1 / 3, align=True)
                            sub_row.label(text=node.label, icon_value=sub_row.icon(tex))
                            if tex:
                                sub_row.template_ID(node, 'image', open='image.open')

                            expand = node.get('CM3D2 Prop Expand', False)
                            if expand:
                                row.operator(CNV_OT_material_prop_expand.bl_idname, icon='TRIA_DOWN', text="", emboss=False).node_name = node.name
                                menu_mateprop_tex(context, box, node)
                            else:
                                row.operator(CNV_OT_material_prop_expand.bl_idname, icon='TRIA_LEFT', text="", emboss=False).node_name = node.name

                    for node in col_list:
                        row = box.row(align=True)
                        sub_row = compat.layout_split(row, factor=1 / 3, align=True)
                        sub_row.label(text=node.label, icon='COLOR')
                        col = node.outputs[0]
                        sub_row.prop(col, 'default_value', text="")

                        expand = node.get('CM3D2 Prop Expand', False)
                        if expand:
                            row.operator(CNV_OT_material_prop_expand.bl_idname, icon='TRIA_DOWN', text="", emboss=False).node_name = node.name
                            menu_mateprop_col(context, box, node)
                        else:
                            row.operator(CNV_OT_material_prop_expand.bl_idname, icon='TRIA_LEFT', text="", emboss=False).node_name = node.name

                    for node in f_list:
                        row = box.row(align=True)

                        sub_row = compat.layout_split(row, factor=1 / 3, align=True)
                        sub_row.label(text=node.label, icon='ARROW_LEFTRIGHT')

                        f = node.outputs[0]
                        sub_row.prop(f, 'default_value', icon='ARROW_LEFTRIGHT', text="値")

                        expand = node.get('CM3D2 Prop Expand', False)
                        if expand:
                            row.operator(CNV_OT_material_prop_expand.bl_idname, icon='TRIA_DOWN', text="", emboss=False).node_name = node.name
                            menu_mateprop_f(context, box, node)
                        else:
                            row.operator(CNV_OT_material_prop_expand.bl_idname, icon='TRIA_LEFT', text="", emboss=False).node_name = node.name

                    # if compat.IS_LEGACY:
                    # 	box.operator('texture.sync_tex_color_ramps', icon='LINKED')
                else:
                    row = box.row()
                    row.alignment = 'LEFT'
                    op = row.operator('wm.context_set_int', icon='RIGHTARROW', text="", emboss=False)
                    op.data_path, op.value, op.relative = 'material["CM3D2 Texture Expand"]', 1, False
                    row.label(text="マテリアルプロパティ", icon_value=common.kiss_icon())
                    # op = row.operator('wm.context_set_int', icon='RIGHTARROW', text="", emboss=False)

            else:
                if is_com_mode:
                    self.layout.operator('material.new_com3d2', text="COM3D2用に変更", icon_value=common.kiss_icon())
                else:
                    self.layout.operator('material.new_cm3d2', text="CM3D2用に変更", icon_value=common.kiss_icon())
                    self.layout.operator('material.new_com3d2', text="COM3D2用に変更", icon_value=common.kiss_icon())


class new_mate_opr():
    is_decorate = bpy.props.BoolProperty(name="種類に合わせてマテリアルを装飾", default=True)
    # is_replace_cm3d2_tex = bpy.props.BoolProperty(name="テクスチャを探す", default=False, description="CM3D2本体のインストールフォルダからtexファイルを探して開きます")

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.separator()
        self.layout.prop(self, 'shader_type', icon='MATERIAL')
        if compat.IS_LEGACY:
            self.layout.prop(self, 'is_decorate', icon=compat.icon('SHADING_TEXTURE'))
        prefs = common.preferences()

        self.layout.prop(prefs, 'is_replace_cm3d2_tex', icon='BORDERMOVE')

    def execute(self, context):
        ob = context.active_object
        me = ob.data
        ob_names = common.remove_serial_number(ob.name).split('.')
        ob_name = ob_names[0]

        if context.material:
            mate = context.material
            if compat.IS_LEGACY:
                for index, slot in enumerate(mate.texture_slots):
                    mate.texture_slots.clear(index)
            else:
                if mate.use_nodes:
                    cm3d2_data.clear_nodes(mate.node_tree.nodes)

        else:
            if not context.material_slot:
                bpy.ops.object.material_slot_add()
            mate = context.blend_data.materials.new(ob_name)
        common.setup_material(mate)

        context.material_slot.material = mate
        tex_list, col_list, f_list = [], [], []

        base_path = common.BASE_PATH_TEX
        prefs = common.preferences()

        _MainTex = ("_MainTex", ob_name, base_path + ob_name + ".png")
        _ToonRamp = ("_ToonRamp", prefs.new_mate_toonramp_name, prefs.new_mate_toonramp_path)
        _ShadowTex = ("_ShadowTex", ob_name + "_shadow", base_path + ob_name + "_shadow.png")
        _ShadowRateToon = ("_ShadowRateToon", prefs.new_mate_shadowratetoon_name, prefs.new_mate_shadowratetoon_path)
        _HiTex = ("_HiTex", ob_name + "_s", base_path + ob_name + "_s.png")
        _OutlineTex = ("_OutlineTex", ob_name + "_line", base_path + ob_name + "_line.png")
        _OutlineToonRamp = ("_OutlineToonRamp", prefs.new_mate_linetoonramp_name, prefs.new_mate_linetoonramp_path)

        _Color = ("_Color", prefs.new_mate_color)
        _ShadowColor = ("_ShadowColor", prefs.new_mate_shadowcolor)
        _RimColor = ("_RimColor", prefs.new_mate_rimcolor)
        _OutlineColor = ("_OutlineColor", prefs.new_mate_outlinecolor)

        _Shininess = ("_Shininess", prefs.new_mate_shininess)
        _OutlineWidth = ("_OutlineWidth", prefs.new_mate_outlinewidth)
        _RimPower = ("_RimPower", prefs.new_mate_rimpower)
        _RimShift = ("_RimShift", prefs.new_mate_rimshift)
        _HiRate = ("_HiRate", prefs.new_mate_hirate)
        _HiPow = ("_HiPow", prefs.new_mate_hipow)
        _Cutoff = ("_Cutoff", prefs.new_mate_cutoff)
        _ZTest = ("_ZTest", prefs.new_mate_ztest)
        _ZTest2 = ("_ZTest2", prefs.new_mate_ztest2)
        _ZTest2Alpha = ("_ZTest2Alpha", prefs.new_mate_ztest2alpha)

        if False:
            pass
        elif self.shader_type == 'CM3D2/Toony_Lighted_Outline':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Outline'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Outline'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            col_list.append(_OutlineColor)
            f_list.append(_Shininess)
            f_list.append(_OutlineWidth)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Trans':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Trans'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Trans'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            f_list.append(_Shininess)
            f_list.append(_Cutoff)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Hair_Outline':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Hair_Outline'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Hair_Outline'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            tex_list.append(_HiTex)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            col_list.append(_OutlineColor)
            f_list.append(_Shininess)
            f_list.append(_OutlineWidth)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
            f_list.append(_HiRate)
            f_list.append(_HiPow)
        elif self.shader_type == 'CM3D2/Mosaic':
            mate['shader1'] = 'CM3D2/Mosaic'
            mate['shader2'] = 'CM3D2__Mosaic'
            tex_list.append(("_RenderTex", ""))
            f_list.append(("_FloatValue1", 30))
        elif self.shader_type == 'Unlit/Texture':
            mate['shader1'] = 'Unlit/Texture'
            mate['shader2'] = 'Unlit__Texture'
            tex_list.append(_MainTex)
            # col_list.append(_Color)
        elif self.shader_type == 'Unlit/Transparent':
            mate['shader1'] = 'Unlit/Transparent'
            mate['shader2'] = 'Unlit__Transparent'
            tex_list.append(_MainTex)
            # col_list.append(_Color)
            # col_list.append(_ShadowColor)
            # col_list.append(_RimColor)
            # f_list.append(_Shininess)
            # f_list.append(_RimPower)
            # f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2/Man':
            mate['shader1'] = 'CM3D2/Man'
            mate['shader2'] = 'CM3D2__Man'
            col_list.append(_Color)
            f_list.append(("_FloatValue2", 0.5))
            f_list.append(("_FloatValue3", 1))
        elif self.shader_type == 'Diffuse':
            mate['shader1'] = 'Legacy Shaders/Diffuse'
            mate['shader2'] = 'Legacy Shaders__Diffuse'
            tex_list.append(_MainTex)
            col_list.append(_Color)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Trans_NoZ':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Trans_NoZ'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Trans_NoZ'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            f_list.append(_Shininess)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Trans_NoZTest':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Trans_NoZTest'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Trans_NoZTest'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            f_list.append(_Shininess)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
            f_list.append(_ZTest)
            f_list.append(_ZTest2)
            f_list.append(_ZTest2Alpha)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Outline_Trans':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Outline_Trans'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Outline_Trans'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            col_list.append(_OutlineColor)
            f_list.append(_Shininess)
            f_list.append(_OutlineWidth)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Outline_Tex':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Outline_Tex'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Outline_Tex'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            tex_list.append(_OutlineTex)
            tex_list.append(_OutlineToonRamp)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            col_list.append(_OutlineColor)
            f_list.append(_Shininess)
            f_list.append(_OutlineWidth)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2/Lighted':
            mate['shader1'] = 'CM3D2/Lighted'
            mate['shader2'] = 'CM3D2__Lighted'
            tex_list.append(_MainTex)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            f_list.append(_Shininess)
        elif self.shader_type == 'CM3D2/Lighted_Cutout_AtC':
            mate['shader1'] = 'CM3D2/Lighted_Cutout_AtC'
            mate['shader2'] = 'CM3D2__Lighted_Cutout_AtC'
            tex_list.append(_MainTex)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            f_list.append(_Shininess)
            f_list.append(_Cutoff)
        elif self.shader_type == 'CM3D2/Lighted_Trans':
            mate['shader1'] = 'CM3D2/Lighted_Trans'
            mate['shader2'] = 'CM3D2__Lighted_Trans'
            tex_list.append(_MainTex)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            f_list.append(_Shininess)
        elif self.shader_type == 'CM3D2/Toony_Lighted':
            mate['shader1'] = 'CM3D2/Toony_Lighted'
            mate['shader2'] = 'CM3D2__Toony_Lighted'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            f_list.append(_Shininess)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Cutout_AtC':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Cutout_AtC'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Cutout_AtC'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            f_list.append(_Shininess)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
            f_list.append(_Cutoff)
        elif self.shader_type == 'CM3D2/Toony_Lighted_Hair':
            mate['shader1'] = 'CM3D2/Toony_Lighted_Hair'
            mate['shader2'] = 'CM3D2__Toony_Lighted_Hair'
            tex_list.append(_MainTex)
            tex_list.append(_ToonRamp)
            tex_list.append(_ShadowTex)
            tex_list.append(_ShadowRateToon)
            tex_list.append(_HiTex)
            col_list.append(_Color)
            col_list.append(_ShadowColor)
            col_list.append(_RimColor)
            f_list.append(_Shininess)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
            f_list.append(_HiRate)
            f_list.append(_HiPow)
        elif self.shader_type == 'Transparent/Diffuse':
            mate['shader1'] = 'Legacy Shaders/Transparent/Diffuse'
            mate['shader2'] = 'Legacy Shaders__Transparent__Diffuse'
            tex_list.append(_MainTex)
            col_list.append(_Color)
            # col_list.append(_ShadowColor)
            # col_list.append(_RimColor)
            # col_list.append(_OutlineColor)
            # f_list.append(_Shininess)
            # f_list.append(_OutlineWidth)
            # f_list.append(_RimPower)
            # f_list.append(_RimShift)
        elif self.shader_type == 'CM3D2_Debug/Debug_CM3D2_Normal2Color':
            mate['shader1'] = 'CM3D2_Debug/Debug_CM3D2_Normal2Color'
            mate['shader2'] = 'CM3D2_Debug__Debug_CM3D2_Normal2Color'
            col_list.append(_Color)
            col_list.append(_RimColor)
            col_list.append(_OutlineColor)
            col_list.append(("_SpecColor", (1, 1, 1, 1)))
            f_list.append(_Shininess)
            f_list.append(_OutlineWidth)
            f_list.append(_RimPower)
            f_list.append(_RimShift)
        
        texpath_dict = common.get_texpath_dict()
        slot_index = 0
        
        for data in tex_list:
            key = data[0]
            tex_name = data[1]
            cm3d2path = data[2]
            # prefsから初期値を取得
            tex_map = prefs.new_mate_tex_offset[:2] + prefs.new_mate_tex_scale[:2]
            tex = common.create_tex(context, mate, key, tex_name, cm3d2path, cm3d2path, tex_map, False, slot_index)

            # tex探し
            if prefs.is_replace_cm3d2_tex:
                replaced = common.replace_cm3d2_tex(tex.image, texpath_dict=texpath_dict, reload_path=False)
                if compat.IS_LEGACY and replaced and key == '_MainTex':
                    for face in me.polygons:
                        if face.material_index == ob.active_material_index:
                            me.uv_textures.active.data[face.index].image = tex.image
            if compat.IS_LEGACY:
                slot_index += 1

        for data in col_list:
            node = common.create_col(context, mate, data[0], data[1][:4], slot_index)
            if compat.IS_LEGACY:
                slot_index += 1

        for data in f_list:
            node = common.create_float(context, mate, data[0], data[1], slot_index)
            if compat.IS_LEGACY:
                slot_index += 1

        if compat.IS_LEGACY:
            common.decorate_material(mate, self.is_decorate, me, ob.active_material_index)
        else:
            cm3d2_data.align_nodes(mate)
            common.decorate_material(mate, self.is_decorate, me, ob.active_material_index)

        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_new_cm3d2(bpy.types.Operator, new_mate_opr):
    bl_idname = 'material.new_cm3d2'
    bl_label = "CM3D2用マテリアルを新規作成"
    bl_description = "Blender-CM3D2-Converterで使用できるマテリアルを新規で作成します"
    bl_options = {'REGISTER', 'UNDO'}

    shader_type = bpy.props.EnumProperty(items=cm3d2_data.Handler.create_shader_items(), name="種類", default='CM3D2/Toony_Lighted_Outline')


@compat.BlRegister()
class CNV_OT_new_com3d2(bpy.types.Operator, new_mate_opr):
    bl_idname = 'material.new_com3d2'
    bl_label = "COM3D2用マテリアルを新規作成"
    bl_description = "Blender-CM3D2-Converterで使用できるマテリアルを新規で作成します"
    bl_options = {'REGISTER', 'UNDO'}

    shader_type = bpy.props.EnumProperty(items=cm3d2_data.Handler.create_comshader_items(), name="種類", default='CM3D2/Toony_Lighted_Outline')


@compat.BlRegister()
class CNV_OT_paste_material(bpy.types.Operator):
    bl_idname = 'material.paste_material'
    bl_label = "クリップボードからマテリアルを貼付け"
    bl_description = "クリップボード内のテキストからマテリアル情報を上書きします"
    bl_options = {'REGISTER', 'UNDO'}

    is_decorate = bpy.props.BoolProperty(name="種類に合わせてマテリアルを装飾", default=False)
    is_replace_cm3d2_tex = bpy.props.BoolProperty(name="テクスチャを探す", default=False, description="CM3D2本体のインストールフォルダからtexファイルを探して開きます")
    is_create = bpy.props.BoolProperty(name="マテリアルの新規作成", default=False)
    override_name = bpy.props.BoolProperty(name="マテリアル名を上書きする", default=False)
    use_dialog = bpy.props.BoolProperty(name="上書き設定", default=True)

    @classmethod
    def poll(cls, context):
        data = context.window_manager.clipboard
        if len(data) < 32:
            return False

        # if not data.startswith('1000'):
        # 	return False
        if '\ntex\n\t' in data or '\ncol\n\t' in data or '\nf\n\t' in data:
            return True

        # if not data.startswith('1000'):
        # 	return False
        # if '\n\t_MainTex\n' in data or '\n\t_Color\n' in data:
        # 	return True
        return False

    def invoke(self, context, event):
        if self.use_dialog:
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context):
        self.layout.prop(self, 'override_name')
        if compat.IS_LEGACY:
            self.layout.prop(self, 'is_decorate')
        prefs = common.preferences()
        self.layout.prop(prefs, 'is_replace_cm3d2_tex', icon='BORDERMOVE')

    def execute(self, context):
        text = context.window_manager.clipboard

        try:
            mat_data = cm3d2_data.MaterialHandler.parse_text(text)
        except Exception as e:
            # tb = sys.exc_info()[2]
            # e.with_traceback(tb)
            self.report(type={'ERROR'}, message='マテリアル情報の貼付けを中止します。' + str(e))
            return {'CANCELLED'}

        mate_name = mat_data.name
        if self.is_create:
            if not context.material_slot:
                bpy.ops.object.material_slot_add()
            mate = context.blend_data.materials.new(mate_name)
            context.material_slot.material = mate
            common.setup_material(mate)
        else:
            mate = context.material
            if self.override_name:
                # シリアル番号が異なる場合は変更しない
                if common.remove_serial_number(mate_name) != common.remove_serial_number(mate.name):
                    mate.name = mate_name

        prefs = common.preferences()
        if compat.IS_LEGACY:
            cm3d2_data.MaterialHandler.apply_to_old(context, mate, mat_data, prefs.is_replace_cm3d2_tex, self.is_decorate)
        else:
            cm3d2_data.MaterialHandler.apply_to(context, mate, mat_data, prefs.is_replace_cm3d2_tex)

        self.report(type={'INFO'}, message="クリップボードからマテリアルを貼付けました")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_copy_material(bpy.types.Operator):
    bl_idname = 'material.copy_material'
    bl_label = "マテリアルをクリップボードにコピー"
    bl_description = "表示しているマテリアルをテキスト形式でクリップボードにコピーします"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mate = getattr(context, 'material')
        if mate:
            return 'shader1' in mate and 'shader2' in mate
        return False

    def execute(self, context):
        mate = context.material
        try:
            if compat.IS_LEGACY:
                mat_data = cm3d2_data.MaterialHandler.parse_mate_old(mate)
            else:
                mat_data = cm3d2_data.MaterialHandler.parse_mate(mate)
        except Exception as e:
            self.report(type={'ERROR'}, message="クリップボードへのコピーを中止します。:" + str(e))
            return {'CANCELLED'}

        context.window_manager.clipboard = mat_data.to_text()
        self.report(type={'INFO'}, message="マテリアルテキストをクリップボードにコピーしました")
        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_decorate_material(bpy.types.Operator):
    bl_idname = 'material.decorate_material'
    bl_label = "マテリアルを装飾"
    bl_description = "スロット内のマテリアルを全て設定に合わせて装飾します"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if not ob or ob.type != 'MESH':
            return False
        for slot in ob.material_slots:
            mate = slot.material
            if mate and 'shader1' in mate and 'shader2' in mate:
                return True
        return False

    def execute(self, context):
        ob = context.active_object
        me = ob.data

        for slot_index, slot in enumerate(ob.material_slots):
            mate = slot.material
            if mate and 'shader1' in mate and 'shader2' in mate:
                common.decorate_material(mate, True, me, slot_index)

        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_quick_texture_show(bpy.types.Operator):
    bl_idname = 'material.quick_texture_show'
    bl_label = "このテクスチャを見る"
    bl_description = "このテクスチャを見る"
    bl_options = {'REGISTER'}

    texture_name = bpy.props.StringProperty(name="テクスチャ名")

    @classmethod
    def poll(cls, context):
        mate = context.material
        if mate:
            if 'shader1' in mate and 'shader2' in mate:
                return True
        return False

    def execute(self, context):
        mate = context.material
        if hasattr(mate, 'texture_slots'):
            for index, slot in enumerate(mate.texture_slots):
                if not slot or not slot.texture:
                    continue
                if slot.texture.name == self.texture_name:
                    mate.active_texture_index = index
                    context.space_data.context = 'TEXTURE'
                    break
        else:
            # TODO テクスチャの表示検討
            pass

        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_setup_material_expand(bpy.types.Operator):
    bl_idname = 'material.setup_mate_expand'
    bl_label = "マテリアルのセットアップ"
    bl_description = "マテリアルの各種フラグを初期化する"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mate = context.material
        if mate:
            if 'shader1' in mate and 'shader2' in mate:
                return True
        return False

    def execute(self, context):
        mate = context.material
        common.setup_material(mate)

        return {'FINISHED'}


@compat.BlRegister()
class CNV_OT_material_prop_expand(bpy.types.Operator, common.NodeHandler):
    bl_idname = 'material.mateprop_expand'
    bl_label = "マテリアルプロパティの詳細情報"
    bl_description = "マテリアルプロパティの詳細情報の表示状態を切り替える"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        mate = context.material
        return mate and 'shader1' in mate and 'shader2' in mate

    def execute(self, context):
        node = self.get_node(context)
        if node is None:
            return {'CANCELLED'}
        prev = node.get('CM3D2 Prop Expand', False)
        node['CM3D2 Prop Expand'] = not prev

        return {'FINISHED'}


LAYOUT_FACTOR = 0.3


def menu_mateprop_tex(context, layout, node):
    base_name = common.remove_serial_number(node.name)
    prop_info = cm3d2_data.PROPS.get(base_name)

    row = layout.row(align=True)
    row.label(text="", icon='BLANK1')
    box = row.box()

    split = compat.layout_split(box, factor=LAYOUT_FACTOR)
    split.label(text="プロパティ タイプ:")
    row = split.row()
    row.label(text="テクスチャ", icon='TEXTURE')

    # check_row = row.row(align=True)
    # sub_row = check_row.row()
    # split = compat.layout_split(box, factor=LAYOUT_FACTOR)
    # split.label(text="設定値名:")
    # split.prop(node, 'name', icon='SORTALPHA', text="")

    img = node.image
    if img and img.source == 'FILE':
        row.operator('texture.reload_textures', text="", icon='FILE_REFRESH').tex_name = img.name

        sub_box = box.box()

        if '.png' in img.name[-8:].lower():
            sub_box.operator('texture.setup_image_name', text="拡張子を省略", icon='FILE')

        # row = compat.layout_split(sub_box, factor=LAYOUT_FACTOR, align=True)
        # row.label(text="テクスチャ名:")
        # row.template_ID(node, 'image', open='image.open')

        if 'cm3d2_path' in img:
            row = compat.layout_split(sub_box, factor=LAYOUT_FACTOR, align=True)
            row.label(text="テクスチャパス:")
            row.prop(img, '["cm3d2_path"]', text="")
        else:
            sub_box.operator('texture.set_cm3d2path', text="テクスチャパスを生成", icon='FILE').node_name = node.name

        row = compat.layout_split(sub_box, factor=LAYOUT_FACTOR, align=True)
        row.label(text="実ファイルパス:")
        # TODO ファイル選択用オペレータを自作(.pngフィルタ)
        row.prop(img, 'filepath', text="")

        # TODO node_nameの渡し方調査。
        if base_name in ['_ToonRamp', '_ShadowRateToon', '_OutlineToonRamp']:
            sub_box.menu('TEXTURE_MT_texture' + base_name, icon='NLA')

        tex_map = node.texture_mapping
        split = compat.layout_split(sub_box, factor=LAYOUT_FACTOR, align=True)
        split.label(text="オフセット:")
        row = split.row(align=True)
        row.prop(tex_map, 'translation', index=0, text="x")
        row.prop(tex_map, 'translation', index=1, text="y")
        row.operator('texture.reset_offset', text="", icon='CANCEL').node_name = node.name

        split = compat.layout_split(sub_box, factor=LAYOUT_FACTOR, align=True)
        split.label(text="スケール:")
        row = split.row(align=True)
        row.prop(tex_map, 'scale', index=0, text="x")
        row.prop(tex_map, 'scale', index=1, text="y")
        row.operator('texture.reset_scale', text="", icon='CANCEL').node_name = node.name

        row = sub_box.row()
        col = row.column()
        if os.path.exists(img.filepath) is False:
            col.enabled = False
        col.operator('image.show_image', text="画像を表示", icon='ZOOM_IN').image_name = img.name

        # else:
        # 	row.label(text="画像を表示", icon='ZOOM_IN')

        if len(img.pixels):
            row.operator('image.quick_export_cm3d2_tex', text="texで保存", icon=compat.icon('FILE_FOLDER')).node_name = node.name
        else:
            row.operator('image.replace_cm3d2_tex', icon='BORDERMOVE').node_name = node.name

    # TODO expand
    desc = prop_info.get('desc')
    if desc:
        sub_box = box.box()
        col = sub_box.column(align=True)
        col.label(text="解説", icon='TEXT')
        for line in desc:
            col.label(text=line)


def menu_mateprop_col(context, layout, node):
    base_name = common.remove_serial_number(node.name)
    prop_info = cm3d2_data.PROPS.get(base_name)

    row = layout.row(align=True)
    row.label(text="", icon='BLANK1')
    box = row.box()

    split = compat.layout_split(box, factor=LAYOUT_FACTOR)
    split.label(text="プロパティ タイプ:")
    row = split.row()
    row.label(text="色", icon='COLOR')

    # check_row = row.row(align=True)
    # sub_row = check_row.row()
    # split = compat.layout_split(box, factor=LAYOUT_FACTOR)
    # split.label(text="設定値名:")
    # split.prop(node, 'name', icon='SORTALPHA', text="")

    # sub_box = box.box()
    row = box.row(align=True)
    col = node.outputs[0]
    col_val = col.default_value
    if node.name in ['_ShadowColor', '_RimColor', '_OutlineColor']:
        row.operator('texture.auto_set_color_value', icon='AUTO', text="自動設定").node_name = node.name
    opr = row.operator('texture.set_color_value', text="", icon=compat.icon('MESH_CIRCLE'))
    opr.node_name, opr.color = node.name, [0, 0, 0, col_val[3]]
    opr = row.operator('texture.set_color_value', text="", icon=compat.icon('SHADING_SOLID'))
    opr.node_name, opr.color = node.name, [1, 1, 1, col_val[3]]

    # 透過は_Colorのみ (TODO さらにTransシェーダの場合に限定)
    if node.name in ['_Color']:
        row = box.row(align=True)
        opr = row.operator('texture.set_color_value', text="", icon='TRIA_LEFT')
        opr.node_name, opr.color = node.name, col_val[:3] + (0,)

        row.prop(col, 'default_value', index=3, icon='IMAGE_RGB_ALPHA', text="色の透明度", slider=True)

        opr = row.operator('texture.set_color_value', text="", icon='TRIA_RIGHT')
        opr.node_name, opr.color = node.name, col_val[:3] + (1,)

    # TODO expand
    desc = prop_info.get('desc')
    if desc:
        sub_box = box.box()
        col = sub_box.column(align=True)
        col.label(text="解説", icon='TEXT')
        for line in desc:
            col.label(text=line)


def menu_mateprop_f(context, layout, node):
    base_name = common.remove_serial_number(node.name)
    prop_info = cm3d2_data.PROPS.get(base_name)

    # row = compat.layout_split(layout, factor=0.05)
    row = layout.row(align=True)
    row.label(text="", icon='BLANK1')
    box = row.box()

    split = compat.layout_split(box, factor=LAYOUT_FACTOR)
    split.label(text="プロパティ タイプ:")
    row = split.row()
    row.label(text="値", icon='ARROW_LEFTRIGHT')

    # check_row = row.row(align=True)
    # sub_row = check_row.row()
    # split = compat.layout_split(box, factor=LAYOUT_FACTOR)
    # split.label(text="設定値名:")
    # split.prop(node, 'name', icon='SORTALPHA', text="")

    # sub_box = layout.box()
    # row = sub_box.row(align=True)
    # disable_slider = prop_info.get('disableSlider')
    # output = node.outputs[0]
    # if disable_slider:
    # 	row.label(output, 'default_value', icon='ARROW_LEFTRIGHT', text="値")
    # else:
    # 	row.prop(output, 'default_value', icon='ARROW_LEFTRIGHT', text="値")

    # コンボメニュー
    # row.menu('TEXTURE_MT_context_texture_values_normal', icon='DOWNARROW_HLT', text="")

    presets = prop_info.get('presets')
    if presets:
        # TODO 複数行
        row = box.row(align=True)
        for preset in presets:
            text = str(preset)
            opr = row.operator('texture.set_value', text=text)
            opr.value, opr.node_name = preset, node.name

    preset_enums = prop_info.get('preset_enums')
    if preset_enums:
        for idx, preset in enumerate(preset_enums):
            if idx % 5 == 0:
                row = box.row(align=True)
            val = preset[0]
            opr = row.operator('texture.set_value', text=preset[1])
            opr.value, opr.node_name = val, node.name

    if prop_info.get('dispExact'):
        split = compat.layout_split(box, factor=LAYOUT_FACTOR)
        split.label(text="正確な値: ")
        split.label(text="{0:f}".format(node.outputs[0].default_value))

    # TODO expand
    desc = prop_info.get('desc')
    if desc:
        sub_box = box.box()
        col = sub_box.column(align=True)
        col.label(text="解説", icon='TEXT')
        for line in desc:
            col.label(text=line)
