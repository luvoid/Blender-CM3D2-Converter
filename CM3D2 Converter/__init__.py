# アドオンを読み込む時に最初にこのファイルが読み込まれます

# アドオン情報
bl_info = {
    "name": "CM3D2 Converter",
    "author": "@saidenka_cm3d2, @trzrz, @luvoid",
    "version": ("luv", 2021, 2, "28e"),
    "blender": (2, 80, 0),
    "location": "ファイル > インポート/エクスポート > CM3D2 Model (.model)",
    "description": "カスタムメイド3D2/カスタムオーダーメイド3D2専用ファイルのインポート/エクスポートを行います",
    "warning": "",
    "wiki_url": "https://github.com/luvoid/Blender-CM3D2-Converter/blob/bl_28/README.md",
    "tracker_url": "https://github.com/luvoid/Blender-CM3D2-Converter",
    "category": "Import-Export"
}

# サブスクリプト群をインポート
if "bpy" in locals():
    import imp

    imp.reload(compat)
    imp.reload(common)
    imp.reload(cm3d2_data)

    imp.reload(model_import)
    imp.reload(model_export)

    imp.reload(anm_import)
    imp.reload(anm_export)

    imp.reload(tex_import)
    imp.reload(tex_export)

    imp.reload(mate_import)
    imp.reload(mate_export)

    imp.reload(menu_file)
    imp.reload(menu_OBJECT_PT_cm3d2_menu)

    imp.reload(misc_DATA_PT_context_arm)
    imp.reload(misc_DATA_PT_modifiers)
    imp.reload(misc_DATA_PT_vertex_groups)
    imp.reload(misc_IMAGE_HT_header)
    imp.reload(misc_IMAGE_PT_image_properties)
    imp.reload(misc_INFO_HT_header)
    imp.reload(misc_INFO_MT_add)
    imp.reload(misc_INFO_MT_curve_add)
    imp.reload(misc_INFO_MT_help)
    imp.reload(misc_MATERIAL_PT_context_material)
    imp.reload(misc_MESH_MT_shape_key_specials)
    imp.reload(misc_MESH_MT_vertex_group_specials)
    imp.reload(misc_OBJECT_PT_context_object)
    imp.reload(misc_OBJECT_PT_transform)
    imp.reload(misc_RENDER_PT_bake)
    imp.reload(misc_RENDER_PT_render)
    imp.reload(misc_TEXTURE_PT_context_texture)
    imp.reload(misc_TEXT_HT_header)
    imp.reload(misc_VIEW3D_MT_edit_mesh_specials)
    imp.reload(misc_VIEW3D_MT_pose_apply)
    imp.reload(misc_VIEW3D_PT_tools_weightpaint)
    imp.reload(misc_VIEW3D_PT_tools_mesh_shapekey)
    imp.reload(misc_DOPESHEET_MT_editor_menus)

    imp.reload(app_translations)

else:
    from . import compat
    from . import common
    from . import cm3d2_data

    from . import model_import
    from . import model_export

    from . import anm_import
    from . import anm_export

    from . import tex_import
    from . import tex_export

    from . import mate_import
    from . import mate_export

    from . import menu_file
    from . import menu_OBJECT_PT_cm3d2_menu

    from . import misc_DATA_PT_context_arm
    from . import misc_DATA_PT_modifiers
    from . import misc_DATA_PT_vertex_groups
    from . import misc_IMAGE_HT_header
    from . import misc_IMAGE_PT_image_properties
    from . import misc_INFO_HT_header
    from . import misc_INFO_MT_add
    from . import misc_INFO_MT_curve_add
    from . import misc_INFO_MT_help
    from . import misc_MATERIAL_PT_context_material
    from . import misc_MESH_MT_shape_key_specials
    from . import misc_MESH_MT_vertex_group_specials
    from . import misc_OBJECT_PT_context_object
    from . import misc_OBJECT_PT_transform
    from . import misc_RENDER_PT_bake
    from . import misc_RENDER_PT_render
    from . import misc_TEXTURE_PT_context_texture
    from . import misc_TEXT_HT_header
    from . import misc_VIEW3D_MT_edit_mesh_specials
    from . import misc_VIEW3D_MT_pose_apply
    from . import misc_VIEW3D_PT_tools_weightpaint
    from . import misc_VIEW3D_PT_tools_mesh_shapekey
    from . import misc_DOPESHEET_MT_editor_menus

    from . import app_translations

