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

''' *QUICK TIP* 
    It may not look like it, but most of this is char-aligned so you can use "Alt Block" selections. 
    (Probably looks off due to mixture of full & half-width characters. A special font might fix that.) 
'''
# {locale: {msg_key: msg_translation, ...}, ...}
# locale is either a lang iso code (fr), a lang+country code (pt_BR), a lang+variant code (sr@latin), or a full code (uz_UZ@cyrilic).
# msg_key is a tupple of (context, org_message)
base_translations_dict = {
    'en_US': {
        # bl_info                                                                  
        (contexts.default, "ファイル > インポート/エクスポート > CM3D2 Model (.model)"):
                                "File > Import/Export > CM3D2 Model (.model)",
        (contexts.default, "カスタムメイド3D2/カスタムオーダーメイド3D2専用ファイルのインポート/エクスポートを行います"):
                                "A plugin dedicated to the editing, importing, and exporting of CM3D2 .model Files.",
        #
        # Addon-Preferences	                                                                                          
        #                              JP                                                                             # : EN                                                                          
        (contexts.default            , "CM3D2インストールフォルダ"                                                              ) : "CM3D2 Location"                                                            ,
        (contexts.default            , "変更している場合は設定しておくと役立つかもしれません"                                                   ) : "You should set the correct directory if you used a different one."         ,
        (contexts.default            , "バックアップの拡張子 (空欄で無効)"                                                           ) : "Backup Extension (Must not be left blank)"                                 ,
        (contexts.default            , "エクスポート時にバックアップを作成時この拡張子で複製します、空欄でバックアップを無効"                                   ) : "The previous Model file with the same name will be given an extension."    ,
        (contexts.default            , "倍率"                                                                           ) : "Scale"                                                                     ,
        (contexts.default            , "Blenderでモデルを扱うときの拡大率"                                                         ) : "The scale at which the models are imported and exported"                   ,
        (contexts.default            , "基本的にボーン名/ウェイト名をBlender用に変換"                                                   ) : "Convert weight names for Blender"                                          ,
        (contexts.default            , "modelインポート時にボーン名/ウェイト名を変換するかどうかのオプションのデフォルトを設定します"                            ) : "Will change the options default when importing or exporting."              ,
        (contexts.default            , "modelファイル置き場"                                                                 ) : "Model Default Path"                                                        ,
        (contexts.default            , "設定すれば、modelを扱う時は必ずここからファイル選択を始めます"                                            ) : "If set. The file selection will open here."                                ,
        (contexts.default            , "modelインポート時のデフォルトパス"                                                          ) : "Model Default Import Path"                                                 ,
        (contexts.default            , "modelインポート時に最初はここが表示されます、インポート毎に保存されます"                                       ) : "When importing a .model file. The file selection prompt will begin here."  ,
        (contexts.default            , "modelエクスポート時のデフォルトパス"                                                         ) : "Model Default Export Path"                                                 ,
        (contexts.default            , "modelエクスポート時に最初はここが表示されます、エクスポート毎に保存されます"                                     ) : "When exporting a .model file. The file selection prompt will begin here."  ,
        (contexts.default            , "anmファイル置き場"                                                                   ) : ".anm Default Path"                                                         ,
        (contexts.default            , "設定すれば、anmを扱う時は必ずここからファイル選択を始めます"                                              ) : "If set. The file selection will open here."                                ,            
        (contexts.default            , "anmインポート時のデフォルトパス"                                                            ) : ".anm Default Import Path"                                                  ,            
        (contexts.default            , "anmインポート時に最初はここが表示されます、インポート毎に保存されます"                                         ) : "When importing a .anm file. The file selection prompt will begin here."    ,            
        (contexts.default            , "anmエクスポート時のデフォルトパス"                                                           ) : ".anm Default Export Path"                                                  ,            
        (contexts.default            , "anmエクスポート時に最初はここが表示されます、エクスポート毎に保存されます"                                       ) : "When exporting a .anm file. The file selection prompt will begin here."    ,            
        (contexts.default            , "texファイル置き場"                                                                   ) : ".tex Default Path"                                                         ,            
        (contexts.default            , "設定すれば、texを扱う時は必ずここからファイル選択を始めます"                                              ) : "If set. The file selection will open here."                                ,            
        (contexts.default            , "texインポート時のデフォルトパス"                                                            ) : ".tex Default Import Path"                                                  ,            
        (contexts.default            , "texインポート時に最初はここが表示されます、インポート毎に保存されます"                                         ) : "When importing a .tex file. The file selection prompt will begin here."    ,            
        (contexts.default            , "texエクスポート時のデフォルトパス"                                                           ) : ".tex Default Export Path"                                                  ,            
        (contexts.default            , "texエクスポート時に最初はここが表示されます、エクスポート毎に保存されます"                                       ) : "When exporting a .tex file. The file selection prompt will begin here."    ,            
        (contexts.default            , "mateファイル置き場"                                                                  ) : ".mate Default Path"                                                        ,            
        (contexts.default            , "設定すれば、mateを扱う時は必ずここからファイル選択を始めます"                                             ) : "If set. The file selection will open here."                                ,            
        (contexts.default            , "同じ設定値が2つ以上ある場合削除"                                                             ) : "Delete if there are two or more same values"                               ,            
        (contexts.default            , "_ShadowColor など"                                                              ) : "_ShadowColor"                                                              ,            
        (contexts.default            , "mateインポート時のデフォルトパス"                                                           ) : ".mate Default Import Path"                                                 ,            
        (contexts.default            , "mateインポート時に最初はここが表示されます、インポート毎に保存されます"                                        ) : "When importing a .mate file. The file selection prompt will begin here."   ,            
        (contexts.default            , "mateエクスポート時のデフォルトパス"                                                          ) : ".mate Default Export Path"                                                 ,            
        (contexts.default            , "mateエクスポート時に最初はここが表示されます、エクスポート毎に保存されます"                                      ) : "When exporting a .mate file. The file selection prompt will begin here."   ,            
        (contexts.default            , "基本的にtexファイルを探す"                                                               ) : "Search for Tex File"                                                       ,            
        (contexts.default            , "texファイルを探すかどうかのオプションのデフォルト値を設定します"                                            ) : "Sets the default of the option to search for tex files"                    ,            
        (contexts.default            , "texファイル置き場"                                                                   ) : "Tex file search area"                                                      ,            
        (contexts.default            , "texファイルを探す時はここから探します"                                                         ) : "Search here for tex files"                                                 ,            
        (contexts.default            , "CM3D2用法線のブレンド率"                                                               ) : "Custom Normal Blend"                                                       ,            
        (contexts.default            , "無変更シェイプキーをスキップ"                                                               ) : "Skip Unchanged Shape Keys"                                                 ,            
        (contexts.default            , "ベースと同じシェイプキーを出力しない"                                                           ) : "Shapekeys that are the same as the basis shapekey will not be imported."   ,            
        (contexts.default            , "モディファイアを適用"                                                                   ) : "Apply Modifiers"                                                           ,            
        (contexts.default            , "テクスチャのオフセット"                                                                  ) : "Texture Offset"                                                            ,            
        (contexts.default            , "テクスチャのスケール"                                                                   ) : "Texture Scale"                                                             ,            
        (contexts.default            , "_ToonRamp 名前"                                                                 ) : "_ToonRamp Name"                                                            ,            
        (contexts.default            , "_ToonRamp パス"                                                                 ) : "_ToonRamp Path"                                                            ,            
        (contexts.default            , "_ShadowRateToon 名前"                                                           ) : "_ShadowRateToon Name"                                                      ,            
        (contexts.default            , "_OutlineToonRamp パス"                                                          ) : "_OutlineToonRamp Path"                                                     ,            
        (contexts.default            , "_ShadowRateToon パス"                                                           ) : "_ShadowRateToon Path"                                                      ,            
        (contexts.default            , "_OutlineToonRamp 名前"                                                          ) : "_OutlineToonRamp Name"                                                     ,            
        #                                                                                                                             
        #Addon-Preferences.draw                                                                                                                                            
        #                              JP                                                                             # : EN                                                                                                                      
        (contexts.default            , "ここの設定は「ユーザー設定の保存」ボタンを押すまで保存されていません"                                           ) : "You must press 'Save User Settings' button for these settings to be saved.",                                                                                                                                     
        (contexts.default            , "設定値を変更した場合、「プリファレンスを保存」ボタンを押下するか、「プリファレンスを自動保存」を有効にして保存してください"                ) : "If you changed your preferences, remember to save them before exiting."    ,                                                                                                                                     
        (contexts.default            , "modelファイル"                                                                    ) : ".Model File"                                                               ,                                                                                                                                     
        (contexts.default            , "ファイル選択時の初期フォルダ"                                                               ) : "Initial folder when selecting files"                                       ,                                                                                                                                     
        (contexts.default            , "anmファイル"                                                                      ) : ".anm File"                                                                 ,                                                                                                                                     
        (contexts.default            , "texファイル"                                                                      ) : "tex file"                                                                  ,                                                                                                                                     
        (contexts.default            , "mateファイル"                                                                     ) : "mate file"                                                                 ,  
        (contexts.default            , "texファイル検索"                                                                    ) : "Search for Tex File"                                                       ,            
        (contexts.default            , "その2"                                                                          ) : "Part 1"                                                                    ,            
        (contexts.default            , "その1"                                                                          ) : "Part 2"                                                                    ,            
        (contexts.default            , "その3"                                                                          ) : "Part 3"                                                                    ,            
        (contexts.default            , "その4"                                                                          ) : "Part 4"                                                                    ,            
        (contexts.default            , "CM3D2用マテリアル新規作成時の初期値"                                                         ) : "Defaults for when a new CM3d2 Material is Created."                        ,            
        (contexts.default            , "各操作の初期パラメータ"                                                                  ) : "Default Export Settings"                                                   ,            
    } # end en_US
}



translations_dict = base_translations_dict.copy()
for msg in translations_tuple:
    key = msg[0]
    for lang, trans, (is_fuzzy, comments) in msg[2:]:
        if trans and not is_fuzzy:
            translations_dict.setdefault(lang, {})[key] = trans