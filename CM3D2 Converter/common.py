import os
import re
import math
import struct
import shutil
import winreg
import bpy
import bmesh
import mathutils
from . import fileutil
from . import compat
from . import cm3d2_data

# アドオン情報
bl_info = {}
ADDON_NAME = "CM3D2 Converter"
BASE_PATH_TEX = "Assets/texture/texture/"
BRANCH = "bl_28"
URL_REPOS = "https://github.com/luvoid/Blender-CM3D2-Converter/"
URL_ATOM = URL_REPOS + "commits/" + BRANCH + ".atom"
URL_MODULE = URL_REPOS + "archive/" + BRANCH + ".zip"
KISS_ICON = None
PREFS = None
TRUE_LOCALE = None # Set by __init__.register()
LOCALE      = None # The closest locale to TRUE_LOCALE available for translation 
preview_collections = {}
texpath_dict = {}


re_png = re.compile(r"\.[Pp][Nn][Gg](\.\d{3})?$")
re_serial = re.compile(r"(\.\d{3})$")
re_prefix = re.compile(r"^[\/\.]*")
re_path_prefix = re.compile(r"^assets/", re.I)
re_ext_png = re.compile(r"\.png$", re.I)
re_bone1 = re.compile(r"([_ ])\*([_ ].*)\.([rRlL])$")
re_bone2 = re.compile(r"([_ ])([rRlL])([_ ].*)$")


# このアドオンの設定値群を呼び出す
def preferences():
    global PREFS
    if PREFS is None:
        PREFS = compat.get_prefs(bpy.context).addons[__package__].preferences
    return PREFS


def kiss_icon():
    global KISS_ICON
    if KISS_ICON is None:
        KISS_ICON = preview_collections['main']['KISS'].icon_id
    return KISS_ICON


# データ名末尾の「.001」などを削除
def remove_serial_number(name, enable=True):
    return re_serial.sub('', name) if enable else name


# データ名末尾の「.001」などが含まれるか判定
def has_serial_number(name):
    return re_serial.search(name) is not None


# 文字列の左右端から空白を削除
def line_trim(line, enable=True):
    return line.strip(' 　\t\r\n') if enable else line


# CM3D2専用ファイル用の文字列書き込み
def write_str(file, raw_str):
    b_str = format(len(raw_str.encode('utf-8')), 'b')
    for i in range(9):
        if 7 < len(b_str):
            file.write(struct.pack('<B', int("1" + b_str[-7:], 2)))
            b_str = b_str[:-7]
        else:
            file.write(struct.pack('<B', int(b_str, 2)))
            break
    file.write(raw_str.encode('utf-8'))

def pack_str(buffer, raw_str):
    b_str = format(len(raw_str.encode('utf-8')), 'b')
    for i in range(9):
        if 7 < len(b_str):
            buffer = buffer + struct.pack('<B', int("1" + b_str[-7:], 2))
            b_str = b_str[:-7]
        else:
            buffer = buffer + struct.pack('<B', int(b_str, 2))
            break
    buffer = buffer + raw_str.encode('utf-8')
    return buffer


# CM3D2専用ファイル用の文字列読み込み
def read_str(file, total_b=""):
    for i in range(9):
        b_str = format(struct.unpack('<B', file.read(1))[0], '08b')
        total_b = b_str[1:] + total_b
        if b_str[0] == '0':
            break
    return file.read(int(total_b, 2)).decode('utf-8')


# ボーン/ウェイト名を Blender → CM3D2
def encode_bone_name(name, enable=True):
    return re.sub(r'([_ ])\*([_ ].*)\.([rRlL])$', r'\1\3\2', name) if enable and name.count('*') == 1 else name


# ボーン/ウェイト名を CM3D2 → Blender
def decode_bone_name(name, enable=True):
    return re.sub(r'([_ ])([rRlL])([_ ].*)$', r'\1*\3.\2', name) if enable else name


