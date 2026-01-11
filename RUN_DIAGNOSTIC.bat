@echo off
echo ================================================================
echo DIAGNOSTIC: Test STEP conversion with FreeCAD
echo ================================================================
echo.
echo IMPORTANTE: Edita test_step_conversion.py y cambia la ruta STEP_FILE
echo            a tu archivo AMS-50-173-000.STEP antes de continuar
echo.
pause
echo.
echo Ejecutando FreeCAD...
echo.

"C:\Program Files\FreeCAD 1.0\bin\FreeCADCmd.exe" -c test_step_conversion.py

echo.
echo ================================================================
echo Test completado
echo ================================================================
pause
