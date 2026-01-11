# Contributing to ApexCad Importer

First off, thank you for considering contributing to ApexCad Importer! 

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples** (sample STEP files if possible)
- **Describe the behavior you observed** and what you expected
- **Include Blender console output** (Window → Toggle System Console)
- **Environment details**:
  - Blender version
  - FreeCAD version
  - Operating System
  - ApexCad Importer version

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description** of the suggested enhancement
- **Explain why this enhancement would be useful**
- **List similar functionality in other software** if applicable

### Pull Requests

#### Before Submitting

1. Check if there's already a PR that solves the problem
2. Test your changes with various STEP/IGES files
3. Ensure no console errors appear
4. Update documentation if needed
5. Follow the existing code style

#### Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following our code style
3. **Test thoroughly**:
   - Import simple STEP files
   - Import IGES files
   - Test large assemblies (100+ parts)
   - Test all scale presets
   - Test Y-up conversion
   - Verify metadata preservation
4. **Update documentation** if you've added/changed features
5. **Commit with clear messages**:
   ```
   Short summary (50 chars or less)
   
   Detailed explanation of changes if needed
   - Bullet points for multiple changes
   - Reference issues: Fixes #123
   ```
6. **Push to your fork** and submit a Pull Request

## Code Style

### Python Style

- Follow PEP 8 guidelines
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 120 characters
- Use descriptive variable names

### Naming Conventions

```python
# Classes (Blender convention)
class APEXCAD_OT_MyOperator(bpy.types.Operator):
    pass

# Functions
def my_function_name(arg1, arg2):
    pass

# Constants
MAX_CHUNK_SIZE = 50

# Private methods
def _internal_method(self):
    pass
```

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
    # Risky operation
    result = operation()
except SpecificException as e:
    # Handle specific error
    self.report({'ERROR'}, f"Operation failed: {str(e)}")
    return {'CANCELLED'}
except Exception as e:
    # Catch-all
    self.report({'ERROR'}, f"Unexpected error: {str(e)}")
    return {'CANCELLED'}
```

## Development Setup

### Prerequisites

- Blender 5.0+
- FreeCAD 0.20+
- VS Code (recommended)
- Blender Development extension by Jacques Lucke

### Setting Up Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Crikomoto/ApexCadImporter.git
   cd ApexCadImporter
   ```

2. **Open in VS Code**:
   ```bash
   code ApexCadImporter.code-workspace
   ```

3. **Install recommended extensions**:
   - Blender Development (jacqueslucke.blender-development)
   - Python (ms-python.python)
   - Pylance (ms-python.vscode-pylance)

4. **Configure Blender executable** in VS Code settings

5. **Start Blender** with addon:
   - Press `Ctrl+Shift+P`
   - Select "Blender: Start"
   - Addon auto-reloads on save

### Testing Changes

1. **Manual Testing**:
   - Import various STEP/IGES files
   - Test with different settings
   - Check console for errors
   - Verify metadata preservation

2. **Test Script**:
   ```python
   # In Blender Python console
   exec(open("test_addon.py").read())
   ```

## Project Structure

```
ApexCadImporter/
├── __init__.py           # Main registration
├── preferences.py        # Addon preferences
├── operators.py          # Import operators
├── ui.py                 # UI panels
├── freecad_bridge.py     # FreeCAD communication
├── importer.py           # Import logic
├── tessellation.py       # Re-tessellation
├── utils.py              # Helper functions
└── docs/                 # Documentation
```

## Adding New Features

### Example: Adding a New Import Option

1. **Add property to operator** (operators.py):
```python
my_new_option: BoolProperty(
    name="My New Option",
    description="Description of the option",
    default=True,
)
```

2. **Update UI** (operators.py draw method):
```python
def draw(self, context):
    layout = self.layout
    box = layout.box()
    box.prop(self, "my_new_option")
```

3. **Implement functionality** (importer.py):
```python
if options.get('my_new_option'):
    # Your code here
    pass
```

4. **Update documentation** (README.md, EXAMPLES.md)

5. **Test thoroughly**

## Commit Message Guidelines

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc)
- **refactor**: Code refactoring
- **test**: Adding/updating tests
- **chore**: Maintenance tasks

### Examples

```
feat: Add support for custom tessellation quality per object

Implements per-object quality override that allows different
tessellation settings for individual parts in an assembly.

Fixes #42
```

```
fix: Prevent crash when importing files with no geometry

Added validation to check if objects have geometry before
attempting mesh export.

Closes #38
```

## Questions?

Feel free to open an issue with the "question" label or reach out through GitHub discussions.

## License

By contributing, you agree that your contributions will be licensed under the same terms as the project (see LICENSE.md).

---

Thank you for contributing to ApexCad Importer! 🚀
