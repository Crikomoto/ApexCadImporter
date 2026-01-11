"""
Operators for ApexCadImporter
Import and re-tessellation operators
"""

import bpy
from bpy.props import StringProperty, EnumProperty, FloatProperty, BoolProperty, IntProperty
from bpy_extras.io_utils import ImportHelper
import os
from . import importer


class APEXCAD_OT_ImportCAD(bpy.types.Operator, ImportHelper):
    """Import STEP/IGES CAD files using FreeCAD backend"""
    bl_idname = "import_scene.apexcad"
    bl_label = "Import STEP/IGES"
    bl_description = "Import CAD files (STEP/IGES) with FreeCAD backend"
    bl_options = {'REGISTER', 'UNDO'}
    
    # File browser properties
    filename_ext = ".stp"
    filter_glob: StringProperty(
        default="*.stp;*.step;*.igs;*.iges",
        options={'HIDDEN'},
    )
    
    # Import options
    scale_preset: EnumProperty(
        name="Scale",
        description="Unit scale conversion",
        items=[
            ('0.001', "mm → m (0.001)", "Millimeters to Meters"),
            ('0.01', "cm → m (0.01)", "Centimeters to Meters"),
            ('1.0', "m → m (1.0)", "Meters to Meters (no scale)"),
            ('0.0254', "inch → m (0.0254)", "Inches to Meters"),
            ('CUSTOM', "Custom", "Custom scale factor"),
        ],
        default='0.001',
    )
    
    custom_scale: FloatProperty(
        name="Custom Scale",
        description="Custom scale factor",
        default=1.0,
        min=0.0001,
        max=1000.0,
    )
    
    hierarchy_mode: EnumProperty(
        name="Hierarchy Mode",
        description="How to organize imported objects",
        items=[
            ('COLLECTION', "Collections", "Use Blender Collections for hierarchy"),
            ('EMPTY', "Empty Objects", "Use Empty objects for hierarchy"),
        ],
        default='COLLECTION',
    )
    
    y_up: BoolProperty(
        name="Y-Up Conversion",
        description="Convert CAD Z-up coordinate system to Blender Y-up",
        default=True,
    )
    
    tessellation_quality: FloatProperty(
        name="Mesh Quality",
        description="Tessellation quality (lower = better quality, slower import)",
        default=0.1,
        min=0.01,
        max=5.0,
    )
    
    def execute(self, context):
        # Get preferences
        prefs = context.preferences.addons[__package__].preferences
        
        # Determine scale
        if self.scale_preset == 'CUSTOM':
            scale = self.custom_scale
        else:
            scale = float(self.scale_preset)
        
        # Get chunk size from preferences
        chunk_size = prefs.max_chunk_size
        
        # Import file
        success, message, imported_objects = importer.import_cad_file(
            context,
            self.filepath,
            scale=scale,
            hierarchy_mode=self.hierarchy_mode,
            y_up=self.y_up,
            chunk_size=chunk_size,
            tessellation_quality=self.tessellation_quality
        )
        
        if success:
            self.report({'INFO'}, message)
            
            # Select imported objects
            bpy.ops.object.select_all(action='DESELECT')
            for obj in imported_objects:
                if obj:
                    obj.select_set(True)
            
            if imported_objects:
                context.view_layer.objects.active = imported_objects[0]
            
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
    
    def draw(self, context):
        layout = self.layout
        
        # Scale settings
        box = layout.box()
        box.label(text="Scale Settings:", icon='EMPTY_ARROWS')
        box.prop(self, "scale_preset", text="")
        if self.scale_preset == 'CUSTOM':
            box.prop(self, "custom_scale")
        
        # Hierarchy settings
        box = layout.box()
        box.label(text="Hierarchy:", icon='OUTLINER')
        box.prop(self, "hierarchy_mode", text="")
        
        # Coordinate system
        box = layout.box()
        box.label(text="Coordinate System:", icon='ORIENTATION_GLOBAL')
        box.prop(self, "y_up")
        
        # Quality settings
        box = layout.box()
        box.label(text="Mesh Quality:", icon='MOD_TRIANGULATE')
        box.prop(self, "tessellation_quality", slider=True)
        box.label(text="Lower values = Better quality (slower)", icon='INFO')


class APEXCAD_OT_Retessellate(bpy.types.Operator):
    """Re-tessellate selected CAD object with different quality settings"""
    bl_idname = "object.apexcad_retessellate"
    bl_label = "Re-tessellate CAD Object"
    bl_description = "Re-import selected object with different tessellation quality (non-destructive)"
    bl_options = {'REGISTER', 'UNDO'}
    
    tessellation_quality: FloatProperty(
        name="New Quality",
        description="New tessellation quality (lower = better)",
        default=0.05,
        min=0.01,
        max=5.0,
    )
    
    @classmethod
    def poll(cls, context):
        """Only enable if selected object was imported by ApexCad"""
        obj = context.active_object
        return obj and obj.get('apexcad_can_retessellate', False)
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or not obj.get('apexcad_can_retessellate'):
            self.report({'ERROR'}, "Selected object is not a CAD import")
            return {'CANCELLED'}
        
        # TODO: Implement re-tessellation
        # This would require storing original CAD file info and re-importing specific part
        
        self.report({'INFO'}, "Re-tessellation feature coming soon")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "tessellation_quality", slider=True)
        layout.label(text="This will re-import the object from CAD source", icon='INFO')


class APEXCAD_OT_ShowImportStats(bpy.types.Operator):
    """Show statistics about imported CAD objects"""
    bl_idname = "object.apexcad_show_stats"
    bl_label = "CAD Import Statistics"
    bl_description = "Show metadata and statistics for CAD objects"
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        obj = context.active_object
        
        # Collect CAD metadata
        cad_props = {}
        for key in obj.keys():
            if key.startswith('cad_'):
                cad_props[key] = obj[key]
        
        if cad_props:
            print("\n" + "="*50)
            print(f"CAD Metadata for: {obj.name}")
            print("="*50)
            for key, value in cad_props.items():
                print(f"  {key}: {value}")
            print("="*50 + "\n")
            
            self.report({'INFO'}, f"Found {len(cad_props)} metadata properties (see console)")
        else:
            self.report({'INFO'}, "No CAD metadata found on this object")
        
        return {'FINISHED'}


# Registration
classes = (
    APEXCAD_OT_ImportCAD,
    APEXCAD_OT_Retessellate,
    APEXCAD_OT_ShowImportStats,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
