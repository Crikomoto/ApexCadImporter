# ApexCad Importer - Usage Examples

## Example Workflows

### Example 1: Importing a Mechanical Part

**Scenario**: Single mechanical part modeled in SolidWorks (millimeters)

```
1. File → Import → STEP/IGES
2. Select: mechanical_part.stp
3. Settings:
   - Scale: mm → m (0.001)
   - Hierarchy: Collections
   - Y-Up: ✓ Enabled
   - Mesh Quality: 0.1
4. Import
```

**Result**: Part imported at correct scale, oriented correctly in Blender

---

### Example 2: Large Assembly (500+ Parts)

**Scenario**: Complete assembly with hundreds of components

```
1. Open Blender Preferences → Add-ons → ApexCad
   - Set Max Chunk Size: 100
   
2. File → Import → STEP/IGES
3. Select: large_assembly.step
4. Settings:
   - Scale: mm → m (0.001)
   - Hierarchy: Collections (recommended for large assemblies)
   - Y-Up: ✓ Enabled
   - Mesh Quality: 0.5 (faster import)
5. Import and wait...
```

**Result**: Assembly imported in chunks, Blender stays responsive

**Follow-up**:
- Select critical parts
- Use Re-tessellate with quality 0.05 for better detail
- Leave non-visible parts at lower quality

---

### Example 3: Architectural Model

**Scenario**: Building or architectural element (meters)

```
1. File → Import → STEP/IGES
2. Select: building.igs
3. Settings:
   - Scale: m → m (1.0)
   - Hierarchy: Collections
   - Y-Up: ✗ Disabled (may already be Y-up)
   - Mesh Quality: 0.2
4. Import
```

**Result**: Building at 1:1 scale

---

### Example 4: Product Visualization

**Scenario**: Consumer product for rendering (inches)

```
1. File → Import → STEP/IGES
2. Select: product_design.stp
3. Settings:
   - Scale: inch → m (0.0254)
   - Hierarchy: Empty Objects (for easier animation)
   - Y-Up: ✓ Enabled
   - Mesh Quality: 0.05 (high quality for rendering)
4. Import
```

**Post-Processing**:
- View CAD metadata (ApexCad panel → Show Metadata)
- Check volume/area information
- Setup materials based on part names

---

### Example 5: Re-tessellation Workflow

**Scenario**: Imported at low quality, need detail on specific parts

```
Initial Import:
1. Import entire assembly at quality 1.0 (fast)
2. Review assembly structure

Selective Re-tessellation:
1. Select critical visible parts
2. 3D Viewport → Sidebar → ApexCad tab
3. Click "Re-tessellate"
4. Set quality: 0.05
5. Apply

Result: Fast initial import, high detail where needed
```

---

## Tips and Tricks

### Choosing the Right Scale

**How to determine CAD units:**
1. Open file info in CAD software
2. Check part dimensions in CAD
3. Common defaults:
   - SolidWorks, Inventor, CATIA: millimeters
   - Fusion 360: varies (check document settings)
   - AutoCAD: varies (check units)
   - FreeCAD: millimeters (default)

**If unsure:**
- Import with scale 1.0
- Measure a known dimension in Blender
- Calculate correct scale = (desired_size / imported_size)
- Re-import with custom scale

### Hierarchy Strategies

**Use Collections when:**
- Large assemblies (100+ parts)
- Want to use Blender's outliner filtering
- Need instancing/linking capabilities
- Rendering complex scenes

**Use Empty Objects when:**
- Need to animate hierarchy
- Want traditional parent-child chains
- Smaller assemblies (<100 parts)
- Need to export to other formats

### Performance Optimization

**For smooth imports:**

```python
# In Blender Python Console (Window → Toggle System Console)
import bpy
prefs = bpy.context.preferences.addons['ApexCadImporter'].preferences

# Adjust chunk size based on RAM
prefs.max_chunk_size = 25  # Smaller chunks for low RAM
prefs.max_chunk_size = 200  # Larger chunks for 32GB+ RAM

# Enable async (should be on by default)
prefs.use_async_import = True
```

### Quality Settings Guide

| Quality | Faces/Part | Use Case | Import Speed |
|---------|-----------|----------|--------------|
| 0.01 | Very High | Hero products, close-ups | Slow |
| 0.05 | High | Product visualization | Medium |
| 0.1 | Medium | General modeling | Fast |
| 0.5 | Low | Large assemblies, preview | Very Fast |
| 1.0 | Very Low | Quick review | Fastest |

### Working with Metadata

**Access CAD properties:**
```python
import bpy

obj = bpy.context.active_object

# Print all CAD metadata
for key, value in obj.items():
    if key.startswith('cad_'):
        print(f"{key}: {value}")

# Access specific properties
volume = obj.get('cad_volume', 0)
area = obj.get('cad_area', 0)

print(f"Part volume: {volume} cubic units")
print(f"Surface area: {area} square units")
```

### Batch Processing

**Import multiple files:**
```python
import bpy
import os
from ApexCadImporter import importer

cad_files = [
    "D:/CAD/part1.stp",
    "D:/CAD/part2.step",
    "D:/CAD/assembly.igs"
]

for filepath in cad_files:
    success, msg, objs = importer.import_cad_file(
        bpy.context,
        filepath,
        scale=0.001,
        hierarchy_mode='COLLECTION',
        y_up=True,
        chunk_size=50,
        tessellation_quality=0.1
    )
    print(f"{os.path.basename(filepath)}: {msg}")
```

### Common Issues and Solutions

**Issue: Parts too small**
→ Used wrong scale (try mm→m instead of m→m)

**Issue: Upside down**
→ Toggle Y-Up conversion

**Issue: Import taking forever**
→ Increase quality value (0.5-1.0)
→ Reduce chunk size if running out of memory

**Issue: Missing parts**
→ Check original CAD file in FreeCAD
→ Some parts may have no geometry (construction elements)

**Issue: Hierarchy is flat**
→ CAD file may not have assembly structure
→ Some formats don't preserve hierarchy

---

## Advanced Scripting

### Custom Import Script

```python
import bpy
from ApexCadImporter import importer

# Custom import with full control
def custom_cad_import(filepath):
    # Pre-import setup
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Import with specific settings
    success, message, objects = importer.import_cad_file(
        bpy.context,
        filepath,
        scale=0.001,  # mm to m
        hierarchy_mode='COLLECTION',
        y_up=True,
        chunk_size=75,
        tessellation_quality=0.08
    )
    
    if success:
        print(f"✓ Imported {len(objects)} objects")
        
        # Post-process: add materials to all parts
        mat = bpy.data.materials.new(name="CAD_Material")
        mat.use_nodes = True
        
        for obj in objects:
            if obj.type == 'MESH':
                if not obj.data.materials:
                    obj.data.materials.append(mat)
    else:
        print(f"✗ Import failed: {message}")
    
    return success, objects

# Use it
custom_cad_import("D:/my_assembly.stp")
```

---

**More Examples**: Check the documentation and experiment with different settings for your specific workflow!