# CM3D2用マテリアルを設定に合わせて装飾
def decorate_material_old(mate, enable=True, me=None, mate_index=-1):
    if not compat.IS_LEGACY or not enable or 'shader1' not in mate:
        return

    shader = mate['shader1']
    if 'CM3D2/Man' == shader:
        mate.use_shadeless = True
        mate.diffuse_color = (0, 1, 1)
    elif 'CM3D2/Mosaic' == shader:
        mate.use_transparency = True
        mate.transparency_method = 'RAYTRACE'
        mate.alpha = 0.25
        mate.raytrace_transparency.ior = 2
    elif 'CM3D2_Debug/Debug_CM3D2_Normal2Color' == shader:
        mate.use_tangent_shading = True
        mate.diffuse_color = (0.5, 0.5, 1)

    else:
        if '/Toony_' in shader:
            mate.diffuse_shader = 'TOON'
            mate.diffuse_toon_smooth = 0.01
            mate.diffuse_toon_size = 1.2
        if 'Trans' in shader:
            mate.use_transparency = True
            mate.alpha = 0.0
            mate.texture_slots[0].use_map_alpha = True
        if 'Unlit/' in shader:
            mate.emit = 0.5
        if '_NoZ' in shader:
            mate.offset_z = 9999

    is_colored = False
    is_textured = [False, False, False, False]
    rimcolor, rimpower, rimshift = mathutils.Color((1, 1, 1)), 0.0, 0.0
    for slot in mate.texture_slots:
        if not slot or not slot.texture:
            continue

        tex = slot.texture
        tex_name = remove_serial_number(tex.name)
        slot.use_map_color_diffuse = False

        if tex_name == '_MainTex':
            slot.use_map_color_diffuse = True
            img = getattr(tex, 'image')
            if img and len(img.pixels):
                if me:
                    color = mathutils.Color(get_image_average_color_uv(img, me, mate_index)[:3])
                else:
                    color = mathutils.Color(get_image_average_color(img)[:3])
                mate.diffuse_color = color
                is_colored = True

        elif tex_name == '_RimColor':
            rimcolor = slot.color[:]
            if not is_colored:
                mate.diffuse_color = slot.color[:]
                mate.diffuse_color.v += 0.5

        elif tex_name == '_Shininess':
            mate.specular_intensity = slot.diffuse_color_factor

        elif tex_name == '_RimPower':
            rimpower = slot.diffuse_color_factor

        elif tex_name == '_RimShift':
            rimshift = slot.diffuse_color_factor

        for index, name in enumerate(['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon']):
            if tex_name == name:
                img = getattr(tex, 'image')
                if img and len(tex.image.pixels):
                    is_textured[index] = tex

        set_texture_color(slot)

    # よりオリジナルに近く描画するノード作成
    if all(is_textured):
        mate.use_nodes = True
        mate.use_shadeless = True

        node_tree = mate.node_tree
        for node in node_tree.nodes[:]:
            node_tree.nodes.remove(node)

        mate_node = node_tree.nodes.new('ShaderNodeExtendedMaterial')
        mate_node.location = (0, 0)
        mate_node.material = mate

        if "CM3D2 Shade" in bpy.context.blend_data.materials:
            shade_mate = bpy.context.blend_data.materials["CM3D2 Shade"]
        else:
            shade_mate = bpy.context.blend_data.materials.new("CM3D2 Shade")
        shade_mate.diffuse_color = (1, 1, 1)
        shade_mate.diffuse_intensity = 1
        shade_mate.specular_intensity = 1
        shade_mate_node = node_tree.nodes.new('ShaderNodeExtendedMaterial')
        shade_mate_node.location = (234.7785, -131.8243)
        shade_mate_node.material = shade_mate

        toon_node = node_tree.nodes.new('ShaderNodeValToRGB')
        toon_node.location = (571.3662, -381.0965)
        toon_img = is_textured[1].image
        toon_w, toon_h = toon_img.size[0], toon_img.size[1]
        for i in range(32 - 2):
            toon_node.color_ramp.elements.new(0.0)
        for i in range(32):
            pos = i / (32 - 1)
            toon_node.color_ramp.elements[i].position = pos
            x = int((toon_w / (32 - 1)) * i)
            pixel_index = x * toon_img.channels
            toon_node.color_ramp.elements[i].color = toon_img.pixels[pixel_index: pixel_index + 4]
        toon_node.color_ramp.interpolation = 'EASE'

        shadow_rate_node = node_tree.nodes.new('ShaderNodeValToRGB')
        shadow_rate_node.location = (488.2785, 7.8446)
        shadow_rate_img = is_textured[3].image
        shadow_rate_w, shadow_rate_h = shadow_rate_img.size[0], shadow_rate_img.size[1]
        for i in range(32 - 2):
            shadow_rate_node.color_ramp.elements.new(0.0)
        for i in range(32):
            pos = i / (32 - 1)
            shadow_rate_node.color_ramp.elements[i].position = pos
            x = int((shadow_rate_w / (32)) * i)
            pixel_index = x * shadow_rate_img.channels
            shadow_rate_node.color_ramp.elements[i].color = shadow_rate_img.pixels[pixel_index: pixel_index + 4]
        shadow_rate_node.color_ramp.interpolation = 'EASE'

        geometry_node = node_tree.nodes.new('ShaderNodeGeometry')
        geometry_node.location = (323.4597, -810.8045)

        shadow_texture_node = node_tree.nodes.new('ShaderNodeTexture')
        shadow_texture_node.location = (626.0117, -666.0227)
        shadow_texture_node.texture = is_textured[2]

        invert_node = node_tree.nodes.new('ShaderNodeInvert')
        invert_node.location = (805.6814, -132.9144)

        shadow_mix_node = node_tree.nodes.new('ShaderNodeMixRGB')
        shadow_mix_node.location = (1031.2714, -201.5598)

        toon_mix_node = node_tree.nodes.new('ShaderNodeMixRGB')
        toon_mix_node.location = (1257.5538, -308.8037)
        toon_mix_node.blend_type = 'MULTIPLY'
        toon_mix_node.inputs[0].default_value = 1.0

        specular_mix_node = node_tree.nodes.new('ShaderNodeMixRGB')
        specular_mix_node.location = (1473.2079, -382.7421)
        specular_mix_node.blend_type = 'SCREEN'
        specular_mix_node.inputs[0].default_value = mate.specular_intensity

        normal_node = node_tree.nodes.new('ShaderNodeNormal')
        normal_node.location = (912.1372, -590.8748)

        rim_ramp_node = node_tree.nodes.new('ShaderNodeValToRGB')
        rim_ramp_node.location = (1119.0664, -570.0284)
        rim_ramp_node.color_ramp.elements[0].color = list(rimcolor[:]) + [1.0]
        rim_ramp_node.color_ramp.elements[0].position = rimshift
        rim_ramp_node.color_ramp.elements[1].color = (0, 0, 0, 1)
        rim_ramp_node.color_ramp.elements[1].position = (rimshift) + ((1.0 - (rimpower * 0.03333)) * 0.5)

        rim_power_node = node_tree.nodes.new('ShaderNodeHueSaturation')
        rim_power_node.location = (1426.6332, -575.6142)
        # rim_power_node.inputs[2].default_value = rimpower * 0.1

        rim_mix_node = node_tree.nodes.new('ShaderNodeMixRGB')
        rim_mix_node.location = (1724.7024, -451.9624)
        rim_mix_node.blend_type = 'ADD'

        out_node = node_tree.nodes.new('ShaderNodeOutput')
        out_node.location = (1957.4023, -480.5365)

        node_tree.links.new(shadow_mix_node.inputs[1], mate_node.outputs[0])
        node_tree.links.new(shadow_rate_node.inputs[0], shade_mate_node.outputs[3])
        node_tree.links.new(invert_node.inputs[1], shadow_rate_node.outputs[0])
        node_tree.links.new(shadow_mix_node.inputs[0], invert_node.outputs[0])
        node_tree.links.new(toon_node.inputs[0], shade_mate_node.outputs[3])
        node_tree.links.new(shadow_texture_node.inputs[0], geometry_node.outputs[4])
        node_tree.links.new(shadow_mix_node.inputs[2], shadow_texture_node.outputs[1])
        node_tree.links.new(toon_node.inputs[0], shade_mate_node.outputs[3])
        node_tree.links.new(toon_mix_node.inputs[1], shadow_mix_node.outputs[0])
        node_tree.links.new(toon_mix_node.inputs[2], toon_node.outputs[0])
        node_tree.links.new(specular_mix_node.inputs[1], toon_mix_node.outputs[0])
        node_tree.links.new(specular_mix_node.inputs[2], shade_mate_node.outputs[4])
        node_tree.links.new(normal_node.inputs[0], mate_node.outputs[2])
        node_tree.links.new(rim_ramp_node.inputs[0], normal_node.outputs[1])
        node_tree.links.new(rim_power_node.inputs[4], rim_ramp_node.outputs[0])
        node_tree.links.new(rim_mix_node.inputs[2], rim_power_node.outputs[0])
        node_tree.links.new(rim_mix_node.inputs[0], shadow_rate_node.outputs[0])
        node_tree.links.new(rim_mix_node.inputs[1], specular_mix_node.outputs[0])
        node_tree.links.new(out_node.inputs[0], rim_mix_node.outputs[0])
        node_tree.links.new(out_node.inputs[1], mate_node.outputs[1])

        for node in node_tree.nodes[:]:
            compat.set_select(node, False)
        node_tree.nodes.active = mate_node
        node_tree.nodes.active.select = True

    else:
        mate.use_nodes = False
        mate.use_shadeless = False

