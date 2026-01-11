# ApexCad Importer for Blender

**Professional STEP and IGES Importer for Blender 5.0+**

Author: **Cristian Koch R.**  
Version: **2.0.0**  
License: MIT

---

## Overview

ApexCad Importer is a professional-grade Blender addon that enables native import of CAD files (STEP and IGES formats) using FreeCAD as a backend conversion engine. Designed for production pipelines with advanced features like auto-smooth shading, material extraction, instance detection, and batch import.

## ✨ Features

### Import & Conversion
- ✅ Native STEP (.stp, .step) and IGES (.igs, .iges) support
- ✅ FreeCAD-powered robust conversion
- ✅ Auto-smooth shading for perfect CAD surface display
- ✅ Material/color extraction from STEP files
- ✅ Automatic instance detection (memory optimization)
- ✅ Scale presets (mm→m, cm→m, inch→m) + custom
- ✅ Y-up coordinate conversion (CAD Z-up → Blender Y-up)
- ✅ Hierarchy preservation (nested assemblies)
- ✅ CAD metadata extraction (volume, area, bbox, colors)

### Advanced Features
- ✅ **Re-tessellation**: Change mesh quality after import (single object or entire hierarchy)
- ✅ **Batch Import**: Import entire folders with error recovery
- ✅ **Instance Detection**: Automatic mesh sharing for duplicate parts
- ✅ **Datum Filtering**: Removes reference planes/axes automatically
- ✅ **Non-blocking**: Asynchronous processing prevents Blender freeze

## 📋 Requirements

- **Blender 5.0+**
- **FreeCAD 1.0+** (or 0.20+)
  - Auto-detected on installation
  - Windows: `FreeCADCmd.exe` in Program Files
  - Linux: `freecad` in PATH
  - macOS: FreeCAD.app

## 🚀 Installation

1. **Download** this repository as ZIP or clone it
2. **Blender** → Edit → Preferences → Add-ons → Install
3. Select the `ApexCadImporter` folder
4. **Enable** "Import-Export: ApexCad Importer"
5. FreeCAD will be **auto-detected** (or set manually in preferences)

## 📖 Usage

### Single File Import

**File → Import → STEP/IGES**

Options:
- **Scale**: mm→m (0.001) for metric CAD files
- **Mesh Quality**: 0.01 = fine, 0.1 = balanced, 1.0 = coarse
- **Y-Up**: Enable for proper Blender orientation
- **Hierarchy**: Collections (recommended) or Empties

### Batch Import

**3D Viewport → N Panel → ApexCad → Batch Import Folder**

- Select folder with multiple STEP/IGES files
- All files import automatically
- Failed files create error collections
- Progress shown in console

### Re-tessellation

**Select object → ApexCad Panel → Re-tessellate**

- **Re-tessellate Object**: Change quality of selected part
- **Re-tessellate Hierarchy**: Change quality of entire assembly

## 🎨 Features in Detail

### Auto Smooth Shading
All imported meshes get `shade_auto_smooth` with 30° angle for perfect CAD surface display (sharp edges preserved, smooth surfaces polished).

### Material Extraction
Colors from STEP files automatically create PBR materials:
- Extracts ShapeColor and DiffuseColor
- Auto-configures roughness (0.3) for CAD look
- Metallic detection for dark colors

### Instance Detection
Identical parts automatically share mesh data:
- Detects duplicates via geometry hash
- Converts to instances (saves 50-90% memory)
- Preserves individual transforms
- Example: 20 identical bolts = 1 mesh, 20 instances

### Metadata Extraction
CAD properties stored as custom properties:
- `cad_volume`: Part volume
- `cad_area`: Surface area
- `cad_bbox`: Bounding box
- `cad_color`: RGBA color
- `apexcad_source_file`: Original file path
- `apexcad_tessellation`: Current quality

## 🔧 Preferences

**Edit → Preferences → Add-ons → ApexCad Importer**

- **FreeCAD Path**: Auto-detected or manual
- **Auto-Detect FreeCAD**: Scans common locations on startup
- **Default Settings**: Scale, hierarchy mode, Y-up
- **Performance**: Max chunk size for large assemblies

## 📊 Performance Tips

1. **Start with low quality** (0.1) for preview
2. **Re-tessellate** specific parts to higher quality (0.01)
3. **Batch import** uses background processing
4. **Instance detection** automatically optimizes memory

## 🐛 Troubleshooting

### FreeCAD Not Found
- Click "Auto-Detect" in preferences
- Or manually browse to:
  - Windows: `C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe`
  - Linux: `/usr/bin/freecad`
  - macOS: `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`

### Import Failed
- Check console (Window → Toggle System Console)
- Verify STEP file is valid (open in FreeCAD first)
- Try lower tessellation quality
- Check FreeCAD version (1.0+ recommended)

### Batch Import Errors
- Failed files create `ERROR_filename.stp` collections
- Check console for specific error messages
- Corrupted files are skipped automatically

## 🔗 Links

- **GitHub**: https://github.com/Crikomoto/ApexCadImporter
- **Issues**: https://github.com/Crikomoto/ApexCadImporter/issues
- **FreeCAD**: https://www.freecad.org

