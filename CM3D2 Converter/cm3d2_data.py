"""CM3D2/COM3D2用のデータ構造を扱うデータクラス"""
import bpy
import copy
import struct
from . import common
from . import compat
from .translations.pgettext_functions import *

SHADER_NAMES_CM3D2 = [
    'CM3D2/Toony_Lighted',
    'CM3D2/Toony_Lighted_Hair',
    'CM3D2/Toony_Lighted_Trans',
    'CM3D2/Toony_Lighted_Trans_NoZ',
    'CM3D2/Toony_Lighted_Outline',
    'CM3D2/Toony_Lighted_Outline_Trans',
    'CM3D2/Toony_Lighted_Hair_Outline',
    'CM3D2/Lighted_Trans',
    'CM3D2/Lighted',
    'Unlit/Texture',
    'Unlit/Transparent',
    'CM3D2/Mosaic',
    'CM3D2/Man',
    'Diffuse',
    'Transparent/Diffuse',
    'CM3D2_Debug/Debug_CM3D2_Normal2Color',
]
SHADER_NAMES_COM3D2 = [
    'CM3D2/Toony_Lighted',
    'CM3D2/Toony_Lighted_Hair',
    'CM3D2/Toony_Lighted_Trans',
    'CM3D2/Toony_Lighted_Trans_NoZ',
    'CM3D2/Toony_Lighted_Trans_NoZTest',
    'CM3D2/Toony_Lighted_Outline',
    'CM3D2/Toony_Lighted_Outline_Tex',
    'CM3D2/Toony_Lighted_Hair_Outline',
    # 'CM3D2/Toony_Lighted_Hair_Outline_Tex',
    'CM3D2/Toony_Lighted_Outline_Trans',
    'CM3D2/Toony_Lighted_Cutout_AtC',
    'CM3D2/Lighted_Cutout_AtC',
    'CM3D2/Lighted_Trans',
    'CM3D2/Lighted',
    'Unlit/Texture',
    'Unlit/Transparent',
    'CM3D2/Mosaic',
    'CM3D2/Man',
    'Diffuse',
    'Transparent/Diffuse',
    'CM3D2_Debug/Debug_CM3D2_Normal2Color',
]
TOON_TEXES = [
    'NoTex', 'ToonBlueA1', 'ToonBlueA2', 'ToonBrownA1', 'ToonGrayA1',
    'ToonGreenA1', 'ToonGreenA2', 'ToonGreenA3',
    'ToonOrangeA1',
    'ToonPinkA1', 'ToonPinkA2', 'ToonPurpleA1',
    'ToonRedA1', 'ToonRedA2',
    'ToonRedmmm1', 'ToonRedmm1', 'ToonRedm1',
    'ToonYellowA1', 'ToonYellowA2', 'ToonYellowA3', 'ToonYellowA4',
    'ToonFace',  # 'ToonFace002',
    'ToonSkin',  # 'ToonSkin002',
    'ToonBlackA1',
    'ToonFace_shadow',
    'ToonDress_shadow',
    'ToonSkin_Shadow',
    'ToonBlackMM1', 'ToonBlackM1', 'ToonGrayMM1', 'ToonGrayM1',
    'ToonPurpleMM1', 'ToonPurpleM1',
    'ToonSilverA1',
    'ToonDressMM_Shadow', 'ToonDressM_Shadow',
]
PROP_DESC = {
    '_MainTex': ["Specifies the texture.", "A texture is really just an image overlayed over the mesh.", "You can even give a texture path instead of just a name", "But don't."],
    '_ToonRamp': ["A gradient that multiplies and colors dark areas."],
    '_ShadowTex': ["Specifies the texture that determines the color of the shadow face.。", "「_ShadowRateToon」 Specifies the range。"],
    '_ShadowRateToon': ["「_ShadowTex」Specify to enable。", "Black is on, white is off."],
    '_OutlineTex': ["Specifies the texture for the outline. (unconfirmed)"],
    '_OutlineToonRamp': ["Toon ramp for the outline texture (Unconfirmed)"],
    '_Color': ["Color。", "White is valid, black is invalid. Leave it white in most cases."],
    '_ShadowColor': ["Color of the shadow", "Keep in mind, this is the color of any shadow casted ON your object"],
    '_RimColor': ["Color of the rim light。", "This is lighting at the edge of your mesh. It's terrible."],
    '_OutlineColor': ["Color of your outline.", "Usually you pick black or something to match your texture color", "It would be better to match a few shades darker"],
    '_Shininess': ["Specular strength。0.0～1.0。", "Think of it as shine. Has it's uses.", "Mostly in making certain materials", "Use it for shiny materials like leather, metal, glass, etc,."],
    '_OutlineWidth': ["Outline's width。", "0.002 is thicc、0.001 isn't。"],
    '_RimPower': ["Rim Light Strength。", "Usually this value is found over 10。", "If it's near 0, it won't display properly。"],
    '_RimShift': ["Width of rim light。", "0.0～1.0 range。0.5 is pretty strong。"],
    '_RenderTex': ["This value affects mosiacs。", "Don't even bother with this unless you know what you're doing.。"],
    '_FloatValue1': ["Mosaic Pixel Count"],
    '_Cutoff': ["Alpha Cutoff Value。", "An alpha value of a texture must be atleast this high to be rendered"],
    # '_Cutout': ["アルファのカットオフ値。", "アルファ値がこの値より大きい部分だけがレンダリングされる"],
    '_ZTest': ["Specify the depth test execution method。"]
}
PROPS = {
    '_MainTex': {
        'type': 'tex',
        'desc': ["Specifies the texture that determines the color of the face。", "普段テスクチャと呼んでいるものは基本コレです。", "テクスチャパスは適当でも動きます。", "しかし、テクスチャ名はきちんと決めましょう。"],
    },
    '_ToonRamp': {
        'type': 'tex',
        'desc': ["暗い部分に乗算するグラデーション画像を指定します。"],
    },
    '_ShadowTex': {
        'type': 'tex',
        'desc': ["陰部分の面の色を決定するテクスチャを指定。", "「_ShadowRateToon」で範囲を指定します。"],
    },
    '_ShadowRateToon': {
        'type': 'tex',
        'desc': ["「_ShadowTex」を有効にする部分を指定します。", "黒色で有効、白色で無効。"],
    },
    '_OutlineTex': {
        'type': 'tex',
        'desc': ["アウトラインを表現するためのテクスチャを指定。"],
    },
    '_OutlineToonRamp': {
        'type': 'tex',
        'desc': ["_OutlineTexの暗い部分に乗算するグラデーション画像を指定します。"],
    },
    '_RenderTex': {
        'type': 'tex',
        'desc': ["モザイクシェーダーにある設定値。", "特に設定の必要なし。"],
    },
    '_Color': {
        'type': 'col',
        'desc': ["面の色を指定。", "白色で無効。基本的に白色で良いでしょう。"],
    },
    '_ShadowColor': {
        'type': 'col',
        'desc': ["影の色を指定。白色で無効。", "別の物体に遮られてできた「影」の色です。"],
    },
    '_RimColor': {
        'type': 'col',
        'desc': ["リムライトの色を指定。", "リムライトとは縁にできる光の反射のことです。"],
    },
    '_OutlineColor': {
        'type': 'col',
        'desc': ["輪郭線の色を指定。", "黒にするか、テクスチャの明度を", "落としたものを指定するとより良いでしょう。"],
    },
    '_Shininess': {
        'type': 'f',
        'desc': ["スペキュラーの強さを指定。0.0～1.0で指定。", "スペキュラーとは面の角度と光源の角度によって", "できるハイライトのことです。", "金属、皮、ガラスなどに使うと良いでしょう。"],
        'presets': [0, 0.1, 0.5, 1, 5],
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    '_OutlineWidth': {
        'type': 'f',
        'desc': ["輪郭線の太さを指定。", "0.002は太め、0.001は細め。"],
        'presets': [0.0001, 0.001, 0.0015, 0.002],
        'dispExact': True,
        # 'default': 0, 'step': 0.001, 'precision': 4,
        # 'min': 0, 'soft_min': 1,
        # 'max': 0, 'soft_max': 1,
    },
    '_RimPower': {
        'type': 'f',
        'desc': ["リムライトの強さを指定。", "この値は10以上なことも多いです。", "0に近い値だと正常に表示されません。"],
        'presets': [0, 25, 50, 100],  # 1, 10, 20, 30
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    '_RimShift': {
        'type': 'f',
        'desc': ["リムライトの幅を指定。", "0.0～1.0で指定。0.5でもかなり強い。"],
        'presets': [0, 0.25, 0.5, 0.75, 1],  # 0.0, 0.25, 0.5, 0.75, 1.0
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    '_FloatValue1': {
        'type': 'f',
        'desc': ["モザイクの粗さ"],
        'presets': [0, 100, 200],
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    '_Cutoff': {
        'type': 'f',
        'desc': ["アルファのカットオフ値。", "アルファ値がこの値より大きい部分だけがレンダリングされる"],
        'presets': [0, 0.1, 0.5, 1, 5],
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    # '_Cutout': ["アルファのカットオフ値。", "アルファ値がこの値より大きい部分だけがレンダリングされる"],
    '_ZTest': {
        'type': 'f',
        'desc': ["デプステストの実行方法を指定する。"],
        'disableSlider': True,
        'preset_enums': [
            (0, "Disabled:0"), (1, "Never:1"), (2, "Less:2"), (3, "Equal:3"), (4, "LessEqual:4"),
            (5, "Greater:5"), (6, "NotEqual:6"), (7, "GreaterEqual:7"), (8, "Always:8")
        ],
    },
    '_FloatValue2': {
        'type': 'f',
        'presets': [-15, 0, 1, 15],
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    '_FloatValue3': {
        'type': 'f',
        'presets': [0, 0.1, 0.5, 1],
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    '_ZTest2': {
        'type': 'f',
        'disableSlider': True,
        'preset_enums': [(0, "0"), (1, "1")],
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    },
    '_ZTest2Alpha': {
        'type': 'f',
        'presets': [0, 0.8, 1],
        # 'default': 0, 'step': 1, 'precision': 2,
        # 'min': -100, 'soft_min': -100,
        # 'max': 100, 'soft_max': 100,
    }
}


class DataHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = DataHandler()

        return cls._instance

    def __init__(self):
        diffuse = {
            'type_name': "Legacy",
            'icon': 'BRUSH_CLAY_STRIPS',
            'shader2': 'Legacy Shaders__Diffuse',
            'tex_list': ['_MainTex'],
            'col_list': ['_Color'],
            'f_list': [],
        }
        trans_diffuse = {
            'type_name': "Legacy Transparent",
            'icon': 'BRUSH_TEXFILL',
            'shader2': 'Legacy Shaders__Transparent__Diffuse',
            'tex_list': ['_MainTex'],
            'col_list': ['_Color'],
            'f_list': [],
        }

        self.shader_dict = {
            'CM3D2/Toony_Lighted': {
                'type_name': "Toony Lighted",
                'icon': compat.icon('SHADING_SOLID'),
                'shader2': 'CM3D2__Toony_Lighted',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor'],
                'f_list': ['_Shininess', '_RimPower', '_RimShift']
            },
            'CM3D2/Toony_Lighted_Hair': {
                'type_name': "Toony Hair Lighted",
                'icon': 'PARTICLEMODE',
                'shader2': 'CM3D2__Toony_Lighted_Hair',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon', '_HiTex'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor'],
                'f_list': ['_Shininess', '_RimPower', '_RimShift', '_HiRate', '_HiPow']
            },
            'CM3D2/Toony_Lighted_Trans': {
                'type_name': "Toony Lighted Trans",
                'icon': compat.icon('SHADING_WIRE'),
                'shader2': 'CM3D2__Toony_Lighted_Trans',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor'],
                'f_list': ['_Shininess', '_Cutoff', '_RimPower', '_RimShift'],
            },
            'CM3D2/Toony_Lighted_Trans_NoZ': {
                'type_name': "Toony Lighted Trans NoZ",
                'icon': 'DRIVER',
                'shader2': 'CM3D2__Toony_Lighted_Trans_NoZ',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor'],
                'f_list': ['_Shininess', '_RimPower', '_RimShift'],
            },
            'CM3D2/Toony_Lighted_Trans_NoZTest': {
                'type_name': "Toony Lighted Trans NoZTest",
                'icon': 'ANIM_DATA',
                'shader2': 'CM3D2__Toony_Lighted_Trans_NoZTest',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor'],
                'f_list': ['_Shininess', '_RimPower', '_RimShift', '_ZTest', '_ZTest2', '_ZTest2Alpha'],
            },
            'CM3D2/Toony_Lighted_Outline': {
                'type_name': "Toony Lighted Outline",
                'icon': 'ANTIALIASED',
                'shader2': 'CM3D2__Toony_Lighted_Outline',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor', '_OutlineColor'],
                'f_list': ['_Shininess', '_OutlineWidth', '_RimPower', '_RimShift'],
            },
            'CM3D2/Toony_Lighted_Outline_Tex': {
                'type_name': "Toony Lighted Outline Tex",
                'icon': 'MATSPHERE',
                'shader2': 'CM3D2__Toony_Lighted_Outline_Tex',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon', '_OutlineTex', '_OutlineToonRamp'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor', '_OutlineColor'],
                'f_list': ['_Shininess', '_OutlineWidth', '_RimPower', '_RimShift'],
            },
            'CM3D2/Toony_Lighted_Hair_Outline': {
                'type_name': "Toony Lighted Hair Outline",
                'icon': 'PARTICLEMODE',
                'shader2': 'CM3D2__Toony_Lighted_Hair_Outline',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon', '_HiTex'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor', '_OutlineColor'],
                'f_list': ['_Shininess', '_OutlineWidth', '_RimPower', '_RimShift', '_HiRate', '_HiPow'],
            },
            # 'CM3D2/Toony_Lighted_Hair_Outline_Tex': {
            # 	'type_name': "トゥーン 輪郭線 Tex 髪",
            # 	'icon': 'PARTICLEMODE',
            # 	'shader2': 'CM3D2__Toony_Lighted_Hair_Outline_Tex',
            # 	'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon', '_HiTex'],
            # 	'col_list': ['_Color', '_ShadowColor', '_RimColor', '_OutlineColor'],
            # 	'f_list': ['_Shininess', '_OutlineWidth', '_RimPower', '_RimShift', '_HiRate', '_HiPow'],
            # },
            'CM3D2/Toony_Lighted_Outline_Trans': {
                'type_name': "Toony Lighted Outline Trans",
                'icon': 'PROP_OFF',
                'shader2': 'CM3D2__Toony_Lighted_Outline_Trans',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor', '_OutlineColor'],
                'f_list': ['_Shininess', '_OutlineWidth', '_RimPower', '_RimShift'],
            },
            'CM3D2/Toony_Lighted_Cutout_AtC': {
                'type_name': "Toony Lighted Cutout",
                'icon': 'IPO_BACK',
                'shader2': 'CM3D2__Toony_Lighted_Cutout_AtC',
                'tex_list': ['_MainTex', '_ToonRamp', '_ShadowTex', '_ShadowRateToon'],
                'col_list': ['_Color', '_ShadowColor', '_RimColor'],
                'f_list': ['_Shininess', '_RimPower', '_RimShift', '_Cutoff'],
            },
            'CM3D2/Lighted_Trans': {
                'type_name': "Lighted Transparent",
                'icon': compat.icon('VIS_SEL_01'),
                'shader2': 'CM3D2__Lighted_Trans',
                'tex_list': ['_MainTex'],
                'col_list': ['_Color', '_ShadowColor'],
                'f_list': ['_Shininess'],
            },
            'CM3D2/Lighted': {
                'type_name': "Lighted",
                'icon': compat.icon('VIS_SEL_11'),
                'shader2': 'CM3D2__Lighted',
                'tex_list': ['_MainTex'],
                'col_list': ['_Color', '_ShadowColor'],
                'f_list': ['_Shininess'],
            },
            'CM3D2/Lighted_Cutout_AtC': {
                'type_name': "Lighted Cutout",
                'icon': 'IPO_BACK',
                'shader2': 'CM3D2__Lighted_Cutout_AtC',
                'tex_list': ['_MainTex'],
                'col_list': ['_Color', '_ShadowColor'],
                'f_list': ['_Shininess', '_Cutoff'],
            },
            'Unlit/Texture': {
                'type_name': "Unlit",
                'icon': 'PARTICLES',
                'shader2': 'Unlit__Texture',
                'tex_list': ['_MainTex'],
                'col_list': [],  # ['_Color'],
                'f_list': [],
            },
            'Unlit/Transparent': {
                'type_name': "Unlit Trans",
                'icon': 'MOD_PARTICLES',
                'shader2': 'Unlit__Texture',
                'tex_list': ['_MainTex'],
                'col_list': [],  # ['_Color'],
                'f_list': [],
            },
            'CM3D2/Mosaic': {
                'type_name': "Mosiac",
                'icon': 'ALIASED',
                'shader2': 'CM3D2__Mosaic',
                'tex_list': ['_RenderTex'],
                'col_list': [],
                'f_list': ['_FloatValue1'],
            },
            'CM3D2/Man': {
                'type_name': "Man (Silhouette)",
                'icon': 'ARMATURE_DATA',
                'shader2': 'CM3D2__Man',
                'tex_list': [],
                'col_list': ['_Color'],
                'f_list': ['_FloatValue2', '_FloatValue3'],
            },
            'Diffuse': diffuse,
            'Legacy Shaders/Diffuse': diffuse,
            'Transparent/Diffuse': trans_diffuse,
            'Legacy Shaders/Transparent/Diffuse': trans_diffuse,
            'CM3D2_Debug/Debug_CM3D2_Normal2Color': {
                'type_name': "Diffuse",
                'icon': compat.icon('NORMALS_VERTEX'),
                'shader2': 'CM3D2_Debug__Debug_CM3D2_Normal2Color',
                'tex_list': [],
                'col_list': ['_Color'],  # , '_RimColor', '_OutlineColor', '_SpecColor'],
                'f_list': []  # ['_Shininess', '_OutlineWidth', '_RimPower', '_RimShift'],
            },
        }

    @classmethod
    def create_shader_items(cls) -> list:
        _inst = cls.instance()
        items = []
        idx = 0
        for name in SHADER_NAMES_CM3D2:
            item = _inst.shader_dict.get(name)
            if item:
                items.append((name, item['type_name'], '', item['icon'], idx))
                idx += 1
        return items

    @classmethod
    def create_comshader_items(cls) -> list:
        _inst = cls.instance()
        items = []
        idx = 0
        for name in SHADER_NAMES_COM3D2:
            item = _inst.shader_dict.get(name)
            if item:
                items.append((name, item['type_name'], '', item['icon'], idx))
                idx += 1
        return items

    @classmethod
    def get_shader_prop(cls, name):
        _inst = cls.instance()
        shader_prop = _inst.shader_dict.get(name)
        if shader_prop:
            return shader_prop

        return {'type_name': 'Unknown', 'icon': 'NONE'}

Handler = DataHandler.instance()


class Material():
    """マテリアルデータクラス"""
    def __init__(self):
        self.version = 1000
        self.name1 = None
        self.name2 = None
        self.shader1 = None
        self.shader2 = None

        self.tex_list = []  # prop_name, (tex_name, tex_path, trans[2], scale[2])
        self.col_list = []  # prop_name, col[4]
        self.f_list = []  # prop_name, f
        self.range_list = [] # prop_name, col[4]

        self.custom_list = dict()

    def sort(self):
        self.tex_list = sorted(self.tex_list, key=lambda item: item[0])
        self.col_list = sorted(self.col_list, key=lambda item: item[0])
        self.f_list = sorted(self.f_list, key=lambda item: item[0])

    @property
    def name(self):
        return self.name2 or self.name1

    def read(self, reader, read_header=True):
        if read_header:
            header = common.read_str(reader)
            if header != 'CM3D2_MATERIAL':
                raise common.CM3D2ImportException(f_tip_("The .mate file has an invalid header: {}", header))
            self.version = struct.unpack('<i', reader.read(4))[0]
            self.name1 = common.read_str(reader)

        self.name2 = common.read_str(reader)

        self.shader1 = common.read_str(reader)
        self.shader2 = common.read_str(reader)
        
        peeked = reader.peek()[0]
        print(f"type({peeked}) = {type(peeked)}")
        if self.version >= 2102 and (peeked in (0, 1)): # CR Edit Mode
            cr_unknown_float_count = struct.unpack('<B', reader.read(1))[0]
            for i in range(cr_unknown_float_count):
                # CR TODO
                self.custom_list[f'cr_unknown_float:{i:03d}'] = struct.unpack('<f', reader.read(4))

        for i in range(99999):
            prop_type = common.read_str(reader)
            if prop_type == 'tex':
                prop_name = common.read_str(reader)
                sub_type = common.read_str(reader)
                if sub_type == 'tex2d':
                    tex_name = common.read_str(reader)
                    tex_path = common.read_str(reader)
                    offset = struct.unpack('<2f', reader.read(4 * 2))
                    scale = struct.unpack('<2f', reader.read(4 * 2))
                    tex_item = [prop_name, tex_name, tex_path, offset, scale]
                else:
                    tex_item = [prop_name]
                self.tex_list.append(tex_item)

            elif prop_type == 'col':
                prop_name = common.read_str(reader)
                col = struct.unpack('<4f', reader.read(4 * 4))
                self.col_list.append([prop_name, col])

            elif prop_type == 'f' or prop_type == 'range': # 'range' from CR Edit
                prop_name = common.read_str(reader)
                f = struct.unpack('<f', reader.read(4))[0]
                self.f_list.append([prop_name, f])
            
            # CR TODO
            elif prop_type == 'keyword':
                prop_name = common.read_str(reader)
                keyword_f = struct.unpack('<f', reader.read(4))[0]
                print(keyword_f, type(keyword_f))
                self.custom_list.setdefault('keyword', dict())[prop_name] = keyword_f #.append([prop_name, keyword_f])
                
            # CR TODO
            elif prop_type == '_ALPHAPREMULTIPLY_ON':
                alpha_bool = struct.unpack('<?', reader.read(1))[0]
                self.custom_list['_ALPHAPREMULTIPLY_ON'] = alpha_bool

            elif prop_type == 'end':
                break
            else:
                raise common.CM3D2ImportException(f_tip_("Unknown setting value '{prop}' was found in the material!", prop=prop_type))

    def write(self, writer, write_header=True):
        if write_header:
            common.write_str(writer, 'CM3D2_MATERIAL')
            writer.write(struct.pack('<i', self.version))
            common.write_str(writer, self.name1)

        common.write_str(writer, self.name2)
        common.write_str(writer, self.shader1)
        common.write_str(writer, self.shader2)

        for tex_item in self.tex_list:
            common.write_str(writer, 'tex')
            common.write_str(writer, tex_item[0])  # prop_name

            if len(tex_item) < 2:
                common.write_str(writer, 'null')
            else:
                common.write_str(writer, 'tex2d')
                common.write_str(writer, tex_item[1])  # tex_name
                common.write_str(writer, tex_item[2])  # tex_path
                trans = tex_item[3]
                writer.write(struct.pack('<2f', trans[0], trans[1]))
                scale = tex_item[4]
                writer.write(struct.pack('<2f', scale[0], scale[1]))

        for col_item in self.col_list:
            common.write_str(writer, 'col')
            common.write_str(writer, col_item[0])  # prop_name

            col = col_item[1]
            writer.write(struct.pack('<4f', col[0], col[1], col[2], col[3]))

        for f_item in self.f_list:
            common.write_str(writer, 'f')
            common.write_str(writer, f_item[0])  # prop_name

            writer.write(struct.pack('<f', f_item[1]))

        common.write_str(writer, 'end')

    def to_text(self):
        output_text = str(self.version) + "\n"
        output_text += self.name1 + "\n"
        output_text += self.name2 + "\n"
        output_text += self.shader1 + "\n"
        output_text += self.shader2 + "\n"
        output_text += "\n"

        for tex_item in self.tex_list:
            output_text += 'tex\n'
            output_text += "\t" + tex_item[0] + "\n"  # prop_name

            if len(tex_item) < 2:
                output_text += '\tnull\n'
            else:
                output_text += '\ttex2d\n'
                output_text += "\t" + tex_item[1] + "\n"  # tex_name
                output_text += "\t" + tex_item[2] + "\n"  # tex_path
                trans = tex_item[3]
                scale = tex_item[4]
                output_text += "\t" + " ".join([str(trans[0]), str(trans[1]), str(scale[0]), str(scale[1])]) + "\n"

        for col_item in self.col_list:
            output_text += 'col\n'
            output_text += "\t" + col_item[0] + "\n"  # prop_name
            col = col_item[1]
            output_text += "\t" + " ".join([str(col[0]), str(col[1]), str(col[2]), str(col[3])]) + "\n"  # prop_name

        for f_item in self.f_list:
            output_text += 'f\n'
            output_text += "\t" + f_item[0] + "\n"  # prop_name
            f = f_item[1]
            output_text += "\t" + str(f) + "\n"

        return output_text

    def to_json(self):
        import json
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2)

    def from_dict(self, data):
        self.name1 = data['name1']
        self.name2 = data['name2']
        self.version = data['version']
        self.shader1 = data['shader1']
        self.shader2 = data['shader2']

        self.tex_list = data['tex_list']  # prop_name, (tex_name, tex_path, trans[2], scale[2])
        self.col_list = data['col_list']  # prop_name, col[4]
        self.f_list = data['f_list']  # prop_name, f


class MaterialHandler:

    @classmethod
    def parse_tex_node(cls, node, remove_serial=True):
        node_name = common.remove_serial_number(node.name, remove_serial)
        tex_item = [node_name]

        try:
            img = node.image
        except:
            raise common.CM3D2ImportException('Failed to get setting value of tex type of material property。')

        if img:
            tex_name = common.remove_serial_number(img.name, remove_serial)
            tex_name = common.re_png.sub(r'\1', tex_name)  # 拡張子を除外
            tex_item.append(tex_name)

            if 'cm3d2_path' in img:
                path = img['cm3d2_path']
            else:
                path = bpy.path.abspath(img.filepath)
            path = common.to_cm3d2path(path)

            tex_item.append(path)
            tex_map = node.texture_mapping
            tex_trans = tex_map.translation[:2]
            tex_scale = tex_map.scale[:2]
            tex_item.append(tex_trans)
            tex_item.append(tex_scale)
        return tex_item

    @classmethod
    def parse_col_node(cls, node, remove_serial=True):
        node_name = common.remove_serial_number(node.name, remove_serial)
        col = node.outputs[0].default_value
        return [node_name, col[:4]]

    @classmethod
    def parse_f_node(cls, node, remove_serial=True):
        node_name = common.remove_serial_number(node.name, remove_serial)
        f = node.outputs[0].default_value
        return [node_name, f]

    @classmethod
    def read(cls, reader, read_header=True, version=None):
        if not read_header and version == None:
            raise ValueError(f_tip_("The argument 'version' is required when 'read_header' is False for MaterialHandler.read()"))
        mat_data = Material()
        if version:
            mat_data.version = version
        mat_data.read(reader, read_header)

        return mat_data

    @classmethod
    def get_shader_prop_dynamic(cls, mate, ):
        lists = { 'VALUE':'f_list', 'RGB':'col_list', 'TEX_IMAGE':'tex_list' }
        shader_prop = copy.deepcopy( DataHandler.get_shader_prop(mate.get('shader1')) )
        for node in mate.node_tree.nodes:
            if node.name[0] != '_':
                continue
            list_name = lists.get(node.type)
            if not list_name:
                continue
            prop_list = shader_prop[list_name]
            if node.name in prop_list:
                continue
            prop_list.append(node.name)
        return shader_prop

    @classmethod
    def parse_mate(cls, mate, remove_serial=True):
        mat_data = Material()

        mate_name = common.remove_serial_number(mate.name, remove_serial)
        mat_data.name1 = mate_name.lower()
        mat_data.name2 = mate_name
        mat_data.shader1 = mate['shader1']
        mat_data.shader2 = mate['shader2']

        nodes = mate.node_tree.nodes
        shader_prop = cls.get_shader_prop_dynamic(mate) #DataHandler.get_shader_prop(mat_data.shader1)
        if shader_prop:
            for node_name in shader_prop['tex_list']:
                node = nodes.get(node_name)
                if node and node.type == 'TEX_IMAGE':
                    tex_item = cls.parse_tex_node(node, remove_serial)
                    mat_data.tex_list.append(tex_item)

            for node_name in shader_prop['col_list']:
                node = nodes.get(node_name)
                if node and node.type == 'RGB':
                    col_item = cls.parse_col_node(node, remove_serial)
                    mat_data.col_list.append(col_item)

            for node_name in shader_prop['f_list']:
                node = nodes.get(node_name)
                if node and node.type == 'VALUE':
                    f_item = cls.parse_f_node(node, remove_serial)
                    mat_data.f_list.append(f_item)

        #for node in nodes:
        #    if not node.name.startswith('_'):
        #        continue
        #
        #    node_type = node.type
        #    if node_type == 'TEX_IMAGE':
        #        tex_item = cls.parse_tex_node(node, remove_serial)
        #        mat_data.tex_list.append(tex_item)
        #    elif node_type == 'RGB':
        #        col_item = cls.parse_col_node(node, remove_serial)
        #        mat_data.col_list.append(col_item)
        #
        #    elif node_type == 'VALUE':
        #        f_item = cls.parse_f_node(node, remove_serial)
        #        mat_data.f_list.append(f_item)
        
        return mat_data

    @classmethod
    def parse_mate_old(cls, mate, remove_serial=True):
        """material parser for blender-2.7x"""
        mat_data = Material()

        mate_name = common.remove_serial_number(mate.name, remove_serial)
        mat_data.name1 = mate_name.lower()
        mat_data.name2 = mate_name
        mat_data.shader1 = mate['shader1']
        mat_data.shader2 = mate['shader2']

        for tindex, tslot in enumerate(mate.texture_slots):
            if not tslot:
                continue

            tex = tslot.texture
            node_name = common.remove_serial_number(tex.name, remove_serial)
            # node_name = tslot.name
            if mate.use_textures[tindex]:
                tex_item = [node_name]
                try:
                    img = tex.image
                except:
                    raise Exception('Unknown setting value was found in the material!')

                if img:
                    tex_name = common.remove_serial_number(img.name, remove_serial)
                    tex_name = common.re_png.sub(r'\1', tex_name)  # 拡張子を除外
                    tex_item.append(tex_name)

                    if 'cm3d2_path' in img:
                        path = img['cm3d2_path']
                    else:
                        path = bpy.path.abspath(img.filepath)
                    path = common.to_cm3d2path(path)

                    tex_item.append(path)
                    tex_trans = tex.offset[:2]
                    tex_scale = tex.scale[:2]
                    tex_item.append(tex_trans)
                    tex_item.append(tex_scale)

                mat_data.tex_list.append(tex_item)
            elif tslot.use_rgb_to_intensity:
                col = tex.color[:3] + [tslot.diffuse_color_factor]
                mat_data.col_list.append([node_name, col[:4]])
            else:
                f = tslot.diffuse_color_factor
                mat_data.f_list.append([node_name, f])

        return mat_data

    @classmethod
    def parse_text(cls, text):
        mat_data = Material()
        lines = text.split('\n')

        mat_data.version = int(lines[0])
        mat_data.name1 = lines[1]
        mat_data.name2 = lines[2]
        mat_data.shader1 = lines[3]
        mat_data.shader2 = lines[4]

        line_seek = 5
        while line_seek < len(lines):
            node_type = common.line_trim(lines[line_seek])
            if not node_type:
                line_seek += 1
                continue
            if node_type == 'tex':
                prop_name = common.line_trim(lines[line_seek + 1])
                sub_type = common.line_trim(lines[line_seek + 2])
                if sub_type == 'tex2d':
                    line_seek += 3
                    tex_name = common.line_trim(lines[line_seek])
                    tex_path = common.line_trim(lines[line_seek + 1])
                    tex_map = common.line_trim(lines[line_seek + 2]).split(' ')
                    for map_datum in range(len(tex_map)):
                        tex_map[map_datum] = float(tex_map[map_datum])
                    mat_data.tex_list.append([prop_name, tex_name, tex_path, tex_map[:2], tex_map[2:]])
                else:
                    mat_data.tex_list.append([prop_name])

                line_seek += 3

            elif node_type == 'col':
                prop_name = common.line_trim(lines[line_seek + 1])
                tex_map = common.line_trim(lines[line_seek + 2]).split(' ')
                for map_datum in range(len(tex_map)):
                    tex_map[map_datum] = float(tex_map[map_datum])

                mat_data.col_list.append([prop_name, tex_map[:]])
                line_seek += 3

            elif node_type == 'f':
                prop_name = common.line_trim(lines[line_seek + 1])
                val = float(common.line_trim(lines[line_seek + 2]))

                mat_data.f_list.append([prop_name, val])
                line_seek += 3
            else:
                raise Exception('Unknown setpoint type was found!')

        return mat_data

    @classmethod
    def parse_json(cls, text):
        import json
        mat_data = Material()
        mat_data.from_dict(json.loads(text))

        return mat_data

    @classmethod
    def apply_to(cls, override, mate, mat_data, replace_tex=True):
        mate['shader1'] = mat_data.shader1
        mate['shader2'] = mat_data.shader2

        if mate.use_nodes is False:
            mate.use_nodes = True

        nodes = mate.node_tree.nodes
        nodes.clear()
        # OUTPUT_MATERIAL, BSDF_PRINCIPLEDは消さない
        #if len(nodes) > 2:
        #    clear_nodes(nodes)

        for tex_item in mat_data.tex_list:
            prop_name = tex_item[0]

            if len(tex_item) < 2:
                common.create_tex(override, mate, prop_name)
            else:
                tex_name = tex_item[1]
                tex_path = tex_item[2]
                tex_map = tex_item[3] + tex_item[4]
                common.create_tex(override, mate, prop_name, tex_name, tex_path, tex_path, tex_map, replace_tex)

        for col_item in mat_data.col_list:
            prop_name = col_item[0]
            col = col_item[1]
            common.create_col(override, mate, prop_name, col)

        for item in mat_data.f_list:
            prop_name = item[0]
            f = item[1]
            common.create_float(override, mate, prop_name, f)

        for key, value in mat_data.custom_list.items():
            mate[key] = value
            if type(value) == bool:
                rna_ui = mate.get('_RNA_UI', dict())
                rna_ui[key] = {
                    "default"  : value,
                    "min"      : 0    ,
                    "max"      : 1    ,
                    "soft_min" : 0    ,
                    "soft_max" : 1    ,
                }
                mate['_RNA_UI'] = rna_ui



        align_nodes(mate)

    @classmethod
    def apply_to_old(cls, override, mate, mat_data, replace_tex=True, decorate=True, skip_same_prop=True):
        ob = override['active_object']
        me = ob.data

        mate['shader1'] = mat_data.shader1
        mate['shader2'] = mat_data.shader2

        slot_index = 0
        olds_slots = {}
        read_texes = set() if skip_same_prop else None

        for item in mat_data.tex_list:
            prop_name = item[0]
            if read_texes:
                if prop_name in read_texes:
                    continue
                read_texes.add(prop_name)

            slot = search_or_create_slot(override, mate, olds_slots, slot_index, prop_name, 'IMAGE')
            slot.use_rgb_to_intensity = False
            mate.use_textures[slot_index] = True

            if len(item) > 4:
                tex = slot.texture
                tex_name = item[1]
                tex_path = item[2]
                if tex_name in read_texes:
                    continue

                if tex_name != common.remove_serial_number(tex.image.name):
                    tex.image.name = tex_name
                tex.image['cm3d2_path'] = tex_path
                tex.image.filepath = tex.image['cm3d2_path']

                slot.offset = item[3]
                slot.scale = item[4]
                if replace_tex:
                    if common.replace_cm3d2_tex(tex.image, reload_path=True) and prop_name == '_MainTex':
                        for face in me.polygons:
                            if face.material_index == ob.active_material_index:
                                me.uv_textures.active.data[face.index].image = tex.image
            slot_index += 1

        for item in mat_data.col_list:
            prop_name = item[0]
            col = item[1]

            slot = search_or_create_slot(override, mate, olds_slots, slot_index, prop_name, 'BLEND')

            mate.use_textures[slot_index] = False
            slot.use_rgb_to_intensity = True
            slot.color = col[:3]
            slot.diffuse_color_factor = col[3]

            slot_index += 1

        for item in mat_data.f_list:
            prop_name = item[0]
            f = item[1]

            slot = search_or_create_slot(override, mate, olds_slots, slot_index, prop_name, 'BLEND')

            mate.use_textures[slot_index] = False
            slot.use_rgb_to_intensity = False
            slot.diffuse_color_factor = f

            slot_index += 1

        # 存在しないスロットをクリア
        for item_index in range(slot_index, len(mate.texture_slots)):
            if mate.texture_slots[item_index]:
                mate.texture_slots.clear(item_index)

        # プレビューへの反映
        for slot in mate.texture_slots:
            if slot:
                common.set_texture_color(slot)

        if decorate:
            common.decorate_material(mate, decorate, me, ob.active_material_index)

    @staticmethod
    def search_or_create_slot(override, mate, olds_slots, slot_index, prop_name, tex_type):
        tex = None
        slot_item = mate.texture_slots[slot_index]
        slot_name = slot_item.name if slot_item else ''

        slot_name = common.remove_serial_number(slot_name)
        # 指定スロットが同名であればそのスロットをそのまま利用する
        if prop_name == slot_name:
            slot = slot_item
        else:
            # スロット名が異なり、既にスロットがある場合はキャッシュに格納
            if slot_item:
                olds_slots[slot_name] = slot_item
            slot = mate.texture_slots.create(slot_index)

            if prop_name in olds_slots:
                tex = olds_slots.pop(prop_name).texture
            else:
                for item_index in range(slot_index + 1, len(mate.texture_slots)):
                    slot_item = mate.texture_slots[item_index]
                    if slot_item is None:
                        break
                    if prop_name == common.remove_serial_number(slot_item.name):
                        tex = slot_item.texture
                        break
            if tex is None:
                tex = override['blend_data'].textures.new(prop_name, tex_type)
            slot.texture = tex
        return slot


def clear_nodes(nodes):
    for node in nodes:
        if node.type not in ['VALUE', 'RGB', 'TEX_IMAGE']:
            nodes.remove(node)


def align_nodes(mate):
    nodes = mate.node_tree.nodes
    # Principled BSDFがある前提での整列
    bsdf = nodes.get('Principled BSDF')
    base_location = (10, 300)
    if bsdf:
        main_tex = nodes.get('_MainTex')
        if main_tex:
            mate.node_tree.links.new(bsdf.inputs['Base Color'], main_tex.outputs['Color'])
            mate.node_tree.links.new(bsdf.inputs['Alpha'], main_tex.outputs['Alpha'])
        shininess = nodes.get('_Shininess')
        if shininess:
            mate.node_tree.links.new(bsdf.inputs['Specular'], shininess.outputs[0])
        base_location = bsdf.location

    shader_name = mate.get('shader1')
    if shader_name:
        location_x = base_location[0] - 400
        location_y = base_location[1] + 60
        shader_prop = MaterialHandler.get_shader_prop_dynamic(mate) #DataHandler.get_shader_prop(shader_name)
        node_list = shader_prop.get('tex_list')
        if node_list:
            for node_name in node_list:
                node = nodes.get(node_name)
                if node:
                    node.location = (location_x, location_y)
                    node.hide = True
                    location_y -= 60

        col_list = shader_prop.get('col_list')
        if col_list:
            for node_name in col_list:
                node = nodes.get(node_name)
                if node:
                    node.location = (location_x, location_y)
                    location_y -= 200

        f_list = shader_prop.get('f_list')
        if f_list:
            for node_name in f_list:
                node = nodes.get(node_name)
                if node:
                    node.location = (location_x, location_y)
                    location_y -= 90
