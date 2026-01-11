"""
FreeCAD Bridge Module
Handles communication with FreeCAD command-line interface
Implements asynchronous processing to prevent Blender freezing
"""

import bpy
import subprocess
import os
import tempfile
import json
import threading
import queue
from pathlib import Path


class FreeCADBridge:
    """
    Manages communication with FreeCAD CLI for CAD file conversion
    Uses background threads to prevent blocking Blender's main thread
    """
    
    def __init__(self, freecad_path):
        self.freecad_path = freecad_path
        self.temp_dir = tempfile.mkdtemp(prefix="apexcad_")
        self.process_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
    def validate_freecad(self):
        """Check if FreeCAD executable is valid"""
        if not os.path.exists(self.freecad_path):
            return False, "FreeCAD executable not found"
        
        try:
            # Test FreeCAD execution
            print(f"ApexCad: Validating FreeCAD at {self.freecad_path}")
            result = subprocess.run(
                [self.freecad_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"ApexCad: FreeCAD validation OK - {version}")
                return True, version
            return False, f"Failed to execute FreeCAD (code {result.returncode})"
        except subprocess.TimeoutExpired:
            return False, "FreeCAD validation timeout (>10s)"
        except Exception as e:
            return False, str(e)
    
    def generate_conversion_script(self, input_file, output_dir, options):
        """
        Generate Python script for FreeCAD to execute
        
        Args:
            input_file: Path to STEP/IGES file
            output_dir: Directory for output files
            options: Dict with conversion options (scale, y_up, etc.)
        
        Returns:
            Path to generated script
        """
        script_content = f'''
import FreeCAD
import Import
import Mesh
import os
import json

# Configuration
input_file = r"{input_file}"
output_dir = r"{output_dir}"
scale_factor = {options.get('scale', 1.0)}
y_up = {options.get('y_up', True)}
tessellation_quality = {options.get('tessellation_quality', 0.1)}

print("ApexCad: Starting conversion...")
print(f"Input: {{input_file}}")

# Import the CAD file
try:
    doc = FreeCAD.newDocument("ApexCadImport")
    
    # Import STEP or IGES
    file_ext = os.path.splitext(input_file)[1].lower()
    if file_ext in ['.stp', '.step']:
        Import.insert(input_file, "ApexCadImport")
    elif file_ext in ['.igs', '.iges']:
        Import.insert(input_file, "ApexCadImport")
    else:
        raise ValueError(f"Unsupported file format: {{file_ext}}")
    
    print(f"ApexCad: Loaded {{len(doc.Objects)}} objects")
    
    # Process objects and create hierarchy data
    hierarchy_data = {{
        "objects": [],
        "root_objects": [],
        "scale": scale_factor,
        "y_up": y_up
    }}
    
    object_map = {{}}
    
    for idx, obj in enumerate(doc.Objects):
        obj_data = {{
            "name": obj.Label,
            "internal_name": obj.Name,
            "type": obj.TypeId,
            "index": idx,
            "metadata": {{}},
            "parent": None,
            "children": []
        }}
        
        # Extract metadata
        if hasattr(obj, 'Shape'):
            shape = obj.Shape
            obj_data["metadata"]["volume"] = shape.Volume if hasattr(shape, 'Volume') else 0
            obj_data["metadata"]["area"] = shape.Area if hasattr(shape, 'Area') else 0
            
            # Get bounding box
            try:
                bbox = shape.BoundBox
                obj_data["metadata"]["bbox"] = {{
                    "min": [bbox.XMin, bbox.YMin, bbox.ZMin],
                    "max": [bbox.XMax, bbox.YMax, bbox.ZMax]
                }}
            except:
                pass
        
        # Get position (if available)
        if hasattr(obj, 'Placement'):
            placement = obj.Placement
            pos = placement.Base
            rot = placement.Rotation
            
            obj_data["transform"] = {{
                "position": [pos.x * scale_factor, pos.y * scale_factor, pos.z * scale_factor],
                "rotation": [rot.Q[0], rot.Q[1], rot.Q[2], rot.Q[3]]  # Quaternion
            }}
        
        # Get parent relationship
        if hasattr(obj, 'Parents') and obj.Parents:
            parent = obj.Parents[0][0]
            obj_data["parent"] = parent.Name
        
        # Export mesh
        if hasattr(obj, 'Shape') and obj.Shape.Faces:
            mesh_file = os.path.join(output_dir, f"{{obj.Name}}.obj")
            
            try:
                # Tessellate shape
                obj.Shape.tessellate(tessellation_quality)
                
                # Export as OBJ (preserves coordinates)
                Mesh.export([obj], mesh_file)
                obj_data["mesh_file"] = mesh_file
                print(f"ApexCad: Exported {{obj.Label}} -> {{mesh_file}}")
            except Exception as e:
                print(f"ApexCad: Warning - Failed to export {{obj.Label}}: {{e}}")
                obj_data["mesh_file"] = None
        
        hierarchy_data["objects"].append(obj_data)
        object_map[obj.Name] = obj_data
    
    # Build parent-child relationships
    for obj_data in hierarchy_data["objects"]:
        if obj_data["parent"]:
            parent_data = object_map.get(obj_data["parent"])
            if parent_data:
                parent_data["children"].append(obj_data["internal_name"])
        else:
            hierarchy_data["root_objects"].append(obj_data["internal_name"])
    
    # Save hierarchy data
    hierarchy_file = os.path.join(output_dir, "hierarchy.json")
    with open(hierarchy_file, 'w') as f:
        json.dump(hierarchy_data, f, indent=2)
    
    print(f"ApexCad: Conversion complete! Hierarchy saved to {{hierarchy_file}}")
    print(f"ApexCad: Processed {{len(hierarchy_data['objects'])}} objects")
    
    FreeCAD.closeDocument("ApexCadImport")
    
except Exception as e:
    print(f"ApexCad: ERROR - {{str(e)}}")
    import traceback
    traceback.print_exc()
    exit(1)
'''
        
        script_path = os.path.join(self.temp_dir, "convert_script.py")
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return script_path
    
    def convert_file_async(self, input_file, output_dir, options, callback=None):
        """
        Convert CAD file asynchronously
        
        Args:
            input_file: Path to STEP/IGES file
            output_dir: Output directory
            options: Conversion options
            callback: Function to call when complete (result_dict)
        """
        def _run_conversion():
            result = self.convert_file_sync(input_file, output_dir, options)
            if callback:
                callback(result)
            self.result_queue.put(result)
        
        thread = threading.Thread(target=_run_conversion, daemon=True)
        thread.start()
        return thread
    
    def convert_file_sync(self, input_file, output_dir, options):
        """
        Convert CAD file synchronously (blocking)
        
        Returns:
            Dict with conversion results
        """
        # Validate input file
        if not os.path.exists(input_file):
            return {
                'success': False,
                'error': f"Input file not found: {input_file}"
            }
        
        file_size = os.path.getsize(input_file) / (1024 * 1024)  # MB
        print(f"ApexCad: Input file: {os.path.basename(input_file)} ({file_size:.2f} MB)")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate conversion script
        script_path = self.generate_conversion_script(input_file, output_dir, options)
        print(f"ApexCad: Generated script at {script_path}")
        
        try:
            # Execute FreeCAD with platform-specific flags
            print(f"ApexCad: Starting FreeCAD conversion...")
            print(f"ApexCad: Command: {self.freecad_path} -c {script_path}")
            
            # Platform-specific flags to prevent window creation
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:  # Linux/Mac
                startupinfo = None
                creation_flags = 0
            
            result = subprocess.run(
                [self.freecad_path, "-c", script_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                startupinfo=startupinfo,
                creationflags=creation_flags
            )
            
            print(f"ApexCad: FreeCAD finished with return code: {result.returncode}")
            
            # Parse output
            output_lines = result.stdout.split('\n')
            
            # Print FreeCAD output for debugging
            print("\n" + "="*50)
            print("FreeCAD Output:")
            print("="*50)
            for line in output_lines[:20]:  # First 20 lines
                if line.strip():
                    print(f"  {line}")
            if len(output_lines) > 20:
                print(f"  ... ({len(output_lines) - 20} more lines)")
            print("="*50 + "\n")
            
            # Check for errors
            if result.returncode != 0:
                print(f"ApexCad: ERROR - FreeCAD failed with code {result.returncode}")
                print(f"ApexCad: STDERR: {result.stderr}")
                return {
                    'success': False,
                    'error': f"FreeCAD conversion failed (code {result.returncode}): {result.stderr}",
                    'output': result.stdout
                }
            
            # Load hierarchy data
            hierarchy_file = os.path.join(output_dir, "hierarchy.json")
            if os.path.exists(hierarchy_file):
                with open(hierarchy_file, 'r') as f:
                    hierarchy_data = json.load(f)
                
                return {
                    'success': True,
                    'hierarchy': hierarchy_data,
                    'output_dir': output_dir,
                    'output': result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': "Hierarchy file not generated",
                    'output': result.stdout
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "FreeCAD conversion timed out (>5 minutes)",
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Conversion error: {str(e)}",
            }
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass


def get_bridge(context):
    """Get or create FreeCAD bridge instance"""
    prefs = context.preferences.addons[__package__.split('.')[0]].preferences
    
    if not prefs.freecad_path:
        return None, "FreeCAD path not configured. Check addon preferences."
    
    if not os.path.exists(prefs.freecad_path):
        return None, f"FreeCAD not found at: {prefs.freecad_path}"
    
    bridge = FreeCADBridge(prefs.freecad_path)
    is_valid, message = bridge.validate_freecad()
    
    if not is_valid:
        return None, f"FreeCAD validation failed: {message}"
    
    return bridge, None
