@echo off
echo ================================================================
echo TEST DIRECTO DE FREECAD (sin Blender)
echo ================================================================
echo.
echo IMPORTANTE: 
echo 1. Abre test_direct.py
echo 2. Cambia la linea 9: input_file = r"D:\RUTA\A\TU\AMS-50-173-000.STEP"
echo 3. Guarda el archivo
echo.
pause
echo.
echo Ejecutando FreeCAD directamente...
echo.

"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" -c test_direct.py

echo.
echo ================================================================
echo Test completado - revisa el output arriba
echo ================================================================
pause
