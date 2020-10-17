# -*- coding: utf-8 -*-
import bpy
import re
import struct
import os
import mathutils
from typing import Any, Optional


# LEGAY: version less than 2.80
IS_LEGACY = not hasattr(bpy.app, 'version') or bpy.app.version < (2, 80)


class BlRegister():
    idnames = set()
    classes = []

    def __init__(self, *args, **kwargs):
        self.make_annotation = kwargs.get('make_annotation', True)
        self.use_bl_attr = kwargs.get('use_bl_attr', True)
        self.only_legacy = kwargs.get('only_legacy', False)
        self.only_latest = kwargs.get('only_latest', False)

    def __call__(self, cls):

        if hasattr(cls, 'bl_idname'):
            bl_idname = cls.bl_idname
        else:
            if self.use_bl_attr:
                bl_ctx = getattr(cls, 'bl_context', '')
                bl_idname = "{}{}{}{}".format(cls.bl_space_type, cls.bl_region_type, bl_ctx, cls.bl_label)
            else:
                bl_idname = cls.__qualname__

        if self.only_legacy:
            if IS_LEGACY:
                BlRegister.add(bl_idname, cls)
        elif self.only_latest:
            if IS_LEGACY is False:
                BlRegister.add(bl_idname, cls)
        else:
            BlRegister.add(bl_idname, cls)

        if self.make_annotation:
            cls = make_annotations(cls)
        return cls

    @classmethod
    def add(cls: type, bl_idname: str, op_class: type) -> None:
        if bl_idname in cls.idnames:
            raise RuntimeError("Duplicate bl_idname: %s" % bl_idname)

        cls.idnames.add(bl_idname)
        cls.classes.append(op_class)

    @classmethod
    def register(cls):
        for cls1 in cls.classes:
            bpy.utils.register_class(cls1)

    @classmethod
    def unregister(cls):
        for cls1 in reversed(cls.classes):
            bpy.utils.unregister_class(cls1)

    @classmethod
    def cleanup(cls):
        cls.classes.clear()
        cls.idnames.clear()


def make_annotations(cls):
    if IS_LEGACY:
        return cls

    cls_props = {}
    for k, v in cls.__dict__.items():
        if isinstance(v, tuple):
            cls_props[k] = v

    annos = cls.__dict__.get('__annotations__')  # type: dict[str, type]
    if annos is None:
        annos = {}
        setattr(cls, '__annotations__', annos)

    for k, v in cls_props.items():
        annos[k] = v
        delattr(cls, k)

    # 親クラスを辿ってアノテーションを生成
    for bc in cls.__bases__:
        # bpyのタイプやbuiltinsの場合はスキップ
        if bc.__module__ in ['bpy_types', 'builtins']:
            continue
        make_annotations(bc)

    return cls


def layout_split(layout, factor=0.0, align=False):
    if IS_LEGACY:
        return layout.split(percentage=factor, align=align)

    return layout.split(factor=factor, align=align)


def get_active():
    if IS_LEGACY:
        return bpy.context.scene.objects.active

    return bpy.context.view_layer.objects.active


def set_active(context, obj):
    if IS_LEGACY:
        context.scene.objects.active = obj
    else:
        context.view_layer.objects.active = obj


def get_active_uv(me):
    if IS_LEGACY:
        uvs = me.uv_textures
    else:
        uvs = me.uv_layers
    return uvs.active


def set_display_type(ob, disp_type):
    if IS_LEGACY:
        ob.draw_type = disp_type
    else:
        ob.display_type = disp_type


def get_select(obj: bpy.types.Object) -> bool:
    if IS_LEGACY:
        return obj.select

    return obj.select_get()


def set_select(obj: bpy.types.Object, select: bool) -> None:
    if IS_LEGACY:
        obj.select = select
    else:
        obj.select_set(select)


def is_select(*args) -> bool:
    """すべてが選択状態であるかを判定する."""
    if IS_LEGACY:
        return all(arg.select for arg in args)

    return all(arg.select_get() for arg in args)


def get_hide(obj: bpy.types.Object) -> bool:
    if IS_LEGACY:
        return obj.hide

    return obj.hide_viewport


def set_hide(obj: bpy.types.Object, hide: bool):
    if IS_LEGACY:
        obj.hide = hide

    else:
        obj.hide_viewport = hide


def link(scene: bpy.types.Scene, obj: bpy.types.Object):
    if IS_LEGACY:
        scene.objects.link(obj)
    else:
        scene.collection.objects.link(obj)


