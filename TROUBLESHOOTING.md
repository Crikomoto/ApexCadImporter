# ApexCad Importer - Troubleshooting Guide

## Blender Freezing / Hanging Issues

### Quick Diagnostics

**Step 1: Test FreeCAD Connection**
1. Open Blender
2. Go to: Edit → Preferences → Add-ons → ApexCad Importer
3. Click **"Test FreeCAD Connection"** button
4. Check Blender console (Window → Toggle System Console)

**Step 2: Run Connection Test Script**
1. In Blender, go to Scripting workspace
2. Open file: `test_freecad_connection.py`
3. Click **Run Script**
4. Check console output

**Step 3: Check What's Happening**
- Open Blender console: Window → Toggle System Console
- Look for messages like:
  - `ApexCad: Starting FreeCAD conversion...`
  - `ApexCad: FreeCAD finished with return code: X`

---

## Common Issues and Solutions

### Issue 1: Blender Freezes Immediately

**Cause:** FreeCAD path not configured or invalid

**Solution:**
```
1. Edit → Preferences → Add-ons → ApexCad
2. Click the 🔍 (magnifying glass) to auto-detect
3. Or manually set path to FreeCAD executable
4. Click "Test FreeCAD Connection"
```

**Verify:**
- Windows: `C:\Program Files\FreeCAD X.XX\bin\FreeCADCmd.exe`
- Linux: `/usr/bin/freecad` or `/usr/bin/freecadcmd`
- Mac: `/Applications/FreeCAD.app/Contents/MacOS/FreeCAD`

---

### Issue 2: Freezes During Import (Small Files Too)

**Cause:** FreeCAD taking too long or crashing

**Diagnostic:**
```python
# Run this in Blender console:
import subprocess
import os

prefs = bpy.context.preferences.addons['ApexCadImporter'].preferences
freecad = prefs.freecad_path

# Test FreeCAD manually
result = subprocess.run([freecad, "--version"], capture_output=True, timeout=10)
print(result.stdout)
```

**Solutions:**

A. **FreeCAD not responding:**
   - Reinstall FreeCAD from https://www.freecad.org
   - Try both `FreeCADCmd.exe` and `freecad.exe`
   - Check antivirus isn't blocking FreeCAD

B. **Timeout issues:**
   - Check console for "timeout" messages
   - Your CAD file might be corrupt
   - Try a different CAD file

C. **Platform-specific:**
   
   **Windows:**
   ```
   - Run Blender as Administrator
   - Disable Windows Defender temporarily
   - Check if FreeCAD opens standalone
   ```
   
   **Linux:**
   ```
   - Install FreeCAD: sudo apt install freecad
   - Check permissions: chmod +x /path/to/freecad
   - Test in terminal: freecad --version
   ```
   
   **Mac:**
   ```
   - Install via Homebrew: brew install --cask freecad
   - Grant permissions in System Preferences
   - Test: /Applications/FreeCAD.app/Contents/MacOS/FreeCAD --version
   ```

---

### Issue 3: Import Starts But Never Finishes

**Cause:** File is larger than expected or very complex

**Check Console For:**
```
ApexCad: Starting FreeCAD conversion...
ApexCad: Running FreeCAD conversion...
(then nothing for minutes)
```

**Solutions:**

1. **Wait Longer:**
   - Default timeout is 5 minutes (300 seconds)
   - Complex assemblies take time
   - Check Task Manager/Activity Monitor - is FreeCAD running?

2. **Simplify File:**
   - Export from CAD software with fewer details
   - Remove unnecessary components
   - Split large assemblies into parts

3. **Increase Timeout:**
   Edit `freecad_bridge.py`, line ~235:
   ```python
   timeout=300,  # Change to 600 (10 minutes) or more
   ```

---

### Issue 4: "FreeCAD conversion failed"

**Check Console For Error Messages:**

**Error Pattern 1: Module not found**
```
ModuleNotFoundError: No module named 'Import'
```
**Solution:** FreeCAD installation incomplete. Reinstall FreeCAD.

