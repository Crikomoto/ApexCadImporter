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
        options['filepath'] = filepath  # Store for source file reference
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
            # Create root Empty in the collection
            root_parent = utils.create_empty(file_name, collection=main_collection)
        else:  # EMPTY mode
            main_collection = self.context.scene.collection
            # Create root Empty in scene collection
            root_parent = utils.create_empty(file_name, collection=main_collection)
        
        self.object_map[file_name] = root_parent
        
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
                self._import_object(obj_data, hierarchy_mode, main_collection, root_parent, output_dir, scale, y_up, options)
        
        # Setup parent-child relationships
        print("ApexCad: Building hierarchy...")
        print(f"ApexCad: object_map contains {len(self.object_map)} entries")
        
        # Debug: show assemblies in map
        assemblies = {k: v for k, v in self.object_map.items() if v and v.type == 'EMPTY'}
        if assemblies:
            print(f"ApexCad: Found {len(assemblies)} assemblies:")
            for internal_name, obj in list(assemblies.items())[:5]:
                print(f"  - '{internal_name}' → {obj.name}")
            if len(assemblies) > 5:
                print(f"  ... and {len(assemblies) - 5} more")
        
        for obj_data in objects_data:
            self._setup_parent_child(obj_data)
        
        # Reconstruct nested hierarchy from naming patterns
        # STEP files imported by FreeCAD lose nested hierarchy
        # We reconstruct it by matching name prefixes
        print("ApexCad: Reconstructing nested hierarchy from names...")
        self._reconstruct_hierarchy()
        
        # Detect and create instances for optimization
        self._detect_and_create_instances()
        
        # Apply Y-up conversion if needed
        if y_up:
            print("ApexCad: Applying Y-up conversion...")
            
            # Rotate root assembly -180° on X axis for Y-up conversion
            # FreeCAD uses Z-up, Blender uses Y-up
            if root_parent and root_parent.type == 'EMPTY':
                import math
                root_parent.rotation_euler = (math.radians(-180), 0, 0)
                print(f"  ↻ Root rotation: X=-180°")
            
            # Apply mesh conversion
            for obj in self.imported_objects:
                if obj and obj.type == 'MESH':
                    utils.apply_y_up_conversion(obj)
        
        return True, "Import successful"
    
    def _import_object(self, obj_data, hierarchy_mode, main_collection, root_parent, output_dir, scale, y_up, options):
        """Import a single object"""
        internal_name = obj_data['internal_name']
        obj_name = utils.sanitize_name(obj_data['name'])
        mesh_file = obj_data.get('mesh_file')
        metadata = obj_data.get('metadata', {})
        transform = obj_data.get('transform', {})
        obj_type = obj_data.get('type', '')
        is_leaf = obj_data.get('is_leaf', True)
        
        # Create Empties for assemblies (containers without geometry)
        if not mesh_file:
            # For containers (assemblies), create an Empty
            if not is_leaf:
                # Assemblies are at origin since children have world coordinates
                empty = utils.create_empty(
                    obj_name,
                    location=[0, 0, 0],
                    parent=root_parent,
                    collection=main_collection
                )
                
                utils.set_custom_properties(empty, metadata)
                self.object_map[internal_name] = empty
                self.imported_objects.append(empty)
                print(f"  ○ Assembly: {obj_name}")
            else:
                # Leaf without geometry (shouldn't happen after datum filtering)
                print(f"  ⊘ Skipped: {obj_name} (no geometry)")
                self.object_map[internal_name] = None
                self.object_map[internal_name] = None
            return
        
        # Get or create collection/parent for this object
        if hierarchy_mode == 'COLLECTION':
            obj_collection = main_collection
            obj_parent = None
        else:
            obj_collection = main_collection
            obj_parent = root_parent
        
        # Import mesh if available
        if os.path.exists(mesh_file):
            # NOTE: The OBJ file from FreeCAD already has transformations baked in
            # (exported from obj.Shape which is in world space)
            # So we import at origin and don't apply transforms
            
            # Import OBJ file with scale applied to geometry only
            imported_obj = utils.import_obj_file(
                mesh_file,
                obj_name,
                location=[0, 0, 0],  # OBJ already in world space
                rotation_quat=None,   # No additional rotation
                parent=obj_parent,
                collection=obj_collection,
                scale=scale  # Only apply scale to vertices
            )
            
            if imported_obj:
                # Store metadata as custom properties
                utils.set_custom_properties(imported_obj, metadata)
                
                # Store original tessellation quality for re-tessellation
                imported_obj['apexcad_original_file'] = obj_data.get('internal_name', '')
                imported_obj['apexcad_source_file'] = options.get('filepath', '')
                imported_obj['apexcad_tessellation'] = options.get('tessellation_quality', 0.01)
                
                # Apply smooth shading with auto smooth
                utils.apply_smooth_shading(imported_obj, auto_smooth_angle=30)
                
                # Create and assign material if color information exists
                if 'color' in metadata:
                    color = metadata['color']
                    mat_name = f"CAD_{obj_name}"
                    material = utils.create_material_from_color(mat_name, color)
                    
                    # Assign material
                    if imported_obj.data.materials:
                        imported_obj.data.materials[0] = material
                    else:
                        imported_obj.data.materials.append(material)
                
                # Store mesh hash for instance detection
                imported_obj['apexcad_mesh_hash'] = utils.mesh_hash(imported_obj.data)
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
        
        if not child_obj:
            # Object was skipped (reference plane, etc.)
            return
            
        if not parent_obj:
            print(f"  ⚠ Parent not found: {parent_name} (for {child_obj.name})")
            return
        
        if child_obj and parent_obj and child_obj != parent_obj:
            # Solo parentear si no está ya parenteado
            if not child_obj.parent or child_obj.parent != parent_obj:
                child_obj.parent = parent_obj
                child_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()
                print(f"  ↳ Parented: {child_obj.name} → {parent_obj.name}")

    def _reconstruct_hierarchy(self):
        """Reconstruct nested hierarchy from name patterns
        
        STEP files imported by FreeCAD lose assembly Group relationships.
        We reconstruct hierarchy by matching naming conventions:
        - AMS-30-511-xxx belongs under AMS-30-513-000
        - AMS-50-172-xxx belongs under AMS-50-172-000
        """
        # Find all assemblies (Empties)
        assemblies = {}
        for internal_name, obj in self.object_map.items():
            if obj and obj.type == 'EMPTY':
                # Remove .001 suffix to get clean name
                clean_name = obj.name.rsplit('.', 1)[0] if '.' in obj.name else obj.name
                assemblies[clean_name] = (internal_name, obj)
        
        if not assemblies:
            print("ApexCad: No assemblies found for hierarchy reconstruction")
            return
        
        print(f"ApexCad: Found {len(assemblies)} assemblies for matching:")
        for name in list(assemblies.keys())[:5]:
            print(f"  - {name}")
        
        reparented = 0
        # Check all objects
        for internal_name, obj in self.object_map.items():
            if not obj or obj.type == 'EMPTY':  # Skip assemblies themselves
                continue
            
            # Get clean object name
            obj_clean = obj.name.rsplit('.', 1)[0] if '.' in obj.name else obj.name
            
            # Find best matching assembly (longest prefix match)
            best_match = None
            best_score = 0
            
            for asm_name, (asm_internal, asm_obj) in assemblies.items():
                # Skip if it's the same object
                if asm_obj == obj:
                    continue
                
                # Check if object name starts with assembly name prefix
                # Use hyphen-separated matching for CAD naming conventions
                parts_obj = obj_clean.upper().split('-')
                parts_asm = asm_name.upper().split('-')
                
                # Calculate matching score
                score = 0
                for i in range(min(len(parts_obj), len(parts_asm))):
                    if parts_obj[i] == parts_asm[i]:
                        # Exact match worth 2 points
                        score += 2
                    elif parts_obj[i].startswith(parts_asm[i][:2]) or parts_asm[i].startswith(parts_obj[i][:2]):
                        # Partial match (first 2 chars) worth 1 point
                        score += 1
                    else:
                        # Stop on first non-match
                        break
                
                # Require minimum score of 4 (e.g., 2 exact matches)
                # and make sure assembly name is different from object name
                if score >= 4 and obj_clean.upper() != asm_name.upper() and score > best_score:
                    best_match = asm_obj
                    best_score = score
            
            # Reparent if we found a better match than current parent
            if best_match and obj.parent != best_match:
                old_parent = obj.parent.name if obj.parent else "None"
                obj.parent = best_match
                obj.matrix_parent_inverse = best_match.matrix_world.inverted()
                reparented += 1
                print(f"  ↻ {obj.name}: {old_parent} → {best_match.name}")
        
        if reparented > 0:
            print(f"ApexCad: Reconstructed {reparented} relationships")
        else:
            print("ApexCad: No reparenting needed")
    
    def _detect_and_create_instances(self):
        """
        Detect identical meshes and convert to instances for optimization
        
        Returns:
            Number of instances created
        """
        print("ApexCad: Detecting identical meshes for instancing...")
        
        # Group objects by mesh hash
        mesh_groups = {}
        
        for obj in self.imported_objects:
            if not obj or obj.type != 'MESH':
                continue
            
            mesh_hash = obj.get('apexcad_mesh_hash')
            if not mesh_hash:
                continue
            
            if mesh_hash not in mesh_groups:
                mesh_groups[mesh_hash] = []
            mesh_groups[mesh_hash].append(obj)
        
        # Convert duplicates to instances
        instances_created = 0
        
        for mesh_hash, objects in mesh_groups.items():
            if len(objects) < 2:
                continue
            
            # Use first object as reference
            reference_obj = objects[0]
            
            # Verify meshes are actually identical (hash can have collisions)
            identical_objects = [reference_obj]
            
            for obj in objects[1:]:
                if utils.are_meshes_identical(reference_obj.data, obj.data):
                    identical_objects.append(obj)
            
            # Convert to instances if we have duplicates
            if len(identical_objects) >= 2:
                print(f"  ⚡ Found {len(identical_objects)} instances of {reference_obj.name}")
                
                for obj in identical_objects[1:]:
                    utils.convert_to_instance(obj, reference_obj)
                    instances_created += 1
        
        if instances_created > 0:
            print(f"ApexCad: Created {instances_created} instances")
        else:
            print("ApexCad: No duplicate meshes found")
        
        return instances_created



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
