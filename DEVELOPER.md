# ApexCad Importer - Developer Guide

## For Developers

This guide is for developers who want to understand, modify, or extend ApexCad Importer.

---

## Architecture Overview

### Module Structure

```
ApexCadImporter/
│
├── __init__.py              # Addon registration & module loading
│   ├── bl_info             # Blender addon metadata
│   └── register/unregister # Module registration system
│
├── preferences.py           # User preferences & settings
│   ├── APEXCAD_AddonPreferences
│   └── APEXCAD_OT_DetectFreeCAD
│
├── freecad_bridge.py       # FreeCAD CLI interface
│   ├── FreeCADBridge class
│   │   ├── validate_freecad()
│   │   ├── generate_conversion_script()
│   │   ├── convert_file_async()
│   │   └── convert_file_sync()
│   └── get_bridge()
│
├── importer.py             # Main import logic
│   ├── CADImporter class
│   │   ├── import_file()
│   │   ├── _import_hierarchy()
│   │   ├── _import_object()
│   │   └── _setup_parent_child()
│   └── import_cad_file()
│
├── operators.py            # Blender operators
│   ├── APEXCAD_OT_ImportCAD
│   ├── APEXCAD_OT_Retessellate
│   └── APEXCAD_OT_ShowImportStats
│
├── ui.py                   # UI panels & menus
│   ├── APEXCAD_PT_MainPanel
│   ├── APEXCAD_PT_ObjectPropertiesPanel
│   └── menu_func_import()
│
├── tessellation.py         # Re-tessellation system
│   ├── TessellationManager class
│   ├── APEXCAD_OT_BatchRetessellate
│   └── APEXCAD_OT_ShowTessellationInfo
│
└── utils.py                # Helper functions
    ├── sanitize_name()
    ├── create_unique_name()
    ├── z_up_to_y_up_matrix()
    ├── set_custom_properties()
    ├── get_collection()
    ├── create_empty()
    ├── import_obj_file()
    └── calculate_bounds()
```

---

## Data Flow

### Import Pipeline

```
1. User Action
   └─> APEXCAD_OT_ImportCAD.execute()
       │
2. Validation
   └─> get_bridge(context)
       └─> Validate FreeCAD path
       │
3. Conversion (Heavy Lifting)
   └─> FreeCADBridge.convert_file_sync()
       ├─> generate_conversion_script()
       │   └─> Creates Python script for FreeCAD
       ├─> subprocess.run([freecad, script])
       │   └─> FreeCAD processes CAD file
       └─> Returns hierarchy.json + OBJ files
       │
4. Import into Blender
   └─> CADImporter.import_file()
       ├─> _import_hierarchy()
       │   ├─> Chunk objects (divide & conquer)
       │   ├─> _import_object() for each
       │   │   └─> import_obj_file()
       │   └─> _setup_parent_child()
       ├─> Apply Y-up conversion
       └─> Return imported objects
       │
5. Finalization
   └─> Select objects, report success
```

### Data Structures

**hierarchy.json format:**
```json
{
  "objects": [
    {
      "name": "Part1",
      "internal_name": "Part001",
      "type": "Part::Feature",
      "index": 0,
      "metadata": {
        "volume": 1234.5,
        "area": 567.8,
        "bbox": {
          "min": [0, 0, 0],
          "max": [10, 10, 10]
        }
      },
      "transform": {
        "position": [0, 0, 0],
        "rotation": [1, 0, 0, 0]
      },
      "mesh_file": "/tmp/Part001.obj",
      "parent": null,
      "children": []
    }
  ],
  "root_objects": ["Part001"],
  "scale": 0.001,
  "y_up": true
}
```

---

## Key Design Patterns

### 1. Divide and Conquer

Large assemblies are processed in chunks:

```python
# In importer.py
chunks = [objects_data[i:i+chunk_size] 
          for i in range(0, total_objects, chunk_size)]

for chunk_idx, chunk in enumerate(chunks):
    for obj_data in chunk:
        self._import_object(obj_data, ...)
```

**Why?** Prevents memory overflow and UI freezing on massive assemblies.

### 2. Bridge Pattern

FreeCAD communication is abstracted:

```python
# freecad_bridge.py
class FreeCADBridge:
    def convert_file_sync(self, input_file, output_dir, options):
        # Generate script
        # Execute FreeCAD
        # Return results
```

**Why?** Isolates FreeCAD-specific code, enables testing, allows async.

### 3. Non-Blocking Execution

FreeCAD runs in subprocess, not inline:

```python
result = subprocess.run([self.freecad_path, "-c", script_path],
                       capture_output=True, timeout=300)
```

**Why?** FreeCAD conversion can take minutes; subprocess prevents Blender freeze.

### 4. Metadata Preservation

CAD properties stored as Blender custom properties:

```python
obj['cad_volume'] = 1234.5
obj['cad_area'] = 567.8
obj['apexcad_can_retessellate'] = True
```

**Why?** Preserves engineering data, enables re-tessellation tracking.

---

## Extending the Addon

