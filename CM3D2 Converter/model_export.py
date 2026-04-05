import struct
import time
import math
import bpy
import bmesh
import mathutils
import numpy as np
from operator import itemgetter
from . import common
from . import compat
from . import cm3d2_data
from .translations.pgettext_functions import *

from CM3D2.Serialization.Collections import *
from CM3D2.Serialization.Files import Model
from CM3D2.Serialization.Structs import *


# メニューを登録する関数
def menu_func(self, context):
    self.layout.operator(CNV_OT_export_cm3d2_model.bl_idname, icon_value=common.kiss_icon())


# メインオペレーター
@compat.BlRegister()
class CNV_OT_export_cm3d2_model(bpy.types.Operator):
    bl_idname = 'export_mesh.export_cm3d2_model'
    bl_label = "CM3D2モデル (.model)"
    bl_description = "カスタムメイド3D2のmodelファイルを書き出します"
    bl_options = {'REGISTER'}

    filepath = bpy.props.StringProperty(subtype='FILE_PATH')
    filename_ext = ".model"
    filter_glob = bpy.props.StringProperty(default="*.model", options={'HIDDEN'})

    scale = bpy.props.FloatProperty(name="倍率", default=0.2, min=0.01, max=100, soft_min=0.01, soft_max=100, step=10, precision=2, description="エクスポート時のメッシュ等の拡大率です")

    is_backup = bpy.props.BoolProperty(name="ファイルをバックアップ", default=True, description="ファイルに上書きする場合にバックアップファイルを複製します")

    version = bpy.props.EnumProperty(
        name="ファイルバージョン",
        items=[
            ('AUTO', 'Auto', 'determine model version from object properties', 'NONE', 0),
            ('1000', '1000', 'model version 1000 (available for cm3d2/com3d2)', 'NONE', 1000),
            ('2000', '2000', 'model version 2000 (com3d2 version)', 'NONE', 2000),
            ('2001', '2001', 'model version 2001 (available only for com3d2)', 'NONE', 2001),
        ], default='AUTO')
    model_name = bpy.props.StringProperty(name="model名", default="*")
    base_bone_name = bpy.props.StringProperty(name="基点ボーン名", default="*")

    items = [
        ('ARMATURE'         , "アーマチュア", "", 'OUTLINER_OB_ARMATURE', 1),
        ('TEXT'             , "テキスト", "", 'FILE_TEXT', 2),
        ('OBJECT_PROPERTY'  , "オブジェクト内プロパティ", "", 'OBJECT_DATAMODE', 3),
        ('ARMATURE_PROPERTY', "アーマチュア内プロパティ", "", 'ARMATURE_DATA', 4),
    ]
    bone_info_mode = bpy.props.EnumProperty(items=items, name="ボーン情報元", default='OBJECT_PROPERTY', description="modelファイルに必要なボーン情報をどこから引っ張ってくるか選びます")

    items = [
        ('TEXT', "テキスト", "", 'FILE_TEXT', 1),
        ('MATERIAL', "マテリアル", "", 'MATERIAL', 2),
    ]
    mate_info_mode = bpy.props.EnumProperty(items=items, name="マテリアル情報元", default='MATERIAL', description="modelファイルに必要なマテリアル情報をどこから引っ張ってくるか選びます")

    is_arrange_name = bpy.props.BoolProperty(name="データ名の連番を削除", default=True, description="「○○.001」のような連番が付属したデータ名からこれらを削除します")

    is_align_to_base_bone = bpy.props.BoolProperty(name="Align to Base Bone", default=True, description="Align the object to it's base bone")
    is_convert_tris = bpy.props.BoolProperty(name="四角面を三角面に", default=True, description="四角ポリゴンを三角ポリゴンに変換してから出力します、元のメッシュには影響ありません")
    is_split_sharp = bpy.props.BoolProperty(name="Split Sharp Edges", default=True, description="Split all edges marked as sharp.")
    is_normalize_weight = bpy.props.BoolProperty(name="ウェイトの合計を1.0に", default=True, description="4つのウェイトの合計値が1.0になるように正規化します")
    is_convert_bone_weight_names = bpy.props.BoolProperty(name="頂点グループ名をCM3D2用に変換", default=True, description="全ての頂点グループ名をCM3D2で使える名前にしてからエクスポートします")
    is_clean_vertex_groups = bpy.props.BoolProperty(name="クリーンな頂点グループ", default=True, description="重みがゼロの場合、頂点グループから頂点を削除します")
    
    is_batch = bpy.props.BoolProperty(name="バッチモード", default=False, description="モードの切替やエラー個所の選択を行いません")

    export_tangent = bpy.props.BoolProperty(name="接空間情報出力", default=False, description="接空間情報(binormals, tangents)を出力する")

    
    shapekey_threshold = bpy.props.FloatProperty(name="Shape Key Threshold", default=0.00100, min=0, soft_min=0.0005, max=0.01, soft_max=0.002, precision=5, description="Lower values increase accuracy and file size. Higher values truncate small changes and reduce file size.")
    export_shapekey_normals = bpy.props.BoolProperty(name="Export Shape Key Normals", default=True, description="Export custom normals for each shape key on export.")
    shapekey_normals_blend = bpy.props.FloatProperty(name="Shape Key Normals Blend", default=0.6, min=0, max=1, precision=3, description="Adjust the influence of shape keys on custom normals")
    use_shapekey_colors = bpy.props.BoolProperty(name="Use Shape Key Colors", default=True, description="Use the shape key normals stored in the vertex colors instead of calculating the normals on export. (Recommend disabling if geometry was customized)")
    

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if ob:
            if ob.type == 'MESH':
                return True
        return False

    def report_cancel(self, report_message, report_type={'ERROR'}, resobj={'CANCELLED'}):
        """エラーメッセージを出力してキャンセルオブジェクトを返す"""
        self.report(type=report_type, message=report_message)
        return resobj

    def precheck(self, context):
        try:
            ModelBuilder.precheck(context)
        except common.CM3D2ExportError as ex:
            return self.report_cancel(ex.message)

    def invoke(self, context, event):
        res = self.precheck(context)
        if res:
            return res
        ob = context.active_object

        # model名とか
        ob_names = common.remove_serial_number(ob.name, self.is_arrange_name).split('.')
        self.model_name = ob_names[0]
        self.base_bone_name = ob_names[1] if 2 <= len(ob_names) else 'Auto'

        # ボーン情報元のデフォルトオプションを取得
        arm_ob = ob.parent
        for mod in ob.modifiers:
            if mod.type == 'ARMATURE' and mod.object:
                arm_ob = mod.object
        if arm_ob and not arm_ob.type == 'ARMATURE':
            arm_ob = None

        info_mode_was_armature = (self.bone_info_mode == 'ARMATURE')
        if "BoneData" in context.blend_data.texts:
            if "LocalBoneData" in context.blend_data.texts:
                self.bone_info_mode = 'TEXT'
        if "BoneData:0" in ob:
            ver = ob.get("ModelVersion")
            if ver and ver >= 1000:
                self.version = str(ver)
            if "LocalBoneData:0" in ob:
                self.bone_info_mode = 'OBJECT_PROPERTY'
        if arm_ob:
            if info_mode_was_armature:
                self.bone_info_mode = 'ARMATURE'
            else:
                self.bone_info_mode = 'ARMATURE_PROPERTY'

        # エクスポート時のデフォルトパスを取得
        #if not self.filepath[-6:] == '.model':
        if common.preferences().model_default_path:
            self.filepath = common.default_cm3d2_dir(common.preferences().model_default_path, self.model_name, "model")
        else:
            self.filepath = common.default_cm3d2_dir(common.preferences().model_export_path, self.model_name, "model")

        # バックアップ関係
        self.is_backup = bool(common.preferences().backup_ext)

        self.scale = 1.0 / common.preferences().scale
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # 'is_batch' がオンなら非表示
    def draw(self, context):
        self.layout.prop(self, 'scale')
        row = self.layout.row()
        row.prop(self, 'is_backup', icon='FILE_BACKUP')
        if not common.preferences().backup_ext:
            row.enabled = False
        self.layout.prop(self, 'is_arrange_name', icon='FILE_TICK')
        box = self.layout.box()
        box.prop(self, 'version', icon='LINENUMBERS_ON')
        box.prop(self, 'model_name', icon='SORTALPHA')

        row = box.row()
        row.prop(self, 'base_bone_name', icon='CONSTRAINT_BONE')
        if self.base_bone_name == 'Auto':
            row.enabled = False

        prefs = common.preferences()
        
        box = self.layout.box()
        col = box.column(align=True)
        col.label(text="ボーン情報元", icon='BONE_DATA')
        col.prop(self, 'bone_info_mode', icon='BONE_DATA', expand=True)
        col = box.column(align=True)
        col.label(text="マテリアル情報元", icon='MATERIAL')
        col.prop(self, 'mate_info_mode', icon='MATERIAL', expand=True)
        
        box = self.layout.box()
        box.label(text="メッシュオプション")
        box.prop(self , 'is_align_to_base_bone', icon=compat.icon('OBJECT_ORIGIN'  ))
        box.prop(self , 'is_convert_tris'      , icon=compat.icon('MESH_DATA'      ))
        box.prop(self , 'is_split_sharp'       , icon=compat.icon('MOD_EDGESPLIT'  ))
        box.prop(self , 'export_tangent'       , icon=compat.icon('CURVE_BEZCIRCLE'))
        sub_box = box.box()
        sub_box.prop(self , 'shapekey_threshold'     , icon=compat.icon('SHAPEKEY_DATA'      ), slider=True)
        sub_box.prop(prefs, 'skip_shapekey'          , icon=compat.icon('SHAPEKEY_DATA'      ), toggle=1)
        sub_box.prop(self , 'export_shapekey_normals', icon=compat.icon('NORMALS_VERTEX_FACE'))
        row = sub_box.row()
        row    .prop(self , 'shapekey_normals_blend' , icon=compat.icon('MOD_NORMALEDIT'     ), slider=True)
        row.enabled = self.export_shapekey_normals
        row = sub_box.row()
        row    .prop(self , 'use_shapekey_colors'    , icon=compat.icon('GROUP_VCOL')         , toggle=0)
        row.enabled = self.export_shapekey_normals
        sub_box = box.box()
        sub_box.prop(self, 'is_normalize_weight', icon='MOD_VERTEX_WEIGHT')
        sub_box.prop(self, 'is_clean_vertex_groups', icon='MOD_VERTEX_WEIGHT')
        sub_box.prop(self, 'is_convert_bone_weight_names', icon_value=common.kiss_icon())
        sub_box
        sub_box = box.box()
        sub_box.prop(prefs, 'is_apply_modifiers', icon='MODIFIER')
        row = sub_box.row()
        row.prop(prefs, 'custom_normal_blend', icon='SNAP_NORMAL', slider=True)
        row.enabled = prefs.is_apply_modifiers

    def copy_and_activate_ob(self, context, ob):
        new_ob = ob.copy()
        new_me = ob.data.copy()
        new_ob.data = new_me
        compat.link(context.scene, new_ob)
        compat.set_active(context, new_ob)
        compat.set_select(new_ob, True)
        return new_ob

    def execute(self, context):
        start_time = time.time()
        prefs = common.preferences()
        
        if not self.is_batch:
            prefs.model_export_path = self.filepath
            prefs.scale = 1.0 / self.scale

        selected_objs = context.selected_objects
        source_objs = []
        ob_source = None
        ob_name = None
        prev_mode = context.active_object.mode
        try:
            ob_source = context.active_object
            ob_name = ob_source.name
            if ob_source not in selected_objs:
                selected_objs.append(ob_source) # luvoid : Fix error where object is active but not selected
            ob_main = None

            if context.active_object.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')

            if self.is_batch:
                # アクティブオブジェクトを１つコピーするだけでjoinしない
                source_objs.append(ob_source)
                compat.set_select(ob_source, False)
                ob_main = self.copy_and_activate_ob(context, ob_source)
                if prefs.is_apply_modifiers:
                    bpy.ops.object.forced_modifier_apply(apply_viewport_visible=True)
            else:
                selected_count = 0
                # 選択されたMESHオブジェクトをコピーしてjoin
                # 必要に応じて、モディファイアの強制適用を行う
                for selected in selected_objs:
                    source_objs.append(selected)

                    compat.set_select(selected, False)

                    if selected.type == 'MESH':
                        ob_created = self.copy_and_activate_ob(context, selected)
                        if selected == ob_source:
                            ob_main = ob_created
                        if prefs.is_apply_modifiers:
                            bpy.ops.object.forced_modifier_apply(apply_viewport_visible=True)

                        selected_count += 1

                if selected_count > 1:
                    if ob_main:
                        compat.set_active(context, ob_main)
                    bpy.ops.object.join()
                    self.report(type={'INFO'}, message=f_tip_("{}個のオブジェクトをマージしました", selected_count))

            ret = self.export(context, ob_main)
            if 'FINISHED' not in ret:
                return ret

            context.window_manager.progress_update(10)
            diff_time = time.time() - start_time
            self.report(type={'INFO'}, message=f_tip_("modelのエクスポートが完了しました。{:.2f} 秒 file={}", diff_time, self.filepath))
            return ret
        finally:
            # 作業データの破棄（コピーデータを削除、選択状態の復元、アクティブオブジェクト、モードの復元）
            if ob_main:
                common.remove_data(ob_main)
                # me_copied = ob_main.data
                # context.blend_data.objects.remove(ob_main, do_unlink=True)
                # context.blend_data.meshes.remove(me_copied, do_unlink=True)

            for obj in source_objs:
                compat.set_select(obj, True)

            if ob_source and ob_name in bpy.data.objects:
                compat.set_active(context, ob_source)

            if prev_mode:
                bpy.ops.object.mode_set(mode=prev_mode)

    def export(self, context, ob):
        if self.is_align_to_base_bone:
            bpy.ops.object.align_to_cm3d2_base_bone(
                scale=1.0/self.scale,
                is_preserve_mesh=True,
                bone_info_mode=self.bone_info_mode
            )
            ob.data.update()
            
        if self.is_split_sharp:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.split_sharp()
            bpy.ops.object.mode_set(mode='OBJECT')
        
        model_builder = self.get_model_builder()
        try:
            model_builder.export(context, ob, self.filepath)
        except ZeroWeightVertexError as ex:
            if not self.is_batch:
                self.select_no_weight_vertices(context, ex.local_bone_name_indices)
        except common.CM3D2ExportError as ex:
            return self.report_cancel(ex.message)
        return {'FINISHED'}

    def get_model_builder(self):
        model_builder = ModelBuilder(self)

        model_builder.scale = self.scale
        model_builder.is_backup = self.is_backup
        model_builder.version = self.version
        model_builder.model_name = self.model_name
        model_builder.base_bone_name = self.base_bone_name
        model_builder.bone_info_mode = self.bone_info_mode
        model_builder.mate_info_mode = self.mate_info_mode
        model_builder.is_arrange_name = self.is_arrange_name
        model_builder.is_align_to_base_bone = self.is_align_to_base_bone
        model_builder.is_convert_tris = self.is_convert_tris
        model_builder.did_split_sharp = self.is_split_sharp
        model_builder.is_normalize_weight = self.is_normalize_weight
        model_builder.is_convert_bone_weight_names = self.is_convert_bone_weight_names
        model_builder.is_clean_vertex_groups = self.is_clean_vertex_groups
        model_builder.is_batch = self.is_batch
        model_builder.export_tangent = self.export_tangent
        model_builder.shapekey_threshold = self.shapekey_threshold
        model_builder.export_shapekey_normals = self.export_shapekey_normals
        model_builder.shapekey_normals_blend = self.shapekey_normals_blend
        model_builder.use_shapekey_colors = self.use_shapekey_colors

        return model_builder

    def select_no_weight_vertices(self, context, local_bone_name_indices):
        """ウェイトが割り当てられていない頂点を選択する"""
        ob = context.active_object
        me = ob.data
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        #bpy.ops.object.mode_set(mode='OBJECT')
        context.tool_settings.mesh_select_mode = (True, False, False)
        for vert in me.vertices:
            for vg in vert.groups:
                if len(ob.vertex_groups) <= vg.group: # Apparently a vertex can be assigned to a non-existent group.
                    continue
                name = common.encode_bone_name(ob.vertex_groups[vg.group].name, self.is_convert_bone_weight_names)
                if name in local_bone_name_indices and 0.0 < vg.weight:
                    vert.select = False
                    break
        bpy.ops.object.mode_set(mode='EDIT')


