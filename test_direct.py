import FreeCAD
import Import
import Mesh
import os
import json
import time

# Configuration - CAMBIA ESTA RUTA
input_file = r"D:\TUS_ARCHIVOS\AMS-50-173-000.STEP"
output_dir = r"C:\Temp\test_output"
scale_factor = 0.001
y_up = True
tessellation_quality = 0.1

os.makedirs(output_dir, exist_ok=True)

print("=" * 60)
print("FREECAD CONVERSION SCRIPT - TEST DIRECTO")
print("=" * 60)
print("Archivo: " + input_file)
print("Iniciando a las " + time.strftime("%H:%M:%S"))
print("=" * 60)

# Import the CAD file
try:
    print("\n[PASO 1/4] Creando documento FreeCAD...")
    t_start = time.time()
    doc = FreeCAD.newDocument("ApexCadImport")
    print("  OK - Documento creado en {:.2f}s".format(time.time()-t_start))
    
    # Import STEP or IGES
    print("\n[PASO 2/4] Importando archivo CAD...")
    print("  Esto puede tomar varios minutos...")
    file_ext = os.path.splitext(input_file)[1].lower()
    t_import = time.time()
    
    if file_ext in [".stp", ".step"]:
        Import.insert(input_file, "ApexCadImport")
    elif file_ext in [".igs", ".iges"]:
        Import.insert(input_file, "ApexCadImport")
    else:
        raise ValueError("Unsupported file format: " + file_ext)
    
    import_time = time.time() - t_import
    print("  OK - Archivo importado in {:.2f}s".format(import_time))
    print("  Objetos cargados: {}".format(len(doc.Objects)))
    
    print("\n[PASO 3/4] Listando objetos...")
    for i, obj in enumerate(doc.Objects[:5]):
        print("  {}: {} ({})".format(i+1, obj.Label, obj.TypeId))
    if len(doc.Objects) > 5:
        print("  ... y {} mas".format(len(doc.Objects) - 5))
    
    print("\n[PASO 4/4] Cerrando...")
    FreeCAD.closeDocument("ApexCadImport")
    
    total_time = time.time() - t_start
    print("\n" + "=" * 60)
    print("TEST EXITOSO")
    print("Tiempo total: {:.2f}s".format(total_time))
    print("  - Importacion: {:.2f}s".format(import_time))
    print("Objetos: {}".format(len(doc.Objects)))
    print("=" * 60)
    
except Exception as e:
    print("ERROR: " + str(e))
    import traceback
    traceback.print_exc()
    exit(1)
