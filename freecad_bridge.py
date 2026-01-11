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
import time
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
        start_time = time.time()
        
        # Validate input file
        if not os.path.exists(input_file):
            return {
                'success': False,
                'error': f"Input file not found: {input_file}"
            }
        
        file_size_mb = os.path.getsize(input_file) / (1024 * 1024)  # MB
        file_size_kb = os.path.getsize(input_file) / 1024  # KB
        print(f"\n{'='*60}")
        print(f"ApexCad: INICIANDO CONVERSIÓN")
        print(f"Archivo: {os.path.basename(input_file)}")
        print(f"Tamaño: {file_size_kb:.1f} KB ({file_size_mb:.2f} MB)")
        print(f"Tiempo: {time.strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate conversion script
        script_start = time.time()
        script_path = self.generate_conversion_script(input_file, output_dir, options)
        script_time = time.time() - script_start
        print(f"[{script_time:.2f}s] Script generado: {script_path}")
        
        try:
            # Execute FreeCAD with platform-specific flags
            exec_start = time.time()
            print(f"\n[{time.time() - start_time:.2f}s] Ejecutando FreeCAD...")
            print(f"Comando: {self.freecad_path} -c {script_path}")
            print(f"Esperando respuesta (timeout: 60s para archivos <1MB)...\n")
            
            # Platform-specific flags to prevent window creation
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creation_flags = subprocess.CREATE_NO_WINDOW
            else:  # Linux/Mac
                startupinfo = None
                creation_flags = 0
            
            # Dynamic timeout based on file size
            timeout = 60 if file_size_mb < 1 else min(300, 60 + int(file_size_mb * 30))
            
            result = subprocess.run(
                [self.freecad_path, "-c", script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                startupinfo=startupinfo,
                creationflags=creation_flags
            )
            
            exec_time = time.time() - exec_start
            print(f"\n[{time.time() - start_time:.2f}s] FreeCAD terminó en {exec_time:.2f}s")
            print(f"Código de retorno: {result.returncode}")
            
            # Parse output
            output_lines = result.stdout.split('\n')
            
            # Print FreeCAD output for debugging
            print("\n" + "="*60)
            print("SALIDA DE FREECAD:")
            print("="*60)
            for line in output_lines:
                if line.strip():
                    print(f"  {line}")
            
            if result.stderr.strip():
                print("\nERRORES/ADVERTENCIAS:")
                print("-"*60)
                for line in result.stderr.split('\n'):
                    if line.strip():
                        print(f"  {line}")
            print("="*60 + "\n")
            
            # Check for errors
            if result.returncode != 0:
                print(f"\n❌ ERROR: FreeCAD falló con código {result.returncode}")
                return {
                    'success': False,
                    'error': f"FreeCAD conversion failed (code {result.returncode}): {result.stderr}",
                    'output': result.stdout
                }
            
            # Load hierarchy data
            load_start = time.time()
            hierarchy_file = os.path.join(output_dir, "hierarchy.json")
            print(f"[{time.time() - start_time:.2f}s] Cargando datos de jerarquía...")
            
            if os.path.exists(hierarchy_file):
                with open(hierarchy_file, 'r') as f:
                    hierarchy_data = json.load(f)
                
                load_time = time.time() - load_start
                total_time = time.time() - start_time
                
                num_objects = len(hierarchy_data.get('objects', []))
                
                print(f"[{total_time:.2f}s] ✓ Jerarquía cargada en {load_time:.2f}s")
                print(f"\n{'='*60}")
                print(f"✓ CONVERSIÓN COMPLETA")
                print(f"Objetos procesados: {num_objects}")
                print(f"Tiempo total: {total_time:.2f}s")
                print(f"  - Generación script: {script_time:.2f}s")
                print(f"  - Ejecución FreeCAD: {exec_time:.2f}s")
                print(f"  - Carga jerarquía: {load_time:.2f}s")
                print(f"{'='*60}\n")
                
                return {
                    'success': True,
                    'hierarchy': hierarchy_data,
                    'output_dir': output_dir,
                    'output': result.stdout,
                    'timing': {
                        'total': total_time,
                        'script_gen': script_time,
                        'freecad_exec': exec_time,
                        'load_hierarchy': load_time
                    }
                }
            else:
                print(f"\n❌ ERROR: Archivo hierarchy.json no fue generado")
                print(f"Directorio de salida: {output_dir}")
                print(f"Archivos presentes: {os.listdir(output_dir)}")
                return {
                    'success': False,
                    'error': "Hierarchy file not generated",
                    'output': result.stdout
                }
        
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"\n❌ TIMEOUT después de {elapsed:.1f}s")
            return {
                'success': False,
                'error': f"FreeCAD conversion timed out after {elapsed:.1f}s",
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ ERROR después de {elapsed:.1f}s: {str(e)}")
            import traceback
            traceback.print_exc()
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
