"""
Minimal init file to test basic loading
"""
print("[ComfyUI-fixableflow] Loading test configuration...")

try:
    from .test_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    print(f"[ComfyUI-fixableflow] Successfully loaded test node")
except Exception as e:
    print(f"[ComfyUI-fixableflow] Failed to load test node: {e}")
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
