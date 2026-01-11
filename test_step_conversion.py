"""
Script de diagnóstico para probar conversión STEP directamente
Ejecutar en CMD/PowerShell (NO en Blender):

    cd "C:\Program Files\FreeCAD 1.0\bin"
    .\FreeCADCmd.exe -c "D:\__DEVELOPMENT__\ApexCadImporter\test_step_conversion.py"

O desde este directorio:
    "C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" -c test_step_conversion.py

Modifica la ruta del archivo STEP abajo antes de ejecutar.
"""

import FreeCAD
import Import
import time
import os

# ========== CONFIGURACIÓN ==========
# CAMBIA ESTA RUTA A TU ARCHIVO STEP:
STEP_FILE = r"D:\TUS_ARCHIVOS\AMS-50-173-000.STEP"
# ===================================

print("="*70)
print("TEST DE CONVERSIÓN STEP - DIAGNÓSTICO")
print("="*70)
print(f"FreeCAD Version: {FreeCAD.Version()}")
print(f"Archivo: {STEP_FILE}")
print(f"Existe: {os.path.exists(STEP_FILE)}")
if os.path.exists(STEP_FILE):
    size_kb = os.path.getsize(STEP_FILE) / 1024
    print(f"Tamaño: {size_kb:.1f} KB")
print(f"Hora inicio: {time.strftime('%H:%M:%S')}")
print("="*70)

if not os.path.exists(STEP_FILE):
    print("\n❌ ERROR: Archivo no encontrado!")
    print("Modifica la variable STEP_FILE en este script")
    exit(1)

try:
    # Test 1: Crear documento
    print("\n[1/3] Creando documento...")
    t1 = time.time()
    doc = FreeCAD.newDocument("Test")
    print(f"  ✓ OK en {time.time()-t1:.2f}s")
    
    # Test 2: Importar STEP (ESTO ES LO QUE SUELE SER LENTO)
    print("\n[2/3] Importando archivo STEP...")
    print("  (Esto puede tomar varios minutos - se paciente)")
    t2 = time.time()
    Import.insert(STEP_FILE, "Test")
    import_time = time.time() - t2
    print(f"  ✓ OK en {import_time:.2f}s")
    
    # Test 3: Contar objetos
    print("\n[3/3] Analizando objetos...")
    t3 = time.time()
    num_objects = len(doc.Objects)
    print(f"  ✓ Encontrados {num_objects} objetos en {time.time()-t3:.2f}s")
    
    # Detalles de objetos
    print("\n" + "="*70)
    print("OBJETOS IMPORTADOS:")
    print("="*70)
    for i, obj in enumerate(doc.Objects[:10]):  # Primeros 10
        print(f"  {i+1}. {obj.Label} ({obj.TypeId})")
    if num_objects > 10:
        print(f"  ... y {num_objects - 10} más")
    
    total_time = time.time() - t1
    print("\n" + "="*70)
    print("RESUMEN:")
    print("="*70)
    print(f"Tiempo total: {total_time:.2f}s")
    print(f"  - Importación STEP: {import_time:.2f}s ({import_time/total_time*100:.1f}%)")
    print(f"Objetos: {num_objects}")
    print("="*70)
    
    if import_time > 30:
        print("\n⚠️  ADVERTENCIA: La importación tomó más de 30s")
        print("Posibles causas:")
        print("  - Archivo STEP muy complejo (muchas curvas/superficies)")
        print("  - FreeCAD 1.0 puede ser más lento que 0.20/0.21")
        print("  - Tu PC puede estar bajo carga")
    
    FreeCAD.closeDocument("Test")
    print("\n✓ Test completado exitosamente")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
