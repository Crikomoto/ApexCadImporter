# ApexCad Importer for Blender

**Professional STEP and IGES Importer for Blender 5.0+**

Author: **Cristian Koch R.**  
Version: 1.0.0

---

## Overview

ApexCad Importer is a professional-grade Blender addon that enables native import of CAD files (STEP and IGES formats) using FreeCAD as a backend conversion engine. Designed for production pipelines, it handles large assemblies with a divide-and-conquer strategy while maintaining stability and performance.

## Features

✨ **Core Capabilities:**
- Import STEP (.stp, .step) and IGES (.igs, .iges) files natively in Blender
- Powered by FreeCAD command-line for robust CAD conversion
- Asynchronous processing to prevent Blender freezing
- Scalable architecture for large assemblies (divide and conquer)

🎯 **Advanced Features:**
- **Scale Conversion**: Preset conversions (mm→m, cm→m, inch→m) or custom scale
- **Hierarchy Preservation**: Import as Collections or Empty-based hierarchies
- **Y-Up Conversion**: Automatic coordinate system conversion from CAD Z-up
- **Metadata Transfer**: CAD metadata embedded as custom properties
- **Pivot Points**: Original pivot points and transforms preserved
- **Non-destructive Re-tessellation**: Adjust mesh quality after import

## Requirements

### Software Requirements:
- **Blender 5.0+** (tested with 5.0.0)
- **FreeCAD 0.20+** with command-line support
  - Windows: `FreeCADCmd.exe` or `freecad.exe` (both work)
  - Linux/Mac: `freecad` or `freecadcmd`
  - The addon will automatically detect either executable

### Installation:

1. **Install FreeCAD:**
   - Windows: Download from [freecad.org](https://www.freecad.org)
   - Linux: `sudo apt install freecad` or equivalent
   - Mac: `brew install --cask freecad`

2. **Install ApexCad Addon:**
   - Download the `ApexCadImporter` folder
   - In Blender: Edit → Preferences → Add-ons → Install
   - Navigate to the folder and select it
   - Enable "Import-Export: ApexCad Importer"

3. **Configure FreeCAD Path:**
   - In addon preferences, click the search icon to auto-detect
   - Or manually set path to FreeCAD executable
   - Verify that "✓ FreeCAD found" appears

## Usage

### Basic Import:

1. **File → Import → STEP/IGES (.stp, .igs)**
2. Select your CAD file
3. Configure import options:
   - **Scale**: Choose unit conversion or custom scale
   - **Hierarchy Mode**: Collections or Empty objects
   - **Y-Up Conversion**: Enable for standard Blender orientation
   - **Mesh Quality**: Lower = better quality (0.01-5.0)
4. Click "Import STEP/IGES"

### Import Options Explained:

#### Scale Settings:
- **mm → m (0.001)**: For CAD files in millimeters (most common)
- **cm → m (0.01)**: For centimeter-based models
- **m → m (1.0)**: No scaling needed
- **inch → m (0.0254)**: For imperial units
- **Custom**: Specify your own scale factor

#### Hierarchy Mode:
- **Collections**: Organizes parts in Blender Collections (recommended)
- **Empty Objects**: Uses Empty objects as hierarchy nodes (traditional)

#### Coordinate System:
- **Y-Up Conversion**: Most CAD uses Z-up; enable this for Blender's Y-up system

#### Mesh Quality:
- Lower values = higher quality, more faces, slower import
- **0.01**: Ultra high quality (slow)
- **0.1**: Good balance (default)
- **1.0**: Fast, lower quality

### Re-tessellation:

After importing, you can adjust mesh quality non-destructively:

1. Select a CAD-imported object
2. In the **ApexCad panel** (3D Viewport → Sidebar → ApexCad tab)
3. Click "Re-tessellate"
4. Choose new quality setting
5. Apply

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
