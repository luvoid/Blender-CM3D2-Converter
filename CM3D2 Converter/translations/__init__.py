import os
import sys
import csv
import bpy
import re
import unicodedata
from bl_i18n_utils import settings as bl_i18n_settings
from .. import compat

# get_true_locale() -> Returns the locale
# get_locale()      -> Returns the closest locale available for translation 

DICT = dict() # The translations dictionary
# {locale: {msg_key: msg_translation, ...}, ...}                                                                                                                                                      
# locale is either a lang iso code (fr), a lang+country code (pt_BR), a lang+variant code (sr@latin), or a full code (uz_UZ@cyrilic).                                                                 
# msg_key is a tupple of (context, org_message)

# max level of verbose messages to print. -1 = Nothing.
verbosity = 0
dump_messages = True

is_verify_contexts  = False
is_check_duplicates = False

handled_locales   = set()
translations_folder = os.path.dirname(__file__)
comments_dict = dict()

csv.register_dialect('cm3d2_converter',
    delimiter        = ','            ,
    doublequote      = False          ,
    escapechar       = '\\'           ,
    lineterminator   = '\n'           ,
    quotechar        = '"'            ,
    quoting          = csv.QUOTE_ALL  ,
    skipinitialspace = False          ,
    strict           = True         
)


i18n_contexts = { identifer: getattr(bpy.app.translations.contexts, identifer) for identifer in bpy.app.translations.contexts_C_to_py.values() }
'''
i18n_contexts = {
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
    if key in DICT[lang].keys():
        return True
    else:
        return False


def get_best_locale_match(locale: str, available=handled_locales) -> str:
    # First check for exact locale tag match
    if locale in available:
        return locale
    
    # Otherwise match based on language, country, or variant.
    match = 'en_US' # default is English as per Blender Dev's recomendations
    affinity = 0
    for locale_tag in DICT.keys():
        language, country, variant, language_country, language_variant = bpy.app.translations.locale_explode(locale_tag)
        
        if   affinity < 4 and language_variant in available:
            affinity  = 4
            match     = locale_tag
        elif affinity < 3 and language_country in available:
            affinity  = 3
            match     = locale_tag
        elif affinity < 2 and language in available:
            affinity  = 2
            match     = locale_tag
        elif affinity < 1 and country in available:
            affinity  = 1
            match     = locale_tag
        # Not worth checking variant alone
        #elif affinity < 0 and variant          in available: 
        #    match    = locale_tag
        #    affinity = 0
    
    return match

def generate_translations(locale: str):
    if False:
        # Handle any special generations here
        # e.g. Using Spanish for Portuguese because they are similar
        #      even though they won't be detected by get_best_locale_match()
        pass
    else:
        # If not specially handled, fill it with best match
        match = get_best_locale_match(locale)
        DICT[locale] = DICT[match]


def get_true_locale() -> str:
    true_locale = ''
    if bpy.app.translations.locale:
        true_locale = bpy.app.translations.locale
    else: # if built without internationalization support
        try:
            import locale
            if system.language =='DEFAULT':
                true_locale = locale.getdefaultlocale()[0]
        except Exception as e: 
            print("Unable to determine locale.", e)
    return true_locale

def get_locale() -> str:
    return get_best_locale_match(get_true_locale())


src_path_pattern = re.compile(r":?\d+$")
py_path_pattern  = re.compile(
    r"(?:bpy\.types)?"
    r"(?:\.|\:|\[[\'\"])" # find a dot, colon, or bracket-reference
    r"([^\.]+?)"          # capture identifier of module/class/attribute
    r"(?:[\'\"]\])?"      # consume any closing brackets or quotes
    r"(?=\.|\:|$)"        # look-ahead for a . or : or the end of the string
)
comment_pattern  = re.compile(r"#\s")
class_hash_dict = dict()
def get_message_source_file(src):
    if not src.startswith('bpy.'):
        file_name = os.path.basename(src)
        file_name = src_path_pattern.sub("", file_name)
        return file_name
    else:
        cls_name = py_path_pattern.match(src)[1]
        if not class_hash_dict:
            for cls in compat.BlRegister.classes:
                class_hash_dict[cls.__name__.lower()] = cls
        
        cls = class_hash_dict.get(cls_name.lower()) # apparently blender changes the case of our classnames sometimes
        if not cls:

            return cls_name

        module_name, file_name = os.path.splitext(cls.__module__)
        if not file_name:
            return "__init__.py"
        elif file_name == "translations":
            return "translations/__init__.py"
        else:
            return file_name[1:] + ".py"

def message_to_csv_line(msg, add_sources=False):
    line = [msg.msgctxt, msg.msgid, msg.msgstr]
    
    sources = f'FROM <{" & ".join(get_message_source_file(src) for src in msg.sources)}>' if add_sources else ""
    comment = comment_pattern.sub("", msg.comment_lines[-1]) if msg.is_commented else ""
    if sources or comment:
        if not sources or sources in comment:
            line.append(f"# {comment}")
        elif not comment:
            line.append(f"# {sources}")
        else:
            line.append(f"# {sources} {comment}")

    class filestring:
        def __init__(self, string:str=""):
            self.string = string

        def write(self, text):
            if type(text) == bytes:
                text = text.decode('utf-8')
            self.string += text

        trans = str.maketrans({'\n':'', '\r':''})
        def str(self):
            return self.string.translate(self.trans)

    string = filestring("")
    csv_writer = csv.writer(string, dialect='cm3d2_converter')
    csv_writer.writerow(line)

    return string.str()

def messages_to_csv(msgs, reports, lang=get_locale(), only_missing=True):
    lang_dict = DICT.get(lang)
    text_data = "Context,Original,Translation,Comments\n" \
                "# encoding UTF-8"
    last_src = None
    shared = []

    messages = sorted(
        ( (key, msg, get_message_source_file(msg.sources[0])) for key, msg in msgs.items() ),
        key = lambda x : x[2]
    )
    for key, msg, src in messages:
        msg.normalize()
        key_check = (msg.msgctxt, msg.msgid)
        if key_check != key:
            print(f"A message with a mismatching key was found: {key} != {key_check}")
        if lang_dict and lang_dict.get(key):
            if only_missing:
                continue
            msg.msgstr = msg.msgstr or lang_dict[key]
            comment = comments_dict[lang].get(key)
            if comment:
                msg.comment_lines.append(comment)
                msg.is_commented = True

        sources = msg.sources
        if 'KM_HIERARCHY' in sources[0]:
            continue
        if len(sources) > 1:
            new_src = get_message_source_file(sources[0])
            if any(get_message_source_file(sub_src) != new_src for sub_src in sources):
                shared.append(msg)
                continue
        
        #src = get_message_source_file(msg.sources[0])
        if src != last_src:
            last_src = src
            text_data = f"{text_data}\n# {src}"
        text_data = f"{text_data}\n{message_to_csv_line(msg)}"

    if len(shared) > 0:
        text_data = f"{text_data}\n# shared"
        for msg in shared:
            text_data = f"{text_data}\n{message_to_csv_line(msg, add_sources=True)}"

    return text_data

def reports_to_csv(reports):
    text_data = "### Generated Reports ###"
    for key, value in reports.items():
        text_data = f"{text_data}\n## {key} ##"
        if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
            for value_item in value:
                text_data = f"{text_data}\n{str(value_item)}"
        else:
            text_data = f"{text_data}\n{str(value)}"
    
    return text_data

# bpy.ops.cm3d2_converter.dump_py_messages(do_checks=False, only_missing=True, language='en_US')
@compat.BlRegister()
class CNV_OT_dump_py_messages(bpy.types.Operator):
    bl_idname      = 'cm3d2_converter.dump_py_messages'
    bl_label       = "Dump Py Messages"
    bl_description = "Dump the CM3D2 Converter's messages for CSV translation"
    bl_options     = {'REGISTER', 'UNDO'}

    do_checks    = bpy.props.BoolProperty(name="Do Checks"   , default=False)
    do_reports   = bpy.props.BoolProperty(name="Do Reports"  , default=False)
    only_missing = bpy.props.BoolProperty(name="Only Missing", default=False)
    only_foreign = bpy.props.BoolProperty(name="Only Foreign", default=False)
    
    items = { 
        (enum_str, enum_name, "", 'NONE', enum_int) \
            for enum_int, enum_name, enum_str in bl_i18n_settings.LANGUAGES
    }
    language = bpy.props.EnumProperty(items=items, name="Language", default=get_locale())
    
    @classmethod
    def poll(cls, context):
        return True

    @staticmethod
    def is_japanese(string):
        for ch in string:
            name = unicodedata.name(ch)
            if 'CJK UNIFIED' in name or 'HIRAGANA' in name or 'KATAKANA' in name:
                return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'do_checks')
        self.layout.prop(self, 'do_reports')
        self.layout.prop(self, 'only_missing')
        self.layout.prop(self, 'language')
        row = self.layout.row()
        row.prop(self, 'only_foreign')
        row.enabled = self.language in ('en_US', 'ja_JP')

    def execute(self, context):
        from . import extract_messages

        msgs = dict()
        reports = extract_messages._gen_reports(
            extract_messages._gen_check_ctxt(bl_i18n_settings) if self.do_checks else None
        )

        extract_messages.dump_rna_messages(
            msgs       = msgs,
            reports    = reports,
            settings   = bl_i18n_settings,
            verbose    = False,
            class_list = compat.BlRegister.classes
        )

        extract_messages.dump_py_messages(
            msgs        = msgs, 
            reports     = reports,
            addons      = [__import__("CM3D2 Converter")],
            settings    = bl_i18n_settings,
            addons_only = True
        )

        # Clean un-wanted messages
        for key in tuple(msgs.keys()):
            msg = msgs.pop(key)
            if '_OT_' in msg.msgid:
                continue
            if self.only_foreign:
                is_ja = self.is_japanese(msg.msgid)
                if is_ja and 'ja' in self.language:
                    continue
                if not is_ja and 'en' in self.language:
                    continue
            # else put it back
            msgs[key] = msg

        txt_data = messages_to_csv(msgs, reports, lang=self.language, only_missing=self.only_missing)
        txt_name = "cm3d2_messages_csv"
        if txt_name in context.blend_data.texts:
            txt = context.blend_data.texts[txt_name]
            txt.clear()
        else:
            txt = context.blend_data.texts.new(txt_name)
        txt.write(txt_data)

        if self.do_reports:
            reports_txt_data = reports_to_csv(reports)
            reports_txt_name = "cm3d2_message_reports"
            if reports_txt_name in context.blend_data.texts:
                reports_txt = context.blend_data.texts[reports_txt_name]
                reports_txt.clear()
            else:
                reports_txt = context.blend_data.texts.new(reports_txt_name)
            reports_txt.write(reports_txt_data)

        self.report(type={'INFO'}, message="Strings have been dumped to {txt_name}. See text editor.".format(txt_name=txt_name))

        return {'FINISHED'}



pre_settings = None

def register(__name__=__name__):
    global DICT
    global comments_dict
    global pre_settings
    system = compat.get_system(bpy.context)
    if hasattr(system, 'use_international_fonts'):
        pre_settings = system.use_international_fonts
        system.use_international_fonts = True

    # Work around for disabled translations when language is 'en_US'
    elif bpy.app.version >= (2, 83, 0) and bpy.app.version <= (2, 91, 2): # might be fixed in some future release
        if system.language == 'en_US':
            pre_settings = system.language
            system.language = 'DEFAULT'
            # This hack is required because when language is changed to 'DEFAULT'
            #   all the options will be set to false next time Blender updates
            def _set():
                system.use_translate_tooltips     = True
                system.use_translate_interface    = True
                system.use_translate_new_dataname = True
            bpy.app.timers.register(_set, first_interval=0)

    # Generate locales from csv files
    for lang in os.listdir(translations_folder):
        lang_folder = os.path.join(translations_folder, lang)
        if not os.path.isdir(lang_folder):
            continue
        if lang.startswith("_") or lang.startswith("."):
            continue

        print_verbose(0, "Loading translations for", lang)
        lang_dict = DICT.get(lang)
        if not lang_dict:
            lang_dict = dict()
            DICT[lang] = lang_dict
            comments_dict[lang] = dict()
        
        orig_count = len(lang_dict)
        for csv_file_name in os.listdir(lang_folder):
            _, ext = os.path.splitext(csv_file_name)
            if ext.lower() != ".csv":
                continue
            
            print_verbose(1, f"Reading {csv_file_name}")
            entry_count = 0
            dupe_count  = 0
            csv_file_path = os.path.join(lang_folder, csv_file_name)
            with open(csv_file_path, 'rt', encoding='utf-8', newline='') as csv_file:
                csv_reader = csv.reader(csv_file, dialect='cm3d2_converter')
                try:
                    for line, row in enumerate(csv_reader):
                        if line == 0: # ignore header
                            continue
                        if len(row) < 3:
                            continue
                        if row[0].lstrip()[0] == "#":
                            # ignore comments
                            continue
                        if row[0] not in i18n_contexts.values():
                            print_verbose(2, f"Unknown translation context \"{row[0]}\" on line {line}")

                        key = (row[0], row[1])
                        if check_duplicate(key, lang):
                            print_verbose(2, f"Duplicate entry on line {line}")
                            entry_count -= 1
                            dupe_count  += 1

                        value = row[2]
                        lang_dict[key] = value
                        entry_count += 1

                        if len(row) > 3: # entry comment
                            comments_dict[lang][key] = row[3]

                        print_verbose(3, f"{line:{4}} {key}: {value}")
                except Error as e:
                    print(f"Error parsing {csv_file_name} in {lang_folder}:")
                    print(e)

            print_verbose(1, f"-> Added {entry_count} translations from {csv_file_name}")
            if is_check_duplicates:
                print_verbose(1, f"-> Replaced {dupe_count} translations with {csv_file_name}")
        print_verbose(0, f"-> Added {len(lang_dict) - orig_count} translations for {lang}")


    # Any special translations that use another as a base should handle that here
    
    # End special translations

    handled_locales = { lang for lang in DICT.keys() }


    # Fill missing translations
    print_verbose(0, f"Generating missing translations...")
    gen_count = 0
    for lang in bpy.app.translations.locales:
        if lang not in DICT.keys():
            print_verbose(1, f"Generating translations for '{lang}'")
            generate_translations(lang)
            gen_count += 1
    # For when system.language == 'DEFAULT'
    true_locale = get_true_locale()
    if true_locale not in DICT.keys():
        print_verbose(1, f"Generating translations for '{true_locale}'")
        generate_translations(true_locale)
        gen_count += 1
    print_verbose(0, f"-> Generated {gen_count} missing translations")

    bpy.app.translations.register(__name__, DICT)

def unregister(__name__=__name__):
    DICT = dict()
    handled_locales = set()
    bpy.app.translations.unregister(__name__)

    global pre_settings
    if pre_settings != None:
        system = compat.get_system(bpy.context)
        if hasattr(system, 'use_international_fonts'):
            system.use_international_fonts = pre_settings
        
        if bpy.app.version >= (2, 83, 0):
            system.language = pre_settings

    pre_settings = None


if __name__ == "__main__":
    register()