### Adding a New Import Format

1. **Update file filter** (operators.py):
```python
filter_glob: StringProperty(
    default="*.stp;*.step;*.igs;*.iges;*.new_format",
    options={'HIDDEN'},
)
```

2. **Add format detection** (freecad_bridge.py):
```python
file_ext = os.path.splitext(input_file)[1].lower()
if file_ext in ['.new_format']:
    Import.insert(input_file, "ApexCadImport")
```

3. Test with sample files

### Adding Custom Metadata

In freecad_bridge.py script generation:

```python
obj_data["metadata"]["custom_property"] = obj.CustomProperty
```

In utils.py property setting:

```python
if "custom_property" in metadata:
    obj['cad_custom_property'] = metadata['custom_property']
```

### Creating New Operators

Template for new operator:

```python
class APEXCAD_OT_MyOperator(bpy.types.Operator):
    bl_idname = "object.apexcad_my_operator"
    bl_label = "My Operation"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def execute(self, context):
        # Your code here
        self.report({'INFO'}, "Operation complete")
        return {'FINISHED'}

# Register in operators.py
classes = (
    # ... existing classes
    APEXCAD_OT_MyOperator,
)
```

---

## Testing

### Manual Testing Checklist

- [ ] Install addon in Blender 5.0
- [ ] Configure FreeCAD path
- [ ] Import simple STEP file (single part)
- [ ] Import IGES file
- [ ] Import large assembly (100+ parts)
- [ ] Test all scale presets
- [ ] Test Y-up conversion on/off
- [ ] Test Collection vs Empty hierarchy
- [ ] Verify metadata preservation
- [ ] Test re-tessellation operator
- [ ] Check console for errors

### Unit Test Structure (Future)

```python
# tests/test_bridge.py
import unittest
from ApexCadImporter import freecad_bridge

class TestFreeCADBridge(unittest.TestCase):
    def test_validate_freecad(self):
        # Test FreeCAD validation
        pass
    
    def test_script_generation(self):
        # Test Python script creation
        pass
```

---

## Performance Optimization

### Current Optimizations

1. **Chunked Processing**: Max 50 objects/chunk (configurable)
2. **OBJ Intermediate Format**: Fast, simple, widely supported
3. **Subprocess Isolation**: FreeCAD runs separately
4. **Lazy Loading**: Only load what's needed
5. **Temporary File Cleanup**: Automatic cleanup on completion

### Future Optimizations

- [ ] Multi-threading for chunk processing
- [ ] Incremental import (resume on failure)
- [ ] Cached tessellation results
- [ ] Binary format for hierarchy data
- [ ] Streaming import for very large files

---

## Debugging

### Enable Debug Output

In Blender:
- Window → Toggle System Console
- All `print()` statements appear here

Add debug prints:
```python
print(f"ApexCad: DEBUG - Processing {obj_name}")
```

### Common Debug Points

1. **FreeCAD Bridge**:
```python
# freecad_bridge.py
print(f"ApexCad: FreeCAD command: {[self.freecad_path, '-c', script_path]}")
print(f"ApexCad: FreeCAD stdout: {result.stdout}")
print(f"ApexCad: FreeCAD stderr: {result.stderr}")
```

2. **Import Flow**:
```python
# importer.py
print(f"ApexCad: Chunk {chunk_idx+1}/{len(chunks)}")
print(f"ApexCad: Imported {obj_name} at {location}")
```

3. **Hierarchy Building**:
```python
# importer.py
print(f"ApexCad: Parent {parent_name} → Child {internal_name}")
```

---

## Code Style

### Naming Conventions

- **Classes**: `APEXCAD_ClassName` (Blender convention)
- **Operators**: `APEXCAD_OT_OperatorName`
- **Panels**: `APEXCAD_PT_PanelName`
- **Functions**: `snake_case`
- **Constants**: `UPPER_CASE`

### Documentation

```python
def function_name(arg1, arg2):
    """
    Brief description of function
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    """
    pass
```

### Error Handling

```python
try:
    # Operation
    result = risky_operation()
except SpecificException as e:
    # Handle specific error
    return False, f"Error: {str(e)}"
except Exception as e:
    # Catch-all
    return False, f"Unexpected error: {str(e)}"
```

---

## Contributing Guidelines

### Before Submitting Changes

1. Test with multiple CAD files
2. Verify no console errors
3. Check memory usage on large files
4. Update documentation if needed
5. Follow existing code style

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation update

## Testing
- [ ] Tested on Windows/Linux/Mac
- [ ] Tested with STEP files
- [ ] Tested with IGES files
- [ ] Tested large assemblies (100+ parts)

## Related Issues
Fixes #issue_number
```

---

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

---

## Resources

- **Blender API**: https://docs.blender.org/api/current/
- **FreeCAD Python API**: https://wiki.freecad.org/Python_scripting_tutorial
- **Blender Addon Tutorial**: https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html

---

**Author**: Cristian Koch R.  
**Contact**: [Your contact info]  
**Repository**: [Repository URL]
