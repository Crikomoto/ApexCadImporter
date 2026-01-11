"""
Manual FreeCAD Detection Test
Run this in Blender to test FreeCAD detection
"""

import os
import subprocess

print("\n" + "="*60)
print("ApexCad: FreeCAD Detection Test")
print("="*60)

# Test 1: Check PATH
print("\n1. Checking PATH environment...")
if os.name == 'nt':
    for exec_name in ["FreeCADCmd.exe", "freecad.exe", "FreeCAD.exe"]:
        try:
            result = subprocess.run(
                ["where", exec_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"   ✓ Found {exec_name} in PATH: {result.stdout.strip()}")
            else:
                print(f"   ✗ {exec_name} not found in PATH")
        except Exception as e:
            print(f"   ✗ Error checking {exec_name}: {e}")
else:
    try:
        result = subprocess.run(
            ["which", "freecad"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"   ✓ Found in PATH: {result.stdout.strip()}")
        else:
            print("   ✗ Not found in PATH")
    except Exception as e:
        print(f"   ✗ Error checking PATH: {e}")

# Test 2: Check common locations
print("\n2. Checking common installation paths...")

if os.name == 'nt':
    paths_to_check = []
    for version in ["0.21", "0.22", "0.20", "1.0", ""]:
        base = rf"C:\Program Files\FreeCAD {version}\bin" if version else r"C:\Program Files\FreeCAD\bin"
        paths_to_check.append(os.path.join(base, "FreeCADCmd.exe"))
        paths_to_check.append(os.path.join(base, "freecad.exe"))
    paths_to_check.append(r"C:\Program Files (x86)\FreeCAD\bin\FreeCADCmd.exe")
    paths_to_check.append(r"C:\Program Files (x86)\FreeCAD\bin\freecad.exe")
else:
    paths_to_check = [
        "/usr/bin/freecad",
        "/usr/local/bin/freecad",
        "/opt/freecad/bin/freecad",
        "/Applications/FreeCAD.app/Contents/MacOS/FreeCAD",
    ]

found_paths = []
for path in paths_to_check:
    if os.path.exists(path):
        print(f"   ✓ Found: {path}")
        found_paths.append(path)
    else:
        print(f"   ✗ Not found: {path}")

# Test 3: Search Program Files (Windows)
if os.name == 'nt':
    print("\n3. Searching Program Files directories...")
    for base in [r"C:\Program Files", r"C:\Program Files (x86)"]:
        if os.path.exists(base):
            try:
                for item in os.listdir(base):
                    if 'freecad' in item.lower():
                        freecad_dir = os.path.join(base, item)
                        # Check for both executables
                        for exec_name in ["FreeCADCmd.exe", "freecad.exe"]:
                            bin_path = os.path.join(freecad_dir, 'bin', exec_name)
                            if os.path.exists(bin_path):
                                print(f"   ✓ Found: {bin_path}")
                                found_paths.append(bin_path)
            except (PermissionError, OSError) as e:
                print(f"   ✗ Error scanning {base}: {e}")

# Test 4: Try to run FreeCAD
print("\n4. Testing FreeCAD execution...")
if found_paths:
    test_path = found_paths[0]
    print(f"   Testing: {test_path}")
    try:
        result = subprocess.run(
            [test_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"   ✓ FreeCAD works! Version info:")
            print(f"     {result.stdout.strip()}")
        else:
            print(f"   ✗ FreeCAD returned error code: {result.returncode}")
            if result.stderr:
                print(f"     Error: {result.stderr}")
    except Exception as e:
        print(f"   ✗ Error running FreeCAD: {e}")
else:
    print("   ⚠ No FreeCAD installation found to test")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
if found_paths:
    print(f"✓ Found {len(found_paths)} FreeCAD installation(s):")
    for path in found_paths:
        print(f"  - {path}")
    print("\nRecommended action:")
    print(f"  Use: {found_paths[0]}")
else:
    print("✗ No FreeCAD installation detected")
    print("\nPlease install FreeCAD from: https://www.freecad.org")
    print("After installation, restart Blender and enable the addon.")

print("="*60 + "\n")