class ZeroWeightVertexError(common.CM3D2ExportError):
    def __init__(self, message: str, local_bone_name_indices: dict[str, int]):
        super().__init__(message)
        self.local_bone_name_indices = local_bone_name_indices


class ModelBuilder:
    def __init__(self, reporter: bpy.types.Operator):
        self.reporter = reporter

        self.scale = 0.2
        self.is_backup = True
        self.version = 'AUTO'
        self.model_name = "*"
        self.base_bone_name = "*"
        self.bone_info_mode = 'OBJECT_PROPERTY'
        self.mate_info_mode = 'MATERIAL'
        self.is_arrange_name = True
        self.is_align_to_base_bone = True
        self.is_convert_tris = True
        self.did_split_sharp = False
        self.is_normalize_weight = True
        self.is_convert_bone_weight_names = True
        self.is_clean_vertex_groups = True
        self.is_batch = False
        self.export_tangent = False
        self.shapekey_threshold = 0.00100
        self.export_shapekey_normals = True
        self.shapekey_normals_blend = 0.6
        self.use_shapekey_colors = True

    @staticmethod
    def precheck(context: bpy.context):
        """データの成否チェック"""
        ob = context.active_object
        if not ob:
            raise common.CM3D2ExportError(f_tip_("アクティブオブジェクトがありません"))
        if ob.type != 'MESH':
            raise common.CM3D2ExportError(f_tip_("メッシュオブジェクトを選択した状態で実行してください"))
        if not len(ob.material_slots):
            raise common.CM3D2ExportError(f_tip_("マテリアルがありません"))
        for slot in ob.material_slots:
            if not slot.material:
                raise common.CM3D2ExportError(f_tip_("空のマテリアルスロットを削除してください"))
            try:
                slot.material['shader1']
                slot.material['shader2']
            except:
                raise common.CM3D2ExportError(
                    f_tip_("マテリアルに「shader1」と「shader2」という名前のカスタムプロパティを用意してください"))
        me = ob.data
        if not me.uv_layers.active:
            raise common.CM3D2ExportError(f_tip_("UVがありません"))
        if 65535 < len(me.vertices):
            raise common.CM3D2ExportError(
                f_tip_("エクスポート可能な頂点数を大幅に超えています、最低でも65535未満には削減してください"))  
    
    def check_bone_data(self, context: bpy.context, ob: bpy.types.Object):
        """データの成否チェック"""
        arm_ob = None
        if self.bone_info_mode == 'ARMATURE':
            arm_ob = ob.parent
            if arm_ob and arm_ob.type != 'ARMATURE':
                raise common.CM3D2ExportError(f_tip_("メッシュオブジェクトの親がアーマチュアではありません"))
            if not arm_ob:
                try:
                    arm_ob = next(mod for mod in ob.modifiers if mod.type == 'ARMATURE' and mod.object)
                except StopIteration:
                    raise common.CM3D2ExportError(
                        f_tip_("アーマチュアが見つかりません、親にするかモディファイアにして下さい"))
                arm_ob = arm_ob.object
        elif self.bone_info_mode == 'TEXT':
            if "BoneData" not in context.blend_data.texts:
                raise common.CM3D2ExportError(f_tip_("テキスト「BoneData」が見つかりません、中止します"))
            if "LocalBoneData" not in context.blend_data.texts:
                raise common.CM3D2ExportError(f_tip_("テキスト「LocalBoneData」が見つかりません、中止します"))
        elif self.bone_info_mode == 'OBJECT_PROPERTY':
            if "BoneData:0" not in ob:
                raise common.CM3D2ExportError(f_tip_("オブジェクトのカスタムプロパティにボーン情報がありません"))
            if "LocalBoneData:0" not in ob:
                raise common.CM3D2ExportError(f_tip_("オブジェクトのカスタムプロパティにボーン情報がありません"))
        elif self.bone_info_mode == 'ARMATURE_PROPERTY':
            arm_ob = ob.parent
            if arm_ob and arm_ob.type != 'ARMATURE':
                raise common.CM3D2ExportError(f_tip_("メッシュオブジェクトの親がアーマチュアではありません"))
            if not arm_ob:
                try:
                    arm_ob = next(mod for mod in ob.modifiers if mod.type == 'ARMATURE' and mod.object)
                except StopIteration:
                    raise common.CM3D2ExportError(  # pylint:disable=raise-missing-from
                        f_tip_("アーマチュアが見つかりません、親にするかモディファイアにして下さい"))
                arm_ob = arm_ob.object
            if "BoneData:0" not in arm_ob.data:
                raise common.CM3D2ExportError(f_tip_("アーマチュアのカスタムプロパティにボーン情報がありません"))
            if "LocalBoneData:0" not in arm_ob.data:
                raise common.CM3D2ExportError(f_tip_("アーマチュアのカスタムプロパティにボーン情報がありません"))
        else:
            raise common.CM3D2ExportError(f_tip_("ボーン情報元のモードがおかしいです"))
        return arm_ob

    def check_mate_data(self, context: bpy.types.Context, ob: bpy.types.Object):
        if self.mate_info_mode == 'TEXT':
            for index, slot in enumerate(ob.material_slots):
                if "Material:" + str(index) not in context.blend_data.texts:
                    raise common.CM3D2ExportError(f_tip_("マテリアル情報元のテキストが足りません"))

    def load_bone_data(self, context: bpy.types.Context, ob: bpy.types.Object, arm_ob: bpy.types.Object):
        """BoneData情報読み込み"""
        base_bone_candidate = None
        bone_data = []
        if self.bone_info_mode == 'ARMATURE':
            bone_data = self.armature_bone_data_parser(context, arm_ob)
            base_bone_candidate = arm_ob.data['BaseBone']
        elif self.bone_info_mode == 'TEXT':
            bone_data_text = context.blend_data.texts["BoneData"]
            if 'BaseBone' in bone_data_text:
                base_bone_candidate = bone_data_text['BaseBone']
            bone_data = self.bone_data_parser(l.body for l in bone_data_text.lines)
        elif self.bone_info_mode in ['OBJECT_PROPERTY', 'ARMATURE_PROPERTY']:
            target = ob if self.bone_info_mode == 'OBJECT_PROPERTY' else arm_ob.data
            if 'BaseBone' in target:
                base_bone_candidate = target['BaseBone']
            bone_data = self.bone_data_parser(self.indexed_data_generator(target, prefix="BoneData:"))
        if len(bone_data) <= 0:
            raise common.CM3D2ExportError(f_tip_("テキスト「BoneData」に有効なデータがありません"))

        if self.base_bone_name not in (b['name'] for b in bone_data):
            if base_bone_candidate and self.base_bone_name == 'Auto':
                self.base_bone_name = base_bone_candidate
            else:
                raise common.CM3D2ExportError(f_tip_("基点ボーンが存在しません"))
        
        return bone_data

    def load_local_bone_data(self, context: bpy.types.Context, ob: bpy.types.Object, arm_ob: bpy.types.Object):
        """LocalBoneData情報読み込み"""
        local_bone_data = []
        if self.bone_info_mode == 'ARMATURE':
            local_bone_data = self.armature_local_bone_data_parser(arm_ob)
        elif self.bone_info_mode == 'TEXT':
            local_bone_data_text = context.blend_data.texts["LocalBoneData"]
            local_bone_data = self.local_bone_data_parser(l.body for l in local_bone_data_text.lines)
        elif self.bone_info_mode in ['OBJECT_PROPERTY', 'ARMATURE_PROPERTY']:
            target = ob if self.bone_info_mode == 'OBJECT_PROPERTY' else arm_ob.data
            local_bone_data = self.local_bone_data_parser(self.indexed_data_generator(target, prefix="LocalBoneData:"))
        if len(local_bone_data) <= 0:
            raise common.CM3D2ExportError(f_tip_("テキスト「LocalBoneData」に有効なデータがありません"))
        return local_bone_data

    def load_vertex_groups(self, context: bpy.types.Context, ob: bpy.types.Object, bone_data, local_bone_data):
        """ウェイト情報読み込み"""
        me = ob.data
        used_local_bone = {index: False for index, bone in enumerate(local_bone_data)}
        bone_name_indices = {bone['name']: index for index, bone in enumerate(bone_data)}
        local_bone_name_indices = {bone['name']: index for index, bone in enumerate(local_bone_data)}
        
        vertices = []
        is_over_one = 0
        is_under_one = 0
        is_in_too_many = 0
        for i, vert in enumerate(me.vertices):
            vgs: list[list[float]] = []
            for vg in vert.groups:
                if len(ob.vertex_groups) <= vg.group: # Apparently a vertex can be assigned to a non-existent group.
                    continue
                name = common.encode_bone_name(ob.vertex_groups[vg.group].name, self.is_convert_bone_weight_names)
                index = local_bone_name_indices.get(name, -1)
                if index >= 0 and (vg.weight > 0.0 or not self.is_clean_vertex_groups):
                    vgs.append([index, vg.weight])
                    # luvoid : track used bones
                    used_local_bone[index] = True
                    boneindex = bone_name_indices.get(name, -1)
                    while boneindex >= 0:
                        parent = bone_data[boneindex]
                        localindex = local_bone_name_indices.get(parent['name'], -1)
                        # could check for `localindex == -1` here, 
                        # but its prescence may be useful in determing if the local bones resolve back to some root
                        used_local_bone[localindex] = True
                        boneindex = parent['parent_index']
            if len(vgs) == 0:
                raise ZeroWeightVertexError(
                    message=f_tip_("ウェイトが割り当てられていない頂点が見つかりました、中止します"),
                    local_bone_name_indices=local_bone_name_indices
                )
            if len(vgs) > 4:
                is_in_too_many += 1
            vgs = sorted(vgs, key=itemgetter(1), reverse=True)[0:4]
            total = sum(vg[1] for vg in vgs)
            if self.is_normalize_weight:
                if True:
                    # This fixed threshold is tuned to leave body001.model unchanged
                    if abs(total - 1) > 1e-6:
                        for vg in vgs:
                            vg[1] /= total
                else: 
                    # Alternative Technique
                    # Floating-point-errors can accumulate over repeated imports/exports here
                    # so perform the normalization in a copy
                    vgs_temp = vgs.copy()
                    for i, vg in enumerate(vgs_temp):
                        vg_temp = vg.copy()
                        vg_temp[1] /= total
                        vgs_temp[i] = vg_temp
                    total_temp = sum(vg_temp[1] for vg_temp in vgs_temp)
                    # Only apply the normalization if it brings the sum closer to 1
                    if abs(total_temp - 1) < abs(total - 1):
                        vgs = vgs_temp
            else:
                if 1.01 < total:
                    is_over_one += 1
                elif total < 0.99:
                    is_under_one += 1
            if len(vgs) < 4:
                vgs += [(0, 0.0)] * (4 - len(vgs))
            vertices.append({
                'index': vert.index,
                'face_indexs': list(map(itemgetter(0), vgs)),
                'weights': list(map(itemgetter(1), vgs)),
            })

        if is_over_one > 0:
            self.reporter.report(
                type={'WARNING'},
                message=f_tip_("ウェイトの合計が1.0を超えている頂点が見つかりました。正規化してください。超過している頂点の数:{}", is_over_one)
            )
        if is_under_one > 0:
            self.reporter.report(
                type={'WARNING'},
                message=f_tip_("ウェイトの合計が1.0未満の頂点が見つかりました。正規化してください。不足している頂点の数:{}", is_under_one)
            )

        # luvoid : warn that there are vertices in too many vertex groups
        if is_in_too_many > 0:
            self.reporter.report(
                type={'WARNING'},
                message=f_tip_("4つを超える頂点グループにある頂点が見つかりました。頂点グループをクリーンアップしてください。不足している頂点の数:{}", is_in_too_many)
            )

        # luvoid : check for unused local bones that the game will delete
        is_deleted = 0
        deleted_names = "The game will delete these local bones"
        for index, is_used in used_local_bone.items():
            print(index, is_used)
            if is_used == False:
                is_deleted += 1
                deleted_names = deleted_names + '\n' + local_bone_data[index]['name']
            elif is_used == True:
                pass
            else:
                print(f_tip_("Unexpected: used_local_bone[{key}] == {value} when len(used_local_bone) == {length}", key=index, value=is_used, length=len(used_local_bone)))
                self.reporter.report(
                    type={'WARNING'},
                    message=f_tip_("Could not find whether bone with index {index} was used. See console for more info.", index=i)
                )
        if is_deleted > 0:
            self.reporter.report(
                type={'WARNING'},
                message=f_tip_("頂点が割り当てられていない{num}つのローカルボーンが見つかりました。 詳細については、ログを参照してください。", num=is_deleted)
            )
            self.reporter.report(type={'INFO'}, message=deleted_names)

        return vertices

    def export(self, context, ob, filepath):
        """モデルファイルを出力"""
        context.window_manager.progress_begin(0, 10)
        context.window_manager.progress_update(0)

        self.precheck(context)
        arm_ob = self.check_bone_data(context, ob)
        self.check_mate_data(context, ob)

        context.window_manager.progress_update(1)

        # model名とか
        # Determine model & basebone names
        ob_names = common.remove_serial_number(ob.name, self.is_arrange_name).split('.')
        if self.model_name == '*':
            self.model_name = ob_names[0]
        if self.base_bone_name == '*':
            self.base_bone_name = ob_names[1] if 2 <= len(ob_names) else 'Auto'

        bone_data = self.load_bone_data(context, ob, arm_ob)
        context.window_manager.progress_update(2)

        local_bone_data = self.load_local_bone_data(context, ob, arm_ob)
        context.window_manager.progress_update(3)

        if ob.active_shape_key_index != 0:
            ob.active_shape_key_index = 0
            ob.data.update()

        vertices = self.load_vertex_groups(context, ob, bone_data, local_bone_data)
        context.window_manager.progress_update(4)

        try:
            writer = common.open_temporary(filepath, 'wb', is_backup=self.is_backup)
        except OSError as ex:
            raise common.CM3D2ExportError(
                f_tip_("ファイルを開くのに失敗しました、アクセス不可かファイルが存在しません。file={}", filepath)
            ) from ex

        model_datas = {
            'bone_data': bone_data,
            'local_bone_data': local_bone_data,
            'vertices': vertices,
        }
        with writer:
            self.write_model(context, ob, writer, **model_datas)
    
    def write_model(self, context, ob: bpy.types.Object, writer, bone_data=[], local_bone_data=[], vertices=[]):
        """モデルデータをファイルオブジェクトに書き込む"""
        me = ob.data
        prefs = common.preferences()

        # ファイル先頭
        common.write_str(writer, 'CM3D2_MESH')
        if self.version == 'AUTO':
            self._version_num = max(ob.get("ModelVersion", 1000), 1000)
        else:
            self._version_num = int(self.version)
        writer.write(struct.pack('<i', self._version_num))

        common.write_str(writer, self.model_name)
        common.write_str(writer, self.base_bone_name)

        # ボーン情報書き出し
        writer.write(struct.pack('<i', len(bone_data)))
        for bone in bone_data:
            common.write_str(writer, bone['name'])
            writer.write(struct.pack('<b', bone['scl']))
        context.window_manager.progress_update(3.3)
        for bone in bone_data:
            writer.write(struct.pack('<i', bone['parent_index']))
        context.window_manager.progress_update(3.7)
        for bone in bone_data:
            writer.write(struct.pack('<3f', bone['co'][0], bone['co'][1], bone['co'][2]))
            writer.write(struct.pack('<4f', bone['rot'][1], bone['rot'][2], bone['rot'][3], bone['rot'][0]))
            if self._version_num >= 2001:
                use_scale = ('scale' in bone)
                writer.write(struct.pack('<b', use_scale))
                if use_scale:
                    bone_scale = bone['scale']
                    writer.write(struct.pack('<3f', bone_scale[0], bone_scale[1], bone_scale[2]))
        context.window_manager.progress_update(4)

        # 正しい頂点数などを取得
        bm = bmesh.new()
        bm.from_mesh(me)
        uv_lay = bm.loops.layers.uv.active
        vert_uvs = []
        vert_uvs_append = vert_uvs.append
        vert_iuv = {}
        vert_indices = {}
        vert_count = 0
        for vert in bm.verts:
            vert_uv = []
            vert_uvs_append(vert_uv)
            for loop in vert.link_loops:
                uv = loop[uv_lay].uv
                if uv not in vert_uv:
                    vert_uv.append(uv)
                    vert_iuv[hash((vert.index, uv.x, uv.y))] = vert_count
                    vert_indices[vert.index] = vert_count
                    vert_count += 1
        if 65535 < vert_count:
            raise common.CM3D2ExportError(f_tip_("頂点数がまだ多いです (現在{}頂点)。あと{}頂点以上減らしてください、中止します", vert_count, vert_count - 65535))
        context.window_manager.progress_update(5)

        writer.write(struct.pack('<2i', vert_count, len(ob.material_slots)))

        # ローカルボーン情報を書き出し
        writer.write(struct.pack('<i', len(local_bone_data)))
        for bone in local_bone_data:
            common.write_str(writer, bone['name'])
        context.window_manager.progress_update(5.3)
        for bone in local_bone_data:
            for f in bone['matrix']:
                writer.write(struct.pack('<f', f))
        context.window_manager.progress_update(5.7)

        # カスタム法線情報を取得
        if me.has_custom_normals:
            custom_normals = [mathutils.Vector() for i in range(len(me.vertices))]
            me.calc_normals_split()
            for loop in me.loops:
                custom_normals[loop.vertex_index] += loop.normal
            for no in custom_normals:
                no.normalize()
        else:
            custom_normals = None

        cm_verts = []
        cm_norms = []
        cm_uvs = []
        # 頂点情報を書き出し
        for i, vert in enumerate(bm.verts):
            co = compat.convert_bl_to_cm_space( vert.co * self.scale )
            if me.has_custom_normals:
                no = custom_normals[vert.index]
            else:
                no = vert.normal.copy()
            no = compat.convert_bl_to_cm_space( no )
            for uv in vert_uvs[i]:
                cm_verts.append(co)
                cm_norms.append(no)
                cm_uvs.append(uv)
                writer.write(struct.pack('<3f', co.x, co.y, co.z))
                writer.write(struct.pack('<3f', no.x, no.y, no.z))
                writer.write(struct.pack('<2f', uv.x, uv.y))
        context.window_manager.progress_update(6)

        cm_tris = self.parse_triangles(bm, ob, uv_lay, vert_iuv, vert_indices)

        # 接空間情報を書き出し
        if self.export_tangent:
            tangents = self.calc_tangents(cm_tris, cm_verts, cm_norms, cm_uvs)
            writer.write(struct.pack('<i', len(tangents)))
            for t in tangents:
                writer.write(struct.pack('<4f', *t))
        else:
            writer.write(struct.pack('<i', 0))

        # ウェイト情報を書き出し
        for vert in vertices:
            for uv in vert_uvs[vert['index']]:
                writer.write(struct.pack('<4H', *vert['face_indexs']))
                writer.write(struct.pack('<4f', *vert['weights']))
        context.window_manager.progress_update(7)

        # 面情報を書き出し
        for tri in cm_tris:
            writer.write(struct.pack('<i', len(tri)))
            for vert_index in tri:
                writer.write(struct.pack('<H', vert_index))
        context.window_manager.progress_update(8)

        # マテリアルを書き出し
        writer.write(struct.pack('<i', len(ob.material_slots)))
        for slot_index, slot in enumerate(ob.material_slots):
            if self.mate_info_mode == 'MATERIAL':
                mat_data = cm3d2_data.MaterialHandler.parse_mate(slot.material, self.is_arrange_name)
                mat_data.write(writer, write_header=False)

            elif self.mate_info_mode == 'TEXT':
                text = context.blend_data.texts["Material:" + str(slot_index)].as_string()
                mat_data = cm3d2_data.MaterialHandler.parse_text(slot.material, self.is_arrange_name)
                mat_data.write(writer, write_header=False)

        context.window_manager.progress_update(9)

        # モーフを書き出し
        if me.shape_keys and len(me.shape_keys.key_blocks) >= 2:
            try:
                self.write_shapekeys(context, ob, writer, vert_uvs, custom_normals)
            finally:
                print("FINISHED SHAPE KEYS WRITE")
                pass
        common.write_str(writer, 'end')

    def build_model(self, context, ob: bpy.types.Object, writer, bone_data=[], local_bone_data=[], vertices=[]):
        """モデルデータをファイルオブジェクトに書き込む"""
        me = ob.data
        
        model = Model()

        # ファイル先頭
        # model.signature = 'CM3D2_MESH'
        if self.version == 'AUTO':
            self._version_num = int(max(ob.get("ModelVersion", 1000), 1000))
        else:
            self._version_num = int(self.version)
        model.version = self._version_num

        model.modelName = self.model_name
        model.meshObjectName = self.base_bone_name

        # ボーン情報書き出し
        model.childNames = LengthPrefixedList[Model.ChildName](len(bone_data))
        for i, bone in enumerate(bone_data):
            childName = model.childNames[i]
            childName.name = bone['name']
            childName.isSclBone = bone['scl']
            model.childNames[i] = childName
        context.window_manager.progress_update(3.3)
        model.childParents.UnsafeSetArray([bone['parent_index'] for bone in bone_data])
        context.window_manager.progress_update(3.7)
        childLocalTransforms = []
        for bone in bone_data:
            localTransform = Model.LocalTransform()
            localTransform.localPosition = Float3(bone['co'][0], bone['co'][1], bone['co'][2])
            localTransform.localPosition = Float4(bone['rot'][1], bone['rot'][2], bone['rot'][3], bone['rot'][0])
            if self._version_num >= 2001 and 'scale' in bone:
                # localTransform.localScale.HasValue = True
                localTransform.localScale = Float3(bone['scale'][0], bone['scale'][1], bone['scale'][2])
            childLocalTransforms.append(localTransform)
        context.window_manager.progress_update(4)

        # 正しい頂点数などを取得
        bm = bmesh.new()
        bm.from_mesh(me)
        uv_lay = bm.loops.layers.uv.active
        vert_uvs = []
        vert_uvs_append = vert_uvs.append
        vert_iuv = {}
        vert_indices = {}
        vert_count = 0
        for vert in bm.verts:
            vert_uv = []
            vert_uvs_append(vert_uv)
            for loop in vert.link_loops:
                uv = loop[uv_lay].uv
                if uv not in vert_uv:
                    vert_uv.append(uv)
                    vert_iuv[hash((vert.index, uv.x, uv.y))] = vert_count
                    vert_indices[vert.index] = vert_count
                    vert_count += 1
        if 65535 < vert_count:
            raise common.CM3D2ExportError(f_tip_("頂点数がまだ多いです (現在{}頂点)。あと{}頂点以上減らしてください、中止します", vert_count, vert_count - 65535))
        context.window_manager.progress_update(5)

        model.vertexCount = vert_count
        model.submeshCount = len(ob.material_slots)

        # ローカルボーン情報を書き出し
        model.boneUseNames.Capacity = len(local_bone_data)
        for i, bone in enumerate(local_bone_data):
            model.boneUseNames.Add(bone['name'])
        context.window_manager.progress_update(5.3)
        bindPoses = []
        for bone in local_bone_data:
            mat = bone['matrix']
            bindPoses.append(Float4x4(
                Float4(mat[ 0], mat[ 1], mat[ 2], mat[ 3]),
                Float4(mat[ 4], mat[ 5], mat[ 6], mat[ 7]),
                Float4(mat[ 8], mat[ 9], mat[10], mat[11]),
                Float4(mat[12], mat[13], mat[14], mat[15])
            ))
        model.bindPoses.UnsafeSetArray(bindPoses)
        context.window_manager.progress_update(5.7)

        # カスタム法線情報を取得
        if me.has_custom_normals:
            custom_normals = [mathutils.Vector() for i in range(len(me.vertices))]
            me.calc_normals_split()
            for loop in me.loops:
                custom_normals[loop.vertex_index] += loop.normal
            for no in custom_normals:
                no.normalize()
        else:
            custom_normals = None

        cm_verts = []
        cm_norms = []
        cm_uvs = []
        # 頂点情報を書き出し
        for i, vert in enumerate(bm.verts):
            co = compat.convert_bl_to_cm_space( vert.co * self.scale )
            if me.has_custom_normals:
                no = custom_normals[vert.index]
            else:
                no = vert.normal.copy()
            no = compat.convert_bl_to_cm_space( no )
            for uv in vert_uvs[i]:
                cm_verts.append(co)
                cm_norms.append(no)
                cm_uvs.append(uv)
                
                writer.write(struct.pack('<3f', co.x, co.y, co.z))
                writer.write(struct.pack('<3f', no.x, no.y, no.z))
                writer.write(struct.pack('<2f', uv.x, uv.y))
        context.window_manager.progress_update(6)

        cm_tris = self.parse_triangles(bm, ob, uv_lay, vert_iuv, vert_indices)

        # 接空間情報を書き出し
        if self.export_tangent:
            tangents = self.calc_tangents(cm_tris, cm_verts, cm_norms, cm_uvs)
            writer.write(struct.pack('<i', len(tangents)))
            for t in tangents:
                writer.write(struct.pack('<4f', *t))
        else:
            writer.write(struct.pack('<i', 0))

        # ウェイト情報を書き出し
        for vert in vertices:
            for uv in vert_uvs[vert['index']]:
                writer.write(struct.pack('<4H', *vert['face_indexs']))
                writer.write(struct.pack('<4f', *vert['weights']))
        context.window_manager.progress_update(7)

        # 面情報を書き出し
        for tri in cm_tris:
            writer.write(struct.pack('<i', len(tri)))
            for vert_index in tri:
                writer.write(struct.pack('<H', vert_index))
        context.window_manager.progress_update(8)

        # マテリアルを書き出し
        writer.write(struct.pack('<i', len(ob.material_slots)))
        for slot_index, slot in enumerate(ob.material_slots):
            if self.mate_info_mode == 'MATERIAL':
                mat_data = cm3d2_data.MaterialHandler.parse_mate(slot.material, self.is_arrange_name)
                mat_data.write(writer, write_header=False)

            elif self.mate_info_mode == 'TEXT':
                text = context.blend_data.texts["Material:" + str(slot_index)].as_string()
                mat_data = cm3d2_data.MaterialHandler.parse_text(slot.material, self.is_arrange_name)
                mat_data.write(writer, write_header=False)

        context.window_manager.progress_update(9)

        # モーフを書き出し
        if me.shape_keys and len(me.shape_keys.key_blocks) >= 2:
            try:
                self.write_shapekeys(context, ob, writer, vert_uvs, custom_normals)
            finally:
                print("FINISHED SHAPE KEYS WRITE")
                pass
        common.write_str(writer, 'end')

    def write_shapekeys(self, context, ob, writer, vert_uvs, custom_normals=None):
        # モーフを書き出し
        me = ob.data
        prefs = common.preferences()
        
        is_use_attributes = (not compat.IS_LEGACY and bpy.app.version >= (2,92))

        loops_vert_index = np.empty((len(me.loops)), dtype=int)
        me.loops.foreach_get('vertex_index', loops_vert_index.ravel())

        def find_normals_attribute(name) -> (bpy.types.Attribute, bool):
            if is_use_attributes:
                normals_color = me.attributes[name] if name in me.attributes.keys() else None
                attribute_is_color = (not normals_color is None) and normals_color.data_type in {'BYTE_COLOR', 'FLOAT_COLOR'}
            else:
                normals_color = me.vertex_colors[name] if name in me.vertex_colors.keys() else None
                attribute_is_color = True
            return normals_color, attribute_is_color

        if self.use_shapekey_colors:
            static_attribute_colors = np.empty((len(me.loops), 4), dtype=float)
            color_offset = np.array([[0.5,0.5,0.5]])
            loops_per_vertex = np.zeros((len(me.vertices)))
            for loop in me.loops:
                loops_per_vertex[loop.vertex_index] += 1
            loops_per_vertex_reciprocal = np.reciprocal(loops_per_vertex, out=loops_per_vertex).reshape((len(me.vertices), 1))
        def get_sk_delta_normals_from_attribute(attribute, is_color, out):
            if is_color:
                attribute.data.foreach_get('color', static_attribute_colors.ravel())
                loop_delta_normals = static_attribute_colors[:,:3]
                loop_delta_normals -= color_offset
                loop_delta_normals *= 2
            else:
                loop_delta_normals = static_attribute_colors[:,:3]
                attribute.data.foreach_get('vector', loop_delta_normals.ravel())
            
            vert_delta_normals = out
            vert_delta_normals.fill(0)

            # for loop in me.loops: vert_delta_normals[loop.vertex_index] += loop_delta_normals[loop.index]
            np.add.at(vert_delta_normals, loops_vert_index, loop_delta_normals) # XXX Slower but handles edge cases better
            #vert_delta_normals[loops_vert_index] += loop_delta_normals # XXX Only first loop's value will be kept
            
            # for delta_normal in vert_delta_normals: delta_normal /= loops_per_vertex[vert.index]
            vert_delta_normals *= loops_per_vertex_reciprocal

            return out #.tolist()

        if me.has_custom_normals:
            basis_custom_normals = np.array(custom_normals, dtype=float)
            static_loop_normals = np.empty((len(me.loops), 3), dtype=float)
            static_vert_lengths = np.empty((len(me.vertices), 1), dtype=float)
        def get_sk_delta_normals_from_custom_normals(shape_key, out):
            vert_custom_normals = out
            vert_custom_normals.fill(0)
            
            loop_custom_normals = static_loop_normals
            np.copyto(loop_custom_normals.ravel(), shape_key.normals_split_get())
            
            # for loop in me.loops: vert_delta_normals[loop.vertex_index] += loop_delta_normals[loop.index]
            if not self.did_split_sharp:
                # XXX Slower
                np.add.at(vert_custom_normals, loops_vert_index, loop_custom_normals)
                vert_len_sq = get_lengths_squared(vert_custom_normals, out=static_vert_lengths)
                vert_len = np.sqrt(vert_len_sq, out=vert_len_sq)
                np.reciprocal(vert_len, out=vert_len)
                vert_custom_normals *= vert_len #.reshape((*vert_len.shape, 1))
            else:
                # loop normals should be the same per-vertex unless there is a sharp edge 
                # or a flat shaded face, but all sharp edges were split, so this method is fine
                # (and Flat shaded faces just won't be supported)
                vert_custom_normals[loops_vert_index] += loop_custom_normals # Only first loop's value will be kept

            vert_custom_normals -= basis_custom_normals
            return out
        
        if not me.has_custom_normals:
            basis_normals = np.empty((len(me.vertices), 3), dtype=float)
            me.vertices.foreach_get('normal', basis_normals.ravel())
        def get_sk_delta_normals_from_normals(shape_key, out):
            vert_normals = out
            np.copyto(vert_normals.ravel(), shape_key.normals_vertex_get())
            vert_delta_normals = np.subtract(vert_normals, basis_normals, out=out)
            return out

        basis_co = np.empty((len(me.vertices), 3), dtype=float)
        me.vertices.foreach_get('co', basis_co.ravel())
        def get_sk_delta_coordinates(shape_key, out):
            delta_coordinates = out
            shape_key.data.foreach_get('co', delta_coordinates.ravel())
            delta_coordinates -= basis_co
            return out

        static_array_sq = np.empty((len(me.vertices), 3), dtype=float)
        def get_lengths_squared(vectors, out):
            np.power(vectors, 2, out=static_array_sq)
            np.sum(static_array_sq, axis=1, out=out.ravel())
            return out

        def write_morph(morph, name):
            common.write_str(writer, 'morph')
            common.write_str(writer, name)
            writer.write(struct.pack('<i', len(morph)))
            for v_index, vec, normal in morph:
                vec    = compat.convert_bl_to_cm_space(vec   )
                normal = compat.convert_bl_to_cm_space(normal)
                writer.write(struct.pack('<H', v_index))
                writer.write(struct.pack('<3f', *vec[:3]))
                writer.write(struct.pack('<3f', *normal[:3]))
        
        # accessing operator properties via "self.x" is SLOW, so store some here
        self__export_shapekey_normals = self.export_shapekey_normals
        self__use_shapekey_colors = self.use_shapekey_colors
        self__shapekey_normals_blend = self.shapekey_normals_blend
        self__scale = self.scale
        
        co_diff_threshold = self.shapekey_threshold / 5
        co_diff_threshold_squared = co_diff_threshold * co_diff_threshold
        no_diff_threshold = self.shapekey_threshold * 10
        no_diff_threshold_squared = no_diff_threshold * no_diff_threshold
        
        # shared arrays
        delta_coordinates  = np.empty((len(me.vertices), 3), dtype=float)
        vert_delta_normals = np.empty((len(me.vertices), 3), dtype=float)
        loop_delta_normals = np.empty((len(me.loops   ), 3), dtype=float)

        delta_co_lensq = np.empty((len(me.vertices)), dtype=float)
        delta_no_lensq = np.empty((len(me.vertices)), dtype=float)

        if not self.export_shapekey_normals:
            vert_delta_normals.fill(0)
            delta_no_lensq.fill(0)

        # HEAVY LOOP
        for shape_key in me.shape_keys.key_blocks[1:]:
            morph = []

            if self__export_shapekey_normals and self__use_shapekey_colors:
                normals_color, attrubute_is_color = find_normals_attribute(f'{shape_key.name}_delta_normals')

            if self__export_shapekey_normals:
                if self__use_shapekey_colors and not normals_color is None:
                    sk_delta_normals = get_sk_delta_normals_from_attribute(normals_color, attrubute_is_color, out=vert_delta_normals)
                elif me.has_custom_normals:
                    sk_delta_normals = get_sk_delta_normals_from_custom_normals(shape_key, out=vert_delta_normals)
                    sk_delta_normals *= self__shapekey_normals_blend
                else:
                    sk_delta_normals = get_sk_delta_normals_from_normals(shape_key, out=vert_delta_normals)
                    sk_delta_normals *= self__shapekey_normals_blend
                
                sk_no_lensq = get_lengths_squared(sk_delta_normals, out=delta_no_lensq)
            else:
                sk_delta_normals = vert_delta_normals
                sk_no_lensq = delta_no_lensq

            sk_co_diffs = get_sk_delta_coordinates(shape_key, out=delta_coordinates)
            sk_co_diffs *= self__scale # scale before getting lengths
            sk_co_lensq = get_lengths_squared(sk_co_diffs, out=delta_co_lensq)

            # SUPER HEAVY LOOP
            outvert_index = 0
            for i in range(len(me.vertices)):
                if sk_co_lensq[i] >= co_diff_threshold_squared or sk_no_lensq[i] >= no_diff_threshold_squared:
                    morph += [ (outvert_index+j, sk_co_diffs[i], sk_delta_normals[i]) for j in range(len(vert_uvs[i])) ]
                else:
                    # ignore because change is too small (greatly lowers file size)
                    pass
                outvert_index += len(vert_uvs[i])

            if prefs.skip_shapekey and not len(morph):
                continue
            else:
                write_morph(morph, shape_key.name)

    def write_tangents(self, writer, me):
        if len(me.uv_layers) < 1:
            return

        num_loops = len(me.loops)

    def parse_triangles(self, bm, ob, uv_lay, vert_iuv, vert_indices):
        def vert_index_from_loops(loops):
            """vert_index generator"""
            for loop in loops:
                uv = loop[uv_lay].uv
                v_index = loop.vert.index
                vert_index = vert_iuv.get(hash((v_index, uv.x, uv.y)))
                if vert_index is None:
                    vert_index = vert_indices.get(v_index, 0)
                yield vert_index

        triangles = []
        for mate_index, slot in enumerate(ob.material_slots):
            tris_faces = []
            for face in bm.faces:
                if face.material_index != mate_index:
                    continue
                if len(face.verts) == 3:
                    tris_faces.extend(vert_index_from_loops(reversed(face.loops)))
                elif len(face.verts) == 4 and self.is_convert_tris:
                    v1 = face.loops[0].vert.co - face.loops[2].vert.co
                    v2 = face.loops[1].vert.co - face.loops[3].vert.co
                    if v1.length < v2.length:
                        f1 = [0, 1, 2]
                        f2 = [0, 2, 3]
                    else:
                        f1 = [0, 1, 3]
                        f2 = [1, 2, 3]
                    faces, faces2 = [], []
                    for i, vert_index in enumerate(vert_index_from_loops(reversed(face.loops))):
                        if i in f1:
                            faces.append(vert_index)
                        if i in f2:
                            faces2.append(vert_index)
                    tris_faces.extend(faces)
                    tris_faces.extend(faces2)
                elif 5 <= len(face.verts) and self.is_convert_tris:
                    face_count = len(face.verts) - 2

                    tris = []
                    seek_min, seek_max = 0, len(face.verts) - 1
                    for i in range(face_count):
                        if not i % 2:
                            tris.append([seek_min, seek_min + 1, seek_max])
                            seek_min += 1
                        else:
                            tris.append([seek_min, seek_max - 1, seek_max])
                            seek_max -= 1

                    tris_indexs = [[] for _ in range(len(tris))]
                    for i, vert_index in enumerate(vert_index_from_loops(reversed(face.loops))):
                        for tris_index, points in enumerate(tris):
                            if i in points:
                                tris_indexs[tris_index].append(vert_index)

                    tris_faces.extend(p for ps in tris_indexs for p in ps)

            triangles.append(tris_faces)
        return triangles

    def calc_tangents(self, cm_tris, cm_verts, cm_norms, cm_uvs):
        count = len(cm_verts)
        tan1 = [None] * count
        tan2 = [None] * count
        for i in range(0, count):
            tan1[i] = mathutils.Vector((0, 0, 0))
            tan2[i] = mathutils.Vector((0, 0, 0))

        for tris in cm_tris:
            tri_len = len(tris)
            tri_idx = 0
            while tri_idx < tri_len:
                i1, i2, i3 = tris[tri_idx], tris[tri_idx + 1], tris[tri_idx + 2]
                v1, v2, v3 = cm_verts[i1], cm_verts[i2], cm_verts[i3]
                w1, w2, w3 = cm_uvs[i1], cm_uvs[i2], cm_uvs[i3]

                a1 = v2 - v1
                a2 = v3 - v1
                s1 = w2 - w1
                s2 = w3 - w1
                
                r_inverse = (s1.x * s2.y - s2.x * s1.y)

                if r_inverse != 0:
                    # print("i1 = {i1}   i2 = {i2}   i3 = {i3}".format(i1=i1, i2=i2, i3=i3))
                    # print("v1 = {v1}   v2 = {v2}   v3 = {v3}".format(v1=v1, v2=v2, v3=v3))
                    # print("w1 = {w1}   w2 = {w2}   w3 = {w3}".format(w1=w1, w2=w2, w3=w3))

                    # print("a1 = {a1}   a2 = {a2}".format(a1=a1, a2=a2))
                    # print("s1 = {s1}   s2 = {s2}".format(s1=s1, s2=s2))
                    
                    # print("r_inverse = ({s1x} * {s2y} - {s2x} * {s1y}) = {r_inverse}".format(r_inverse=r_inverse, s1x=s1.x, s1y=s1.y, s2x=s2.x, s2y=s2.y))
                                                
                    r = 1.0 / r_inverse
                    sdir = mathutils.Vector(((s2.y * a1.x - s1.y * a2.x) * r, (s2.y * a1.y - s1.y * a2.y) * r, (s2.y * a1.z - s1.y * a2.z) * r))
                    tan1[i1] += sdir
                    tan1[i2] += sdir
                    tan1[i3] += sdir

                    tdir = mathutils.Vector(((s1.x * a2.x - s2.x * a1.x) * r, (s1.x * a2.y - s2.x * a1.y) * r, (s1.x * a2.z - s2.x * a1.z) * r))
                    tan2[i1] += tdir
                    tan2[i2] += tdir
                    tan2[i3] += tdir

                tri_idx += 3

        tangents = [None] * count
        for i in range(0, count):
            n = cm_norms[i]
            ti = tan1[i]
            t = (ti - n * n.dot(ti)).normalized()

            c = n.cross(ti)
            val = c.dot(tan2[i])
            w = 1.0 if val < 0 else -1.0
            tangents[i] = (-t.x, t.y, t.z, w)

        return tangents

    def armature_bone_data_parser(self, context, ob):
        """アーマチュアを解析してBoneDataを返す"""
        arm = ob.data
        
        pre_active = compat.get_active(context)
        pre_mode = ob.mode

        compat.set_active(context, ob)
        bpy.ops.object.mode_set(mode='EDIT')

        bones = []
        bone_name_indices = {}
        already_bone_names = []
        bones_queue = arm.edit_bones[:]
        while len(bones_queue):
            bone = bones_queue.pop(0)

            if not bone.parent:
                already_bone_names.append(bone.name)
                bones.append(bone)
                bone_name_indices[bone.name] = len(bone_name_indices)
                continue
            elif bone.parent.name in already_bone_names:
                already_bone_names.append(bone.name)
                bones.append(bone)
                bone_name_indices[bone.name] = len(bone_name_indices)
                continue

            bones_queue.append(bone)

        bone_data = []
        for bone in bones:

            # Also check for UnknownFlag for backwards compatibility
            is_scl_bone = bone['cm3d2_scl_bone'] if 'cm3d2_scl_bone' in bone \
                     else bone['UnknownFlag']    if 'UnknownFlag'    in bone \
                     else 0 
            parent_index = bone_name_indices[bone.parent.name] if bone.parent else -1

            mat = bone.matrix.copy()
            
            if bone.parent:
                mat = compat.convert_bl_to_cm_bone_rotation(mat)
                mat = compat.mul(bone.parent.matrix.inverted(), mat)
                mat = compat.convert_bl_to_cm_bone_space(mat)
            else:
                mat = compat.convert_bl_to_cm_bone_rotation(mat)
                mat = compat.convert_bl_to_cm_space(mat)
            
            co = mat.to_translation() * self.scale
            rot = mat.to_quaternion()
            
            #if bone.parent:
            #    co.x, co.y, co.z = -co.y, -co.x, co.z
            #    rot.w, rot.x, rot.y, rot.z = rot.w, rot.y, rot.x, -rot.z
            #else:
            #    co.x, co.y, co.z = -co.x, co.z, -co.y
            #
            #    fix_quat  = compat.Z_UP_TO_Y_UP_QUAT    #mathutils.Euler((0, 0, math.radians(-90)), 'XYZ').to_quaternion()
            #    fix_quat2 = compat.BLEND_TO_OPENGL_QUAT #mathutils.Euler((math.radians(-90), 0, 0), 'XYZ').to_quaternion()
            #    rot = compat.mul3(rot, fix_quat, fix_quat2)
            #    #rot = compat.mul3(fix_quat2, rot, fix_quat)
            #
            #    rot.w, rot.x, rot.y, rot.z = -rot.y, -rot.z, -rot.x, rot.w
            
            # luvoid : I copied this from the Bone-Util Addon by trzr
            #if bone.parent:
            #    co.x, co.y, co.z = -co.y, co.z, co.x
            #    rot.w, rot.x, rot.y, rot.z = rot.w, rot.y, -rot.z, -rot.x
            #else:
            #    co.x, co.y, co.z = -co.x, co.z, -co.y
            #    
            #    rot = compat.mul(rot, mathutils.Quaternion((0, 0, 1), math.radians(90)))
            #    rot.w, rot.x, rot.y, rot.z = -rot.w, -rot.x, rot.z, -rot.y
            
            #opengl_mat = compat.convert_blend_z_up_to_opengl_y_up_mat4(bone.matrix)
            #
            #if bone.parent:
            #    opengl_mat = compat.mul(compat.convert_blend_z_up_to_opengl_y_up_mat4(bone.parent.matrix).inverted(), opengl_mat)
            #
            #co = opengl_mat.to_translation() * self.scale
            #rot = opengl_mat.to_quaternion()

            data = {
                'name': common.encode_bone_name(bone.name, self.is_convert_bone_weight_names),
                'scl': is_scl_bone,
                'parent_index': parent_index,
                'co': co.copy(),
                'rot': rot.copy(),
            }
            scale = arm.edit_bones[bone.name].get('cm3d2_bone_scale')
            if scale:
                data['scale'] = scale
            bone_data.append(data)
        
        bpy.ops.object.mode_set(mode=pre_mode)
        compat.set_active(context, pre_active)
        return bone_data

    @staticmethod
    def bone_data_parser(container):
        """BoneData テキストをパースして辞書を要素とするリストを返す"""
        bone_data = []
        bone_name_indices = {}
        for line in container:
            data = line.split(',')
            if len(data) < 5:
                continue

            parent_name = data[2]
            if parent_name.isdigit():
                parent_index = int(parent_name)
            else:
                parent_index = bone_name_indices.get(parent_name, -1)

            bone_datum = {
                'name': data[0],
                'scl': int(data[1]),
                'parent_index': parent_index,
                'co': list(map(float, data[3].split())),
                'rot': list(map(float, data[4].split())),
            }
            # scale info (for version 2001 or later)
            if len(data) >= 7:
                if data[5] == '1':
                    bone_scale = data[6]
                    bone_datum['scale'] = list(map(float, bone_scale.split()))
            bone_data.append(bone_datum)
            bone_name_indices[data[0]] = len(bone_name_indices)
        return bone_data

    def armature_local_bone_data_parser(self, ob):
        """アーマチュアを解析してBoneDataを返す"""
        arm = ob.data

        # XXX Instead of just adding all bones, only bones / bones-with-decendants 
        #     that have use_deform == True or mathcing vertex groups should be used
        bones = []
        bone_name_indices = {}
        already_bone_names = []
        bones_queue = arm.bones[:]
        while len(bones_queue):
            bone = bones_queue.pop(0)

            if not bone.parent:
                already_bone_names.append(bone.name)
                bones.append(bone)
                bone_name_indices[bone.name] = len(bone_name_indices)
                continue
            elif bone.parent.name in already_bone_names:
                already_bone_names.append(bone.name)
                bones.append(bone)
                bone_name_indices[bone.name] = len(bone_name_indices)
                continue

            bones_queue.append(bone)

        local_bone_data = []
        for bone in bones:
            mat = bone.matrix_local.copy()
            mat = compat.mul(mathutils.Matrix.Scale(-1, 4, (1, 0, 0)), mat)
            mat = compat.convert_bl_to_cm_bone_rotation(mat)
            pos = mat.translation.copy()
            
            mat.transpose()
            mat.row[3] = (0.0, 0.0, 0.0, 1.0)
            pos = compat.mul(mat.to_3x3(), pos)
            pos *= -self.scale
            mat.translation = pos
            mat.transpose()
            
            #co = mat.to_translation() * self.scale
            #rot = mat.to_quaternion()
            #
            #co.rotate(rot.inverted())
            #co.x, co.y, co.z = co.y, co.x, -co.z
            #
            #fix_quat = mathutils.Euler((0, 0, math.radians(-90)), 'XYZ').to_quaternion()
            #rot = compat.mul(rot, fix_quat)
            #rot.w, rot.x, rot.y, rot.z = -rot.z, -rot.y, -rot.x, rot.w
            #
            #co_mat = mathutils.Matrix.Translation(co)
            #rot_mat = rot.to_matrix().to_4x4()
            #mat = compat.mul(co_mat, rot_mat)
            #
            #copy_mat = mat.copy()
            #mat[0][0], mat[0][1], mat[0][2], mat[0][3] = copy_mat[0][0], copy_mat[1][0], copy_mat[2][0], copy_mat[3][0]
            #mat[1][0], mat[1][1], mat[1][2], mat[1][3] = copy_mat[0][1], copy_mat[1][1], copy_mat[2][1], copy_mat[3][1]
            #mat[2][0], mat[2][1], mat[2][2], mat[2][3] = copy_mat[0][2], copy_mat[1][2], copy_mat[2][2], copy_mat[3][2]
            #mat[3][0], mat[3][1], mat[3][2], mat[3][3] = copy_mat[0][3], copy_mat[1][3], copy_mat[2][3], copy_mat[3][3]

            mat_array = []
            for vec in mat:
                mat_array.extend(vec[:])
            
            local_bone_data.append({
                'name': common.encode_bone_name(bone.name, self.is_convert_bone_weight_names),
                'matrix': mat_array,
            })
        return local_bone_data

    @staticmethod
    def local_bone_data_parser(container):
        """LocalBoneData テキストをパースして辞書を要素とするリストを返す"""
        local_bone_data = []
        for line in container:
            data = line.split(',')
            if len(data) != 2:
                continue
            local_bone_data.append({
                'name': data[0],
                'matrix': list(map(float, data[1].split())),
            })
        return local_bone_data

    @staticmethod
    def indexed_data_generator(container, prefix='', max_index=9**9, max_pass=50):
        """コンテナ内の数値インデックスをキーに持つ要素を昇順に返すジェネレーター"""
        pass_count = 0
        for i in range(max_index):
            name = prefix + str(i)
            if name not in container:
                pass_count += 1
                if max_pass < pass_count:
                    return
                continue
            yield container[name]

