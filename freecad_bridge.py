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
        # Build script content using string concatenation to avoid f-string nesting issues
        script_lines = [
            'import FreeCAD',
            'import Import',
            'import Mesh',
            'import os',
            'import json',
            'import time',
            '',
            '# Configuration',
            f'input_file = r"{input_file}"',
            f'output_dir = r"{output_dir}"',
            f'scale_factor = {options.get("scale", 1.0)}',
            f'y_up = {options.get("y_up", True)}',
            f'tessellation_quality = {options.get("tessellation_quality", 0.1)}',
            '',
            'print("=" * 60)',
            'print("FREECAD CONVERSION SCRIPT")',
            'print("=" * 60)',
            'print("Archivo: " + input_file)',
            'print("Iniciando a las " + time.strftime("%H:%M:%S"))',
            'print("=" * 60)',
            '',
            '# Import the CAD file',
            'try:',
            '    print("\\n[PASO 1/4] Creando documento FreeCAD...")',
            '    t_start = time.time()',
            '    doc = FreeCAD.newDocument("ApexCadImport")',
            '    print("  OK - Documento creado en {:.2f}s".format(time.time()-t_start))',
            '    ',
            '    # Import STEP or IGES',
            '    print("\\n[PASO 2/4] Importando archivo CAD...")',
            '    print("  Esto puede tomar varios minutos...")',
            '    file_ext = os.path.splitext(input_file)[1].lower()',
            '    t_import = time.time()',
            '    ',
            '    if file_ext in [".stp", ".step"]:',
            '        Import.insert(input_file, "ApexCadImport")',
            '    elif file_ext in [".igs", ".iges"]:',
            '        Import.insert(input_file, "ApexCadImport")',
            '    else:',
            '        raise ValueError("Unsupported file format: " + file_ext)',
            '    ',
            '    import_time = time.time() - t_import',
            '    print("  OK - Archivo importado in {:.2f}s".format(import_time))',
            '    print("  Objetos cargados: {}".format(len(doc.Objects)))',
            '    ',
            '    # Process objects',
            '    print("\\n[PASO 3/4] Procesando {} objetos...".format(len(doc.Objects)))',
            '    t_process = time.time()',
            '    ',
            '    hierarchy_data = {',
            '        "objects": [],',
            '        "root_objects": [],',
            '        "scale": scale_factor,',
            '        "y_up": y_up',
            '    }',
            '    ',
            '    object_map = {}',
            '    ',
            '    # Datum objects to skip (reference planes, axes, origins)',
            '    datum_types = ["App::Origin", "App::Plane", "App::Line", "PartDesign::Plane", "PartDesign::Line", "PartDesign::Point"]',
            '    datum_names = ["Origin", "X-axis", "Y-axis", "Z-axis", "XY-plane", "XZ-plane", "YZ-plane"]',
            '    ',
            '    for idx, obj in enumerate(doc.Objects):',
            '        # Skip datum/reference objects completely',
            '        if obj.TypeId in datum_types:',
            '            continue',
            '        if obj.Label in datum_names or obj.Label.endswith(("001", "002", "003")) and any(obj.Label.startswith(d.replace("-", "")) for d in datum_names):',
            '            # Skip Origin001, X-axis002, etc.',
            '            continue',
            '        ',
            '        if idx % 10 == 0 and idx > 0:',
            '            print("  Procesando objeto {}/{}...".format(idx, len(doc.Objects)))',
            '        ',
            '        obj_data = {',
            '            "name": obj.Label,',
            '            "internal_name": obj.Name,',
            '            "type": obj.TypeId,',
            '            "index": idx,',
            '            "metadata": {},',
            '            "parent": None,',
            '            "children": []',
            '        }',
            '        ',
            '        # Extract metadata',
            '        if hasattr(obj, "Shape"):',
            '            shape = obj.Shape',
            '            obj_data["metadata"]["volume"] = shape.Volume if hasattr(shape, "Volume") else 0',
            '            obj_data["metadata"]["area"] = shape.Area if hasattr(shape, "Area") else 0',
            '            ',
            '            try:',
            '                bbox = shape.BoundBox',
            '                obj_data["metadata"]["bbox"] = {',
            '                    "min": [bbox.XMin, bbox.YMin, bbox.ZMin],',
            '                    "max": [bbox.XMax, bbox.YMax, bbox.ZMax]',
            '                }',
            '            except:',
            '                pass',
            '        ',
            '        # Extract color/material information',
            '        if hasattr(obj, "ViewObject") and obj.ViewObject:',
            '            vobj = obj.ViewObject',
            '            ',
            '            # Try to get shape color (STEP files often have colors)',
            '            if hasattr(vobj, "ShapeColor"):',
            '                color = vobj.ShapeColor',
            '                # FreeCAD colors are tuples (r, g, b) in 0-1 range',
            '                obj_data["metadata"]["color"] = [color[0], color[1], color[2], 1.0]',
            '            ',
            '            # Try to get diffuse color',
            '            elif hasattr(vobj, "DiffuseColor") and vobj.DiffuseColor:',
            '                # DiffuseColor is per-face, take first color',
            '                color = vobj.DiffuseColor[0] if vobj.DiffuseColor else None',
            '                if color:',
            '                    obj_data["metadata"]["color"] = [color[0], color[1], color[2], color[3]]',
            '        ',
            '        # Extract standard CAD properties',
            '        if hasattr(obj, "Description"):',
            '            obj_data["metadata"]["description"] = obj.Description',
            '        if hasattr(obj, "Material") and isinstance(obj.Material, str):',
            '            obj_data["metadata"]["material_name"] = obj.Material',
            '        ',
            '        # Get position',
            '        if hasattr(obj, "Placement"):',
            '            placement = obj.Placement',
            '            pos = placement.Base',
            '            rot = placement.Rotation',
            '            obj_data["transform"] = {',
            '                "position": [pos.x, pos.y, pos.z],',  # NO aplicar scale aquí
            '                "rotation": [rot.Q[0], rot.Q[1], rot.Q[2], rot.Q[3]]',
            '            }',
            '        ',
            '        # Get parent relationship',
            '        # First try using Parents property',
            '        if hasattr(obj, "Parents") and obj.Parents:',
            '            parent = obj.Parents[0][0]',
            '            obj_data["parent"] = parent.Name',
            '        ',
            '        # Determine if this is a leaf object (actual geometry) or container',
            '        is_leaf = True',
            '        if hasattr(obj, "Group") and obj.Group:',
            '            is_leaf = False',
            '        obj_data["is_leaf"] = is_leaf',
            '        ',
            '        # Export mesh ONLY for leaf objects with actual geometry',
            '        if hasattr(obj, "Shape") and obj.Shape.Faces and is_leaf:',
            '            mesh_file = os.path.join(output_dir, obj.Name + ".obj")',
            '            try:',
            '                obj.Shape.tessellate(tessellation_quality)',
            '                ',
            '                # Export individual object using MeshPart for better separation',
            '                import MeshPart',
            '                mesh = MeshPart.meshFromShape(obj.Shape, LinearDeflection=tessellation_quality, AngularDeflection=0.5, Relative=False)',
            '                mesh.write(mesh_file, "OBJ", obj.Name)',
            '                ',
            '                obj_data["mesh_file"] = mesh_file',
            '                print("  Exported: {} (leaf object)".format(obj.Label))',
            '            except Exception as e:',
            '                print("  Warning - Failed to export {}: {}".format(obj.Label, str(e)))',
            '                obj_data["mesh_file"] = None',
            '        else:',
            '            obj_data["mesh_file"] = None',
            '            if not is_leaf:',
            '                print("  Container: {}".format(obj.Label))',
            '        ',
            '        hierarchy_data["objects"].append(obj_data)',
            '        object_map[obj.Name] = obj_data',
            '    ',
            '    # Build hierarchy from Group property (used by App::Part)',
            '    for obj in doc.Objects:',
            '        if hasattr(obj, "Group") and obj.Group:',
            '            for child in obj.Group:',
            '                if child.Name in object_map:',
            '                    child_data = object_map[child.Name]',
            '                    if not child_data.get("parent"):',
            '                        child_data["parent"] = obj.Name',
            '    ',
            '    # Build children lists',
            '    for obj_data in hierarchy_data["objects"]:',
            '        if obj_data["parent"]:',
            '            parent_data = object_map.get(obj_data["parent"])',
            '            if parent_data:',
            '                parent_data["children"].append(obj_data["internal_name"])',
            '        else:',
            '            hierarchy_data["root_objects"].append(obj_data["internal_name"])',
            '    ',
            '    process_time = time.time() - t_process',
            '    print("  OK - Procesamiento completado in {:.2f}s".format(process_time))',
            '    ',
            '    # Save hierarchy data',
            '    print("\\n[PASO 4/4] Guardando datos...")',
            '    t_save = time.time()',
            '    hierarchy_file = os.path.join(output_dir, "hierarchy.json")',
            '    with open(hierarchy_file, "w") as f:',
            '        json.dump(hierarchy_data, f, indent=2)',
            '    save_time = time.time() - t_save',
            '    print("  OK - Guardado en {:.2f}s".format(save_time))',
            '    ',
            '    total_time = time.time() - t_start',
            '    print("\\n" + "=" * 60)',
            '    print("CONVERSION EXITOSA")',
            '    print("Tiempo total: {:.2f}s".format(total_time))',
            '    print("  - Importacion STEP: {:.2f}s".format(import_time))',
            '    print("  - Procesamiento: {:.2f}s".format(process_time))',
            '    print("  - Guardado: {:.2f}s".format(save_time))',
            '    print("Objetos procesados: {}".format(len(hierarchy_data["objects"])))',
            '    print("=" * 60)',
            '    ',
            '    FreeCAD.closeDocument("ApexCadImport")',
            '    ',
            'except Exception as e:',
            '    print("ERROR: " + str(e))',
            '    import traceback',
            '    traceback.print_exc()',
            '    exit(1)',
        ]
        
        script_content = '\n'.join(script_lines)
        
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
            
            # Dynamic timeout based on file size (generoso para diagnóstico)
            timeout = 180 if file_size_mb < 1 else min(600, 180 + int(file_size_mb * 60))
            
            print(f"\n[{time.time() - start_time:.2f}s] Ejecutando FreeCAD...")
            print(f"Comando: {self.freecad_path} -c {script_path}")
            print(f"Timeout: {timeout}s\n")
            print("="*60)
            print("SALIDA DE FREECAD EN VIVO:")
            print("="*60)
            
            # Platform-specific flags to prevent window creation
            if os.name == 'nt':  # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                creation_flags = 0  # Sin CREATE_NO_WINDOW para diagnóstico
            else:  # Linux/Mac
                startupinfo = None
                creation_flags = 0
            
            # Sin capture_output para ver salida en tiempo real
            result = subprocess.run(
                [self.freecad_path, "-c", script_path],
                stdin=subprocess.DEVNULL,
                timeout=timeout,
                startupinfo=startupinfo,
                creationflags=creation_flags
            )
            
            exec_time = time.time() - exec_start
            print("="*60)
            print(f"\n[{time.time() - start_time:.2f}s] FreeCAD terminó en {exec_time:.2f}s")
            print(f"Código de retorno: {result.returncode}")
            
            # Check for errors
            if result.returncode != 0:
                print(f"\n❌ ERROR: FreeCAD falló con código {result.returncode}")
                return {
                    'success': False,
                    'error': f"FreeCAD conversion failed (code {result.returncode})",
                    'output': ''
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
                    'output': '',
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
                    'output': ''
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
