"""
Minimal test node to verify ComfyUI can load custom nodes
"""

class TestNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "Hello World"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "execute"
    CATEGORY = "ComfyUI-fixableflow/Test"
    
    def execute(self, text):
        return (f"Test successful: {text}",)

NODE_CLASS_MAPPINGS = {
    "TestNode": TestNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TestNode": "Test Node (fixableflow)"
}
