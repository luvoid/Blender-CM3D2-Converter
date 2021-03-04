import os
import csv
import bpy
import bpy.app.translations
from bpy.app.translations import contexts
'''
contexts = {
    default_real        = None                ,
    default             = '*'                 ,
    operator_default    = 'Operator'          ,
    ui_events_keymaps   = 'UI_Events_KeyMaps' ,
    plural              = 'Plural'            ,
    id_action           = 'Action'            ,
    id_armature         = 'Armature'          ,
    id_brush            = 'Brush'             ,
    id_camera           = 'Camera'            ,
    id_cachefile        = 'CacheFile'         ,
    id_collection       = 'Collection'        ,
    id_curve            = 'Curve'             ,
    id_fs_linestyle     = 'FreestyleLineStyle',
    id_gpencil          = 'GPencil'           ,
    id_hair             = 'Hair'              ,
    id_id               = 'ID'                ,
    id_image            = 'Image'             ,
    id_shapekey         = 'Key'               ,
    id_light            = 'Light'             ,
    id_library          = 'Library'           ,
    id_lattice          = 'Lattice'           ,
    id_mask             = 'Mask'              ,
    id_material         = 'Material'          ,
    id_metaball         = 'Metaball'          ,
    id_mesh             = 'Mesh'              ,
    id_movieclip        = 'MovieClip'         ,
    id_nodetree         = 'NodeTree'          ,
    id_object           = 'Object'            ,
    id_paintcurve       = 'PaintCurve'        ,
    id_palette          = 'Palette'           ,
    id_particlesettings = 'ParticleSettings'  ,
    id_pointcloud       = 'PointCloud'        ,
    id_lightprobe       = 'LightProbe'        ,
    id_scene            = 'Scene'             ,
    id_screen           = 'Screen'            ,
    id_sequence         = 'Sequence'          ,
    id_simulation       = 'Simulation'        ,
    id_speaker          = 'Speaker'           ,
    id_sound            = 'Sound'             ,
    id_texture          = 'Texture'           ,
    id_text             = 'Text'              ,
    id_vfont            = 'VFont'             ,
    id_volume           = 'Volume'            ,
    id_world            = 'World'             ,
    id_workspace        = 'WorkSpace'         ,
    id_windowmanager    = 'WindowManager'
}
'''

translations_tuple = ()                                                                                                                                                                                                                                                                                                                                                                     
# {locale: {msg_key: msg_translation, ...}, ...}                                                                                                                                                      
# locale is either a lang iso code (fr), a lang+country code (pt_BR), a lang+variant code (sr@latin), or a full code (uz_UZ@cyrilic).                                                                 
# msg_key is a tupple of (context, org_message)                                                                                                                                                       
base_translations_dict = {}

translations_folder = os.path.join(os.path.dirname(__file__), "translations")
for lang in os.listdir(translations_folder):
    lang_dict = base_translations_dict.get(lang)
    if not lang_dict:
        lang_dict = dict()
        base_translations_dict[lang] = lang_dict

    lang_folder = os.path.join(translations_folder, lang)
    for csv_file_name in os.listdir(lang_folder):
        _, ext = os.path.splitext(csv_file_name)
        if ext.lower() != ".csv":
            continue
        
        csv_file_path = os.path.join(lang_folder, csv_file_name)
        with open(csv_file_path, 'rt', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                if row[0].lstrip()[0] == "#":
                    # ignore comments
                    continue

                key   = (row[0], row[1])
                value = row[2]
                lang_dict[key] = value


translations_dict = base_translations_dict.copy()
for msg in translations_tuple:
    key = msg[0]
    for lang, trans, (is_fuzzy, comments) in msg[2:]:
        if trans and not is_fuzzy:
            translations_dict.setdefault(lang, {})[key] = trans