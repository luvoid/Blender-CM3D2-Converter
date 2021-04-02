# アドオンを読み込む時に最初にこのファイルが読み込まれます

# アドオン情報
bl_info = {
    "name": "CM3D2 Converter",
    "author": "@saidenka_cm3d2, @trzrz, @luvoid",
    "version": ("luv", 2021, 4, 2),
    "blender": (2, 80, 0),
    "location" : "File > Import/Export > CM3D2 Model (.model)",
    "description" : "A plugin dedicated to the editing, importing, and exporting of CM3D2 .model Files.",
    "warning": "",
    "wiki_url": "https://github.com/luvoid/Blender-CM3D2-Converter/blob/en_US/README.md",
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

    imp.reload(translations)

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

    from . import translations

import bpy, os.path, bpy.utils.previews


# Backwards compatability
if compat.IS_LEGACY:
    bl_info["blender"] = (2, 78, 0)



# アドオン設定
@compat.BlRegister()
class AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    cm3d2_path = bpy.props.StringProperty(name="CM3D2 Location", subtype='DIR_PATH', description="You should set the correct directory if you used a different one.")
    backup_ext = bpy.props.StringProperty(name="Backup Extension (Must not be left blank)", description="The previous Model file with the same name will be given an extension.", default='bak')

    scale = bpy.props.FloatProperty(name="Scale", description="The scale at which the models are imported and exported", default=5, min=0.01, max=100, soft_min=0.01, soft_max=100, step=10, precision=2)
    is_convert_bone_weight_names = bpy.props.BoolProperty(name="Convert weight names for Blender", default=False, description="Will change the options default when importing or exporting.")
    model_default_path = bpy.props.StringProperty(name="Model Default Path", subtype='DIR_PATH', description="If set. The file selection will open here.")
    model_import_path = bpy.props.StringProperty(name="Model Default Import Path", subtype='FILE_PATH', description="When importing a .model file. The file selection prompt will begin here.")
    model_export_path = bpy.props.StringProperty(name="Model Default Export Path", subtype='FILE_PATH', description="When exporting a .model file. The file selection prompt will begin here.")

    anm_default_path = bpy.props.StringProperty(name=".anm Default Path", subtype='DIR_PATH', description="If set. The file selection will open here.")
    anm_import_path = bpy.props.StringProperty(name=".anm Default Import Path", subtype='FILE_PATH', description="When importing a .anm file. The file selection prompt will begin here.")
    anm_export_path = bpy.props.StringProperty(name=".anm Default Export Path", subtype='FILE_PATH', description="When exporting a .anm file. The file selection prompt will begin here.")

    tex_default_path = bpy.props.StringProperty(name=".tex Default Path", subtype='DIR_PATH', description="If set. The file selection will open here.")
    tex_import_path = bpy.props.StringProperty(name=".tex Default Import Path", subtype='FILE_PATH', description="When importing a .tex file. The file selection prompt will begin here.")
    tex_export_path = bpy.props.StringProperty(name=".tex Default Export Path", subtype='FILE_PATH', description="When exporting a .tex file. The file selection prompt will begin here.")

    mate_default_path = bpy.props.StringProperty(name=".mate Default Path", subtype='DIR_PATH', description="If set. The file selection will open here.")
    mate_unread_same_value = bpy.props.BoolProperty(name="Delete if there are two or more same values", default=True, description="_ShadowColor")
    mate_import_path = bpy.props.StringProperty(name=".mate Default Import Path", subtype='FILE_PATH', description="When importing a .mate file. The file selection prompt will begin here.")
    mate_export_path = bpy.props.StringProperty(name=".mate Default Export Path", subtype='FILE_PATH', description="When exporting a .mate file. The file selection prompt will begin here.")

    menu_default_path = bpy.props.StringProperty(name=".menu Default Path"       , subtype='DIR_PATH' , description="If set. The file selection will open here.")
    menu_import_path  = bpy.props.StringProperty(name=".menu Default Import Path", subtype='FILE_PATH', description="When importing a .menu file. The file selection prompt will begin here.")
    menu_export_path  = bpy.props.StringProperty(name=".menu Default Export Path", subtype='FILE_PATH', description="When exporting a .menu file. The file selection prompt will begin here.")

    is_replace_cm3d2_tex = bpy.props.BoolProperty(name="Search for Tex File", default=True, description="Sets the default of the option to search for tex files")
    default_tex_path0 = bpy.props.StringProperty(name="Tex file search area", subtype='DIR_PATH', description="Search here for tex files")
    default_tex_path1 = bpy.props.StringProperty(name="Tex file search area", subtype='DIR_PATH', description="Search here for tex files")
    default_tex_path2 = bpy.props.StringProperty(name="Tex file search area", subtype='DIR_PATH', description="Search here for tex files")
    default_tex_path3 = bpy.props.StringProperty(name="Tex file search area", subtype='DIR_PATH', description="Search here for tex files")

    
    custom_normal_blend = bpy.props.FloatProperty(name="Custom Normal Blend", default=0.5, min=0, max=1, soft_min=0, soft_max=1, step=3, precision=0)
    skip_shapekey = bpy.props.BoolProperty(name="Skip Unchanged Shape Keys", default=True, description="Shapekeys that are the same as the basis shapekey will not be imported.")
    is_apply_modifiers = bpy.props.BoolProperty(name="Apply Modifiers", default=False)

    new_mate_tex_offset = bpy.props.FloatVectorProperty(name="Texture Offset", default=(0, 0), min=-1, max=1, soft_min=-1, soft_max=1, step=10, precision=3, size=2)
    new_mate_tex_scale = bpy.props.FloatVectorProperty(name="Texture Scale", default=(1, 1), min=0, max=1, soft_min=0, soft_max=1, step=10, precision=3, size=2)

    new_mate_toonramp_name = bpy.props.StringProperty(name="_ToonRamp Name", default="toonGrayA1")
    new_mate_toonramp_path = bpy.props.StringProperty(name="_ToonRamp Path", default=common.BASE_PATH_TEX + "toon/toonGrayA1.png")

    new_mate_shadowratetoon_name = bpy.props.StringProperty(name="_ShadowRateToon Name", default="toonDress_shadow")
    new_mate_shadowratetoon_path = bpy.props.StringProperty(name="_ShadowRateToon Path", default=common.BASE_PATH_TEX + "toon/toonDress_shadow.png")

    new_mate_linetoonramp_name = bpy.props.StringProperty(name="_OutlineToonRamp Name", default="toonGrayA1")
    new_mate_linetoonramp_path = bpy.props.StringProperty(name="_OutlineToonRamp Path", default=common.BASE_PATH_TEX + "toon/toonGrayA1.png")

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
            self.layout.label(text="You must press 'Save User Settings' button for these settings to be saved.", icon='QUESTION')
        else:
            self.layout.label(text="If you changed your preferences, remember to save them before exiting.", icon='QUESTION')
        
        col = self.layout.column()
        col.label(text="CM3D2 Converter Info")
        factor = 0.25
        split = compat.layout_split(col.row(), factor)
        split.label(text="Add-on Version: ")
        split.label(text=".".join(str(i) for i in bl_info["version"]))
        split = compat.layout_split(col.row(), factor)
        split.label(text="Branch: ")
        split.label(text=common.BRANCH)
        split = compat.layout_split(col.row(), factor)
        split.label(text="Repo URL: ")
        split.label(text=common.URL_REPOS)
        split = compat.layout_split(col.row(), factor)
        split.label(text="Blender Version: ")
        split.label(text=".".join(str(i) for i in bpy.app.version) if hasattr(bpy.app, 'version') else "Legacy")
        split = compat.layout_split(col.row(), factor)
        split.label(text="Blender Language: ")
        split.label(text=compat.get_system(bpy.context).language or 'None')
        default_locale = 'UNKNOWN'
        try:
            import locale
            default_locale = locale.getdefaultlocale()[0]
        except:
            pass
        split = compat.layout_split(col.row(), factor)
        split.label(text="Default Language: ")
        split.label(text=default_locale)

        self.layout.label(text="."*9999)
        self.layout.label(text="Preferences:")

        self.layout.prop(self, 'cm3d2_path', icon_value=common.kiss_icon())
        self.layout.prop(self, 'backup_ext', icon='FILE_BACKUP')

        box = self.layout.box()
        box.label(text=".model File", icon='MESH_ICOSPHERE')
        row = box.row()
        row.prop(self, 'scale', icon=compat.icon('ARROW_LEFTRIGHT'))
        row.prop(self, 'is_convert_bone_weight_names', icon='BLENDER')
        brws_icon = compat.icon('FILEBROWSER')
        box.prop(self, 'model_default_path', icon=brws_icon, text="Initial folder when selecting files")

        box = self.layout.box()
        box.label(text=".anm File", icon='POSE_HLT')
        box.prop(self, 'anm_default_path', icon=brws_icon, text="Initial folder when selecting files")

        box = self.layout.box()
        box.label(text=".tex File", icon='FILE_IMAGE')
        box.prop(self, 'tex_default_path', icon=brws_icon, text="Initial folder when selecting files")

        box = self.layout.box()
        box.label(text=".mate File", icon='MATERIAL')
        box.prop(self, 'mate_unread_same_value', icon='DISCLOSURE_TRI_DOWN')
        box.prop(self, 'mate_default_path', icon=brws_icon, text="Initial folder when selecting files")

        box = self.layout.box()
        box.label(text=".menu File", icon='COPY_ID')
        box.prop(self, 'menu_default_path', icon=brws_icon, text="Initial folder when selecting files")

        box = self.layout.box()
        box.label(text="Search for Tex File", icon='BORDERMOVE')
        box.prop(self, 'is_replace_cm3d2_tex', icon='VIEWZOOM')
        box.prop(self, 'default_tex_path0', icon='LAYER_ACTIVE', text="Part 1")
        box.prop(self, 'default_tex_path1', icon='LAYER_ACTIVE', text="Part 2")
        box.prop(self, 'default_tex_path2', icon='LAYER_ACTIVE', text="Part 3")
        box.prop(self, 'default_tex_path3', icon='LAYER_ACTIVE', text="Part 4")

        box = self.layout.box()
        box.label(text="Defaults for when a new CM3d2 Material is Created.", icon='MATERIAL')
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
        box.label(text="Default Export Settings", icon='MATERIAL')
        row = box.row()  # export
        row.prop(self, 'custom_normal_blend', icon='SNAP_NORMAL')
        row.prop(self, 'skip_shapekey', icon='SHAPEKEY_DATA')
        row.prop(self, 'is_apply_modifiers', icon='MODIFIER')
        # row = box.row()
        row = self.layout.row()
        row.operator('script.update_cm3d2_converter', icon='FILE_REFRESH')
        row.menu('INFO_MT_help_CM3D2_Converter_RSS', icon='INFO')

        self.layout.operator('cm3d2_converter.dump_py_messages')


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
        bpy.types.INFO_MT_file_import.append(menu_file.import_menu_func)
        bpy.types.INFO_MT_file_export.append(model_export.menu_func)
        bpy.types.INFO_MT_file_export.append(anm_export.menu_func)
        bpy.types.INFO_MT_file_export.append(menu_file.export_menu_func)

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
        # .menu
        bpy.types.TOPBAR_MT_file_import.append(menu_file.import_menu_func)
        bpy.types.TOPBAR_MT_file_export.append(menu_file.export_menu_func)

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

    translations.register(__name__)
    
    # Change wiki_url based on locale (only works in legacy version)
    locale = translations.get_locale()
    if locale != 'ja_JP':   
        bl_info['wiki_url'] = common.URL_REPOS + f"blob/bl_28/translations/{locale}/README.md"


# プラグインをアンインストールしたときの処理
def unregister():
    if compat.IS_LEGACY:
        bpy.types.INFO_MT_file_import.remove(model_import.menu_func)
        bpy.types.INFO_MT_file_import.remove(anm_import.menu_func)
        bpy.types.INFO_MT_file_import.remove(menu_file.import_menu_func)
        bpy.types.INFO_MT_file_export.remove(model_export.menu_func)
        bpy.types.INFO_MT_file_export.remove(anm_export.menu_func)
        bpy.types.INFO_MT_file_export.remove(menu_file.export_menu_func)

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
        bpy.types.TOPBAR_MT_file_import.remove(menu_file.import_menu_func)
        bpy.types.TOPBAR_MT_file_export.remove(menu_file.export_menu_func)

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

    translations.unregister(__name__)

# メイン関数
if __name__ == "__main__":
    register()
