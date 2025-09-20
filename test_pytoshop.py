#!/usr/bin/env python
"""
Test pytoshop imports and available classes
"""

import sys
print(f"Python version: {sys.version}")

try:
    import pytoshop
    print(f"pytoshop installed: version {pytoshop.__version__ if hasattr(pytoshop, '__version__') else 'unknown'}")
    
    # Check what's available in pytoshop.layers
    from pytoshop import layers
    print("\nAvailable in pytoshop.layers:")
    for item in dir(layers):
        if not item.startswith('_'):
            print(f"  - {item}")
    
    # Try different import methods
    print("\nTrying different imports:")
    
    try:
        from pytoshop.layers import PixelLayer
        print("  ✓ from pytoshop.layers import PixelLayer - SUCCESS")
    except ImportError as e:
        print(f"  ✗ from pytoshop.layers import PixelLayer - FAILED: {e}")
    
    try:
        from pytoshop.user.layers import PixelLayer
        print("  ✓ from pytoshop.user.layers import PixelLayer - SUCCESS")
    except ImportError as e:
        print(f"  ✗ from pytoshop.user.layers import PixelLayer - FAILED: {e}")
    
    try:
        import pytoshop.user.layers as layers
        print(f"  ✓ pytoshop.user.layers imported, has PixelLayer: {hasattr(layers, 'PixelLayer')}")
    except ImportError as e:
        print(f"  ✗ pytoshop.user.layers - FAILED: {e}")
    
    # Check core classes
    print("\nCore pytoshop structure:")
    try:
        from pytoshop.core import PsdFile
        print("  ✓ PsdFile available from pytoshop.core")
    except ImportError:
        print("  ✗ PsdFile not in pytoshop.core")
    
    try:
        from pytoshop import PsdFile
        print("  ✓ PsdFile available from pytoshop directly")
    except ImportError:
        print("  ✗ PsdFile not available from pytoshop directly")
        
except ImportError as e:
    print(f"pytoshop not installed: {e}")
    print("\nTo install pytoshop:")
    print("  pip install cython")
    print("  pip install pytoshop -I --no-cache-dir")

print("\n" + "="*60)
print("For onnxruntime issue, install:")
print("  pip install onnxruntime")
print("  # or for GPU support:")
print("  pip install onnxruntime-gpu")
