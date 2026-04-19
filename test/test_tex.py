import bpy

from .blenderunittest import BlenderTestCase


class TexExportTest(BlenderTestCase):
    def test_export_tex_with_missing_cm3d2_path(self):
        img = bpy.data.images.new("test_export_tex", width=1, height=1)
        self.assertIsNone(img.get('cm3d2_path'))

        override = bpy.context.copy()
        override['edit_image'] = img
        override['window_manager'] = bpy.context.window_manager

        output_path = f"{self.output_dir}/{self._testMethodName}.tex"
        result = bpy.ops.image.export_cm3d2_tex(override, 'EXEC_DEFAULT', filepath=output_path)
        self.assertEqual(result, {'FINISHED'})