import bpy, os.path, bpy.utils.previews


# Backwards compatability
if compat.IS_LEGACY:
    bl_info["blender"] = (2, 78, 0)



# アドオン設定
@compat.BlRegister()
class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    cm3d2_path = bpy.props.StringProperty(name="CM3D2インストールフォルダ", subtype='DIR_PATH', description="変更している場合は設定しておくと役立つかもしれません")
    backup_ext = bpy.props.StringProperty(name="バックアップの拡張子 (空欄で無効)", description="エクスポート時にバックアップを作成時この拡張子で複製します、空欄でバックアップを無効", default='bak')

    scale = bpy.props.FloatProperty(name="倍率", description="Blenderでモデルを扱うときの拡大率", default=5, min=0.01, max=100, soft_min=0.01, soft_max=100, step=10, precision=2)
    is_convert_bone_weight_names = bpy.props.BoolProperty(name="基本的にボーン名/ウェイト名をBlender用に変換", default=False, description="modelインポート時にボーン名/ウェイト名を変換するかどうかのオプションのデフォルトを設定します")
    model_default_path = bpy.props.StringProperty(name="modelファイル置き場", subtype='DIR_PATH', description="設定すれば、modelを扱う時は必ずここからファイル選択を始めます")
    model_import_path = bpy.props.StringProperty(name="modelインポート時のデフォルトパス", subtype='FILE_PATH', description="modelインポート時に最初はここが表示されます、インポート毎に保存されます")
    model_export_path = bpy.props.StringProperty(name="modelエクスポート時のデフォルトパス", subtype='FILE_PATH', description="modelエクスポート時に最初はここが表示されます、エクスポート毎に保存されます")

    anm_default_path = bpy.props.StringProperty(name="anmファイル置き場", subtype='DIR_PATH', description="設定すれば、anmを扱う時は必ずここからファイル選択を始めます")
    anm_import_path = bpy.props.StringProperty(name="anmインポート時のデフォルトパス", subtype='FILE_PATH', description="anmインポート時に最初はここが表示されます、インポート毎に保存されます")
    anm_export_path = bpy.props.StringProperty(name="anmエクスポート時のデフォルトパス", subtype='FILE_PATH', description="anmエクスポート時に最初はここが表示されます、エクスポート毎に保存されます")

    tex_default_path = bpy.props.StringProperty(name="texファイル置き場", subtype='DIR_PATH', description="設定すれば、texを扱う時は必ずここからファイル選択を始めます")
    tex_import_path = bpy.props.StringProperty(name="texインポート時のデフォルトパス", subtype='FILE_PATH', description="texインポート時に最初はここが表示されます、インポート毎に保存されます")
    tex_export_path = bpy.props.StringProperty(name="texエクスポート時のデフォルトパス", subtype='FILE_PATH', description="texエクスポート時に最初はここが表示されます、エクスポート毎に保存されます")

    mate_default_path = bpy.props.StringProperty(name="mateファイル置き場", subtype='DIR_PATH', description="設定すれば、mateを扱う時は必ずここからファイル選択を始めます")
    mate_unread_same_value = bpy.props.BoolProperty(name="同じ設定値が2つ以上ある場合削除", default=True, description="_ShadowColor など")
    mate_import_path = bpy.props.StringProperty(name="mateインポート時のデフォルトパス", subtype='FILE_PATH', description="mateインポート時に最初はここが表示されます、インポート毎に保存されます")
    mate_export_path = bpy.props.StringProperty(name="mateエクスポート時のデフォルトパス", subtype='FILE_PATH', description="mateエクスポート時に最初はここが表示されます、エクスポート毎に保存されます")
    
    menu_default_path = bpy.props.StringProperty(name=".menu Default Path"       , subtype='DIR_PATH' , description="If set. The file selection will open here.")
    menu_import_path  = bpy.props.StringProperty(name=".menu Default Import Path", subtype='FILE_PATH', description="When importing a .menu file. The file selection prompt will begin here.")
    menu_export_path  = bpy.props.StringProperty(name=".menu Default Export Path", subtype='FILE_PATH', description="When exporting a .menu file. The file selection prompt will begin here.")
    
    is_replace_cm3d2_tex = bpy.props.BoolProperty(name="基本的にtexファイルを探す", default=True, description="texファイルを探すかどうかのオプションのデフォルト値を設定します")
    default_tex_path0 = bpy.props.StringProperty(name="texファイル置き場", subtype='DIR_PATH', description="texファイルを探す時はここから探します")
    default_tex_path1 = bpy.props.StringProperty(name="texファイル置き場", subtype='DIR_PATH', description="texファイルを探す時はここから探します")
    default_tex_path2 = bpy.props.StringProperty(name="texファイル置き場", subtype='DIR_PATH', description="texファイルを探す時はここから探します")
    default_tex_path3 = bpy.props.StringProperty(name="texファイル置き場", subtype='DIR_PATH', description="texファイルを探す時はここから探します")

    custom_normal_blend = bpy.props.FloatProperty(name="CM3D2用法線のブレンド率", default=0.5, min=0, max=1, soft_min=0, soft_max=1, step=3, precision=3)
    skip_shapekey = bpy.props.BoolProperty(name="無変更シェイプキーをスキップ", default=True, description="ベースと同じシェイプキーを出力しない")
    is_apply_modifiers = bpy.props.BoolProperty(name="モディファイアを適用", default=False)

    new_mate_tex_offset = bpy.props.FloatVectorProperty(name="テクスチャのオフセット", default=(0, 0), min=-1, max=1, soft_min=-1, soft_max=1, step=10, precision=3, size=2)
    new_mate_tex_scale = bpy.props.FloatVectorProperty(name="テクスチャのスケール", default=(1, 1), min=0, max=1, soft_min=0, soft_max=1, step=10, precision=3, size=2)

    new_mate_toonramp_name = bpy.props.StringProperty(name="_ToonRamp 名前", default="toonGrayA1")
    new_mate_toonramp_path = bpy.props.StringProperty(name="_ToonRamp パス", default=common.BASE_PATH_TEX + "toon/toonGrayA1.png")

    new_mate_shadowratetoon_name = bpy.props.StringProperty(name="_ShadowRateToon 名前", default="toonDress_shadow")
    new_mate_shadowratetoon_path = bpy.props.StringProperty(name="_ShadowRateToon パス", default=common.BASE_PATH_TEX + "toon/toonDress_shadow.png")

    new_mate_linetoonramp_name = bpy.props.StringProperty(name="_OutlineToonRamp 名前", default="toonGrayA1")
    new_mate_linetoonramp_path = bpy.props.StringProperty(name="_OutlineToonRamp パス", default=common.BASE_PATH_TEX + "toon/toonGrayA1.png")

    new_mate_color = bpy.props.FloatVectorProperty(name="_Color", default=(1, 1, 1, 1), min=0, max=1, soft_min=0, soft_max=1, step=10, precision=2, subtype='COLOR', size=4)
    new_mate_shadowcolor = bpy.props.FloatVectorProperty(name="_ShadowColor", default=(0, 0, 0, 1), min=0, max=1, soft_min=0, soft_max=1, step=10, precision=2, subtype='COLOR', size=4)
    new_mate_rimcolor = bpy.props.FloatVectorProperty(name="_RimColor", default=(0.5, 0.5, 0.5, 1), min=0, max=1, soft_min=0, soft_max=1, step=10, precision=2, subtype='COLOR', size=4)
    new_mate_outlinecolor = bpy.props.FloatVectorProperty(name="_OutlineColor", default=(0, 0, 0, 1), min=0, max=1, soft_min=0, soft_max=1, step=10, precision=2, subtype='COLOR', size=4)

    new_mate_shininess  = bpy.props.FloatProperty(name="_Shininess", default=0, min=-100, max=100, soft_min=-100, soft_max=100, step=1, precision=2)
    new_mate_outlinewidth = bpy.props.FloatProperty(name="_OutlineWidth", default=0.0015, min=-100, max=100, soft_min=-100, soft_max=100, step=1, precision=2)
    new_mate_rimpower = bpy.props.FloatProperty(name="_RimPower", default=25, min=-100, max=100, soft_min=-100, soft_max=100, step=1, precision=2)
    new_mate_rimshift = bpy.props.FloatProperty(name="_RimShift", default=0, min=-100, max=100, soft_min=-100, soft_max=100, step=1, precision=2)
    new_mate_hirate = bpy.props.FloatProperty(name="_HiRate", default=0.5, min=-100, max=100, soft_min=-100, soft_max=100, step=1, precision=2)
    new_mate_hipow = bpy.props.FloatProperty(name="_HiPow", default=0.001, min=-100, max=100, soft_min=-100, soft_max=100, step=1, precision=2)
    new_mate_cutoff = bpy.props.FloatProperty(name="_Cutoff", default=0.5, min=0, max=1, soft_min=0, soft_max=1, step=10, precision=2)
    new_mate_cutout = bpy.props.FloatProperty(name="_Cutout", default=0.482143, min=0, max=1, soft_min=0, soft_max=1, step=10, precision=6)
    new_mate_ztest = bpy.props.FloatProperty(name="_ZTest", default=4, min=0, max=8, soft_min=0, soft_max=8, step=1)
    new_mate_ztest2 = bpy.props.FloatProperty(name="_ZTest2", default=1, min=0, max=1, soft_min=0, soft_max=1, step=1)
    new_mate_ztest2alpha = bpy.props.FloatProperty(name="_ZTest2Alpha", default=0.8, min=0, max=1, soft_min=0, soft_max=1, step=1, precision=2)

    bone_display_type = bpy.props.EnumProperty(
        items=[
            ('OCTAHEDRAL', "Octahedral", "Display bones as octahedral shape (default)."                            ),
            ('STICK'     , "Stick"     , "Display bones as simple 2D lines with dots."                             ),
            ('BBONE'     , "B-Bone"    , "Display bones as boxes, showing subdivision and B-Splines."              ),
            ('ENVELOPE'  , "Envelope"  , "Display bones as extruded spheres, showing deformation influence volume."),
            ('WIRE'      , "Wire"      , "Display bones as thin wires, showing subdivision and B-Splines."         ),
        ],
        name="Display Type",
        default='STICK',
    )
    show_bone_names         = bpy.props.BoolProperty(name="Show Bone Names"       , default=False, description="Display bone names"                     )
    show_bone_axes          = bpy.props.BoolProperty(name="Show Bone Axes"        , default=False, description="Display bone axes"                      )
    show_bone_custom_shapes = bpy.props.BoolProperty(name="Show Bone Shapes"      , default=True , description="Display bones with their custom shapes" )
    show_bone_group_colors  = bpy.props.BoolProperty(name="Show Bone Group Colors", default=True , description="Display bone group colors"              )
    show_bone_in_front      = bpy.props.BoolProperty(name="Show Bones in Front"   , default=True , description="Make the object draw in front of others")

    def draw(self, context):
        if compat.IS_LEGACY:
            self.layout.label(text="ここの設定は「ユーザー設定の保存」ボタンを押すまで保存されていません", icon='QUESTION')
        else:
            self.layout.label(text="設定値を変更した場合、「プリファレンスを保存」ボタンを押下するか、「プリファレンスを自動保存」を有効にして保存してください", icon='QUESTION')
        self.layout.prop(self, 'cm3d2_path', icon_value=common.kiss_icon())
        self.layout.prop(self, 'backup_ext', icon='FILE_BACKUP')

        box = self.layout.box()
        box.label(text=".modelファイル", icon='MESH_ICOSPHERE')
        row = box.row()
        row.prop(self, 'scale', icon=compat.icon('ARROW_LEFTRIGHT'))
        row.prop(self, 'is_convert_bone_weight_names', icon='BLENDER')
        brws_icon = compat.icon('FILEBROWSER')
        box.prop(self, 'model_default_path', icon=brws_icon, text="ファイル選択時の初期フォルダ")

        box = self.layout.box()
        box.label(text="anmファイル", icon='POSE_HLT')
        box.prop(self, 'anm_default_path', icon=brws_icon, text="ファイル選択時の初期フォルダ")

        box = self.layout.box()
        box.label(text=".texファイル", icon='FILE_IMAGE')
        box.prop(self, 'tex_default_path', icon=brws_icon, text="ファイル選択時の初期フォルダ")

        box = self.layout.box()
        box.label(text=".mateファイル", icon='MATERIAL')
        box.prop(self, 'mate_unread_same_value', icon='DISCLOSURE_TRI_DOWN')
        box.prop(self, 'mate_default_path', icon=brws_icon, text="ファイル選択時の初期フォルダ")

        box = self.layout.box()
        box.label(text=".menu File", icon='COPY_ID')
        box.prop(self, 'menu_default_path', icon=brws_icon, text="Initial folder when selecting files")

        box = self.layout.box()
        box.label(text="texファイル検索", icon='BORDERMOVE')
        box.prop(self, 'is_replace_cm3d2_tex', icon='VIEWZOOM')
        box.prop(self, 'default_tex_path0', icon='LAYER_ACTIVE', text="その1")
        box.prop(self, 'default_tex_path1', icon='LAYER_ACTIVE', text="その2")
        box.prop(self, 'default_tex_path2', icon='LAYER_ACTIVE', text="その3")
        box.prop(self, 'default_tex_path3', icon='LAYER_ACTIVE', text="その4")

        box = self.layout.box()
        box.label(text="CM3D2用マテリアル新規作成時の初期値", icon='MATERIAL')
        row = box.row()
        row.prop(self, 'new_mate_tex_offset', icon='MOD_MULTIRES')
        row.prop(self, 'new_mate_tex_scale', icon='ARROW_LEFTRIGHT')
        row = box.row()
        row.prop(self, 'new_mate_toonramp_name', icon='BRUSH_TEXFILL')
        row.prop(self, 'new_mate_toonramp_path', icon='ANIM')
        row = box.row()
        row.prop(self, 'new_mate_shadowratetoon_name', icon='BRUSH_TEXMASK')
        row.prop(self, 'new_mate_shadowratetoon_path', icon='ANIM')
        row = box.row()
        row.prop(self, 'new_mate_color', icon='COLOR')
        row.prop(self, 'new_mate_shadowcolor', icon='IMAGE_ALPHA')
        row.prop(self, 'new_mate_rimcolor', icon=compat.icon('SHADING_RENDERED'))
        row.prop(self, 'new_mate_outlinecolor', icon=compat.icon('SHADING_SOLID'))
        row = box.row()
        row.prop(self, 'new_mate_shininess', icon=compat.icon('NODE_MATERIAL'))
        row.prop(self, 'new_mate_outlinewidth', icon=compat.icon('SHADING_SOLID'))
        row.prop(self, 'new_mate_rimpower', icon=compat.icon('SHADING_RENDERED'))
        row.prop(self, 'new_mate_rimshift', icon='ARROW_LEFTRIGHT')
        row.prop(self, 'new_mate_hirate')
        row.prop(self, 'new_mate_hipow')

        box = self.layout.box()
        box.label(text="Default Armature Settings", icon='ARMATURE_DATA')
        if not compat.IS_LEGACY:
            box.use_property_split = True
        box.prop(self, "bone_display_type", text="Display As")
        if compat.IS_LEGACY:
            flow = box.column_flow(align=True)
        else:
            flow = box.grid_flow(align=True)
        col = flow.column(); col.prop(self, "show_bone_names",         text="Names"       )
        col = flow.column(); col.prop(self, "show_bone_axes",          text="Axes"        )
        col = flow.column(); col.prop(self, "show_bone_custom_shapes", text="Shapes"      )
        col = flow.column(); col.prop(self, "show_bone_group_colors",  text="Group Colors")
        col = flow.column(); col.prop(self, "show_bone_in_front",      text="In Front"    )

        box = self.layout.box()
        box.label(text="各操作の初期パラメータ", icon='MATERIAL')
        row = box.row()  # export
        row.prop(self, 'custom_normal_blend', icon='SNAP_NORMAL')
        row.prop(self, 'skip_shapekey', icon='SHAPEKEY_DATA')
        row.prop(self, 'is_apply_modifiers', icon='MODIFIER')
        # row = box.row()
        row = self.layout.row()
        row.operator('script.update_cm3d2_converter', icon='FILE_REFRESH')
        row.menu('INFO_MT_help_CM3D2_Converter_RSS', icon='INFO')