# CM3D2用マテリアルを設定に合わせて装飾
def decorate_material(mate, enable=True, me=None, mate_index=-1):
    if not enable or 'shader1' not in mate:
        return
    if compat.IS_LEGACY:
        return decorate_material_old(mate, enable=enable, me=me, mate_index=mate_index)

    # luvoid : set properties of the mate
    shader = mate['shader1']
    mate.preview_render_type  = 'FLAT'
    mate.blend_method         = 'BLEND' if 'Trans' in shader else 'OPAQUE'
    mate.use_backface_culling = 'Outline' not in shader

    # luvoid : create cm3d2 shader node group and material output node
    cmnode = None
    if not compat.IS_LEGACY:
        mate.use_nodes = True
        #cm3d2_data.clear_nodes(mate.node_tree.nodes)
        cmtree = bpy.data.node_groups.get('CM3D2 Shader')
        if not cmtree:
            blend_path = os.path.join(os.path.dirname(__file__), "append_data.blend")
            with bpy.data.libraries.load(blend_path) as (data_from, data_to):
                data_to.node_groups = ['CM3D2 Shader']
            cmtree = data_to.node_groups[0]
        cmnode = mate.node_tree.nodes.new('ShaderNodeGroup')
        cmnode.node_tree = cmtree
        matout = mate.node_tree.nodes.new('ShaderNodeOutputMaterial')
        matout.location = (300,0)
        mate.node_tree.links.new(matout.inputs.get('Surface'), cmnode.outputs.get('Surface'))

    for key, node in mate.node_tree.nodes.items():
        if not key.startswith('_'):
            continue
        if type(node) == bpy.types.ShaderNodeTexImage:
            # luvoid : attatch tex node to cmnode sockets
            socket = cmnode.inputs.get(key+" Color")
            if socket:
                mate.node_tree.links.new(socket, node.outputs.get('Color'))
            socket = cmnode.inputs.get(key+" Alpha")
            if socket:
                mate.node_tree.links.new(socket, node.outputs.get('Alpha'))
        else:
            # luvoid : attatch color/float node to cmnode socket
            input_socket = cmnode.inputs.get(key)
            output_socket = node.outputs.get('Color') or node.outputs.get('Value')
            if input_socket and output_socket:
                mate.node_tree.links.new(input_socket, output_socket)

    


# 画像のおおよその平均色を取得
def get_image_average_color(img, sample_count=10):
    if not len(img.pixels):
        return mathutils.Color([0, 0, 0])

    pixel_count = img.size[0] * img.size[1]
    channels = img.channels

    max_s = 0.0
    max_s_color, average_color = mathutils.Color([0, 0, 0]), mathutils.Color([0, 0, 0])
    seek_interval = pixel_count / sample_count
    for sample_index in range(sample_count):

        index = int(seek_interval * sample_index) * channels
        color = mathutils.Color(img.pixels[index: index + 3])
        average_color += color
        if max_s < color.s:
            max_s_color, max_s = color, color.s

    average_color /= sample_count
    output_color = (average_color + max_s_color) / 2
    output_color.s *= 1.5
    return max_s_color


# 画像のおおよその平均色を取得 (UV版)
def get_image_average_color_uv(img, me=None, mate_index=-1, sample_count=10):
    if not len(img.pixels): return mathutils.Color([0, 0, 0])

    img_width, img_height, img_channel = img.size[0], img.size[1], img.channels

    bm = bmesh.new()
    bm.from_mesh(me)
    uv_lay = bm.loops.layers.uv.active
    uvs = [l[uv_lay].uv[:] for f in bm.faces if f.material_index == mate_index for l in f.loops]
    bm.free()

    if len(uvs) <= sample_count:
        return get_image_average_color(img)

    average_color = mathutils.Color([0, 0, 0])
    max_s = 0.0
    max_s_color = mathutils.Color([0, 0, 0])
    seek_interval = len(uvs) / sample_count
    for sample_index in range(sample_count):

        uv_index = int(seek_interval * sample_index)
        x, y = uvs[uv_index]

        x = math.modf(x)[0]
        if x < 0.0:
            x += 1.0
        y = math.modf(y)[0]
        if y < 0.0:
            y += 1.0

        x, y = int(x * img_width), int(y * img_height)

        pixel_index = ((y * img_width) + x) * img_channel
        color = mathutils.Color(img.pixels[pixel_index: pixel_index + 3])

        average_color += color
        if max_s < color.s:
            max_s_color, max_s = color, color.s

    average_color /= sample_count
    output_color = (average_color + max_s_color) / 2
    output_color.s *= 1.5
    return output_color


def get_cm3d2_dir():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\KISS\カスタムメイド3D2') as key:
            return winreg.QueryValueEx(key, 'InstallPath')[0]
    except:
        return None


def get_com3d2_dir():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\KISS\カスタムオーダーメイド3D2') as key:
            return winreg.QueryValueEx(key, 'InstallPath')[0]
    except:
        return None


