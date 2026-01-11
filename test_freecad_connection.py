"""
Quick FreeCAD Connection Test
Run this in Blender to test if FreeCAD is responding
"""

import bpy
import subprocess
import os
import tempfile

def test_freecad_connection():
    """Test if FreeCAD is working properly"""
    
    print("\n" + "="*60)
    print("ApexCad: FreeCAD Connection Test")
    print("="*60)
    
    # Get addon preferences
    try:
        prefs = bpy.context.preferences.addons['ApexCadImporter'].preferences
        freecad_path = prefs.freecad_path
    except:
        print("✗ ApexCad addon not found or not enabled")
        return False
    
    if not freecad_path:
        print("✗ FreeCAD path not configured")
        print("  → Go to Edit → Preferences → Add-ons → ApexCad")
        return False
    
    print(f"✓ FreeCAD path configured: {freecad_path}")
    
    # Check if file exists
    if not os.path.exists(freecad_path):
        print(f"✗ FreeCAD executable not found at: {freecad_path}")
        return False
    
    print(f"✓ FreeCAD executable exists")
    
    # Test 1: Version check
    print("\nTest 1: Version Check")
    try:
        result = subprocess.run(
            [freecad_path, "--version"],
            capture_output=True,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            print(f"✓ FreeCAD responds to --version")
            print(f"  Version: {result.stdout.strip()[:100]}")
        else:
            print(f"✗ FreeCAD failed (code {result.returncode})")
            print(f"  Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ FreeCAD timed out (>15s)")
        return False
    except Exception as e:
        print(f"✗ Error running FreeCAD: {e}")
        return False
    
    # Test 2: Simple Python script execution
    print("\nTest 2: Script Execution")
    
    # Create a simple test script
    test_script = """
import sys
print("ApexCad Test: FreeCAD Python is working")
print(f"Python version: {sys.version}")
print("Test completed successfully")
"""
    
    temp_dir = tempfile.mkdtemp(prefix="apexcad_test_")
    script_path = os.path.join(temp_dir, "test_script.py")
    
    try:
        with open(script_path, 'w') as f:
            f.write(test_script)
        
        print(f"  Running test script...")
        
        # Platform-specific flags
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creation_flags = subprocess.CREATE_NO_WINDOW
        else:
            startupinfo = None
            creation_flags = 0
        
        result = subprocess.run(
            [freecad_path, "-c", script_path],
            capture_output=True,
            text=True,
            timeout=20,
            startupinfo=startupinfo,
            creationflags=creation_flags
        )
        
        if result.returncode == 0:
            print("✓ FreeCAD executed script successfully")
            print("\n  Output:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"    {line}")
        else:
            print(f"✗ Script execution failed (code {result.returncode})")
            print(f"  STDOUT: {result.stdout}")
            print(f"  STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Script execution timed out (>20s)")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        # Cleanup
        try:
            os.remove(script_path)
            os.rmdir(temp_dir)
        except:
            pass
    
    # All tests passed
    print("\n" + "="*60)
    print("✓✓✓ ALL TESTS PASSED ✓✓✓")
    print("="*60)
    print("\nFreeCAD is working correctly!")
    print("You can now try importing CAD files.")
    print("="*60 + "\n")
    
    return True

# Run the test
if __name__ == "__main__":
    test_freecad_connection()
else:
    # When imported, also run
    test_freecad_connection()
