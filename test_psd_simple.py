"""
PSD保存の最小テストケース
"""

import numpy as np
from pytoshop.user import nested_layers
from pytoshop import enums

# 簡単なテスト画像を作成
width, height = 100, 100

# RGBチャンネルを作成
r_channel = np.ones((height, width), dtype=np.uint8) * 128
g_channel = np.ones((height, width), dtype=np.uint8) * 128
b_channel = np.ones((height, width), dtype=np.uint8) * 128

# レイヤーを作成
layer = nested_layers.Image(
    name="Test Layer",
    visible=True,
    opacity=255,
    group_id=0,
    blend_mode=enums.BlendMode.normal,
    top=0,
    left=0,
    channels=[r_channel, g_channel, b_channel],
    metadata=None,
    layer_color=0,
    color_mode=None
)

# PSDファイルとして保存
print("Creating PSD...")
try:
    output = nested_layers.nested_layers_to_psd([layer], color_mode=3)  # RGB mode
    with open("test.psd", 'wb') as f:
        output.write(f)
    print("PSD saved successfully!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
