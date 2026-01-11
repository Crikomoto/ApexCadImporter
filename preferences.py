"""
Preferences and Settings for ApexCadImporter
Stores FreeCAD path and global import settings
"""

import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty
import os
import subprocess


class APEXCAD_AddonPreferences(AddonPreferences):
    bl_idname = __package__
    
    # FreeCAD executable path
    freecad_path: StringProperty(
        name="FreeCAD Path",
        description="Path to FreeCAD executable (FreeCADCmd or freecad)",
        subtype='FILE_PATH',
        default="",
    )
    
    # Auto-detect FreeCAD on startup
    auto_detect_freecad: BoolProperty(
        name="Auto-Detect FreeCAD",
        description="Automatically search for FreeCAD installation",
        default=True,
    )
    
    # Default import settings
    default_scale: EnumProperty(
        name="Default Scale",
        description="Default scale factor for imports",
        items=[
            ('0.001', "mm to m (0.001)", "Millimeters to Meters"),
            ('0.01', "cm to m (0.01)", "Centimeters to Meters"),
            ('1.0', "m to m (1.0)", "Meters to Meters"),
            ('0.0254', "inch to m (0.0254)", "Inches to Meters"),
        ],
        default='0.001',
    )
    
    default_hierarchy_mode: EnumProperty(
        name="Default Hierarchy",
        description="Default hierarchy organization mode",
        items=[
            ('EMPTY', "Empties", "Use Empty objects for hierarchy"),
            ('COLLECTION', "Collections", "Use Collections for hierarchy"),
        ],
        default='COLLECTION',
    )
    
    default_y_up: BoolProperty(
        name="Y-Up by Default",
        description="Convert Z-up CAD files to Y-up",
        default=True,
    )
    
    # Performance settings
    max_chunk_size: IntProperty(
        name="Max Chunk Size",
        description="Maximum number of parts to process in one batch (divide and conquer)",
        default=50,
        min=1,
        max=500,
    )
    
    use_async_import: BoolProperty(
        name="Async Import",
        description="Use asynchronous import to prevent Blender freeze",
        default=True,
    )
    
    def draw(self, context):
        layout = self.layout
        
        # FreeCAD Configuration
        box = layout.box()
        box.label(text="FreeCAD Configuration:", icon='SETTINGS')
        
        row = box.row()
        row.prop(self, "freecad_path")
        row.operator("apexcad.detect_freecad", text="", icon='VIEWZOOM')
        
        row = box.row()
        row.prop(self, "auto_detect_freecad")
        
        # Check if FreeCAD is valid
        if self.freecad_path:
            if os.path.exists(self.freecad_path):
                box.label(text="✓ FreeCAD found", icon='CHECKMARK')
            else:
                box.label(text="✗ FreeCAD path invalid", icon='ERROR')
        else:
            box.label(text="⚠ FreeCAD path not set", icon='INFO')
        
        # Default Import Settings
        box = layout.box()
        box.label(text="Default Import Settings:", icon='IMPORT')
        box.prop(self, "default_scale")
        box.prop(self, "default_hierarchy_mode")
        box.prop(self, "default_y_up")
        
        # Performance Settings
        box = layout.box()
        box.label(text="Performance Settings:", icon='PREFERENCES')
        box.prop(self, "max_chunk_size")
        box.prop(self, "use_async_import")


class APEXCAD_OT_DetectFreeCAD(bpy.types.Operator):
    """Auto-detect FreeCAD installation"""
    bl_idname = "apexcad.detect_freecad"
    bl_label = "Detect FreeCAD"
    bl_description = "Automatically detect FreeCAD installation"
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        
        # Common FreeCAD installation paths
        common_paths = [
            r"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe",
            r"C:\Program Files\FreeCAD 0.20\bin\FreeCADCmd.exe",
            r"C:\Program Files\FreeCAD\bin\FreeCADCmd.exe",
            r"C:\Program Files (x86)\FreeCAD\bin\FreeCADCmd.exe",
            "/usr/bin/freecad",
            "/usr/bin/freecadcmd",
            "/usr/local/bin/freecad",
            "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD",
        ]
        
        # Check PATH environment
        try:
            result = subprocess.run(
                ["where" if os.name == 'nt' else "which", "freecadcmd" if os.name == 'nt' else "freecad"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip().split('\n')[0]
                if os.path.exists(path):
                    prefs.freecad_path = path
                    self.report({'INFO'}, f"FreeCAD found: {path}")
                    return {'FINISHED'}
        except:
            pass
        
        # Check common installation paths
        for path in common_paths:
            if os.path.exists(path):
                prefs.freecad_path = path
                self.report({'INFO'}, f"FreeCAD found: {path}")
                return {'FINISHED'}
        
        self.report({'WARNING'}, "FreeCAD not found. Please set path manually.")
        return {'CANCELLED'}


# Registration
classes = (
    APEXCAD_AddonPreferences,
    APEXCAD_OT_DetectFreeCAD,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