# CM3D2のインストールフォルダを取得＋α
def default_cm3d2_dir(base_dir, file_name, new_ext):
    if not base_dir:
        prefs = preferences()
        if prefs.cm3d2_path:
            base_dir = os.path.join(prefs.cm3d2_path, "GameData", "*." + new_ext)
        else:
            base_dir = get_cm3d2_dir()
            if base_dir is None:
                base_dir = get_com3d2_dir()

            if base_dir:
                prefs.cm3d2_path = base_dir
                base_dir = os.path.join(base_dir, "GameData", "*." + new_ext)

        if base_dir is None:
            base_dir = "."

    if file_name:
        base_dir = os.path.join(os.path.split(base_dir)[0], file_name)
    base_dir = os.path.splitext(base_dir)[0] + "." + new_ext
    return base_dir


# 一時ファイル書き込みと自動バックアップを行うファイルオブジェクトを返す
def open_temporary(filepath, mode, is_backup=False):
    backup_ext = preferences().backup_ext
    if is_backup and backup_ext:
        backup_filepath = filepath + '.' + backup_ext
    else:
        backup_filepath = None
    return fileutil.TemporaryFileWriter(filepath, mode, backup_filepath=backup_filepath)


# ファイルを上書きするならバックアップ処理
def file_backup(filepath, enable=True):
    backup_ext = preferences().backup_ext
    if enable and backup_ext and os.path.exists(filepath):
        shutil.copyfile(filepath, filepath + "." + backup_ext)


