# VS Code Development Setup for ApexCad Importer

## Quick Start with Blender Development Extension

### 1. Install Required Extensions

The workspace already recommends these extensions. Install them when prompted, or manually:

- **Blender Development** by Jacques Lucke (`jacqueslucke.blender-development`)
- **Python** by Microsoft (`ms-python.python`)
- **Pylance** by Microsoft (`ms-python.vscode-pylance`)

### 2. Open Workspace

```bash
# Open the workspace file
code ApexCadImporter.code-workspace
```

Or in VS Code: File → Open Workspace from File → `ApexCadImporter.code-workspace`

### 3. Configure Blender Executable

Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and select:
- **"Blender: Set Blender Executable Path"**
- Browse to your Blender 5.0 executable

### 4. Start Blender with Addon

Two methods:

#### Method A: Command Palette
1. Press `Ctrl+Shift+P`
2. Select **"Blender: Start"**
3. Blender launches with addon loaded

#### Method B: Debug Panel
1. Go to Run and Debug panel (`Ctrl+Shift+D`)
2. Select **"Blender: Start"** configuration
3. Press F5 or click ▶️

### 5. Live Reload

With the extension configured:
- Make changes to any Python file
- Save the file (`Ctrl+S`)
- **Addon automatically reloads in Blender!**

No need to restart Blender or manually reload the addon.

## Development Workflow

### Typical Development Cycle

```
1. Edit Python file in VS Code
2. Save (Ctrl+S)
3. Extension reloads addon in Blender
4. Test in Blender
5. Check console for errors
6. Repeat
```

### Debugging

#### Print Debugging
```python
print(f"ApexCad: DEBUG - Variable value: {my_var}")
```
Output appears in Blender's System Console (Window → Toggle System Console)

#### VS Code Debugging (Advanced)
The extension supports breakpoint debugging:

1. Set breakpoints in VS Code (click left of line numbers)
2. Use **"Blender: Debug Script"** launch configuration
3. Debug panel shows variables, call stack, etc.

Note: Full debugging requires additional setup. See extension documentation.

## Extension Features

### Available Commands

Press `Ctrl+Shift+P` and type "Blender:" to see:

- **Blender: Start** - Launch Blender with addon
- **Blender: Reload Addons** - Manually reload addon
- **Blender: Set Blender Executable Path** - Configure Blender path
- **Blender: Build and Start** - Build addon and launch
- **Blender: Run Script** - Execute current Python file in Blender

### Keyboard Shortcuts

Default shortcuts:
- `Ctrl+Shift+P` - Command Palette
- `F5` - Start debugging
- `Ctrl+S` - Save and auto-reload
- `Ctrl+Shift+D` - Open Debug panel

## Workspace Configuration

The workspace is configured with:

### Auto-reload on Save
```json
"blender.addon.reloadOnSave": true
```

### Load Directory
```json
"blender.addon.loadDirectory": "${workspaceFolder}"
```
Points to the addon folder for loading.

### Python Settings
- Flake8 linting enabled
- Pylint disabled (Blender API not available in VS Code)
- Import errors suppressed for `bpy`, `bmesh`, `mathutils`

## Tips and Tricks

### 1. Multi-file Editing

Open multiple files side-by-side:
- `Ctrl+\` - Split editor
- Drag file tabs to rearrange

### 2. Search Across Files

- `Ctrl+Shift+F` - Search in all files
- Useful for finding where a function is used

### 3. Go to Definition

- `F12` - Jump to definition
- `Alt+F12` - Peek definition
- `Ctrl+Click` - Also jumps to definition

### 4. Git Integration

VS Code has built-in Git support:
- Source Control panel (`Ctrl+Shift+G`)
- See changes, stage, commit, push
- Inline diff view

### 5. Terminal Integration

- `Ctrl+`` - Toggle integrated terminal
- Run git commands, Python scripts, etc.

### 6. Problems Panel

- `Ctrl+Shift+M` - View linting errors
- Shows flake8 issues in real-time

## Troubleshooting

### Extension Not Loading Addon

**Check:**
1. Blender executable path is correct
2. Workspace folder contains `__init__.py`
3. `bl_info` is valid in `__init__.py`

**Solution:**
- Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"
- Check Output panel: View → Output → Select "Blender Development"

### Auto-reload Not Working

**Check:**
1. `blender.addon.reloadOnSave` is `true` in settings
2. Addon is enabled in Blender
3. No syntax errors (check Problems panel)

**Solution:**
- Manual reload: `Ctrl+Shift+P` → "Blender: Reload Addons"
- Check Blender console for errors

### Import Errors in VS Code

It's normal to see import errors for:
- `bpy` (Blender Python API)
- `bmesh` (Blender mesh module)
- `mathutils` (Blender math utilities)

These are available in Blender, not in VS Code. The workspace suppresses these errors:

```json
"python.analysis.diagnosticSeverityOverrides": {
    "reportMissingImports": "none"
}
```

### Blender Won't Start

**Check:**
1. Blender path is correct
2. Blender version is 5.0+
3. No other Blender instances running

**Solution:**
- Re-set Blender path: `Ctrl+Shift+P` → "Blender: Set Blender Executable Path"
- Check Output panel for error messages

## Advanced Configuration

### Custom Blender Arguments

Edit `.vscode/launch.json`:

```json
{
    "name": "Blender: Start",
    "type": "blender",
    "request": "launch",
    "args": ["--factory-startup", "--python-console"]
}
```

Useful arguments:
- `--factory-startup` - Start with default settings
- `--python-console` - Open Python console
- `--debug` - Enable debug mode
- `--log-level 0` - Show all log messages

### Multiple Blender Versions

Configure multiple executables in settings:

```json
"blender.executables": [
    {
        "name": "Blender 5.0",
        "path": "C:/Program Files/Blender 5.0/blender.exe"
    },
    {
        "name": "Blender 4.2",
        "path": "C:/Program Files/Blender 4.2/blender.exe"
    }
]
```

Switch between them in Command Palette.

## Resources

### Extension Documentation
- [Blender Development Extension](https://github.com/JacquesLucke/blender_vscode)

### Blender API
- [Blender Python API](https://docs.blender.org/api/current/)
- [Addon Tutorial](https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html)

### VS Code
- [VS Code Keyboard Shortcuts](https://code.visualstudio.com/shortcuts/keyboard-shortcuts-windows.pdf)
- [VS Code Python](https://code.visualstudio.com/docs/languages/python)

## Common Development Tasks

### Adding a New Operator

1. Edit `operators.py`
2. Add new class: `APEXCAD_OT_NewOperator`
3. Add to `classes` tuple
4. Save (auto-reloads in Blender)
5. Test: Search in Blender (F3) for operator

### Modifying Import Logic

1. Edit `importer.py`
2. Add debug prints
3. Save (auto-reloads)
4. Import test file in Blender
5. Check console output

### Updating UI

1. Edit `ui.py`
2. Modify panel layout
3. Save (auto-reloads)
4. Check 3D Viewport sidebar

### Testing Changes

1. Edit files
2. Save all (`Ctrl+K S`)
3. In Blender:
   - File → Import → STEP/IGES
   - Test your changes
   - Window → Toggle System Console (check output)

---

**Happy Coding!** 🚀

For questions about the extension, see the [official docs](https://github.com/JacquesLucke/blender_vscode).
