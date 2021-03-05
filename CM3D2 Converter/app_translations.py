import os
import sys
import csv
import bpy
import bpy.app.translations
from bpy.app.translations import contexts

# max level of verbose messages to print. -1 = Nothing.
verbosity = 0

is_verify_contexts  = False
is_check_duplicates = False

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

                                                                                                                                                                                                                                                                                                                                                         
# {locale: {msg_key: msg_translation, ...}, ...}                                                                                                                                                      
# locale is either a lang iso code (fr), a lang+country code (pt_BR), a lang+variant code (sr@latin), or a full code (uz_UZ@cyrilic).                                                                 
# msg_key is a tupple of (context, org_message)                                                                                                                                                       
translations_dict = {}


def print_verbose(level:int, *args, tab:str="\t", sep:str=" ", end:str="\n", file=sys.stdout, flush:bool=False, **format_args) -> None:
    if level > verbosity:
        return
    message = tab * level + sep.join(str(arg) for arg in args)
    if format_args:
        message = message.format(**format_args)
    return print(message, end=end, file=file, flush=flush)

def verify_context(context: str) -> bool:
    if not is_verify_contexts:
        return True

def check_duplicate(key: tuple, lang: str) -> bool:
    if not is_check_duplicates:
        return False
    if key in translations_dict[lang].keys():
        return True
    else:
        return False


translations_folder = os.path.join(os.path.dirname(__file__), "translations")
for lang in os.listdir(translations_folder):
    print_verbose(0, "Loading translations for", lang)
    lang_dict = translations_dict.get(lang)
    if not lang_dict:
        lang_dict = dict()
        translations_dict[lang] = lang_dict
    
    orig_count = len(lang_dict)
    lang_folder = os.path.join(translations_folder, lang)
    for csv_file_name in os.listdir(lang_folder):
        _, ext = os.path.splitext(csv_file_name)
        if ext.lower() != ".csv":
            continue
        
        print_verbose(1, f"Reading {csv_file_name}")
        entry_count = 0
        dupe_count  = 0
        csv_file_path = os.path.join(lang_folder, csv_file_name)
        with open(csv_file_path, 'rt', encoding='utf-8') as csv_file:
            csv_reader = csv.reader(csv_file)
            for line, row in enumerate(csv_reader):
                if line == 0: # ignore header
                    continue
                if len(row) < 3:
                    continue
                if row[0].lstrip()[0] == "#":
                    # ignore comments
                    continue
                if row[0] != "*":
                    print_verbose(2, f"Unknown translation context \"{row[0]}\" on line {line}")

                key = (row[0], row[1])
                if check_duplicate(key, lang):
                    print_verbose(2, f"Duplicate entry on line {line}")
                    entry_count -= 1
                    dupe_count  += 1

                value = row[2]
                lang_dict[key] = value
                entry_count += 1

                print_verbose(3, f"{line:{4}} {key}: {value}")

        print_verbose(1, f"-> Added {entry_count} translations from {csv_file_name}")
        if is_check_duplicates:
            print_verbose(1, f"-> Replaced {dupe_count} translations with {csv_file_name}")
    print_verbose(0, f"-> Added {len(lang_dict) - orig_count} translations for {lang}")