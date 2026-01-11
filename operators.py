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
        description="Tessellation quality (lower = better quality, smoother surfaces). 0.01 = very fine, 1.0 = very coarse",
        default=0.01,
        min=0.001,
        max=5.0,
    )
    
    def execute(self, context):
        # Get preferences
        prefs = context.preferences.addons[__package__].preferences
        
        # Validate FreeCAD path first
        if not prefs.freecad_path:
            self.report({'ERROR'}, "FreeCAD path not configured. Check addon preferences.")
            return {'CANCELLED'}
        
        if not os.path.exists(prefs.freecad_path):
            self.report({'ERROR'}, f"FreeCAD not found at: {prefs.freecad_path}")
            return {'CANCELLED'}
        
        # Validate input file
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, f"Input file not found: {self.filepath}")
            return {'CANCELLED'}
        
        file_size = os.path.getsize(self.filepath) / (1024 * 1024)  # MB
        print(f"ApexCad: Importing {os.path.basename(self.filepath)} ({file_size:.2f} MB)")
        
        # Determine scale
        if self.scale_preset == 'CUSTOM':
            scale = self.custom_scale
        else:
            scale = float(self.scale_preset)
        
        # Get chunk size from preferences
        chunk_size = prefs.max_chunk_size
        
        # Show progress message
        self.report({'INFO'}, f"Starting import... This may take a while.")
        
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
    bl_description = "Re-import selected object with different tessellation quality"
    bl_options = {'REGISTER', 'UNDO'}
    
    tessellation_quality: FloatProperty(
        name="New Quality",
        description="New tessellation quality (lower = better, smoother surfaces)",
        default=0.01,
        min=0.001,
        max=5.0,
    )
    
    @classmethod
    def poll(cls, context):
        """Only enable if selected object was imported by ApexCad"""
        obj = context.active_object
        return obj and obj.get('apexcad_tessellation') is not None
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or not obj.get('apexcad_tessellation'):
            self.report({'ERROR'}, "Selected object is not a CAD import")
            return {'CANCELLED'}
        
        # Get original import info
        original_file = obj.get('apexcad_source_file')
        internal_name = obj.get('apexcad_original_file')
        old_quality = obj.get('apexcad_tessellation', 0.01)
        
        if not original_file or not internal_name:
            self.report({'ERROR'}, "Missing source file information. Re-tessellation not available.")
            return {'CANCELLED'}
        
        if not os.path.exists(original_file):
            self.report({'ERROR'}, f"Source file not found: {original_file}")
            return {'CANCELLED'}
        
        # Check if quality actually changed
        if abs(self.tessellation_quality - old_quality) < 0.0001:
            self.report({'INFO'}, "Quality unchanged")
            return {'CANCELLED'}
        
        print(f"ApexCad: Re-tessellating {obj.name}: {old_quality:.4f} → {self.tessellation_quality:.4f}")
        self.report({'INFO'}, f"Re-importing {obj.name}...")
        
        # Store object state
        obj_name = obj.name
        location = obj.location.copy()
        rotation = obj.rotation_euler.copy()
        scale_vec = obj.scale.copy()
        parent = obj.parent
        materials = [mat for mat in obj.data.materials]
        custom_props = {k: obj[k] for k in obj.keys()}
        
        # Re-import entire file with new quality
        prefs = context.preferences.addons[__package__].preferences
        success, message, imported_objects = importer.import_cad_file(
            context,
            original_file,
            scale=0.001,  # Use stored scale or default
            hierarchy_mode='COLLECTION',
            y_up=True,
            chunk_size=prefs.max_chunk_size,
            tessellation_quality=self.tessellation_quality
        )
        
        if not success:
            self.report({'ERROR'}, f"Re-import failed: {message}")
            return {'CANCELLED'}
        
        # Find the new object with matching internal name
        new_obj = None
        for imported_obj in imported_objects:
            if imported_obj and imported_obj.get('apexcad_original_file') == internal_name:
                new_obj = imported_obj
                break
        
        if new_obj:
            # Delete old object
            bpy.data.objects.remove(obj, do_unlink=True)
            
            # Restore state to new object
            new_obj.name = obj_name
            new_obj.location = location
            new_obj.rotation_euler = rotation
            new_obj.scale = scale_vec
            new_obj.parent = parent
            
            # Select new object
            bpy.ops.object.select_all(action='DESELECT')
            new_obj.select_set(True)
            context.view_layer.objects.active = new_obj
            
            self.report({'INFO'}, f"Re-tessellated {obj_name} successfully")
        else:
            self.report({'WARNING'}, "Re-import successful but couldn't find matching object")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        # Set current tessellation as default
        obj = context.active_object
        if obj and obj.get('apexcad_tessellation'):
            self.tessellation_quality = obj['apexcad_tessellation']
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj and obj.get('apexcad_tessellation'):
            layout.label(text=f"Current: {obj['apexcad_tessellation']:.4f}")
        
        layout.prop(self, "tessellation_quality", slider=True)
        layout.label(text="Lower = Better quality (more faces)", icon='INFO')


