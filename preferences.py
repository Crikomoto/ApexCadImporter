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
    
    def search_program_files(self, base_path, executable_name):
        """Search recursively in Program Files for FreeCAD"""
        if not os.path.exists(base_path):
            return None
        
        try:
            # Look for FreeCAD folders
            for item in os.listdir(base_path):
                if 'freecad' in item.lower():
                    freecad_dir = os.path.join(base_path, item)
                    # Check bin folder
                    bin_path = os.path.join(freecad_dir, 'bin', executable_name)
                    if os.path.exists(bin_path):
                        return bin_path
                    # Sometimes it's directly in the folder
                    direct_path = os.path.join(freecad_dir, executable_name)
                    if os.path.exists(direct_path):
                        return direct_path
        except (PermissionError, OSError):
            pass
        
        return None
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        
        print("ApexCad: Searching for FreeCAD installation...")
        
        # Windows-specific detection
        if os.name == 'nt':
            # Try PATH environment first
            try:
                result = subprocess.run(
                    ["where", "FreeCADCmd.exe"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    path = result.stdout.strip().split('\n')[0]
                    if os.path.exists(path):
                        prefs.freecad_path = path
                        self.report({'INFO'}, f"FreeCAD found in PATH: {path}")
                        print(f"ApexCad: Found FreeCAD at {path}")
                        return {'FINISHED'}
            except:
                pass
            
            # Search in Program Files
            program_files_paths = [
                r"C:\Program Files",
                r"C:\Program Files (x86)",
            ]
            
            for base_path in program_files_paths:
                found_path = self.search_program_files(base_path, "FreeCADCmd.exe")
                if found_path:
                    prefs.freecad_path = found_path
                    self.report({'INFO'}, f"FreeCAD found: {found_path}")
                    print(f"ApexCad: Found FreeCAD at {found_path}")
                    return {'FINISHED'}
            
            # Specific common paths as fallback
            common_paths = [
                r"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe",
                r"C:\Program Files\FreeCAD 0.22\bin\FreeCADCmd.exe",
                r"C:\Program Files\FreeCAD 0.20\bin\FreeCADCmd.exe",
                r"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe",
                r"C:\Program Files\FreeCAD\bin\FreeCADCmd.exe",
                r"C:\Program Files (x86)\FreeCAD\bin\FreeCADCmd.exe",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    prefs.freecad_path = path
                    self.report({'INFO'}, f"FreeCAD found: {path}")
                    print(f"ApexCad: Found FreeCAD at {path}")
                    return {'FINISHED'}
        
        # Linux/Mac detection
        else:
            # Try which/whereis
            for cmd in ["freecad", "freecadcmd", "FreeCAD"]:
                try:
                    result = subprocess.run(
                        ["which", cmd],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        path = result.stdout.strip()
                        if os.path.exists(path):
                            prefs.freecad_path = path
                            self.report({'INFO'}, f"FreeCAD found: {path}")
                            print(f"ApexCad: Found FreeCAD at {path}")
                            return {'FINISHED'}
                except:
                    pass
            
            # Common Unix paths
            common_paths = [
                "/usr/bin/freecad",
                "/usr/bin/freecadcmd",
                "/usr/local/bin/freecad",
                "/usr/local/bin/freecadcmd",
                "/opt/freecad/bin/freecad",
                "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD",
                "/Applications/FreeCAD.app/Contents/Resources/bin/FreeCAD",
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    prefs.freecad_path = path
                    self.report({'INFO'}, f"FreeCAD found: {path}")
                    print(f"ApexCad: Found FreeCAD at {path}")
                    return {'FINISHED'}
        
        # Not found
        print("ApexCad: FreeCAD not found in common locations")
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
