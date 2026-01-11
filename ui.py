"""
UI Panels and Menus for ApexCadImporter
"""

import bpy


class APEXCAD_PT_MainPanel(bpy.types.Panel):
    """Main panel for CAD import tools in 3D Viewport"""
    bl_label = "ApexCad Importer"
    bl_idname = "APEXCAD_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ApexCad'
    
    def draw(self, context):
        layout = self.layout
        
        # Import section
        box = layout.box()
        box.label(text="Import CAD Files:", icon='IMPORT')
        box.operator("import_scene.apexcad", text="Import STEP/IGES", icon='MESH_CUBE')
        box.operator("import_scene.apexcad_batch", text="Batch Import Folder", icon='FILEBROWSER')
        
        # Re-tessellation section
        box = layout.box()
        box.label(text="Re-tessellation:", icon='MOD_TRIANGULATE')
        
        obj = context.active_object
        if obj and obj.get('apexcad_tessellation') is not None:
            box.operator("object.apexcad_retessellate", text="Re-tessellate Object", icon='FILE_REFRESH')
            box.operator("object.apexcad_retessellate_hierarchy", text="Re-tessellate Hierarchy", icon='OUTLINER')
            box.label(text=f"Object: {obj.name}", icon='OBJECT_DATA')
            
            # Show current tessellation quality
            tess = obj.get('apexcad_tessellation', 0.01)
            box.label(text=f"Quality: {tess:.4f}", icon='MESH_DATA')
            
            # Show if it's an instance
            if obj.get('apexcad_instance_of'):
                ref = obj.get('apexcad_instance_of')
                box.label(text=f"Instance of: {ref}", icon='LINKED')
        else:
            box.label(text="Select CAD object to re-tessellate", icon='INFO')
        
        # Metadata section
        box = layout.box()
        box.label(text="CAD Information:", icon='INFO')
        box.operator("object.apexcad_show_stats", text="Show Metadata", icon='PROPERTIES')


class APEXCAD_PT_ObjectPropertiesPanel(bpy.types.Panel):
    """Panel showing CAD properties in object properties"""
    bl_label = "CAD Properties"
    bl_idname = "APEXCAD_PT_object_properties"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    
    @classmethod
    def poll(cls, context):
        """Only show if object has CAD metadata"""
        obj = context.active_object
        if not obj:
            return False
        
        # Check if object has any CAD properties
        for key in obj.keys():
            if key.startswith('cad_') or key.startswith('apexcad_'):
                return True
        return False
    
    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        
        if not obj:
            return
        
        # Display CAD metadata
        box = layout.box()
        box.label(text="CAD Metadata:", icon='PROPERTIES')
        
        cad_props = {}
        for key in obj.keys():
            if key.startswith('cad_'):
                cad_props[key] = obj[key]
        
        if cad_props:
            col = box.column(align=True)
            for key, value in sorted(cad_props.items()):
                # Format the key for display
                display_key = key.replace('cad_', '').replace('_', ' ').title()
                
                # Format value based on type
                if isinstance(value, float):
                    display_value = f"{value:.4f}"
                elif isinstance(value, (list, tuple)):
                    display_value = f"[{', '.join(f'{v:.2f}' for v in value)}]"
                else:
                    display_value = str(value)
                
                row = col.row()
                row.label(text=f"{display_key}:")
                row.label(text=display_value)
        
        # Display ApexCad import info
        apex_props = {}
        for key in obj.keys():
            if key.startswith('apexcad_'):
                apex_props[key] = obj[key]
        
        if apex_props:
            box = layout.box()
            box.label(text="Import Information:", icon='INFO')
            col = box.column(align=True)
            
            # Show tessellation
            if 'apexcad_tessellation' in apex_props:
                row = col.row()
                row.label(text="Tessellation Quality:")
                row.label(text=f"{apex_props['apexcad_tessellation']:.4f}")
            
            # Show if instance
            if 'apexcad_instance_of' in apex_props:
                row = col.row()
                row.label(text="Instance of:")
                row.label(text=apex_props['apexcad_instance_of'])
            
            # Show source file
            if 'apexcad_source_file' in apex_props:
                import os
                source = apex_props['apexcad_source_file']
                row = col.row()
                row.label(text="Source:")
                row.label(text=os.path.basename(source))
        
        # Re-tessellation options
        if obj.get('apexcad_tessellation') is not None:
            box = layout.box()
            box.label(text="Re-tessellation:", icon='MOD_TRIANGULATE')
            box.operator("object.apexcad_retessellate", text="Re-tessellate Object", icon='FILE_REFRESH')


def menu_func_import(self, context):
    """Add import menu entry"""
    self.layout.operator(
        "import_scene.apexcad",
        text="STEP/IGES (.stp, .igs)",
        icon='MESH_CUBE'
    )


# Registration
classes = (
    APEXCAD_PT_MainPanel,
    APEXCAD_PT_ObjectPropertiesPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
