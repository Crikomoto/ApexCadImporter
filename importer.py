"""
CAD File Importer
Main import logic with divide-and-conquer strategy for large files
Preserves hierarchy, metadata, and pivots
"""

import bpy
import os
import tempfile
from . import freecad_bridge
from . import utils


class CADImporter:
    """
    Main importer class for STEP/IGES files
    Implements divide-and-conquer for large assemblies
    """
    
    def __init__(self, context):
        self.context = context
        self.imported_objects = []
        self.object_map = {}  # Maps internal names to Blender objects
        self.collection_map = {}  # Maps names to collections
        
    def import_file(self, filepath, options):
        """
        Import CAD file with specified options
        
        Args:
            filepath: Path to STEP/IGES file
            options: Dict with import options:
                - scale: Scale factor (float)
                - hierarchy_mode: 'EMPTY' or 'COLLECTION'
                - y_up: Convert to Y-up (bool)
                - chunk_size: Max objects per batch (int)
                - tessellation_quality: Mesh quality (float)
        
        Returns:
            (success, message, imported_objects)
        """
        # Get FreeCAD bridge
        bridge, error = freecad_bridge.get_bridge(self.context)
        if error:
            print(f"ApexCad: Bridge error - {error}")
            return False, error, []
        
        # Validate FreeCAD before starting
        print("ApexCad: Validating FreeCAD installation...")
        is_valid, validation_msg = bridge.validate_freecad()
        if not is_valid:
            error_msg = f"FreeCAD validation failed: {validation_msg}"
            print(f"ApexCad: {error_msg}")
            return False, error_msg, []
        
        print(f"ApexCad: FreeCAD validation OK - {validation_msg}")
        
        # Create temporary output directory
        output_dir = tempfile.mkdtemp(prefix="apexcad_import_")
        print(f"ApexCad: Output directory: {output_dir}")
        
        # Prepare conversion options
        conversion_options = {
            'scale': options.get('scale', 1.0),
            'y_up': options.get('y_up', True),
            'tessellation_quality': options.get('tessellation_quality', 0.1),
        }
        
        print(f"ApexCad: Starting import of {os.path.basename(filepath)}")
        print(f"ApexCad: Options: {conversion_options}")
        
        # Convert file using FreeCAD
        print("ApexCad: Starting FreeCAD conversion (this may take a while)...")
        result = bridge.convert_file_sync(filepath, output_dir, conversion_options)
        
        if not result['success']:
            error_msg = result.get('error', 'Unknown error')
            print(f"ApexCad: Conversion failed - {error_msg}")
            return False, error_msg, []
        
        print("ApexCad: FreeCAD conversion completed successfully")
        
        if not result['success']:
            return False, result.get('error', 'Unknown error'), []
        
        # Import into Blender
        hierarchy = result['hierarchy']
        success, message = self._import_hierarchy(hierarchy, options, output_dir)
        
        # Cleanup
        bridge.cleanup()
        
        if success:
            return True, f"Successfully imported {len(self.imported_objects)} objects", self.imported_objects
        else:
            return False, message, []
    
    def _import_hierarchy(self, hierarchy, options, output_dir):
        """
        Import hierarchy into Blender
        Implements divide-and-conquer for large assemblies
        """
        hierarchy_mode = options.get('hierarchy_mode', 'COLLECTION')
        y_up = options.get('y_up', True)
        scale = hierarchy.get('scale', 1.0)
        chunk_size = options.get('chunk_size', 50)
        
        objects_data = hierarchy.get('objects', [])
        root_objects = hierarchy.get('root_objects', [])
        
        if not objects_data:
            return False, "No objects found in file"
        
        print(f"ApexCad: Importing {len(objects_data)} objects...")
        
        # Create main collection/empty for the import
        file_name = os.path.splitext(os.path.basename(options.get('filepath', 'Import')))[0]
        file_name = utils.sanitize_name(file_name)
        
        if hierarchy_mode == 'COLLECTION':
            main_collection = utils.get_collection(self.context, file_name)
            self.collection_map[file_name] = main_collection
            root_parent = None
        else:  # EMPTY mode
            root_parent = utils.create_empty(file_name, collection=self.context.scene.collection)
            self.object_map[file_name] = root_parent
            main_collection = self.context.scene.collection
        
        # Build object map first (for parent references)
        for obj_data in objects_data:
            internal_name = obj_data['internal_name']
            self.object_map[internal_name] = None  # Placeholder
        
        # Process objects in chunks (divide and conquer)
        total_objects = len(objects_data)
        chunks = [objects_data[i:i+chunk_size] for i in range(0, total_objects, chunk_size)]
        
        print(f"ApexCad: Processing in {len(chunks)} chunks of max {chunk_size} objects")
        
        for chunk_idx, chunk in enumerate(chunks):
            print(f"ApexCad: Processing chunk {chunk_idx+1}/{len(chunks)}")
            
            for obj_data in chunk:
                self._import_object(obj_data, hierarchy_mode, main_collection, root_parent, output_dir, scale, y_up)
        
        # Setup parent-child relationships
        print("ApexCad: Building hierarchy...")
        for obj_data in objects_data:
            self._setup_parent_child(obj_data)
        
        # Apply Y-up conversion if needed
        if y_up:
            print("ApexCad: Applying Y-up conversion...")
            for obj in self.imported_objects:
                if obj and obj.type == 'MESH':
                    utils.apply_y_up_conversion(obj)
        
        return True, "Import successful"
    
    def _import_object(self, obj_data, hierarchy_mode, main_collection, root_parent, output_dir, scale, y_up):
        """Import a single object"""
        internal_name = obj_data['internal_name']
        obj_name = utils.sanitize_name(obj_data['name'])
        mesh_file = obj_data.get('mesh_file')
        metadata = obj_data.get('metadata', {})
        transform = obj_data.get('transform', {})
        
        # Get or create collection/parent for this object
        if hierarchy_mode == 'COLLECTION':
            obj_collection = main_collection
            obj_parent = None
        else:
            obj_collection = main_collection
            obj_parent = root_parent
        
        # Import mesh if available
        if mesh_file and os.path.exists(mesh_file):
            location = transform.get('position', [0, 0, 0])
            rotation_quat = transform.get('rotation', None)
            
            # Import OBJ file
            imported_obj = utils.import_obj_file(
                mesh_file,
                obj_name,
                location=location,
                rotation_quat=rotation_quat,
                parent=obj_parent,
                collection=obj_collection,
                scale=scale
            )
            
            if imported_obj:
                # Store metadata as custom properties
                utils.set_custom_properties(imported_obj, metadata)
                
                # Store original tessellation quality for re-tessellation
                imported_obj['apexcad_original_file'] = obj_data.get('internal_name', '')
                imported_obj['apexcad_can_retessellate'] = True
                
                self.object_map[internal_name] = imported_obj
                self.imported_objects.append(imported_obj)
                
                print(f"  ✓ Imported: {obj_name}")
            else:
                print(f"  ✗ Failed to import: {obj_name}")
        else:
            # Create empty placeholder for objects without geometry
            if hierarchy_mode == 'EMPTY':
                location = transform.get('position', [0, 0, 0])
                empty = utils.create_empty(
                    obj_name,
                    location=location,
                    parent=obj_parent,
                    collection=obj_collection
                )
                utils.set_custom_properties(empty, metadata)
                self.object_map[internal_name] = empty
                self.imported_objects.append(empty)
                print(f"  ○ Created empty: {obj_name}")
    
    def _setup_parent_child(self, obj_data):
        """Setup parent-child relationships after all objects are created"""
        internal_name = obj_data['internal_name']
        parent_name = obj_data.get('parent')
        
        if not parent_name:
            return
        
        child_obj = self.object_map.get(internal_name)
        parent_obj = self.object_map.get(parent_name)
        
        if child_obj and parent_obj and child_obj != parent_obj:
            # Only set parent if not already set
            if not child_obj.parent:
                child_obj.parent = parent_obj


def import_cad_file(context, filepath, scale=1.0, hierarchy_mode='COLLECTION', y_up=True, chunk_size=50, tessellation_quality=0.1):
    """
    Convenience function to import CAD file
    
    Args:
        context: Blender context
        filepath: Path to STEP/IGES file
        scale: Scale factor
        hierarchy_mode: 'EMPTY' or 'COLLECTION'
        y_up: Convert to Y-up
        chunk_size: Max objects per chunk
        tessellation_quality: Mesh quality (lower = better quality, slower)
    
    Returns:
        (success, message, imported_objects)
    """
    importer = CADImporter(context)
    
    options = {
        'filepath': filepath,
        'scale': scale,
        'hierarchy_mode': hierarchy_mode,
        'y_up': y_up,
        'chunk_size': chunk_size,
        'tessellation_quality': tessellation_quality,
    }
    
    return importer.import_file(filepath, options)