def unlink(scene: bpy.types.Scene, obj: bpy.types.Object):
    if IS_LEGACY:
        scene.objects.unlink(obj)
    else:
        scene.collection.objects.unlink(obj)


def get_cursor_loc(context):
    if IS_LEGACY:
        return context.space_data.cursor_location
    else:
        return context.scene.cursor.location


def get_lights(blend_data):
    if IS_LEGACY:
        return blend_data.iamps
    else:
        return blend_data.lights


def mul(x, y):
    if IS_LEGACY:
        return x * y

    return x @ y


def mul3(x, y, z):
    if IS_LEGACY:
        return x * y * z

    return x @ y @ z


def mul4(w, x, y, z):
    if IS_LEGACY:
        return w * x * y * z

    return w @ x @ y @ z
    
def opengl_quat_to_mat3(q):
    w = q.w
    x = q.x
    y = q.y
    z = q.z
    
    return mathutils.Matrix(
        [( 1 - 2*y*y - 2*z*z,     2*x*y + 2*w*z,     2*x*z - 2*w*y), 
         (     2*x*y - 2*w*z, 1 - 2*x*x - 2*z*z,     2*y*z + 2*w*x), 
         (     2*x*z + 2*w*y,     2*y*z - 2*w*x, 1 - 2*x*x - 2*y*y)]
    )

def opengl_to_blend_mat4(mat4):
    return mul(
        mat4,
        mathutils.Matrix(
            [( 1,  0,  0,  0), 
             ( 0,  0,  1,  0), 
             ( 0,  1,  0,  0),
             ( 0,  0,  0,  1)]
        )
    )
    
def set_bone_matrix(bone, mat):
    bone.matrix = mat
    if not IS_LEGACY and isinstance(bone, bpy.types.EditBone):
        #print("Bone align_roll: ", (mat[0][0],mat[1][0],mat[2][0]))
        bone.align_roll((mat[0][0],mat[1][0],mat[2][0]))


LEGACY_ICONS = {
    'ADD': 'ZOOMIN',
    'REMOVE': 'ZOOMOUT',
    'ARROW_LEFTRIGHT': 'MAN_SCALE',
    'FILE_FOLDER': 'FILESEL',
    'FILE_NEW': 'NEW',
    'FILEBROWSER': 'FILESEL',
    'FILE_IMAGE': 'IMAGE_COL',
    'LIGHT_HEMI': 'LAMP_HEMI',
    'MOD_DATA_TRANSFER': 'RETOPO',
    'BRUSH_SOFTEN': 'MATCAP_19',
    'CLIPUV_DEHLT': 'MATCAP_24',
    'MESH_CIRCLE': 'MATCAP_24',
    'PIVOT_INDIVIDUAL': 'ROTATECOLLECTION',
    'SHADING_SOLID': 'SOLID',
    'SHADING_WIRE': 'WIRE',
    'SHADING_RENDERED': 'SMOOTH',
    'SHADING_TEXTURE': 'TEXTURE_SHADED',
    'NORMALS_VERTEX': 'MATCAP_23',
    'VIS_SEL_01': 'VISIBLE_IPO_OFF',
    'VIS_SEL_11': 'VISIBLE_IPO_ON',
    # 'BRUSH_TEXFILL': 'MATCAP_05',
    'NODE_MATERIAL': 'MATCAP_05',
    'HOLDOUT_ON': 'MATCAP_13',
    'CON_LOCLIKE': 'MAN_TRANS',
    'CON_ROTLIKE': 'MAN_ROT',
    'CON_SIZELIKE': 'MAN_SCALE',
}


def icon(key):
    if IS_LEGACY:
        # 対応アイコンがdictにない場合はNONEとする
        return LEGACY_ICONS.get(key, 'NONE')

    return key


def region_type():
    if IS_LEGACY:
        return 'TOOLS'

    return 'UI'


def pref_type():
    if IS_LEGACY:
        return 'USER_PREFERENCES'

    return 'PREFERENCES'


def get_prefs(context):
    if IS_LEGACY:
        return context.user_preferences

    return context.preferences


def get_system(context):
    if IS_LEGACY:
        return get_prefs(context).system

    return get_prefs(context).view


def get_tex_image(context, node_name=None):
    if IS_LEGACY:
        if hasattr(context, 'texture'):
            tex = context.texture
            if tex:
                return tex.image
    else:
        mate = context.material
        if mate and mate.use_nodes:
            node = mate.node_tree.nodes.get(node_name)
            if node and node.type == 'TEX_IMAGE':
                return node.image

    return None