# サブフォルダを再帰的に検索してリスト化
def find_tex_all_files(dir):
    for root, dirs, files in os.walk(dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext == ".tex" or ext == ".png":
                yield os.path.join(root, f)


# テクスチャ置き場のパスのリストを返す
def get_default_tex_paths():
    prefs = preferences()
    default_paths = [prefs.default_tex_path0, prefs.default_tex_path1, prefs.default_tex_path2, prefs.default_tex_path3]
    if not any(default_paths):
        target_dirs = []
        cm3d2_dir = prefs.cm3d2_path
        if not cm3d2_dir:
            cm3d2_dir = get_cm3d2_dir()

        if cm3d2_dir:
            target_dirs.append(os.path.join(cm3d2_dir, "GameData", "texture"))
            target_dirs.append(os.path.join(cm3d2_dir, "GameData", "texture2"))
            target_dirs.append(os.path.join(cm3d2_dir, "Sybaris", "GameData"))
            target_dirs.append(os.path.join(cm3d2_dir, "Mod"))

        # com3d2_dir = prefs.com3d2_path
        # if not com3d2_dir:
        #     com3d2_dir = get_cm3d2_dir()
        # if com3d2_dir:
        #     target_dirs.append(os.path.join(com3d2_dir, "GameData", "parts"))
        #     target_dirs.append(os.path.join(com3d2_dir, "GameData", "parts2"))
        #     target_dirs.append(os.path.join(com3d2_dir, "MOD"))

        tex_dirs = [path for path in target_dirs if os.path.isdir(path)]

        for index, path in enumerate(tex_dirs):
            setattr(prefs, 'default_tex_path' + str(index), path)
    else:
        tex_dirs = [getattr(prefs, 'default_tex_path' + str(i)) for i in range(4) if getattr(prefs, 'default_tex_path' + str(i))]
    return tex_dirs


# テクスチャ置き場の全ファイルを返す
def get_tex_storage_files():
    files = []
    tex_dirs = get_default_tex_paths()
    for tex_dir in tex_dirs:
        tex_dir = bpy.path.abspath(tex_dir)
        files.extend(find_tex_all_files(tex_dir))
    return files


def get_texpath_dict(reload=False):
    if reload or len(texpath_dict) == 0:
        texpath_dict.clear()
        tex_dirs = get_default_tex_paths()
        for tex_dir in tex_dirs:
            for path in find_tex_all_files(tex_dir):
                path = bpy.path.abspath(path)
                file_name = os.path.basename(path).lower()
                # 先に見つけたファイルを優先
                if file_name not in texpath_dict:
                    texpath_dict[file_name] = path
    return texpath_dict


def reload_png(img, texpath_dict, png_name):
    png_path = texpath_dict.get(png_name)
    if png_path:
        img.filepath = png_path
        img.reload()
        return True
    return False


def replace_cm3d2_tex(img, texpath_dict: dict=None, reload_path: bool=True) -> bool:
    """replace tex file.
    pngファイルを先に走査し、見つからなければtexファイルを探す.
    texはpngに展開して読み込みを行う.
    reload_path=Trueの場合、png,texファイルが見つからない場合にキャッシュを再構成し、
    再度検索を行う.

    Parameters:
        img (Image): イメージオブジェクト
        texpath_dict (dict): テクスチャパスのdict (キャッシュ)
        reload_path (bool): 見つからない場合にキャッシュを再読込するか

    Returns:
        bool: tex load successful
    """
    if texpath_dict is None:
        texpath_dict = get_texpath_dict()

    if __replace_cm3d2_tex(img, texpath_dict):
        return True
    if reload_path:
        texpath_dict = get_texpath_dict(True)
        return __replace_cm3d2_tex(img, texpath_dict)
    return False


def __replace_cm3d2_tex(img, texpath_dict: dict) -> bool:
    source_name = remove_serial_number(img.name).lower()

    source_png_name = source_name + ".png"
    if reload_png(img, texpath_dict, source_png_name):
        return True

    source_tex_name = source_name + ".tex"
    tex_path = texpath_dict.get(source_tex_name)
    try:
        if tex_path is None:
            return False
        tex_data = load_cm3d2tex(tex_path)
        if tex_data is None:
            return False
        
        png_path = tex_path[:-4] + ".png"
        with open(png_path, 'wb') as png_file:
            png_file.write(tex_data[-1])
        img.filepath = png_path
        img.reload()
        return True
    except:
        pass
    return False


# texファイルの読み込み
def load_cm3d2tex(path, skip_data=False):

    with open(path, 'rb') as file:
        header_ext = read_str(file)
        if header_ext != 'CM3D2_TEX':
            return None
        version = struct.unpack('<i', file.read(4))[0]
        read_str(file)

        # default value
        tex_format = 5
        uv_rects = None
        data = None
        if version >= 1010:
            if version >= 1011:
                num_rect = struct.unpack('<i', file.read(4))[0]
                uv_rects = []
                for i in range(num_rect):
                    # x, y, w, h
                    uv_rects.append(struct.unpack('<4f', file.read(4 * 4)))
            width = struct.unpack('<i', file.read(4))[0]
            height = struct.unpack('<i', file.read(4))[0]
            tex_format = struct.unpack('<i', file.read(4))[0]
            # if tex_format == 10 or tex_format == 12: return None
        if not skip_data:
            png_size = struct.unpack('<i', file.read(4))[0]
            data = file.read(png_size)
        return version, tex_format, uv_rects, data


def create_tex(context, mate, node_name, tex_name=None, filepath=None, cm3d2path=None, tex_map_data=None, replace_tex=False, slot_index=-1):
    if isinstance(context, bpy.types.Context):
        context = context.copy()

    if compat.IS_LEGACY:
        slot = mate.texture_slots.create(slot_index)
        tex = context['blend_data'].textures.new(node_name, 'IMAGE')
        slot.texture = tex

        if tex_name:
            slot.offset[0] = tex_map_data[0]
            slot.offset[1] = tex_map_data[1]
            slot.scale[0] = tex_map_data[2]
            slot.scale[1] = tex_map_data[3]

            if os.path.exists(filepath):
                img = bpy.data.images.load(filepath)
                img.name = tex_name
            else:
                img = context['blend_data'].images.new(tex_name, 128, 128)
                img.filepath = filepath
            img['cm3d2_path'] = cm3d2path
            img.source = 'FILE'
            tex.image = img

            if replace_tex:
                replaced = replace_cm3d2_tex(tex.image, reload_path=False)
                if replaced and node_name == '_MainTex':
                    ob = context['active_object']
                    me = ob.data
                    for face in me.polygons:
                        if face.material_index == ob.active_material_index:
                            me.uv_textures.active.data[face.index].image = tex.image

    else:
        # if mate.use_nodes is False:
        # 	mate.use_nodes = True
        nodes = mate.node_tree.nodes
        tex = nodes.get(node_name)
        if tex is None:
            tex = mate.node_tree.nodes.new(type='ShaderNodeTexImage')
            tex.name = tex.label = node_name
            tex.show_texture = True

        if tex_name:
            if tex.image is None:
                if os.path.exists(filepath):
                    img = bpy.data.images.load(filepath)
                    img.name = tex_name
                else:
                    img = context['blend_data'].images.new(tex_name, 128, 128)
                    img.filepath = filepath
                img.source = 'FILE'
                tex.image = img
                img['cm3d2_path'] = cm3d2path
            else:
                img = tex.image
                path = img.get('cm3d2_path')
                if path != cm3d2path:
                    img['cm3d2_path'] = cm3d2path
                    img.filepath = filepath

            tex_map = tex.texture_mapping
            tex_map.translation[0] = tex_map_data[0]
            tex_map.translation[1] = tex_map_data[1]
            tex_map.scale[0] = tex_map_data[2]
            tex_map.scale[1] = tex_map_data[3]

        # tex.color = tex_data['color'][:3]
        # tex.outputs['Color'].default_value = tex_data['color'][:]
        # tex.outputs['ALpha'].default_value = tex_data['color'][3]

            # tex探し
            if replace_tex:
                replaced = replace_cm3d2_tex(tex.image, reload_path=False)
                # TODO 2.8での実施方法を調査. shader editorで十分？

    return tex


def create_col(context, mate, node_name, color, slot_index=-1):
    if isinstance(context, bpy.types.Context):
        context = context.copy()

    if compat.IS_LEGACY:
        if slot_index >= 0:
            mate.use_textures[slot_index] = False
        node = mate.texture_slots.create(slot_index)
        node.color = color[:3]
        node.diffuse_color_factor = color[3]
        node.use_rgb_to_intensity = True
        tex = context['blend_data'].textures.new(node_name, 'BLEND')
        node.texture = tex
        node.use = False
    else:
        node = mate.node_tree.nodes.get(node_name)
        if node is None:
            node = mate.node_tree.nodes.new(type='ShaderNodeRGB')
            node.name = node.label = node_name
        node.outputs[0].default_value = color

    return node


def create_float(context, mate, node_name, value, slot_index=-1):
    if isinstance(context, bpy.types.Context):
        context = context.copy()

    if compat.IS_LEGACY:
        if slot_index >= 0:
            mate.use_textures[slot_index] = False
        node = mate.texture_slots.create(slot_index)
        node.diffuse_color_factor = value
        node.use_rgb_to_intensity = False
        tex = context['blend_data'].textures.new(node_name, 'BLEND')
        node.texture = tex
        node.use = False
    else:
        node = mate.node_tree.nodes.get(node_name)
        if node is None:
            node = mate.node_tree.nodes.new(type='ShaderNodeValue')
            node.name = node.label = node_name
        node.outputs[0].default_value = value

    return node


def setup_material(mate):
    if mate:
        if 'CM3D2 Texture Expand' not in mate:
            mate['CM3D2 Texture Expand'] = True

        if not compat.IS_LEGACY:
            mate.use_nodes = True


def setup_image_name(img):
    """イメージの名前から拡張子を除外する"""
    # consider case with serial number. ex) sample.png.001
    img.name = re_png.sub(r'\1', img.name)


def get_tex_cm3d2path(filepath):
    return BASE_PATH_TEX + os.path.basename(filepath)


def to_cm3d2path(path):
    path = path.replace('\\', '/')
    path = re_prefix.sub('', path)
    if not re_path_prefix.search(path):
        path = get_tex_cm3d2path(path)
    return path


# col f タイプの設定値を値に合わせて着色
def set_texture_color(slot):
    if not slot or not slot.texture or slot.use:
        return

    slot_type = 'col' if slot.use_rgb_to_intensity else 'f'
    tex = slot.texture
    base_name = remove_serial_number(tex.name)
    tex.type = 'BLEND'

    if hasattr(tex, 'progression'):
        tex.progression = 'DIAGONAL'
    tex.use_color_ramp = True
    tex.use_preview_alpha = True
    elements = tex.color_ramp.elements

    element_count = 4
    if element_count < len(elements):
        for i in range(len(elements) - element_count):
            elements.remove(elements[-1])
    elif len(elements) < element_count:
        for i in range(element_count - len(elements)):
            elements.new(1.0)

    elements[0].position, elements[1].position, elements[2].position, elements[3].position = 0.2, 0.21, 0.25, 0.26

    if slot_type == 'col':
        elements[0].color = [0.2, 1, 0.2, 1]
        elements[-1].color = slot.color[:] + (slot.diffuse_color_factor, )
        if 0.3 < mathutils.Color(slot.color[:3]).v:
            elements[1].color, elements[2].color = [0, 0, 0, 1], [0, 0, 0, 1]
        else:
            elements[1].color, elements[2].color = [1, 1, 1, 1], [1, 1, 1, 1]

    elif slot_type == 'f':
        elements[0].color = [0.2, 0.2, 1, 1]
        multi = 1.0
        if base_name == '_OutlineWidth':
            multi = 200
        elif base_name == '_RimPower':
            multi = 1.0 / 30.0
        value = slot.diffuse_color_factor * multi
        elements[-1].color = [value, value, value, 1]
        if 0.3 < value:
            elements[1].color, elements[2].color = [0, 0, 0, 1], [0, 0, 0, 1]
        else:
            elements[1].color, elements[2].color = [1, 1, 1, 1], [1, 1, 1, 1]


# 必要なエリアタイプを設定を変更してでも取得
def get_request_area(context, request_type, except_types=None):
    if except_types is None:
        except_types = ['VIEW_3D', 'PROPERTIES', 'INFO', compat.pref_type()]

    request_areas = [(a, a.width * a.height) for a in context.screen.areas if a.type == request_type]
    candidate_areas = [(a, a.width * a.height) for a in context.screen.areas if a.type not in except_types]

    return_areas = request_areas[:] if len(request_areas) else candidate_areas
    if not len(return_areas):
        return None

    return_areas.sort(key=lambda i: i[1])
    return_area = return_areas[-1][0]
    return_area.type = request_type
    return return_area


# 複数のデータを完全に削除
def remove_data(target_data):
    try:
        target_data = target_data[:]
    except:
        target_data = [target_data]

    if compat.IS_LEGACY:
        for data in target_data:
            if data.__class__.__name__ == 'Object':
                if data.name in bpy.context.scene.objects:
                    bpy.context.scene.objects.unlink(data)
    else:
        for data in target_data:
            if data.__class__.__name__ == 'Object':
                if data.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(data)

    # https://developer.blender.org/T49837
    # によると、xxx.remove(data, do_unlink=True)で十分
    #
    # for data in target_data:
    # 	users = getattr(data, 'users')
    # 	if users and 'user_clear' in dir(data):
    # 		data.user_clear()

    for data in target_data:
        for data_str in dir(bpy.data):
            if not data_str.endswith('s'):
                continue
            try:
                if data.__class__.__name__ == eval('bpy.data.%s[0].__class__.__name__' % data_str):
                    exec('bpy.data.%s.remove(data, do_unlink=True)' % data_str)
                    break
            except:
                pass


# オブジェクトのマテリアルを削除/復元するクラス
class material_restore:
    def __init__(self, ob):
        override = bpy.context.copy()
        override['object'] = ob
        self.object = ob

        self.slots = [slot.material if slot.material else None for slot in ob.material_slots]

        self.mesh_data = []
        for index, slot in enumerate(ob.material_slots):
            mesh_datum = []
            for face in ob.data.polygons:
                if face.material_index == index:
                    mesh_datum.append(face.index)
            self.mesh_data.append(mesh_datum)

        for slot in ob.material_slots[:]:
            bpy.ops.object.material_slot_remove(override)

    def restore(self):
        override = bpy.context.copy()
        override['object'] = self.object

        for slot in self.object.material_slots[:]:
            bpy.ops.object.material_slot_remove(override)

        for index, mate in enumerate(self.slots):
            bpy.ops.object.material_slot_add(override)
            slot = self.object.material_slots[index]
            if slot:
                slot.material = mate
            for face_index in self.mesh_data[index]:
                self.object.data.polygons[face_index].material_index = index


# 現在のレイヤー内のオブジェクトをレンダリングしなくする/戻す
class hide_render_restore:
    def __init__(self, render_objects=[]):
        try:
            render_objects = render_objects[:]
        except:
            render_objects = [render_objects]

        if not len(render_objects):
            render_objects = bpy.context.selected_objects[:]

        self.render_objects = render_objects[:]
        self.render_object_names = [ob.name for ob in render_objects]

        self.rendered_objects = []
        for ob in render_objects:
            if ob.hide_render:
                self.rendered_objects.append(ob)
                ob.hide_render = False

        self.hide_rendered_objects = []
        if compat.IS_LEGACY:
            for ob in bpy.data.objects:
                for layer_index, is_used in enumerate(bpy.context.scene.layers):
                    if not is_used:
                        continue
                    if ob.layers[layer_index] and is_used and ob.name not in self.render_object_names and not ob.hide_render:
                        self.hide_rendered_objects.append(ob)
                        ob.hide_render = True
                        break
        else:
            clct_children = bpy.context.scene.collection.children
            for ob in bpy.data.objects:
                if ob.name not in self.render_object_names and not ob.hide_render:
                    # ble-2.8ではlayerではなく、collectionからのリンクで判断
                    for clct in bpy.context.window.view_layer.layer_collection.children:
                        if clct.exclude is False and ob.name in clct_children[clct.name].objects.keys():
                            self.hide_rendered_objects.append(ob)
                            ob.hide_render = True
                            break

    def restore(self):
        for ob in self.rendered_objects:
            ob.hide_render = True
        for ob in self.hide_rendered_objects:
            ob.hide_render = False


# 指定エリアに変数をセット
def set_area_space_attr(area, attr_name, value):
    if not area:
        return
    for space in area.spaces:
        if space.type == area.type:
            space.__setattr__(attr_name, value)
            break


# スムーズなグラフを返す1
def in_out_quad_blend(f):
    if f <= 0.5:
        return 2.0 * math.sqrt(f)
    f -= 0.5
    return 2.0 * f * (1.0 - f) + 0.5


# スムーズなグラフを返す2
def bezier_blend(f):
    return math.sqrt(f) * (3.0 - 2.0 * f)


# 三角関数でスムーズなグラフを返す
def trigonometric_smooth(x):
    return math.sin((x - 0.5) * math.pi) * 0.5 + 0.5


# エクスポート例外クラス
class CM3D2ExportException(Exception):
    pass


# ノード取得クラス
class NodeHandler():
    node_name = bpy.props.StringProperty(name='NodeName')

    def get_node(self, context):
        mate = context.material
        if mate and mate.use_nodes:
            return mate.node_tree.nodes.get(self.node_name)

            # if node is None:
            # # 見つからない場合は、シリアル番号付きのノードを探す
            # prefix = self.node_name + '.'
            # for n in nodes:
            # 	if n.name.startwith(prefix):
            # 		node = n
            # 		break

        return None

@compat.BlRegister()
class CNV_UL_generic_selector(bpy.types.UIList):
    bl_label       = "CNV_UL_generic_selector"
    bl_options     = {'DEFAULT_CLOSED'}
    bl_region_type = 'WINDOW'
    bl_space_type  = 'PROPERTIES'

    # Constants (flags)
    # Be careful not to shadow FILTER_ITEM!
    #bitflag_soft_filter = 1073741824 >> 0
    bitflag_soft_filter  = 1073741824 >> 3

    bitflag_forced_value = 1073741824 >> 10
    bitflag_forced_true  = 1073741824 >> 11
    bitflag_forced_false = 1073741824 >> 12

    
    cached_values = {}
    expanded_layout = False

    # Custom properties, saved with .blend file.
    use_filter_name_reverse = bpy.props.BoolProperty(
        name="Reverse Name",
        default=False,
        options=set(),
        description="Reverse name filtering",
    )
    #use_filter_deform = bpy.props.BoolProperty(
    #    name="Only Deform",
    #    default=True,
    #    options=set(),
    #    description="Only show deforming vertex groups",
    #)
    #use_filter_deform_reverse = bpy.props.BoolProperty(
    #    name="Other",
    #    default=False,
    #    options=set(),
    #    description="Only show non-deforming vertex groups",
    #)
    #use_filter_empty = bpy.props.BoolProperty(
    #    name="Filter Empty",
    #    default=False,
    #    options=set(),
    #    description="Whether to filter empty vertex groups",
    #)
    #use_filter_empty_reverse = bpy.props.BoolProperty(
    #    name="Reverse Empty",
    #    default=False,
    #    options=set(),
    #    description="Reverse empty filtering",
    #)
    
    # This allows us to have mutually exclusive options, which are also all disable-able!
    def _gen_order_update(name1, name2):
        def _u(self, ctxt):
            if (getattr(self, name1)):
                setattr(self, name2, False)
        return _u
    use_order_name = bpy.props.BoolProperty(
        name="Name", default=False, options=set(),
        description="Sort groups by their name (case-insensitive)",
        update=_gen_order_update("use_order_name", "use_order_importance"),
    )
    use_filter_orderby_invert = bpy.props.BoolProperty(
        name="Order by Invert",
        default=False,
        options=set(),
        description="Invert the sort by order"
    )
    #use_order_importance = bpy.props.BoolProperty(
    #    name="Importance",
    #    default=False,
    #    options=set(),
    #    description="Sort groups by their average weight in the mesh",
    #    update=_gen_order_update("use_order_importance", "use_order_name"),
    #)
        
    # Usual draw item function.
    def draw_item(self, context, layout, data, item, icon_value, active_data, active_propname, index, flt_flag):
        # Just in case, we do not use it here!
        self.use_filter_invert = False

        # assert(isinstance(item, bpy.types.VertexGroup)
        #vgroup = getattr(data, 'matched_vgroups')[item.index]
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # Here we use one feature of new filtering feature: it can pass data to draw_item, through flt_flag
            # parameter, which contains exactly what filter_items set in its filter list for this item!
            # In this case, we show empty groups grayed out.
            cached_value = self.cached_values.get(item.name, None)
            if (cached_value != None) and (cached_value != item.value):
                item.preferred = item.value

            force_values = flt_flag & self.bitflag_forced_value
            print("GET force_values =", force_values)
            if force_values:
                print("FORCE VALUES")
                if flt_flag & self.bitflag_forced_true:
                    item.value = True
                elif flt_flag & self.bitflag_forced_false:
                    item.value = False
                else:
                    item.value = item.preferred

            self.cached_values[item.name] = item.value

            if flt_flag & self.bitflag_soft_filter:
                row = layout.row()
                row.enabled = False
                #row.alignment = 'LEFT'
                row.prop(item, "value", text=item.name, icon=item.icon)
            else:
                layout.prop(item, "value", text=item.name, icon=item.icon)
            
            #layout.prop(item, "value", text=item.name, icon=item.icon)
            icon = 'RADIOBUT_ON' if item.preferred else 'RADIOBUT_OFF'
            layout.prop(item, "preferred", text="", icon=compat.icon(icon), emboss=False)
        
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            if flt_flag & self.VGROUP_EMPTY:
                layout.enabled = False
            layout.label(text="", icon_value=icon)

    def draw_filter(self, context, layout):
        # Nothing much to say here, it's usual UI code...
        row = layout.row()
        if not self.expanded_layout:
            layout.active = True
            layout.enabled = True
            row.active = True
            row.enabled = True
            self.expanded_layout = True

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")
        icon = 'ZOOM_OUT' if self.use_filter_name_reverse else 'ZOOM_IN'
        subrow.prop(self, "use_filter_name_reverse", text="", icon=icon)

        #subrow = row.row(align=True)
        #subrow.prop(self, "use_filter_deform", toggle=True)
        #icon = 'ZOOM_OUT' if self.use_filter_deform_reverse else 'ZOOM_IN'
        #subrow.prop(self, "use_filter_deform_reverse", text="", icon=icon)

        #subrow = row.row(align=True)
        #subrow.prop(self, "use_filter_empty", toggle=True)
        #icon = 'ZOOM_OUT' if self.use_filter_empty_reverse else 'ZOOM_IN'
        #subrow.prop(self, "use_filter_empty_reverse", text="", icon=icon)

        row = layout.row(align=True)
        row.label(text="Order by:")
        row.prop(self, "use_order_name", toggle=True)
        #row.prop(self, "use_order_importance", toggle=True)
        icon = 'TRIA_UP' if self.use_filter_orderby_invert else 'TRIA_DOWN'
        row.prop(self, "use_filter_orderby_invert", text="", icon=icon)

    def filter_items(self, context, data, propname):
        # This function gets the collection property (as the usual tuple (data, propname)), and must return two lists:
        # * The first one is for filtering, it must contain 32bit integers were self.bitflag_filter_item marks the
        #   matching item as filtered (i.e. to be shown), and 31 other bits are free for custom needs. Here we use the
        #   first one to mark VGROUP_EMPTY.
        # * The second one is for reordering, it must return a list containing the new indices of the items (which
        #   gives us a mapping org_idx -> new_idx).
        # Please note that the default UI_UL_list defines helper functions for common tasks (see its doc for more info).
        # If you do not make filtering and/or ordering, return empty list(s) (this will be more efficient than
        # returning full lists doing nothing!).
        items = getattr(data, propname)
        
        #if self.armature == None:
        #    target_ob, source_ob = common.get_target_and_source_ob(context)
        #    armature_ob = target_ob.find_armature() or source_ob.find_armature()
        #    self.armature = armature_ob and armature_ob.data or False
        #
        #if not self.local_bone_names:
        #    target_ob, source_ob = common.get_target_and_source_ob(context)
        #    bone_data_ob = (target_ob.get("LocalBoneData:0") and target_ob) or (source_ob.get("LocalBoneData:0") and source_ob) or None
        #    if bone_data_ob:
        #        local_bone_data = model_export.CNV_OT_export_cm3d2_model.local_bone_data_parser(model_export.CNV_OT_export_cm3d2_model.indexed_data_generator(bone_data_ob, prefix="LocalBoneData:"))
        #        self.local_bone_names = [ bone['name'] for bone in local_bone_data ]
        
        if not self.cached_values:
            self.cached_values = { item.name: item.value for item in items }
        #vgroups = [ getattr(data, 'matched_vgroups')[item.index][0]   for item in items ]
        helper_funcs = bpy.types.UI_UL_list

        # Default return values.
        flt_flags = []
        flt_neworder = []

        # Pre-compute of vgroups data, CPU-intensive. :/
        #vgroups_empty = self.filter_items_empty_vgroups(context, vgroups)

        # Filtering by name
        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, items, "name",
                                                          reverse=self.use_filter_name_reverse)
        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(items)
        
        #for idx, vg in enumerate(items):
        #    # Filter by deform.
        #    if self.use_filter_deform:
        #        flt_flags[idx] |= self.VGROUP_DEFORM
        #        if self.use_filter_deform:
        #            if self.armature and self.armature.get(vg.name):
        #                if not self.use_filter_deform_reverse:
        #                    flt_flags[idx] &= ~self.VGROUP_DEFORM
        #            elif bone_data_ob and (vg.name in self.local_bone_names):
        #                if not self.use_filter_deform_reverse:
        #                    flt_flags[idx] &= ~self.VGROUP_DEFORM
        #            elif self.use_filter_deform_reverse or (not self.armature and not self.local_bone_names):
        #                flt_flags[idx] &= ~self.VGROUP_DEFORM
        #    else:
        #        flt_flags[idx] &= ~self.VGROUP_DEFORM
        #
        #    # Filter by emptiness.
        #    #if vgroups_empty[vg.index][0]:
        #    #    flt_flags[idx] |= self.VGROUP_EMPTY
        #    #    if self.use_filter_empty and self.use_filter_empty_reverse:
        #    #        flt_flags[idx] &= ~self.bitflag_filter_item
        #    #elif self.use_filter_empty and not self.use_filter_empty_reverse:
        #    #    flt_flags[idx] &= ~self.bitflag_filter_item
        
        # Reorder by name or average weight.
        if self.use_order_name:
            flt_neworder = helper_funcs.sort_items_by_name(items, "name")
        #elif self.use_order_importance:
        #    _sort = [(idx, vgroups_empty[vg.index][1]) for idx, vg in enumerate(vgroups)]
        #    flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1], True)

        return flt_flags, flt_neworder



