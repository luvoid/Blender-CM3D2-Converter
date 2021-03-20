import bpy

# Translation functions
_      = bpy.app.translations.pgettext
iface_ = bpy.app.translations.pgettext_iface
tip_   = bpy.app.translations.pgettext_tip
data_  = bpy.app.translations.pgettext_data


def __format_with_translation_function(func):
    # create a new format function using the specified function for translation
    def _format(msgid: str, *args, msgctxt=None, **kwargs) -> str:
        f_msg  = func(msgid=msgid, msgctxt=msgctxt)
        f_args = [
            func(msgid=arg, msgctxt=msgctxt) if type(arg) == str else arg 
            for arg in args 
        ]
        f_kwargs = {
            key: func(msgid=arg, msgctxt=msgctxt) if type(arg) == str else arg
            for key, arg in kwargs.items() 
        }
        return f_msg.format(*f_args, **f_kwargs)

    return _format


# Format translation functions
f_       = __format_with_translation_function( _      )
f_iface_ = __format_with_translation_function( iface_ )
f_tip_   = __format_with_translation_function( tip_   )
f_data_  = __format_with_translation_function( data_  )
