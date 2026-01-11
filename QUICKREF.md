# ApexCad Importer - Quick Reference

## 🚀 Quick Start

1. **Install FreeCAD** → https://www.freecad.org
2. **Copy addon** to Blender addons folder
3. **Enable** in Preferences → Add-ons
4. **Configure** FreeCAD path (auto-detect button)
5. **Import** via File → Import → STEP/IGES

---

## ⌨️ Common Operations

| Action | Location |
|--------|----------|
| Import CAD file | File → Import → STEP/IGES |
| View metadata | 3D Viewport → Sidebar → ApexCad → Show Metadata |
| Re-tessellate | Select object → ApexCad panel → Re-tessellate |
| Configure addon | Edit → Preferences → Add-ons → ApexCad |
| Auto-detect FreeCAD | Preferences → 🔍 icon |

---

## 📏 Scale Presets

| Preset | Factor | Use When |
|--------|--------|----------|
| mm → m | 0.001 | CAD in millimeters (most common) |
| cm → m | 0.01 | CAD in centimeters |
| m → m | 1.0 | Already in meters |
| inch → m | 0.0254 | Imperial units |

---

## 🎯 Quality Settings

| Value | Quality | Speed | Use Case |
|-------|---------|-------|----------|
| 0.01 | Ultra | Slowest | Hero products, close-ups |
| 0.05 | High | Slow | Product viz, renders |
| 0.1 | Medium | Normal | General use (default) |
| 0.5 | Low | Fast | Large assemblies |
| 1.0 | Preview | Fastest | Quick review |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Objects too small | Use mm→m scale instead of m→m |
| Upside down | Toggle Y-Up conversion |
| FreeCAD not found | Auto-detect or set path manually |
| Import slow | Increase quality value (0.5-1.0) |
| Blender freezes | Check "Async Import" in prefs |

---

## 📂 File Formats

**Supported:**
- ✅ STEP (.stp, .step)
- ✅ IGES (.igs, .iges)

**Requirements:**
- FreeCAD 0.20+ must be installed

---

## 🎨 Hierarchy Modes

**Collections:**
- Best for large assemblies (100+ parts)
- Uses Blender collection system
- Easy filtering in Outliner
- Recommended for most cases

**Empty Objects:**
- Traditional parent-child chains
- Better for animation
- Easier to export
- Good for smaller assemblies

---

## 📊 Performance Tips

**Large Files (1000+ parts):**
1. Increase Max Chunk Size → 100-200
2. Import at lower quality → 0.5-1.0
3. Re-tessellate critical parts later
4. Use Collections hierarchy

**Memory Issues:**
- Reduce chunk size → 25-30
- Import in sections if possible
- Close other applications

---

## 💾 Metadata

**Imported data includes:**
- Part volumes and areas
- Bounding box dimensions
- Original CAD names
- Assembly hierarchy
- Transform information

**Access via:**
- ApexCad panel → Show Metadata
- Properties → Object Properties → CAD Properties
- Python: `obj['cad_property_name']`

---

## 🔨 Common Workflows

### Mechanical Parts
```
Scale: mm → m
Hierarchy: Collections
Y-Up: ✓
Quality: 0.1
```

### Architecture
```
Scale: m → m or cm → m
Hierarchy: Collections
Y-Up: check original
Quality: 0.2
```

### Product Rendering
```
Scale: depends on source
Hierarchy: Empty (for animation)
Y-Up: ✓
Quality: 0.05 (high)
```

### Large Assembly Preview
```
Scale: mm → m
Hierarchy: Collections
Y-Up: ✓
Quality: 1.0 (fast)
Then re-tessellate selected parts
```

---

## 📖 Documentation Files

- **README.md** - Full documentation
- **INSTALL.md** - Installation guide
- **EXAMPLES.md** - Usage examples
- **DEVELOPER.md** - Developer guide
- **CHANGELOG.md** - Version history

---

## 🐛 Getting Help

1. Check console: Window → Toggle System Console
2. Verify FreeCAD installation
3. Review documentation
4. Check error messages
5. Test with simple file first

---

## 📝 Python API

```python
from ApexCadImporter import importer

success, msg, objs = importer.import_cad_file(
    bpy.context,
    filepath="path/to/file.stp",
    scale=0.001,
    hierarchy_mode='COLLECTION',
    y_up=True,
    chunk_size=50,
    tessellation_quality=0.1
)
```

---

**Version:** 1.0.0  
**Author:** Cristian Koch R.  
**Blender:** 5.0+  
**FreeCAD:** 0.20+
