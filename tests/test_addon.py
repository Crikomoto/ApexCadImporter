"""
Manual Test Script for ApexCad Importer
Run this script inside Blender's Scripting workspace to test the addon

Instructions:
1. Install ApexCad Importer addon
2. Configure FreeCAD path in preferences
3. Open Blender Scripting workspace
4. Load this script
5. Replace TEST_FILE path with your STEP/IGES file
6. Run script
"""

import bpy
import os

# ==========================================
# CONFIGURATION - EDIT THESE VALUES
# ==========================================

# Path to a test STEP or IGES file
TEST_FILE = "D:/path/to/your/test_file.stp"  # <-- CHANGE THIS

# Test parameters
TEST_SCALE = 0.001  # mm to m
TEST_HIERARCHY = 'COLLECTION'  # or 'EMPTY'
TEST_Y_UP = True
TEST_QUALITY = 0.1

# ==========================================
# TEST FUNCTIONS
# ==========================================

def test_preferences():
    """Test 1: Check if addon preferences are accessible"""
    print("\n" + "="*50)
    print("TEST 1: Addon Preferences")
    print("="*50)
    
    try:
        prefs = bpy.context.preferences.addons['ApexCadImporter'].preferences
        print(f"✓ Preferences accessible")
        print(f"  FreeCAD Path: {prefs.freecad_path}")
        print(f"  Default Scale: {prefs.default_scale}")
        print(f"  Max Chunk Size: {prefs.max_chunk_size}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_freecad_detection():
    """Test 2: Detect FreeCAD installation"""
    print("\n" + "="*50)
    print("TEST 2: FreeCAD Detection")
    print("="*50)
    
    try:
        bpy.ops.apexcad.detect_freecad()
        prefs = bpy.context.preferences.addons['ApexCadImporter'].preferences
        
        if prefs.freecad_path and os.path.exists(prefs.freecad_path):
            print(f"✓ FreeCAD detected: {prefs.freecad_path}")
            return True
        else:
            print(f"✗ FreeCAD not found")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_bridge_validation():
    """Test 3: Validate FreeCAD bridge"""
    print("\n" + "="*50)
    print("TEST 3: FreeCAD Bridge Validation")
    print("="*50)
    
    try:
        from ApexCadImporter import freecad_bridge
        
        bridge, error = freecad_bridge.get_bridge(bpy.context)
        
        if bridge:
            is_valid, message = bridge.validate_freecad()
            if is_valid:
                print(f"✓ FreeCAD bridge valid")
                print(f"  Version info: {message}")
                return True
            else:
                print(f"✗ Validation failed: {message}")
                return False
        else:
            print(f"✗ Bridge creation failed: {error}")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_import_operator():
    """Test 4: Test import operator (without actual import)"""
    print("\n" + "="*50)
    print("TEST 4: Import Operator")
    print("="*50)
    
    try:
        # Check if operator exists
        if hasattr(bpy.ops.import_scene, 'apexcad'):
            print("✓ Import operator registered")
            print(f"  Operator ID: import_scene.apexcad")
            return True
        else:
            print("✗ Import operator not found")
            return False
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_actual_import():
    """Test 5: Actual file import (requires valid STEP/IGES file)"""
    print("\n" + "="*50)
    print("TEST 5: Actual Import")
    print("="*50)
    
    if not os.path.exists(TEST_FILE):
        print(f"✗ Test file not found: {TEST_FILE}")
        print(f"  Please edit TEST_FILE path at top of script")
        return False
    
    print(f"Importing: {TEST_FILE}")
    print(f"Settings: scale={TEST_SCALE}, hierarchy={TEST_HIERARCHY}, y_up={TEST_Y_UP}, quality={TEST_QUALITY}")
    
    try:
        # Clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        # Import using the addon
        from ApexCadImporter import importer
        
        success, message, objects = importer.import_cad_file(
            bpy.context,
            TEST_FILE,
            scale=TEST_SCALE,
            hierarchy_mode=TEST_HIERARCHY,
            y_up=TEST_Y_UP,
            chunk_size=50,
            tessellation_quality=TEST_QUALITY
        )
        
        if success:
            print(f"✓ Import successful!")
            print(f"  Message: {message}")
            print(f"  Objects imported: {len(objects)}")
            
            # List imported objects
            for i, obj in enumerate(objects[:10]):  # Show first 10
                print(f"    {i+1}. {obj.name} ({obj.type})")
            
            if len(objects) > 10:
                print(f"    ... and {len(objects)-10} more")
            
            return True
        else:
            print(f"✗ Import failed: {message}")
            return False
            
    except Exception as e:
        print(f"✗ Failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata():
    """Test 6: Check metadata on imported objects"""
    print("\n" + "="*50)
    print("TEST 6: Metadata Preservation")
    print("="*50)
    
    try:
        # Get first object in scene
        if not bpy.context.scene.objects:
            print("✗ No objects in scene")
            return False
        
        obj = bpy.context.scene.objects[0]
        
        # Check for CAD metadata
        cad_props = {}
        for key in obj.keys():
            if key.startswith('cad_') or key.startswith('apexcad_'):
                cad_props[key] = obj[key]
        
        if cad_props:
            print(f"✓ Metadata found on {obj.name}")
            print(f"  Properties found: {len(cad_props)}")
            for key, value in list(cad_props.items())[:5]:
                print(f"    {key}: {value}")
            if len(cad_props) > 5:
                print(f"    ... and {len(cad_props)-5} more")
            return True
        else:
            print(f"⚠ No CAD metadata found")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_ui_panels():
    """Test 7: Check if UI panels are registered"""
    print("\n" + "="*50)
    print("TEST 7: UI Panels")
    print("="*50)
    
    try:
        panels_found = 0
        
        # Check for main panel
        if hasattr(bpy.types, 'APEXCAD_PT_main_panel'):
            print("✓ Main panel registered")
            panels_found += 1
        
        # Check for properties panel
        if hasattr(bpy.types, 'APEXCAD_PT_object_properties'):
            print("✓ Object properties panel registered")
            panels_found += 1
        
        if panels_found > 0:
            print(f"✓ Found {panels_found} UI panels")
            return True
        else:
            print("✗ No UI panels found")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


# ==========================================
# RUN ALL TESTS
# ==========================================

def run_all_tests():
    """Run all tests in sequence"""
    print("\n" + "="*70)
    print("APEXCAD IMPORTER - MANUAL TEST SUITE")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Preferences", test_preferences()))
    results.append(("FreeCAD Detection", test_freecad_detection()))
    results.append(("Bridge Validation", test_bridge_validation()))
    results.append(("Import Operator", test_import_operator()))
    results.append(("UI Panels", test_ui_panels()))
    
    # Only run import test if file exists
    if os.path.exists(TEST_FILE):
        results.append(("Actual Import", test_actual_import()))
        results.append(("Metadata Check", test_metadata()))
    else:
        print("\n⚠ Skipping import tests - TEST_FILE not found")
        print(f"  Edit TEST_FILE variable and set path to a valid STEP/IGES file")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} | {name}")
    
    print("="*70)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All tests passed! Addon is working correctly.")
    else:
        print(f"\n⚠ {total-passed} test(s) failed. Check output above for details.")
    
    return passed == total


# ==========================================
# EXECUTE
# ==========================================

if __name__ == "__main__":
    run_all_tests()