# プラグインをインストールしたときの処理
def register():
    pcoll = bpy.utils.previews.new()
    dir = os.path.dirname(__file__)
    pcoll.load('KISS', os.path.join(dir, "kiss.png"), 'IMAGE')
    common.preview_collections['main'] = pcoll
    common.bl_info = bl_info

    compat.BlRegister.register()
    if compat.IS_LEGACY:
        bpy.types.INFO_MT_file_import.append(model_import.menu_func)
        bpy.types.INFO_MT_file_import.append(anm_import.menu_func)
        bpy.types.INFO_MT_file_export.append(model_export.menu_func)
        bpy.types.INFO_MT_file_export.append(anm_export.menu_func)

        bpy.types.INFO_MT_add.append(misc_INFO_MT_add.menu_func)
        bpy.types.INFO_MT_curve_add.append(misc_INFO_MT_curve_add.menu_func)
        bpy.types.INFO_MT_help.append(misc_INFO_MT_help.menu_func)

        bpy.types.MATERIAL_PT_context_material.append(misc_MATERIAL_PT_context_material.menu_func)
        bpy.types.RENDER_PT_bake.append(misc_RENDER_PT_bake.menu_func)
        bpy.types.RENDER_PT_render.append(misc_RENDER_PT_render.menu_func)
        bpy.types.TEXTURE_PT_context_texture.append(misc_TEXTURE_PT_context_texture.menu_func)
        bpy.types.VIEW3D_PT_tools_weightpaint.append(misc_VIEW3D_PT_tools_weightpaint.menu_func)

        # menu
        bpy.types.MESH_MT_shape_key_specials.append(misc_MESH_MT_shape_key_specials.menu_func)
        bpy.types.MESH_MT_vertex_group_specials.append(misc_MESH_MT_vertex_group_specials.menu_func)
        bpy.types.VIEW3D_MT_edit_mesh_specials.append(misc_VIEW3D_MT_edit_mesh_specials.menu_func)
    else:
        bpy.types.TOPBAR_MT_file_import.append(model_import.menu_func)
        bpy.types.TOPBAR_MT_file_export.append(model_export.menu_func)
        # anm
        bpy.types.TOPBAR_MT_file_import.append(anm_import.menu_func)
        bpy.types.TOPBAR_MT_file_export.append(anm_export.menu_func)

        bpy.types.VIEW3D_MT_add.append(misc_INFO_MT_add.menu_func)
        bpy.types.VIEW3D_MT_curve_add.append(misc_INFO_MT_curve_add.menu_func)
        # (更新機能)
        bpy.types.TOPBAR_MT_help.append(misc_INFO_MT_help.menu_func)

        # マテリアルパネルの追加先がないため、別途Panelを追加
        # bpy.types.MATERIAL_PT_context_xxx.append(misc_MATERIAL_PT_context_material.menu_func)

        # TODO 修正＆動作確認後にコメント解除  (ベイク)
        # レンダーエンジンがCycles指定時のみになる
        # bpy.types.CYCLES_RENDER_PT_bake.append(misc_RENDER_PT_bake.menu_func)
        bpy.types.RENDER_PT_context.append(misc_RENDER_PT_render.menu_func)
        bpy.types.VIEW3D_PT_tools_weightpaint_options.append(misc_VIEW3D_PT_tools_weightpaint.menu_func)

        # context menu
        bpy.types.MESH_MT_shape_key_context_menu.append(misc_MESH_MT_shape_key_specials.menu_func)
        bpy.types.MESH_MT_vertex_group_context_menu.append(misc_MESH_MT_vertex_group_specials.menu_func)
        bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(misc_VIEW3D_MT_edit_mesh_specials.menu_func)

    bpy.types.IMAGE_MT_image.append(tex_import.menu_func)
    bpy.types.IMAGE_MT_image.append(tex_export.menu_func)

    bpy.types.TEXT_MT_text.append(mate_import.TEXT_MT_text)
    bpy.types.TEXT_MT_text.append(mate_export.TEXT_MT_text)

    bpy.types.DATA_PT_context_arm.append(misc_DATA_PT_context_arm.menu_func)
    bpy.types.DATA_PT_modifiers.append(misc_DATA_PT_modifiers.menu_func)
    bpy.types.DATA_PT_vertex_groups.append(misc_DATA_PT_vertex_groups.menu_func)
    bpy.types.IMAGE_HT_header.append(misc_IMAGE_HT_header.menu_func)
    bpy.types.IMAGE_PT_image_properties.append(misc_IMAGE_PT_image_properties.menu_func)
    bpy.types.INFO_HT_header.append(misc_INFO_HT_header.menu_func)

    bpy.types.OBJECT_PT_context_object.append(misc_OBJECT_PT_context_object.menu_func)
    bpy.types.OBJECT_PT_transform.append(misc_OBJECT_PT_transform.menu_func)
    bpy.types.TEXT_HT_header.append(misc_TEXT_HT_header.menu_func)
    bpy.types.VIEW3D_MT_pose_apply.append(misc_VIEW3D_MT_pose_apply.menu_func)

    setattr(bpy.types.Object, 'cm3d2_bone_morph' , bpy.props.PointerProperty(type=misc_DATA_PT_context_arm.CNV_PG_cm3d2_bone_morph ))
    setattr(bpy.types.Object, 'cm3d2_wide_slider', bpy.props.PointerProperty(type=misc_DATA_PT_context_arm.CNV_PG_cm3d2_wide_slider))
    setattr(bpy.types.Object, 'cm3d2_menu'       , bpy.props.PointerProperty(type=menu_file.OBJECT_PG_CM3D2Menu                    ))
    
    bpy.types.DOPESHEET_MT_editor_menus.append(misc_DOPESHEET_MT_editor_menus.menu_func)
    bpy.types.GRAPH_MT_editor_menus.append(misc_DOPESHEET_MT_editor_menus.menu_func)

    system = compat.get_system(bpy.context)
    if hasattr(system, 'use_international_fonts') and not system.use_international_fonts:
        system.use_international_fonts = True
    if not system.use_translate_interface:
        system.use_translate_interface = True
    
    bpy.app.translations.register(__name__, app_translations.translations_dict)
    
    # A region lock? In an international plugin? Nah, we can't have that.
    #try:
    #    import locale
    #    if system.language == 'DEFAULT' and locale.getdefaultlocale()[0] != 'ja_JP':
    #        system.language = 'en_US'
    #except:
    #    pass
    #
    #try:
    #    import locale
    #    if locale.getdefaultlocale()[0] != 'ja_JP':
    #        unregister()
    #except:
    #    pass


