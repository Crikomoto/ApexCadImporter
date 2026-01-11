# ApexCad Importer - Release Notes v2.0

## 🎉 Major Update: Professional CAD Workflow Features

### ✨ New Features

#### 1. **Auto Smooth Shading** 
- ✅ Automatic smooth shading applied to all imported meshes
- ✅ Auto-smooth angle set to 30° for optimal CAD geometry display
- ✅ Eliminates faceted appearance on curved surfaces
- **Location**: `utils.py` - `apply_smooth_shading()` function

#### 2. **Material & Color Support**
- ✅ Extracts colors from STEP files via FreeCAD ViewObject
- ✅ Automatically creates and assigns PBR materials in Blender
- ✅ Supports:
  - ShapeColor (primary)
  - DiffuseColor (per-face, fallback)
  - Material properties (if present in STEP)
- ✅ Auto-configures materials for CAD appearance (low roughness, metallic detection)
- **Location**: `freecad_bridge.py` (lines 156-173), `utils.py` - `create_material_from_color()`

#### 3. **Instance Detection & Optimization**
- ✅ Automatically detects identical meshes using hash-based algorithm
- ✅ Converts duplicates to instances (shares mesh data)
- ✅ Reduces memory usage for assemblies with repeated parts (bolts, screws, etc.)
- ✅ Reports: `⚡ Found N instances of [object]`
- **Algorithm**: Mesh hash (vert count + face count + volume) + geometric verification
- **Location**: `importer.py` - `_detect_and_create_instances()`, `utils.py` - instance functions

#### 4. **CAD Metadata Extraction**
- ✅ Extracts and stores:
  - **Volume** (cubic units)
  - **Surface Area** (square units)
  - **Bounding Box** (min/max coordinates)
  - **Color** (RGBA)
  - **Description** (if present in STEP)
  - **Material Name** (if present)
- ✅ Stored as custom properties on each object (`cad_volume`, `cad_area`, etc.)
- ✅ Visible in Properties panel and via "Show Metadata" operator
- **Location**: `freecad_bridge.py` (lines 141-180)

#### 5. **Re-tessellation Support** (UI Ready)
- ✅ UI panel for re-tessellating objects on-the-fly
- ✅ Stores original tessellation quality and source file path
- ✅ Operator: `object.apexcad_retessellate`
- ⚠️ **Status**: UI complete, full re-import coming in next update
- **Properties Stored**:
  - `apexcad_source_file` - Original STEP/IGES file path
  - `apexcad_original_file` - Internal FreeCAD object name
  - `apexcad_tessellation` - Current tessellation quality
- **Location**: `operators.py` - `APEXCAD_OT_Retessellate`

#### 6. **Enhanced UI Panels**
- ✅ **3D Viewport Panel** (`N` panel → ApexCad):
  - Import button
  - Re-tessellation controls
  - Shows current object info (name, quality, instance status)
- ✅ **Object Properties Panel**:
  - CAD Metadata display
  - Import information (tessellation, source file, instance status)
  - Re-tessellation button
- **Location**: `ui.py`

---

## 🔧 Technical Details

### Instance Detection Algorithm
```python
1. Calculate mesh hash: "{vert_count}_{face_count}_{volume:.6f}"
2. Group objects by hash
3. Verify geometry identity (sample 10 vertices)
4. Convert duplicates to instances (share mesh data, keep transforms)
5. Mark with 'apexcad_instance_of' property
```

### Material Creation
```python
Color extraction priority:
1. ViewObject.ShapeColor (primary for STEP)
2. ViewObject.DiffuseColor[0] (per-face)
3. Fallback: No material

Material properties:
- Base Color: from STEP
- Roughness: 0.3 (CAD-like)
- Metallic: 0.5 (if dark colors, avg < 0.3)
```

### Metadata Properties
Objects now have these custom properties:
- `cad_volume`: Volume in cubic units
- `cad_area`: Surface area in square units
- `cad_bbox`: Bounding box {min: [x,y,z], max: [x,y,z]}
- `cad_color`: RGBA color [r, g, b, a]
- `cad_description`: Text description from STEP (if exists)
- `cad_material_name`: Material name from STEP (if exists)
- `apexcad_mesh_hash`: Geometry hash for instance detection
- `apexcad_instance_of`: Reference object name (if instance)
- `apexcad_tessellation`: Current tessellation quality
- `apexcad_source_file`: Original STEP/IGES file path
- `apexcad_original_file`: FreeCAD internal object name

---

## 📊 Performance Impact

### Before vs After
| Feature | Before | After | Benefit |
|---------|--------|-------|---------|
| **Shading** | Faceted | Smooth | Better visualization |
| **Materials** | None | Auto PBR | Production-ready look |
| **Instances** | Duplicates | Shared mesh | ~50-90% memory reduction* |
| **Metadata** | Lost | Preserved | Full CAD traceability |

*For assemblies with repeated parts (e.g., 20 identical bolts)

---

## 🚀 Usage Examples

### Import with all features
```python
import bpy
bpy.ops.import_scene.apexcad(
    filepath="assembly.step",
    scale_preset='0.001',  # mm to m
    tessellation_quality=0.01,  # Fine quality
    y_up=True
)
```

### Check metadata
```python
obj = bpy.context.active_object
print(f"Volume: {obj.get('cad_volume', 0):.4f}")
print(f"Color: {obj.get('cad_color', 'None')}")
print(f"Is instance: {obj.get('apexcad_instance_of') is not None}")
```

### Re-tessellate (UI)
1. Select imported CAD object
2. Open Properties panel → Object Properties
3. Find "Re-tessellation" section
4. Click "Re-tessellate Object"
5. Adjust quality slider

---

## 🐛 Known Limitations

1. **Re-tessellation**: Currently only updates property, full re-import coming soon
2. **Materials**: Only basic PBR, advanced STEP materials not yet supported
3. **Instance detection**: Uses sampling for performance, may miss very similar but different geometries
4. **Color extraction**: Depends on ViewObject availability in FreeCAD (may fail for some STEP exporters)

---

## 🔜 Roadmap (Next Update)

1. **Full re-tessellation**: Re-import individual objects from cache
2. **Material library**: Named material system for repeated colors
3. **Assembly metadata**: Extract assembly-level properties
4. **Performance**: Multi-threaded instance detection for huge assemblies

---

## 🧪 Testing

Test file: `AMS-50-173-000.STEP` (520 KB, 42 objects)
- ✅ Smooth shading applied to all meshes
- ✅ Materials created from STEP colors (if present)
- ✅ Instances detected (e.g., 4× AMS-30-511-03X parts)
- ✅ Metadata extracted and stored
- ✅ UI panels functional

---

## 📝 Notes for Users

### As a FreeCAD Professional:
- Colors extracted directly from STEP ViewObject (industry standard)
- Metadata preservation ensures CAD traceability
- Instance detection reduces file size for large assemblies

### As a Blender Professional:
- PBR materials auto-configured for realistic rendering
- Smooth shading eliminates post-import cleanup
- Custom properties available for scripting/automation

### Workflow Recommendation:
1. Import STEP with default settings (0.01 tessellation)
2. Check materials and instances in console output
3. Use "Show Metadata" to verify CAD properties
4. Adjust shading/materials as needed for rendering
5. Use instance system for animation/rigging optimization

---

**Version**: 2.0.0  
**Date**: 2026-01-11  
**Compatibility**: Blender 5.0+, FreeCAD 1.0+
