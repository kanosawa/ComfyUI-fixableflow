#!/usr/bin/env python
"""
pytoshopパッケージの実際の構造を詳しく調査
"""

import sys
import os

try:
    import pytoshop
    print(f"pytoshop is installed at: {pytoshop.__file__}")
    print(f"pytoshop version: {pytoshop.__version__ if hasattr(pytoshop, '__version__') else 'unknown'}")
    print("\n" + "="*60)
    
    # pytoshopのディレクトリ構造を表示
    import pkgutil
    print("pytoshop package structure:")
    for importer, modname, ispkg in pkgutil.walk_packages(pytoshop.__path__, prefix="pytoshop."):
        print(f"  {'[PKG]' if ispkg else '[MOD]'} {modname}")
    
    print("\n" + "="*60)
    print("Checking specific imports:")
    
    # 各種インポートをテスト
    tests = [
        ("pytoshop.layers", "layers module"),
        ("pytoshop.user", "user module"),
        ("pytoshop.user.layers", "user.layers module"),
        ("pytoshop.core", "core module"),
        ("pytoshop.enums", "enums module"),
    ]
    
    for module_path, description in tests:
        try:
            module = __import__(module_path, fromlist=[''])
            print(f"\n✓ {description} ({module_path}):")
            attrs = [x for x in dir(module) if not x.startswith('_')]
            print(f"  Available: {', '.join(attrs[:10])}")
            if len(attrs) > 10:
                print(f"  ... and {len(attrs)-10} more")
        except ImportError as e:
            print(f"\n✗ {description} ({module_path}): {e}")
    
    print("\n" + "="*60)
    print("Searching for PixelLayer class:")
    
    # PixelLayerクラスを探す
    import inspect
    
    def find_class_in_module(module, class_name):
        """再帰的にモジュール内のクラスを探す"""
        found = []
        for name, obj in inspect.getmembers(module):
            if name == class_name and inspect.isclass(obj):
                found.append(f"{module.__name__}.{name}")
            elif inspect.ismodule(obj) and obj.__name__.startswith('pytoshop'):
                # サブモジュールも探索
                try:
                    subfound = find_class_in_module(obj, class_name)
                    found.extend(subfound)
                except:
                    pass
        return found
    
    locations = find_class_in_module(pytoshop, 'PixelLayer')
    if locations:
        print(f"Found PixelLayer in: {locations}")
    else:
        print("PixelLayer not found in standard locations")
    
    # 実際に動作するインポートを見つける
    print("\n" + "="*60)
    print("Testing actual imports:")
    
    # Layerクラスを探す（代替として使える可能性）
    layer_classes = []
    for name, obj in inspect.getmembers(pytoshop, inspect.isclass):
        if 'layer' in name.lower():
            layer_classes.append(name)
    
    if layer_classes:
        print(f"Found layer-related classes in pytoshop: {layer_classes}")
    
    # pytoshop.user.layersを詳しく見る
    try:
        from pytoshop import user
        print("\nExamining pytoshop.user:")
        user_attrs = [x for x in dir(user) if not x.startswith('_')]
        print(f"  Attributes: {user_attrs}")
        
        if hasattr(user, 'layers'):
            print("\n  user.layers exists!")
            layers_attrs = [x for x in dir(user.layers) if not x.startswith('_')]
            print(f"  user.layers attributes: {layers_attrs}")
            
            # Layerクラスの詳細を確認
            if hasattr(user.layers, 'Layer'):
                Layer = user.layers.Layer
                print(f"\n  Layer class found: {Layer}")
                print(f"  Layer methods: {[m for m in dir(Layer) if not m.startswith('_')][:10]}")
    except Exception as e:
        print(f"Error examining user module: {e}")
        
except ImportError as e:
    print(f"pytoshop is not installed: {e}")
    print("\nTo install pytoshop:")
    print("  pip install cython")
    print("  pip install pytoshop -I --no-cache-dir")
