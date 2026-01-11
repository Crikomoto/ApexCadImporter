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
    Import OBJ file directly by parsing and creating mesh
    This avoids issues with Blender's OBJ importer merging objects
    
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
    
    # Parse OBJ file manually
    vertices = []
    faces = []
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                if not parts:
                    continue
                
                if parts[0] == 'v':  # Vertex
                    # OBJ format: v x y z - apply scale during parsing
                    vertices.append((
                        float(parts[1]) * scale, 
                        float(parts[2]) * scale, 
                        float(parts[3]) * scale
                    ))
                
                elif parts[0] == 'f':  # Face
                    # OBJ format: f v1 v2 v3 or f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3
                    # We only need vertex indices (convert to 0-based)
                    face_verts = []
                    for vert in parts[1:]:
                        # Split by / and take first element (vertex index)
                        vert_idx = int(vert.split('/')[0]) - 1  # OBJ is 1-based
                        face_verts.append(vert_idx)
                    faces.append(face_verts)
        
        if not vertices:
            print(f"ApexCad: No vertices in OBJ file: {filepath}")
            return None
        
        # Create mesh
        mesh = bpy.data.meshes.new(obj_name)
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        
        # Validate mesh
        mesh.validate()
        
        # Create object
        obj = bpy.data.objects.new(obj_name, mesh)
        
        # Apply transformations
        obj.location = location
        
        if rotation_quat:
            q = Quaternion((rotation_quat[0], rotation_quat[1], rotation_quat[2], rotation_quat[3]))
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = q
        
        # Set parent
        if parent:
            obj.parent = parent
        
        # Link to collection
        if collection:
            collection.objects.link(obj)
        else:
            bpy.context.scene.collection.objects.link(obj)
        
        return obj
        
    except Exception as e:
        print(f"ApexCad: Error parsing OBJ file {filepath}: {e}")
        import traceback
        traceback.print_exc()
        return None


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


def apply_smooth_shading(obj, auto_smooth_angle=30):
    """
    Apply auto smooth shading to CAD mesh for optimal surface display
    
    Args:
        obj: Blender mesh object
        auto_smooth_angle: Auto smooth angle in degrees (default 30°)
    """
    if obj.type != 'MESH':
        return
    
    # Store selection state
    was_selected = obj.select_get()
    was_active = bpy.context.view_layer.objects.active
    
    # Select object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    # Apply shade auto smooth (Blender 4.1+)
    # This is better than shade_smooth for CAD surfaces
    try:
        if hasattr(bpy.ops.object, 'shade_auto_smooth'):
            # New unified operator (Blender 5.0+)
            bpy.ops.object.shade_auto_smooth(angle=math.radians(auto_smooth_angle))
        else:
            # Fallback: shade smooth + legacy auto smooth
            bpy.ops.object.shade_smooth()
            if hasattr(obj.data, 'use_auto_smooth'):
                obj.data.use_auto_smooth = True
                obj.data.auto_smooth_angle = math.radians(auto_smooth_angle)
    except Exception as e:
        # Final fallback: just shade smooth
        try:
            bpy.ops.object.shade_smooth()
        except:
            pass
    
    # Restore selection
    obj.select_set(was_selected)
    bpy.context.view_layer.objects.active = was_active


def create_material_from_color(name, color_rgba):
    """
    Create material from RGBA color
    
    Args:
        name: Material name
        color_rgba: RGBA tuple (r, g, b, a) in 0-1 range
    
    Returns:
        Material object
    """
    # Check if material exists
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    
    # Create new material
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    
    # Get principled BSDF
    nodes = mat.node_tree.nodes
    principled = nodes.get('Principled BSDF')
    
    if principled:
        # Set base color
        principled.inputs['Base Color'].default_value = color_rgba
        
        # Adjust for CAD materials (less rough, more metallic if dark)
        principled.inputs['Roughness'].default_value = 0.3
        
        # If color is dark, assume metallic
        avg_color = (color_rgba[0] + color_rgba[1] + color_rgba[2]) / 3
        if avg_color < 0.3:
            principled.inputs['Metallic'].default_value = 0.5
    
    return mat


def mesh_hash(mesh_data):
    """
    Calculate hash of mesh geometry for instance detection
    
    Args:
        mesh_data: Blender mesh data
    
    Returns:
        Hash string representing geometry
    """
    # Use vertex count, face count, and volume as simple hash
    vert_count = len(mesh_data.vertices)
    face_count = len(mesh_data.polygons)
    
    # Calculate approximate volume from bounding box
    if vert_count > 0:
        min_co = Vector(mesh_data.vertices[0].co)
        max_co = Vector(mesh_data.vertices[0].co)
        
        for v in mesh_data.vertices:
            for i in range(3):
                min_co[i] = min(min_co[i], v.co[i])
                max_co[i] = max(max_co[i], v.co[i])
        
        size = max_co - min_co
        volume = size.x * size.y * size.z
    else:
        volume = 0
    
    # Create hash from counts and volume
    return f"{vert_count}_{face_count}_{volume:.6f}"


def are_meshes_identical(mesh1, mesh2, tolerance=0.0001):
    """
    Check if two meshes are geometrically identical
    
    Args:
        mesh1, mesh2: Blender mesh data blocks
        tolerance: Floating point comparison tolerance
    
    Returns:
        True if meshes are identical
    """
    # Quick checks
    if len(mesh1.vertices) != len(mesh2.vertices):
        return False
    if len(mesh1.polygons) != len(mesh2.polygons):
        return False
    
    # Compare vertices (sample first 10 for performance)
    sample_size = min(10, len(mesh1.vertices))
    for i in range(sample_size):
        v1 = mesh1.vertices[i].co
        v2 = mesh2.vertices[i].co
        if (v1 - v2).length > tolerance:
            return False
    
    return True


def convert_to_instance(obj, reference_obj):
    """
    Convert object to instance of reference object
    
    Args:
        obj: Object to convert to instance
        reference_obj: Reference object with original mesh
    """
    # Store transform
    location = obj.location.copy()
    rotation = obj.rotation_euler.copy()
    scale = obj.scale.copy()
    parent = obj.parent
    
    # Replace mesh data with reference
    obj.data = reference_obj.data
    
    # Restore transform
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale
    obj.parent = parent
    
    # Mark as instance
    obj['apexcad_instance_of'] = reference_obj.name