@compat.BlRegister()
class CNV_SelectorItem(bpy.types.PropertyGroup):
    bl_label       = "CNV_SelectorItem"
    bl_region_type = 'WINDOW'
    bl_space_type  = 'PROPERTIES'

    name      = bpy.props.StringProperty (name="Name"    , default="Unknown")
    value     = bpy.props.BoolProperty   (name="Value"   , default=True     )
    index     = bpy.props.IntProperty    (name="Index"   , default=-1       )
    preferred = bpy.props.BoolProperty   (name="Prefered", default=True     )
    icon      = bpy.props.StringProperty (name="Icon"    , default='NONE'   )

    filter0   = bpy.props.BoolProperty   (name="Filter 0", default=False    )
    filter1   = bpy.props.BoolProperty   (name="Filter 1", default=False    )
    filter2   = bpy.props.BoolProperty   (name="Filter 2", default=False    )
    filter3   = bpy.props.BoolProperty   (name="Filter 3", default=False    )





# luvoid : for loop helper returns values with matching keys
def values_of_matched_keys(dict1, dict2):
    value_list = []
    items1 = dict1.items()
    items2 = dict2.items()
    if len(items1) <= len(items2): 
        items1.reverse()
        for k1, v1 in items1:
            for i in range(len(items2)-1, 0-1, -1):
                k2, v2 = items2[i]
                if k1 == k2:
                    value_list.append((v1,v2))
                    del items2[i]
    else:
        items2.reverse()
        for k2, v2 in items2:
            for i in range(len(items1)-1, 0-1, -1):
                k1, v1 = items1[i]
                if k1 == k2:
                    value_list.append((v1,v2))
                    del items1[i]
    
    value_list.reverse()
    return value_list


# luvoid : helper to easily get source and target objects
def get_target_and_source_ob(context, copyTarget=False, copySource=False):
    target_ob = None
    source_ob = None
    target_original_ob = None
    source_original_ob = None

    target_original_ob = context.object
    if copyTarget:
        target_ob = target_original_ob.copy()
        target_ob.data = target_original_ob.data.copy()
    else:
        target_ob = target_original_ob

    for ob in context.selected_objects:
        if ob != target_ob:
            source_original_ob = ob
            break
    
    if copySource:
        source_ob = source_original_ob.copy()
        source_ob.data = source_original_ob.data.copy()
    else:
        source_ob = source_original_ob
    
    if copyTarget:
        if copySource:
            return target_ob, source_ob, target_original_ob, source_original_ob
        else:
            return target_ob, source_ob, target_original_ob
    elif copySource:
        return  target_ob, source_ob, source_original_ob
    else:
        return  target_ob, source_ob
