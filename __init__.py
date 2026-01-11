"""
ApexCadImporter - Professional STEP and IGES Importer for Blender
Author: Cristian Koch R.
Version: 1.0.0
Description: Native STEP/IGES import using FreeCAD backend with advanced tessellation control

This addon provides robust CAD file import capabilities with:
- Native STEP (.stp, .step) and IGES (.igs, .iges) support
- FreeCAD-powered conversion (non-blocking background processing)
- Hierarchy preservation (Empty or Collection based)
- Metadata transfer from CAD files
- Non-destructive re-tessellation
- Y-up axis conversion
- Scalable architecture for large assemblies (divide and conquer)
"""

bl_info = {
    "name": "ApexCad Importer",
    "author": "Cristian Koch R.",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "File > Import > STEP/IGES (.stp, .igs)",
    "description": "Import STEP and IGES files using FreeCAD backend with advanced control",
    "warning": "Requires FreeCAD installation",
    "doc_url": "https://github.com/Crikomoto/ApexCadImporter",
    "tracker_url": "https://github.com/Crikomoto/ApexCadImporter/issues",
    "category": "Import-Export",
}

import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty, BoolProperty, IntProperty

# Module imports
from . import preferences
from . import operators
from . import ui
from . import freecad_bridge
from . import importer
from . import tessellation
from . import utils

# Modules list for registration
modules = [
    preferences,
    operators,
    ui,
    tessellation,
]


def auto_detect_freecad_delayed():
    """Auto-detect FreeCAD after registration is complete"""
    try:
        prefs = bpy.context.preferences.addons[__package__].preferences
        if prefs.auto_detect_freecad and not prefs.freecad_path:
            print("ApexCad: Auto-detecting FreeCAD installation...")
            bpy.ops.apexcad.detect_freecad()
    except Exception as e:
        print(f"ApexCad: Auto-detect skipped - {e}")
    return None


def register():
    """Register all addon modules and classes"""
    # Register each module
    for module in modules:
        if hasattr(module, 'register'):
            module.register()
    
    # Register file import menu
    bpy.types.TOPBAR_MT_file_import.append(ui.menu_func_import)
    
    # Auto-detect FreeCAD after a short delay (ensures preferences are ready)
    bpy.app.timers.register(auto_detect_freecad_delayed, first_interval=0.1)
    
    print("ApexCadImporter: Successfully registered")


def unregister():
    """Unregister all addon modules and classes"""
    # Unregister file import menu
    bpy.types.TOPBAR_MT_file_import.remove(ui.menu_func_import)
    
    # Unregister each module in reverse order
    for module in reversed(modules):
        if hasattr(module, 'unregister'):
            module.unregister()
    
    print("ApexCadImporter: Successfully unregistered")


if __name__ == "__main__":
    register()
