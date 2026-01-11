# ApexCad Importer - Changelog

## Version 1.0.0 (Initial Release)

### Features
- ✅ STEP file import (.stp, .step)
- ✅ IGES file import (.igs, .iges)
- ✅ FreeCAD backend integration
- ✅ Asynchronous processing (non-blocking)
- ✅ Multiple scale presets (mm, cm, m, inch)
- ✅ Custom scale factor support
- ✅ Hierarchy preservation (Collections or Empty objects)
- ✅ Y-up coordinate system conversion
- ✅ Metadata transfer from CAD files
- ✅ Pivot point preservation
- ✅ Divide-and-conquer strategy for large assemblies
- ✅ Configurable chunk size processing
- ✅ Auto-detection of FreeCAD installation
- ✅ Custom properties panel for CAD metadata
- ✅ 3D Viewport sidebar panel
- ✅ Tessellation quality control
- ✅ Non-destructive re-tessellation framework

### Technical Implementation
- Modular architecture with 8 core modules
- FreeCAD CLI bridge with subprocess management
- JSON-based hierarchy data transfer
- OBJ intermediate format for mesh data
- Quaternion rotation preservation
- Bounding box metadata extraction
- Volume and area calculations
- Safe name sanitization
- Unique name generation system

### User Interface
- File browser import dialog
- Comprehensive import options panel
- Preferences page with FreeCAD configuration
- 3D Viewport sidebar integration
- Object Properties panel integration
- Metadata viewer operator
- Re-tessellation dialog

### Performance
- Chunked processing (default 50 objects/chunk)
- Background FreeCAD execution
- Temporary file cleanup
- Memory-efficient OBJ loading
- Progress tracking and reporting

### Documentation
- Complete README with usage guide
- Installation instructions
- Troubleshooting section
- Technical architecture documentation
- Performance optimization tips

### Known Limitations
- Re-tessellation requires full re-import (framework in place)
- Assembly constraints not yet imported
- Material/color information not transferred
- Limited to FreeCAD-supported formats

### Compatibility
- Blender 5.0.0+
- FreeCAD 0.20+
- Windows, Linux, macOS

---

## Roadmap

### Version 1.1.0 (Planned)
- Complete re-tessellation implementation
- Cache original CAD files for re-tessellation
- Selective part re-import
- Progress bar for long imports
- Cancel operation support

### Version 1.2.0 (Planned)
- Material and color import
- Assembly constraint visualization
- Named selection sets
- Layer/level organization

### Version 2.0.0 (Future)
- Direct FreeCAD file (.FCStd) support
- Incremental update system
- Live link with FreeCAD
- Parametric feature preservation
- Sketch/constraint import

---

**Author**: Cristian Koch R.  
**License**: Custom  
**Repository**: ApexCadImporter