## 📝 Changelog

### v2.0.0 (2026-01-11)
- Auto smooth shading for CAD surfaces
- Material/color extraction from STEP
- Instance detection for duplicate parts
- Re-tessellation (object + hierarchy)
- Batch import with error recovery
- Datum filtering (50% fewer objects)
- Enhanced FreeCAD auto-detection

### v1.0.0
- Initial release
- STEP/IGES import
- Basic hierarchy support

## 📄 License

MIT License - See LICENSE.md

---

**Made with ❤️ for the Blender + CAD community**

Or use the Properties panel → Object Properties → CAD Properties section.

### Viewing CAD Metadata:

Imported objects retain CAD metadata:
- **3D Viewport → Sidebar → ApexCad → Show Metadata**
- Or **Properties → Object Properties → CAD Properties panel**

Metadata includes:
- Volume, surface area
- Bounding box dimensions
- Original CAD part names
- Custom CAD properties

## Performance Tips

### For Large Assemblies (1000+ parts):

1. **Increase Chunk Size**: Preferences → Max Chunk Size → 100-200
2. **Use Lower Initial Quality**: Import at 0.5-1.0, then selectively re-tessellate critical parts
3. **Enable Async Import**: Keeps Blender responsive (enabled by default)
4. **Hierarchy by Collections**: More efficient than Empty objects for large assemblies

### Memory Management:

The addon uses a divide-and-conquer strategy:
- Processes objects in chunks (default 50 at a time)
- Prevents memory overflow on massive assemblies
- FreeCAD does heavy lifting, not Blender

## Troubleshooting

### "FreeCAD path not configured"
→ Set FreeCAD path in addon preferences, use auto-detect button

### "FreeCAD conversion failed"
→ Check FreeCAD is properly installed and path is correct
→ Try running FreeCAD manually to verify installation

### Import is slow
→ Increase mesh quality value (0.5-1.0)
→ Check chunk size in preferences
→ Large files naturally take time due to tessellation

### Objects appear too small/large
→ Verify scale setting (CAD units vs Blender meters)
→ Most mechanical CAD uses millimeters (use 0.001 scale)

### Hierarchy not correct
→ Some CAD files have flat hierarchies
→ Try different hierarchy modes
→ Check original CAD file structure in FreeCAD

### Y-up orientation wrong
→ Toggle Y-Up Conversion option
→ Some CAD formats already use Y-up

## Technical Architecture

### Modular Design:

```
ApexCadImporter/
├── __init__.py           # Main registration and module loading
├── preferences.py        # Addon preferences and settings
├── operators.py          # Import and re-tessellation operators
├── ui.py                 # UI panels and menus
├── freecad_bridge.py     # FreeCAD CLI communication
├── importer.py           # Main import logic (divide & conquer)
├── tessellation.py       # Re-tessellation system
└── utils.py              # Helper functions
```

### Workflow:

1. **User initiates import** → Operator triggered
2. **FreeCAD Bridge** → Generates Python script for FreeCAD
3. **FreeCAD Processing** → Converts CAD to OBJ meshes + JSON hierarchy
4. **Importer** → Loads OBJs in chunks, builds hierarchy
5. **Utils** → Applies transformations, metadata, Y-up conversion
6. **Result** → Clean Blender scene with organized CAD data

### Divide and Conquer Strategy:

For files with hundreds/thousands of parts:
- Processes in configurable chunks (default 50)
- Prevents Blender UI freeze
- Maintains memory efficiency
- Progress tracking per chunk

## Future Development

Planned features:
- ✅ Basic STEP/IGES import
- ✅ Hierarchy preservation
- ✅ Metadata transfer
- ✅ Y-up conversion
- 🔄 Full re-tessellation implementation (in progress)
- 📋 Assembly constraints import
- 📋 Material/color information transfer
- 📋 Incremental update of changed parts
- 📋 Direct FreeCAD file (.FCStd) support

## Development

### VS Code Setup

This addon is developed using VS Code with the Blender Development extension by Jacques Lucke:

1. Install the extension: `jacqueslucke.blender-development`
2. Open the workspace: `ApexCadImporter.code-workspace`
3. Configure Blender executable path in VS Code settings
4. Use `Ctrl+Shift+P` → "Blender: Start" to launch Blender with addon
5. Addon auto-reloads on save for rapid development

### Repository

- **GitHub**: https://github.com/Crikomoto/ApexCadImporter
- **Issues**: Report bugs and request features on GitHub
- **Contributions**: Pull requests welcome!

## Support

For issues, questions, or contributions:
- **GitHub Issues**: https://github.com/Crikomoto/ApexCadImporter/issues
- Check documentation above
- Verify FreeCAD installation
- Review Blender console for detailed error messages

## License

Copyright © 2026 Cristian Koch R.

This addon is provided as-is for professional use in Blender.

## Credits

- **Developer**: Cristian Koch R.
- **Repository**: https://github.com/Crikomoto/ApexCadImporter
- **CAD Engine**: FreeCAD (LGPL)
- **Target Platform**: Blender 5.0+

---

**ApexCad Importer** - Bringing professional CAD workflows to Blender