class APEXCAD_OT_RetessellateHierarchy(bpy.types.Operator):
    """Re-tessellate entire CAD hierarchy with new quality settings"""
    bl_idname = "object.apexcad_retessellate_hierarchy"
    bl_label = "Re-tessellate Hierarchy"
    bl_description = "Re-import entire CAD assembly with different tessellation quality"
    bl_options = {'REGISTER', 'UNDO'}
    
    tessellation_quality: FloatProperty(
        name="New Quality",
        description="New tessellation quality for all objects",
        default=0.01,
        min=0.001,
        max=5.0,
    )
    
    @classmethod
    def poll(cls, context):
        """Only enable if selected object is part of CAD hierarchy"""
        obj = context.active_object
        return obj and obj.get('apexcad_source_file') is not None
    
    def execute(self, context):
        obj = context.active_object
        source_file = obj.get('apexcad_source_file')
        
        if not source_file or not os.path.exists(source_file):
            self.report({'ERROR'}, "Source file not found")
            return {'CANCELLED'}
        
        # Find all objects from same source file
        objects_to_update = []
        for o in bpy.data.objects:
            if o.get('apexcad_source_file') == source_file:
                objects_to_update.append(o)
        
        if not objects_to_update:
            self.report({'ERROR'}, "No objects found from this source")
            return {'CANCELLED'}
        
        print(f"ApexCad: Re-tessellating {len(objects_to_update)} objects from {os.path.basename(source_file)}")
        self.report({'INFO'}, f"Re-importing {len(objects_to_update)} objects...")
        
        # Delete all objects from this import
        for o in objects_to_update:
            bpy.data.objects.remove(o, do_unlink=True)
        
        # Re-import with new quality
        prefs = context.preferences.addons[__package__].preferences
        success, message, imported_objects = importer.import_cad_file(
            context,
            source_file,
            scale=0.001,
            hierarchy_mode='COLLECTION',
            y_up=True,
            chunk_size=prefs.max_chunk_size,
            tessellation_quality=self.tessellation_quality
        )
        
        if success:
            self.report({'INFO'}, f"Re-tessellated {len(imported_objects)} objects successfully")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Re-import failed: {message}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        obj = context.active_object
        if obj and obj.get('apexcad_tessellation'):
            self.tessellation_quality = obj['apexcad_tessellation']
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if obj:
            source = obj.get('apexcad_source_file', '')
            layout.label(text=f"Source: {os.path.basename(source)}")
            
            # Count objects
            count = sum(1 for o in bpy.data.objects if o.get('apexcad_source_file') == source)
            layout.label(text=f"Objects: {count}", icon='MESH_DATA')
        
        layout.prop(self, "tessellation_quality", slider=True)
        layout.label(text="This will re-import all objects", icon='INFO')


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


