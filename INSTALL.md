# ApexCad Importer - Installation Guide

## Quick Start

### 1. Prerequisites

**Install FreeCAD:**

#### Windows:
1. Download FreeCAD from https://www.freecad.org/downloads.php
2. Install to default location (e.g., `C:\Program Files\FreeCAD 0.21\`)
3. Verify `FreeCADCmd.exe` exists in the `bin` folder

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install freecad
```

#### Mac:
```bash
brew install --cask freecad
```

### 2. Install Addon in Blender

#### Method 1: Direct Installation (Recommended)
1. Download or clone the `ApexCadImporter` folder
2. Copy entire folder to Blender addons directory:
   - **Windows**: `C:\Users\[YourUser]\AppData\Roaming\Blender Foundation\Blender\5.0\scripts\addons\`
   - **Linux**: `~/.config/blender/5.0/scripts/addons/`
   - **Mac**: `~/Library/Application Support/Blender/5.0/scripts/addons/`
3. Restart Blender
4. Edit → Preferences → Add-ons
5. Search for "ApexCad"
6. Enable the checkbox

#### Method 2: Install from ZIP
1. Compress the `ApexCadImporter` folder to a ZIP file
2. In Blender: Edit → Preferences → Add-ons → Install
3. Select the ZIP file
4. Enable "Import-Export: ApexCad Importer"

### 3. Configure FreeCAD Path

1. In Blender Preferences → Add-ons → ApexCad Importer
2. Click the magnifying glass icon to **auto-detect** FreeCAD
3. If auto-detect fails, manually browse to FreeCAD executable:
   - **Windows**: `C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe`
   - **Linux**: `/usr/bin/freecad`
   - **Mac**: `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`
4. Look for "✓ FreeCAD found" confirmation

### 4. Test Import

1. File → Import → STEP/IGES (.stp, .igs)
2. Select a test STEP file
3. Use default settings
4. Click "Import STEP/IGES"

If successful, you should see objects imported into your scene!

## Troubleshooting Installation

### Issue: "FreeCAD not found"

**Solution:**
- Verify FreeCAD is installed correctly
- Open terminal/command prompt and try:
  - Windows: `"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe" --version`
  - Linux/Mac: `freecad --version`
- If this works, copy the path to addon preferences

### Issue: Addon doesn't appear in list

**Solution:**
- Make sure folder structure is correct:
  ```
  addons/
    ApexCadImporter/
      __init__.py
      preferences.py
      operators.py
      ...
  ```
- Check Blender console for error messages (Window → Toggle System Console)
- Verify Blender version is 5.0 or higher

### Issue: Import fails with Python errors

**Solution:**
- Check Blender console for detailed error
- Verify all module files are present
- Try reinstalling the addon
- Make sure no files were corrupted during download

## Verification Checklist

✅ FreeCAD installed and executable  
✅ ApexCad addon folder in correct location  
✅ Addon enabled in Blender preferences  
✅ FreeCAD path configured correctly  
✅ Green checkmark "✓ FreeCAD found" in preferences  
✅ "STEP/IGES" appears in File → Import menu  
✅ ApexCad panel visible in 3D Viewport sidebar  

## Next Steps

Once installed:
- Read the [README.md](README.md) for usage instructions
- Configure default import settings in preferences
- Try importing a simple STEP file
- Explore the ApexCad panel in the 3D Viewport sidebar

---

**Need Help?**  
Check the full documentation in README.md or review the Blender console for error messages.
