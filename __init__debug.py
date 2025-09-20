"""
Debug version of __init__.py to identify loading issues
"""
import sys
import os
import traceback

print("=" * 60)
print("ComfyUI-fixableflow: Starting to load...")
print(f"Python version: {sys.version}")
print(f"Loading from: {os.path.dirname(__file__)}")
print("=" * 60)

# Initialize empty mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Try to import RGB Line Art Divider
try:
    print("Attempting to import rgb_line_art_divider...")
    from .rgb_line_art_divider import RGB_NODE_CLASS_MAPPINGS, RGB_NODE_DISPLAY_NAME_MAPPINGS
    NODE_CLASS_MAPPINGS.update(RGB_NODE_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(RGB_NODE_DISPLAY_NAME_MAPPINGS)
    print(f"✓ RGB Line Art Divider loaded: {list(RGB_NODE_CLASS_MAPPINGS.keys())}")
except Exception as e:
    print(f"✗ Failed to load RGB Line Art Divider:")
    print(f"  Error: {str(e)}")
    traceback.print_exc()

# Try to import Layer Divider Simplified
try:
    print("\nAttempting to import layer_divider_simplified...")
    from .layer_divider_simplified import NODE_CLASS_MAPPINGS as LEGACY_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as LEGACY_DISPLAY_MAPPINGS
    NODE_CLASS_MAPPINGS.update(LEGACY_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(LEGACY_DISPLAY_MAPPINGS)
    print(f"✓ Layer Divider Simplified loaded: {list(LEGACY_MAPPINGS.keys())}")
except Exception as e:
    print(f"✗ Failed to load Layer Divider Simplified:")
    print(f"  Error: {str(e)}")
    traceback.print_exc()

# Check required packages
print("\n" + "=" * 60)
print("Checking required packages...")
required_packages = [
    'cv2',
    'skimage',
    'sklearn',
    'pandas',
    'numpy',
    'pytoshop',
    'PIL'
]

for package in required_packages:
    try:
        __import__(package)
        print(f"✓ {package} is installed")
    except ImportError:
        print(f"✗ {package} is NOT installed")

# Final summary
print("\n" + "=" * 60)
print(f"Total nodes loaded: {len(NODE_CLASS_MAPPINGS)}")
if NODE_CLASS_MAPPINGS:
    print("Available nodes:")
    for name, display in NODE_DISPLAY_NAME_MAPPINGS.items():
        print(f"  - {name}: {display}")
else:
    print("⚠️ No nodes were loaded successfully!")

print("=" * 60)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