# プラグインをアンインストールしたときの処理
def unregister():
    if compat.IS_LEGACY:
        bpy.types.INFO_MT_file_import.remove(model_import.menu_func)
        bpy.types.INFO_MT_file_import.remove(anm_import.menu_func)
        bpy.types.INFO_MT_file_export.remove(model_export.menu_func)
        bpy.types.INFO_MT_file_export.remove(anm_export.menu_func)

        bpy.types.INFO_MT_add.remove(misc_INFO_MT_add.menu_func)
        bpy.types.INFO_MT_curve_add.remove(misc_INFO_MT_curve_add.menu_func)
        bpy.types.INFO_MT_help.remove(misc_INFO_MT_help.menu_func)

        bpy.types.MATERIAL_PT_context_material.remove(misc_MATERIAL_PT_context_material.menu_func)
        bpy.types.RENDER_PT_bake.remove(misc_RENDER_PT_bake.menu_func)
        bpy.types.RENDER_PT_render.remove(misc_RENDER_PT_render.menu_func)
        bpy.types.TEXTURE_PT_context_texture.remove(misc_TEXTURE_PT_context_texture.menu_func)
        bpy.types.VIEW3D_PT_tools_weightpaint.remove(misc_VIEW3D_PT_tools_weightpaint.menu_func)

        # menu
        bpy.types.MESH_MT_shape_key_specials.remove(misc_MESH_MT_shape_key_specials.menu_func)
        bpy.types.MESH_MT_vertex_group_specials.remove(misc_MESH_MT_vertex_group_specials.menu_func)
        bpy.types.VIEW3D_MT_edit_mesh_specials.remove(misc_VIEW3D_MT_edit_mesh_specials.menu_func)
    else:
        bpy.types.TOPBAR_MT_file_import.remove(model_import.menu_func)
        bpy.types.TOPBAR_MT_file_export.remove(model_export.menu_func)
        bpy.types.TOPBAR_MT_file_import.remove(anm_import.menu_func)
        bpy.types.TOPBAR_MT_file_export.remove(anm_export.menu_func)

        bpy.types.VIEW3D_MT_add.remove(misc_INFO_MT_add.menu_func)
        bpy.types.VIEW3D_MT_curve_add.remove(misc_INFO_MT_curve_add.menu_func)
        bpy.types.TOPBAR_MT_help.remove(misc_INFO_MT_help.menu_func)

        # bpy.types.MATERIAL_MT_context_menu.remove(misc_MATERIAL_PT_context_material.menu_func)
        # bpy.types.CYCLES_RENDER_PT_bake.remove(misc_RENDER_PT_bake.menu_func)
        bpy.types.RENDER_PT_context.remove(misc_RENDER_PT_render.menu_func)

        bpy.types.VIEW3D_PT_tools_weightpaint_options.remove(misc_VIEW3D_PT_tools_weightpaint.menu_func)
        # menu
        bpy.types.MESH_MT_shape_key_context_menu.remove(misc_MESH_MT_shape_key_specials.menu_func)
        bpy.types.MESH_MT_vertex_group_context_menu.remove(misc_MESH_MT_vertex_group_specials.menu_func)
        bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(misc_VIEW3D_MT_edit_mesh_specials.menu_func)

    bpy.types.IMAGE_MT_image.remove(tex_import.menu_func)
    bpy.types.IMAGE_MT_image.remove(tex_export.menu_func)

    bpy.types.TEXT_MT_text.remove(mate_import.TEXT_MT_text)
    bpy.types.TEXT_MT_text.remove(mate_export.TEXT_MT_text)

    bpy.types.DATA_PT_context_arm.remove(misc_DATA_PT_context_arm.menu_func)
    bpy.types.DATA_PT_modifiers.remove(misc_DATA_PT_modifiers.menu_func)
    bpy.types.DATA_PT_vertex_groups.remove(misc_DATA_PT_vertex_groups.menu_func)
    bpy.types.IMAGE_HT_header.remove(misc_IMAGE_HT_header.menu_func)
    bpy.types.IMAGE_PT_image_properties.remove(misc_IMAGE_PT_image_properties.menu_func)
    bpy.types.INFO_HT_header.remove(misc_INFO_HT_header.menu_func)

    bpy.types.OBJECT_PT_context_object.remove(misc_OBJECT_PT_context_object.menu_func)
    bpy.types.OBJECT_PT_transform.remove(misc_OBJECT_PT_transform.menu_func)
    bpy.types.TEXT_HT_header.remove(misc_TEXT_HT_header.menu_func)
    bpy.types.VIEW3D_MT_pose_apply.remove(misc_VIEW3D_MT_pose_apply.menu_func)

    if hasattr(bpy.types.Object, 'cm3d2_bone_morph'):
        delattr(bpy.types.Object, 'cm3d2_bone_morph')
    if hasattr(bpy.types.Object, 'cm3d2_wide_slider'):
        delattr(bpy.types.Object, 'cm3d2_wide_slider')
    if hasattr(bpy.types.Object, 'cm3d2_menu'):
        delattr(bpy.types.Object, 'cm3d2_menu')

    bpy.types.DOPESHEET_MT_editor_menus.remove(misc_DOPESHEET_MT_editor_menus.menu_func)
    bpy.types.GRAPH_MT_editor_menus.remove(misc_DOPESHEET_MT_editor_menus.menu_func)

    for pcoll in common.preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    common.preview_collections.clear()

    compat.BlRegister.unregister()

    bpy.app.translations.unregister(__name__)

# メイン関数
if __name__ == "__main__":
    register()