**Error Pattern 2: Permission denied**
```
PermissionError: [Errno 13] Permission denied
```
**Solution:**
- Run Blender with administrator/sudo
- Check file permissions
- Disable antivirus temporarily

**Error Pattern 3: File format error**
```
ValueError: Unsupported file format
```
**Solution:**
- Check file extension: .stp, .step, .igs, .iges
- File might be corrupted
- Try opening in FreeCAD standalone first

---

## Platform-Specific Issues

### Windows

**Issue: CREATE_NO_WINDOW error**
```python
# If you see errors about CREATE_NO_WINDOW, edit freecad_bridge.py
# Comment out the window flags:

# if os.name == 'nt':  # Windows
#     startupinfo = subprocess.STARTUPINFO()
#     startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
#     creation_flags = subprocess.CREATE_NO_WINDOW
# else:
#     startupinfo = None
#     creation_flags = 0

# Replace with:
startupinfo = None
creation_flags = 0
```

**Issue: Path with spaces**
- Use quotes in path
- Or use short path: `C:\PROGRA~1\FreeCAD\...`

### Linux

**Issue: FreeCAD not in PATH**
```bash
# Add to ~/.bashrc:
export PATH="/usr/local/bin:$PATH"

# Or create symlink:
sudo ln -s /path/to/freecad /usr/local/bin/freecad
```

**Issue: Missing dependencies**
```bash
sudo apt-get install freecad python3-freecad
```

### Mac

**Issue: "FreeCAD cannot be opened"**
```bash
# Remove quarantine flag:
xattr -d com.apple.quarantine /Applications/FreeCAD.app

# Grant permissions:
System Preferences → Security & Privacy → Allow FreeCAD
```

**Issue: Wrong Python version**
- Mac FreeCAD may use different Python
- Install FreeCAD via Homebrew for consistency

---

## Debug Mode

### Enable Verbose Logging

Edit `freecad_bridge.py`, add debug prints:

```python
def convert_file_sync(self, input_file, output_dir, options):
    print(f"DEBUG: Input file: {input_file}")
    print(f"DEBUG: Output dir: {output_dir}")
    print(f"DEBUG: Options: {options}")
    print(f"DEBUG: FreeCAD path: {self.freecad_path}")
    
    # ... rest of function
```

### Monitor FreeCAD Process

**Windows:**
- Open Task Manager
- Look for `FreeCADCmd.exe` or `freecad.exe`
- Check CPU/Memory usage

**Linux/Mac:**
```bash
# In terminal:
watch -n 1 'ps aux | grep -i freecad'
```

---

## Test Files

### Create Minimal Test Case

1. **Simple Cube (fastest test):**
   - Create cube in FreeCAD
   - Export as STEP
   - Try importing

2. **Provided Sample Files:**
   - Download from FreeCAD examples
   - Test with known-good files
   - Isolate if issue is file-specific

---

## Still Having Issues?

### Gather Information

Run diagnostic script [`test_freecad_detection.py`](test_freecad_detection.py):
```python
# In Blender Scripting workspace
exec(open("test_freecad_detection.py").read())
```

Copy the output and:

1. **Check GitHub Issues:**
   https://github.com/Crikomoto/ApexCadImporter/issues

2. **Create New Issue:**
   - Include full console output
   - Blender version
   - FreeCAD version
   - Operating System
   - File size/type
   - Steps to reproduce

3. **Temporary Workaround:**
   - Use FreeCAD standalone to convert to OBJ
   - Import OBJ in Blender
   - (Loses hierarchy/metadata but works)

---

## Emergency Workaround

If addon keeps freezing Blender:

```python
# Manual conversion in FreeCAD:
# 1. Open FreeCAD
# 2. File → Open → your.stp file
# 3. File → Export → OBJ format
# 4. Import OBJ in Blender

# Or use FreeCAD command line:
FreeCADCmd -c convert.py

# Where convert.py contains:
import FreeCAD
import Import
Import.insert("input.stp", "Doc")
FreeCAD.getDocument("Doc").getObject("Part").Shape.exportStl("output.stl")
```

---

**Last Updated:** January 11, 2026  
**Version:** 1.0.0
