"""
Script simple para probar la velocidad de FreeCAD
Ejecutar en Blender: Alt+Shift+P > Run Script
"""
import bpy
import subprocess
import time
import os
import tempfile

# Obtener el path de FreeCAD de las preferencias
prefs = bpy.context.preferences.addons.get('ApexCadImporter')
if not prefs:
    print("ERROR: Addon ApexCadImporter no está instalado")
else:
    freecad_path = prefs.preferences.freecad_path
    
    if not freecad_path or not os.path.exists(freecad_path):
        print(f"ERROR: FreeCAD no encontrado en: {freecad_path}")
    else:
        print(f"\n{'='*60}")
        print(f"TEST DE VELOCIDAD DE FREECAD")
        print(f"{'='*60}")
        print(f"Ejecutable: {freecad_path}")
        
        # Test 1: Version check
        print(f"\n1. Verificando versión...")
        start = time.time()
        result = subprocess.run(
            [freecad_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        elapsed = time.time() - start
        print(f"   Tiempo: {elapsed:.2f}s")
        print(f"   Versión: {result.stdout.strip()}")
        
        # Test 2: Script simple
        print(f"\n2. Ejecutando script simple...")
        script = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        script.write("""
import time
start = time.time()
print(f"FreeCAD iniciado en {time.time() - start:.2f}s")

# Simular trabajo
import FreeCAD
doc = FreeCAD.newDocument("Test")
elapsed = time.time() - start
print(f"Documento creado en {elapsed:.2f}s")
FreeCAD.closeDocument("Test")
print(f"Total: {time.time() - start:.2f}s")
""")
        script.close()
        
        start = time.time()
        
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creation_flags = subprocess.CREATE_NO_WINDOW
        else:
            startupinfo = None
            creation_flags = 0
        
        result = subprocess.run(
            [freecad_path, "-c", script.name],
            capture_output=True,
            text=True,
            timeout=30,
            startupinfo=startupinfo,
            creationflags=creation_flags
        )
        elapsed = time.time() - start
        
        print(f"   Tiempo total: {elapsed:.2f}s")
        print(f"   Salida de FreeCAD:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"     {line}")
        
        os.unlink(script.name)
        
        print(f"\n{'='*60}")
        print(f"Si cada test tomó >10s, FreeCAD está lento en tu sistema")
        print(f"{'='*60}\n")
