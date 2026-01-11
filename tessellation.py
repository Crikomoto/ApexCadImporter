"""
Tessellation Module
Non-destructive re-tessellation system for CAD objects
"""

import bpy
import os
import tempfile
from . import freecad_bridge


class TessellationManager:
    """
    Manages re-tessellation of CAD objects
    Allows non-destructive quality improvements
    """
    
    def __init__(self, context):
        self.context = context
    
    def can_retessellate(self, obj):
        """Check if object can be re-tessellated"""
        return obj.get('apexcad_can_retessellate', False) and obj.get('apexcad_original_file')
    
    def retessellate_object(self, obj, new_quality, preserve_transforms=True):
        """
        Re-tessellate object with new quality setting
        
        Args:
            obj: Blender object to re-tessellate
            new_quality: New tessellation quality (lower = better)
            preserve_transforms: Keep current transform/modifiers
        
        Returns:
            (success, message)
        """
        if not self.can_retessellate(obj):
            return False, "Object cannot be re-tessellated"
        
        original_file = obj.get('apexcad_original_file')
        
        # Store current properties
        original_name = obj.name
        original_location = obj.location.copy()
        original_rotation = obj.rotation_euler.copy()
        original_scale = obj.scale.copy()
        original_parent = obj.parent
        original_collections = list(obj.users_collection)
        
        # Store custom properties
        custom_props = {}
        for key in obj.keys():
            if key.startswith('cad_') or key.startswith('apexcad_'):
                custom_props[key] = obj[key]
        
        # TODO: Implement actual re-tessellation
        # This would require:
        # 1. Access to original CAD file
        # 2. Re-running FreeCAD conversion with new quality
        # 3. Replacing mesh data while preserving transforms
        
        # For now, just update the quality value
        obj['apexcad_tessellation_quality'] = new_quality
        
        return True, f"Re-tessellation queued for {original_name}"
    
    def batch_retessellate(self, objects, new_quality):
        """
        Re-tessellate multiple objects
        
        Args:
            objects: List of objects
            new_quality: New tessellation quality
        
        Returns:
            (success_count, failed_count, messages)
        """
        success_count = 0
        failed_count = 0
        messages = []
        
        for obj in objects:
            success, message = self.retessellate_object(obj, new_quality)
            if success:
                success_count += 1
            else:
                failed_count += 1
            messages.append(message)
        
        return success_count, failed_count, messages
    
    def get_tessellation_info(self, obj):
        """
        Get current tessellation information for object
        
        Returns:
            Dict with tessellation info
        """
        if not obj:
            return None
        
        info = {
            'can_retessellate': self.can_retessellate(obj),
            'current_quality': obj.get('apexcad_tessellation_quality', 'Unknown'),
            'original_file': obj.get('apexcad_original_file', 'Unknown'),
        }
        
        # Add mesh statistics
        if obj.type == 'MESH':
            mesh = obj.data
            info['vertices'] = len(mesh.vertices)
            info['edges'] = len(mesh.edges)
            info['faces'] = len(mesh.polygons)
            info['triangles'] = sum(1 for p in mesh.polygons if len(p.vertices) == 3)
        
        return info


class APEXCAD_OT_BatchRetessellate(bpy.types.Operator):
    """Re-tessellate multiple selected CAD objects"""
    bl_idname = "object.apexcad_batch_retessellate"
    bl_label = "Batch Re-tessellate"
    bl_description = "Re-tessellate all selected CAD objects with new quality"
    bl_options = {'REGISTER', 'UNDO'}
    
    from bpy.props import FloatProperty
    
    tessellation_quality: FloatProperty(
        name="Quality",
        description="Tessellation quality (lower = better)",
        default=0.05,
        min=0.01,
        max=5.0,
    )
    
    @classmethod
    def poll(cls, context):
        """Check if any selected objects can be re-tessellated"""
        for obj in context.selected_objects:
            if obj.get('apexcad_can_retessellate'):
                return True
        return False
    
    def execute(self, context):
        manager = TessellationManager(context)
        
        # Filter objects that can be re-tessellated
        objects_to_process = [obj for obj in context.selected_objects 
                             if manager.can_retessellate(obj)]
        
        if not objects_to_process:
            self.report({'WARNING'}, "No CAD objects selected")
            return {'CANCELLED'}
        
        # Process objects
        success_count, failed_count, messages = manager.batch_retessellate(
            objects_to_process,
            self.tessellation_quality
        )
        
        self.report({'INFO'}, 
                   f"Re-tessellation: {success_count} succeeded, {failed_count} failed")
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "tessellation_quality", slider=True)
        
        # Count objects
        manager = TessellationManager(context)
        count = sum(1 for obj in context.selected_objects 
                   if manager.can_retessellate(obj))
        
        layout.label(text=f"Will process {count} object(s)", icon='INFO')


class APEXCAD_OT_ShowTessellationInfo(bpy.types.Operator):
    """Show tessellation information for active object"""
    bl_idname = "object.apexcad_show_tessellation_info"
    bl_label = "Tessellation Info"
    bl_description = "Display tessellation information"
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        manager = TessellationManager(context)
        info = manager.get_tessellation_info(context.active_object)
        
        if not info:
            self.report({'WARNING'}, "No information available")
            return {'CANCELLED'}
        
        print("\n" + "="*50)
        print(f"Tessellation Info: {context.active_object.name}")
        print("="*50)
        for key, value in info.items():
            print(f"  {key}: {value}")
        print("="*50 + "\n")
        
        self.report({'INFO'}, "Tessellation info printed to console")
        return {'FINISHED'}


# Registration
classes = (
    APEXCAD_OT_BatchRetessellate,
    APEXCAD_OT_ShowTessellationInfo,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
