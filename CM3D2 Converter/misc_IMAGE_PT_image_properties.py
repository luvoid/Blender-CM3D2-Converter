# 「UV/画像エディター」エリア → プロパティ → 「画像」パネル
from . import common


# メニュー等に項目追加
def menu_func(self, context):
    img = getattr(context, 'edit_image')
    if img and 'cm3d2_path' in img:
        box = self.layout.box()
        box.label(text="CM3D2用", icon_value=common.kiss_icon())
        box.prop(img, '["cm3d2_path"]', icon='ANIM_DATA', text="内部パス")
