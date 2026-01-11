"""
Utility Functions for ApexCadImporter
Coordinate conversion, naming, metadata handling
"""

import bpy
import bmesh
import math
from mathutils import Matrix, Vector, Quaternion, Euler


def sanitize_name(name):
    """
    Sanitize object names for Blender
    Remove invalid characters and ensure uniqueness
    """
    # Remove invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        name = name.replace(char, '_')
    
    # Ensure name is not empty
    if not name or name.isspace():
        name = "CAD_Object"
    
    return name.strip()


def create_unique_name(name, existing_names):
    """Create unique name by appending number if needed"""
    if name not in existing_names:
        return name
    
    base_name = name
    counter = 1
    
    # Remove existing number suffix if present
    if name[-4:-3] == '.' and name[-3:].isdigit():
        base_name = name[:-4]
    
    while name in existing_names:
        name = f"{base_name}.{counter:03d}"
        counter += 1
    
    return name


def z_up_to_y_up_matrix():
    """
    Create transformation matrix to convert Z-up to Y-up
    Rotates -90 degrees around X axis
    """
    return Matrix.Rotation(math.radians(-90), 4, 'X')


def apply_y_up_conversion(obj):
    """Apply Y-up conversion to object"""
    if obj.type == 'MESH':
        # Apply rotation to mesh data
        obj.data.transform(z_up_to_y_up_matrix())
        obj.data.update()


def quaternion_to_euler(quat, order='XYZ'):
    """Convert quaternion to Euler angles"""
    q = Quaternion((quat[0], quat[1], quat[2], quat[3]))
    return q.to_euler(order)


def set_custom_properties(obj, metadata):
    """
    Set custom properties on object from metadata
    
    Args:
        obj: Blender object
        metadata: Dict of metadata from CAD file
    """
    if not metadata:
        return
    
    # Add custom properties
    for key, value in metadata.items():
        if isinstance(value, (int, float, str, bool)):
            try:
                obj[f"cad_{key}"] = value
            except:
                pass
        elif isinstance(value, dict):
            # Flatten nested dicts
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, (int, float, str, bool)):
                    try:
                        obj[f"cad_{key}_{sub_key}"] = sub_value
                    except:
                        pass
        elif isinstance(value, list) and len(value) <= 3:
            # Store as vector property
            try:
                obj[f"cad_{key}"] = value
            except:
                pass


def get_collection(context, name, parent=None):
    """
    Get or create a collection
    
    Args:
        context: Blender context
        name: Collection name
        parent: Parent collection (None for root)
    
    Returns:
        Collection object
    """
    # Check if collection exists
    if name in bpy.data.collections:
        collection = bpy.data.collections[name]
    else:
        collection = bpy.data.collections.new(name)
    
    # Link to parent or scene
    if parent:
        if collection.name not in parent.children:
            parent.children.link(collection)
    else:
        if collection.name not in context.scene.collection.children:
            context.scene.collection.children.link(collection)
    
    return collection


def create_empty(name, location=(0, 0, 0), rotation=(0, 0, 0), parent=None, collection=None):
    """
    Create an Empty object
    
    Args:
        name: Object name
        location: Location tuple
        rotation: Rotation tuple (Euler angles)
        parent: Parent object
        collection: Collection to link to
    
    Returns:
        Empty object
    """
    empty = bpy.data.objects.new(name, None)
    empty.location = location
    empty.rotation_euler = rotation
    
    if parent:
        empty.parent = parent
    
    if collection:
        collection.objects.link(empty)
    else:
        bpy.context.scene.collection.objects.link(empty)
    
    return empty


def import_obj_file(filepath, obj_name, location=(0, 0, 0), rotation_quat=None, parent=None, collection=None, scale=1.0):
    """
    Import OBJ file and setup object
    
    Args:
        filepath: Path to OBJ file
        obj_name: Name for imported object
        location: Object location
        rotation_quat: Rotation quaternion [w, x, y, z]
        parent: Parent object
        collection: Collection to link to
        scale: Scale factor
    
    Returns:
        Imported mesh object or None
    """
    import os
    
    if not os.path.exists(filepath):
        print(f"ApexCad: Warning - OBJ file not found: {filepath}")
        return None
    
    # Store current objects
    before_import = set(bpy.context.scene.objects)
    
    # Import OBJ
    try:
        bpy.ops.wm.obj_import(filepath=filepath)
    except:
        # Fallback for older Blender versions
        try:
            bpy.ops.import_scene.obj(filepath=filepath)
        except Exception as e:
            print(f"ApexCad: Error importing OBJ: {e}")
            return None
    
    # Find newly imported objects
    after_import = set(bpy.context.scene.objects)
    new_objects = after_import - before_import
    
    if not new_objects:
        print(f"ApexCad: No objects imported from {filepath}")
        return None
    
    # Get the main imported object (usually first mesh)
    imported_obj = None
    for obj in new_objects:
        if obj.type == 'MESH':
            imported_obj = obj
            break
    
    if not imported_obj and new_objects:
        imported_obj = list(new_objects)[0]
    
    if imported_obj:
        # Rename object
        imported_obj.name = obj_name
        if imported_obj.data:
            imported_obj.data.name = obj_name
        
        # Apply transformations
        imported_obj.location = location
        
        if rotation_quat:
            q = Quaternion((rotation_quat[0], rotation_quat[1], rotation_quat[2], rotation_quat[3]))
            imported_obj.rotation_mode = 'QUATERNION'
            imported_obj.rotation_quaternion = q
        
        # Apply scale
        if scale != 1.0:
            imported_obj.scale = (scale, scale, scale)
        
        # Set parent
        if parent:
            imported_obj.parent = parent
        
        # Move to collection
        if collection:
            # Remove from all collections
            for coll in imported_obj.users_collection:
                coll.objects.unlink(imported_obj)
            # Link to target collection
            collection.objects.link(imported_obj)
    
    # Clean up other imported objects (cameras, lights, etc.)
    for obj in new_objects:
        if obj != imported_obj:
            bpy.data.objects.remove(obj, do_unlink=True)
    
    return imported_obj


def calculate_bounds(objects):
    """
    Calculate bounding box for list of objects
    
    Returns:
        (min_coord, max_coord, center, size)
    """
    if not objects:
        return None
    
    min_coord = Vector((float('inf'), float('inf'), float('inf')))
    max_coord = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for obj in objects:
        if obj.type == 'MESH':
            for vertex in obj.data.vertices:
                world_coord = obj.matrix_world @ vertex.co
                min_coord.x = min(min_coord.x, world_coord.x)
                min_coord.y = min(min_coord.y, world_coord.y)
                min_coord.z = min(min_coord.z, world_coord.z)
                max_coord.x = max(max_coord.x, world_coord.x)
                max_coord.y = max(max_coord.y, world_coord.y)
                max_coord.z = max(max_coord.z, world_coord.z)
    
    center = (min_coord + max_coord) / 2
    size = max_coord - min_coord
    
    return min_coord, max_coord, center, size


def select_objects(objects, active=None):
    """Select objects and optionally set active"""
    bpy.ops.object.select_all(action='DESELECT')
    
    for obj in objects:
        obj.select_set(True)
    
    if active and active in objects:
        bpy.context.view_layer.objects.active = active
    elif objects:
        bpy.context.view_layer.objects.active = objects[0]