class APEXCAD_OT_BatchImport(bpy.types.Operator):
    """Batch import multiple CAD files from a folder"""
    bl_idname = "import_scene.apexcad_batch"
    bl_label = "Batch Import CAD Files"
    bl_description = "Import all STEP/IGES files from a folder"
    bl_options = {'REGISTER'}
    
    directory: StringProperty(
        name="Folder Path",
        description="Folder containing CAD files",
        subtype='DIR_PATH'
    )
    
    tessellation_quality: FloatProperty(
        name="Mesh Quality",
        description="Tessellation quality for all imports",
        default=0.01,
        min=0.001,
        max=5.0,
    )
    
    scale_preset: EnumProperty(
        name="Scale",
        items=[
            ('0.001', "mm → m", ""),
            ('0.01', "cm → m", ""),
            ('1.0', "m → m", ""),
        ],
        default='0.001',
    )
    
    def execute(self, context):
        import glob
        
        if not self.directory or not os.path.exists(self.directory):
            self.report({'ERROR'}, "Invalid folder path")
            return {'CANCELLED'}
        
        # Validate FreeCAD first
        prefs = context.preferences.addons[__package__].preferences
        
        if not prefs.freecad_path:
            self.report({'ERROR'}, "FreeCAD path not configured. Check addon preferences.")
            return {'CANCELLED'}
        
        if not os.path.exists(prefs.freecad_path):
            self.report({'ERROR'}, f"FreeCAD not found at: {prefs.freecad_path}")
            return {'CANCELLED'}
        
        # Find all CAD files (deduplicate in case of duplicates)
        patterns = ['*.stp', '*.step', '*.igs', '*.iges', '*.STP', '*.STEP', '*.IGS', '*.IGES']
        cad_files = set()
        for pattern in patterns:
            cad_files.update(glob.glob(os.path.join(self.directory, pattern)))
        cad_files = sorted(list(cad_files))
        
        if not cad_files:
            self.report({'ERROR'}, f"No CAD files found in {self.directory}")
            return {'CANCELLED'}
        
        print(f"\nApexCad: Batch importing {len(cad_files)} files from {self.directory}")
        print("="*60)
        
        scale = float(self.scale_preset)
        
        # Results tracking
        successful = []
        failed = []
        
        # Create main collection for batch import
        batch_collection = bpy.data.collections.new(f"Batch_{os.path.basename(self.directory)}")
        context.scene.collection.children.link(batch_collection)
        
        # Import each file
        for idx, filepath in enumerate(cad_files, 1):
            filename = os.path.basename(filepath)
            print(f"\n[{idx}/{len(cad_files)}] Importing {filename}...")
            
            try:
                success, message, imported_objects = importer.import_cad_file(
                    context,
                    filepath,
                    scale=scale,
                    hierarchy_mode='COLLECTION',
                    y_up=True,
                    chunk_size=prefs.max_chunk_size,
                    tessellation_quality=self.tessellation_quality
                )
                
                if success:
                    successful.append(filename)
                    print(f"  ✓ {filename} - {len(imported_objects)} objects")
                    
                    # Move to batch collection
                    for obj in imported_objects:
                        if obj and obj.name in context.scene.collection.objects:
                            context.scene.collection.objects.unlink(obj)
                            batch_collection.objects.link(obj)
                else:
                    failed.append((filename, message))
                    print(f"  ✗ {filename} - {message}")
                    
                    # Create error marker collection
                    error_collection = bpy.data.collections.new(f"ERROR_{filename}")
                    batch_collection.children.link(error_collection)
                    
            except Exception as e:
                error_msg = str(e)
                failed.append((filename, error_msg))
                print(f"  ✗ {filename} - Exception: {error_msg}")
                
                # Create error marker collection
                try:
                    error_collection = bpy.data.collections.new(f"ERROR_{filename}")
                    batch_collection.children.link(error_collection)
                except:
                    pass
        
        # Report results
        print("\n" + "="*60)
        print("BATCH IMPORT COMPLETE")
        print(f"  Successful: {len(successful)}/{len(cad_files)}")
        print(f"  Failed: {len(failed)}/{len(cad_files)}")
        
        if failed:
            print("\nFailed files:")
            for filename, error in failed:
                print(f"  - {filename}: {error}")
        
        print("="*60)
        
        if successful:
            self.report({'INFO'}, f"Imported {len(successful)}/{len(cad_files)} files successfully")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "All imports failed")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scale_preset")
        layout.prop(self, "tessellation_quality", slider=True)
        layout.label(text="Failed imports will create error collections", icon='INFO')


class APEXCAD_OT_TestFreeCAD(bpy.types.Operator):
    """Test FreeCAD connection and functionality"""
    bl_idname = "apexcad.test_freecad"
    bl_label = "Test FreeCAD Connection"
    bl_description = "Verify FreeCAD is working correctly"
    
    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        
        if not prefs.freecad_path:
            self.report({'ERROR'}, "FreeCAD path not configured")
            return {'CANCELLED'}
        
        if not os.path.exists(prefs.freecad_path):
            self.report({'ERROR'}, f"FreeCAD not found at: {prefs.freecad_path}")
            return {'CANCELLED'}
        
        # Test version
        try:
            import subprocess
            result = subprocess.run(
                [prefs.freecad_path, "--version"],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                version = result.stdout.strip()[:100]
                self.report({'INFO'}, f"FreeCAD OK: {version}")
                print(f"\nApexCad: FreeCAD test successful")
                print(f"  Path: {prefs.freecad_path}")
                print(f"  Version: {version}\n")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"FreeCAD failed (code {result.returncode})")
                return {'CANCELLED'}
        except subprocess.TimeoutExpired:
            self.report({'ERROR'}, "FreeCAD test timed out (>15s)")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Test failed: {str(e)}")
            return {'CANCELLED'}


# Registration
classes = (
    APEXCAD_OT_ImportCAD,
    APEXCAD_OT_Retessellate,
    APEXCAD_OT_RetessellateHierarchy,
    APEXCAD_OT_BatchImport,
    APEXCAD_OT_ShowImportStats,
    APEXCAD_OT_TestFreeCAD,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
