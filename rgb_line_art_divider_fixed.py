"""
RGB Line Art Layer Divider - FIXED VERSION
線画と下塗り画像を入力として、RGB値ごとに領域分割してPSDを生成するノード
pytoshopの正しいインポート方法を使用
"""

from PIL import Image
import numpy as np
import torch
import os
import folder_paths
from .ldivider.ld_convertor import pil2cv
from pytoshop.enums import BlendMode
import cv2
from collections import defaultdict
import pytoshop
from pytoshop.core import PsdFile

# 正しいインポート方法：pytoshop.user.nested_layersを使用
from pytoshop.user import nested_layers
from pytoshop import enums

# パス設定
comfy_path = os.path.dirname(folder_paths.__file__)
layer_divider_path = f'{comfy_path}/custom_nodes/ComfyUI-LayerDivider'
output_dir = f"{layer_divider_path}/output"

if not os.path.exists(f'{output_dir}'):
    os.makedirs(f'{output_dir}')


def HWC3(x):
    """画像形式の変換ヘルパー関数"""
    assert x.dtype == np.uint8
    if x.ndim == 2:
        x = x[:, :, None]
    assert x.ndim == 3
    H, W, C = x.shape
    assert C == 1 or C == 3 or C == 4
    if C == 3:
        return x
    if C == 1:
        return np.concatenate([x, x, x], axis=2)
    if C == 4:
        color = x[:, :, 0:3].astype(np.float32)
        alpha = x[:, :, 3:4].astype(np.float32) / 255.0
        y = color * alpha + 255.0 * (1.0 - alpha)
        y = y.clip(0, 255).astype(np.uint8)
        return y


def to_comfy_img(np_img):
    """NumPy配列をComfyUI形式の画像に変換"""
    out_imgs = []
    out_imgs.append(HWC3(np_img))
    out_imgs = np.stack(out_imgs)
    out_imgs = torch.from_numpy(out_imgs.astype(np.float32) / 255.)
    return out_imgs


def to_comfy_imgs(np_imgs):
    """複数のNumPy配列をComfyUI形式の画像バッチに変換"""
    out_imgs = []
    for np_img in np_imgs:
        out_imgs.append(HWC3(np_img))
    out_imgs = np.stack(out_imgs)
    out_imgs = torch.from_numpy(out_imgs.astype(np.float32) / 255.)
    return out_imgs


def extract_color_regions(base_image_cv, tolerance=10):
    """
    下塗り画像からRGB値ごとに領域を抽出
    
    Args:
        base_image_cv: 下塗り画像（BGRA形式）
        tolerance: 同じ色と判定する許容値
    
    Returns:
        color_regions: {(R,G,B): mask} の辞書
    """
    # BGRAからBGRに変換（アルファチャンネルを考慮）
    if base_image_cv.shape[2] == 4:
        bgr_image = base_image_cv[:, :, :3]
        alpha = base_image_cv[:, :, 3]
    else:
        bgr_image = base_image_cv
        alpha = np.ones((base_image_cv.shape[0], base_image_cv.shape[1]), dtype=np.uint8) * 255
    
    # RGBに変換（OpenCVはBGRなので）
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    
    # ユニークな色を取得
    height, width = rgb_image.shape[:2]
    pixels = rgb_image.reshape(-1, 3)
    alpha_flat = alpha.reshape(-1)
    
    # アルファ値が0でないピクセルのみを対象とする
    valid_pixels = pixels[alpha_flat > 0]
    
    # 色をグループ化（tolerance考慮）
    color_regions = defaultdict(list)
    processed = set()
    
    for i, pixel in enumerate(valid_pixels):
        if i in processed:
            continue
            
        # tolerance範囲内の色を同じグループとして扱う
        color_key = tuple(pixel)
        similar_indices = []
        
        for j, other_pixel in enumerate(valid_pixels):
            if j not in processed:
                diff = np.abs(pixel.astype(int) - other_pixel.astype(int))
                if np.all(diff <= tolerance):
                    similar_indices.append(j)
                    processed.add(j)
        
        if similar_indices:
            # 平均色を計算してキーとする
            similar_colors = valid_pixels[similar_indices]
            avg_color = np.mean(similar_colors, axis=0).astype(int)
            color_key = tuple(avg_color)
            
            # マスクを作成
            mask = np.zeros((height, width), dtype=np.uint8)
            for idx in similar_indices:
                # 元のインデックスを復元
                original_idx = np.where(alpha_flat > 0)[0][idx]
                y = original_idx // width
                x = original_idx % width
                mask[y, x] = 255
            
            color_regions[color_key] = mask
    
    # 実際の領域マスクを作成
    final_regions = {}
    for color, indices in color_regions.items():
        if isinstance(indices, np.ndarray):
            final_regions[color] = indices
        else:
            # インデックスからマスクを作成
            mask = np.zeros((height, width), dtype=np.uint8)
            for idx in indices:
                mask.flat[idx] = 255
            final_regions[color] = mask
    
    return final_regions


def create_region_layers(base_image_cv, color_regions):
    """
    色領域ごとにレイヤーを作成
    
    Args:
        base_image_cv: 元画像（BGRA形式）
        color_regions: {(R,G,B): mask} の辞書
    
    Returns:
        layers: レイヤーリスト
        names: レイヤー名リスト
    """
    layers = []
    names = []
    
    for color, mask in color_regions.items():
        # マスクを適用してレイヤーを作成
        layer = np.zeros_like(base_image_cv)
        
        # マスクがある部分だけ色を適用
        mask_3d = np.stack([mask] * 4, axis=2)
        layer[mask_3d > 0] = base_image_cv[mask_3d > 0]
        
        layers.append(layer)
        # レイヤー名をRGB値で作成
        names.append(f"Color_R{color[0]}_G{color[1]}_B{color[2]}")
    
    return layers, names


def save_psd_with_nested_layers(base_image_cv, line_art_cv, color_layers, layer_names, 
                                output_dir, blend_mode=BlendMode.multiply, filename_prefix="rgb_divided"):
    """
    nested_layersを使用してPSDファイルを保存
    
    Args:
        base_image_cv: ベース画像（BGRA形式）
        line_art_cv: 線画（BGRA形式）
        color_layers: 色領域レイヤーのリスト
        layer_names: レイヤー名のリスト
        output_dir: 出力ディレクトリ
        blend_mode: 線画のブレンドモード
        filename_prefix: ファイル名プレフィックス
    
    Returns:
        filename: 保存したファイル名
    """
    from datetime import datetime
    
    # ファイル名生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.psd")
    
    height, width = base_image_cv.shape[:2]
    layers_list = []
    
    # 背景レイヤーを追加
    bg_arr = base_image_cv[:, :, [2, 1, 0]]  # BGRからRGBに変換
    if base_image_cv.shape[2] == 4:
        channels = [bg_arr[:, :, 0], bg_arr[:, :, 1], bg_arr[:, :, 2], base_image_cv[:, :, 3]]
    else:
        channels = [bg_arr[:, :, 0], bg_arr[:, :, 1], bg_arr[:, :, 2]]
    
    bg_layer = nested_layers.Image(
        name="Background",
        visible=True,
        opacity=255,
        group_id=0,
        blend_mode=enums.BlendMode.normal,
        top=0,
        left=0,
        channels=channels,
        metadata=None,
        layer_color=0,
        color_mode=None
    )
    layers_list.append(bg_layer)
    
    # 色領域レイヤーを追加
    for layer_data, name in zip(color_layers, layer_names):
        rgb_data = layer_data[:, :, [2, 1, 0]]  # BGRからRGBに変換
        if layer_data.shape[2] == 4:
            channels = [rgb_data[:, :, 0], rgb_data[:, :, 1], rgb_data[:, :, 2], layer_data[:, :, 3]]
        else:
            channels = [rgb_data[:, :, 0], rgb_data[:, :, 1], rgb_data[:, :, 2]]
        
        layer = nested_layers.Image(
            name=name,
            visible=True,
            opacity=255,
            group_id=0,
            blend_mode=enums.BlendMode.normal,
            top=0,
            left=0,
            channels=channels,
            metadata=None,
            layer_color=0,
            color_mode=None
        )
        layers_list.append(layer)
    
    # 線画レイヤーを最上位に追加
    line_rgb = line_art_cv[:, :, [2, 1, 0]]  # BGRからRGBに変換
    if line_art_cv.shape[2] == 4:
        channels = [line_rgb[:, :, 0], line_rgb[:, :, 1], line_rgb[:, :, 2], line_art_cv[:, :, 3]]
    else:
        channels = [line_rgb[:, :, 0], line_rgb[:, :, 1], line_rgb[:, :, 2]]
    
    line_layer = nested_layers.Image(
        name="Line Art",
        visible=True,
        opacity=255,
        group_id=0,
        blend_mode=blend_mode,
        top=0,
        left=0,
        channels=channels,
        metadata=None,
        layer_color=0,
        color_mode=None
    )
    layers_list.append(line_layer)
    
    # PSDファイルとして保存
    output = nested_layers.nested_layers_to_psd(layers_list, color_mode=3)  # RGB mode
    with open(filename, 'wb') as f:
        output.write(f)
    
    return filename


class RGBLineArtDivider:
    """
    RGB線画と下塗り画像から領域分割PSDを生成するノード
    """
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "line_art": ("IMAGE",),
                "base_color": ("IMAGE",),
                "color_tolerance": ("INT", {
                    "default": 10,
                    "min": 0,
                    "max": 50,
                    "step": 1,
                    "display": "slider"
                }),
                "line_blend_mode": (["multiply", "normal", "darken", "overlay"],),
                "merge_small_regions": ("BOOLEAN", {
                    "default": True
                }),
                "min_region_size": ("INT", {
                    "default": 100,
                    "min": 10,
                    "max": 1000,
                    "step": 10,
                    "display": "slider"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "INT", "STRING")
    RETURN_NAMES = ("composite", "base_color", "layer_count", "psd_path")
    FUNCTION = "execute"
    CATEGORY = "LayerDivider"

    def execute(self, line_art, base_color, color_tolerance, line_blend_mode, 
                merge_small_regions, min_region_size):
        
        # 画像をNumPy配列に変換
        line_art_np = line_art.cpu().detach().numpy().__mul__(255.).astype(np.uint8)[0]
        base_color_np = base_color.cpu().detach().numpy().__mul__(255.).astype(np.uint8)[0]
        
        # PIL Imageに変換
        line_art_pil = Image.fromarray(line_art_np)
        base_color_pil = Image.fromarray(base_color_np)
        
        # OpenCV形式（BGRA）に変換
        line_art_cv = pil2cv(line_art_pil)
        base_color_cv = pil2cv(base_color_pil)
        
        # BGRAに変換（アルファチャンネルを追加）
        if line_art_cv.shape[2] == 3:
            line_art_cv = cv2.cvtColor(line_art_cv, cv2.COLOR_BGR2BGRA)
        if base_color_cv.shape[2] == 3:
            base_color_cv = cv2.cvtColor(base_color_cv, cv2.COLOR_BGR2BGRA)
        
        # 色領域を抽出
        color_regions = extract_color_regions(base_color_cv, tolerance=color_tolerance)
        
        # 小さい領域をマージ（オプション）
        if merge_small_regions:
            filtered_regions = {}
            small_region_mask = np.zeros(base_color_cv.shape[:2], dtype=np.uint8)
            
            for color, mask in color_regions.items():
                region_size = np.sum(mask > 0)
                if region_size >= min_region_size:
                    filtered_regions[color] = mask
                else:
                    small_region_mask = cv2.bitwise_or(small_region_mask, mask)
            
            # 小さい領域を「その他」としてまとめる
            if np.any(small_region_mask > 0):
                filtered_regions[(128, 128, 128)] = small_region_mask  # グレーとして追加
            
            color_regions = filtered_regions
        
        # レイヤーを作成
        color_layers, layer_names = create_region_layers(base_color_cv, color_regions)
        
        # BlendModeの設定
        blend_mode_map = {
            "multiply": enums.BlendMode.multiply,
            "normal": enums.BlendMode.normal,
            "darken": enums.BlendMode.darken,
            "overlay": enums.BlendMode.overlay
        }
        
        # PSDファイルを保存（nested_layersを使用）
        filename = save_psd_with_nested_layers(
            base_color_cv,
            line_art_cv,
            color_layers,
            layer_names,
            output_dir,
            blend_mode_map[line_blend_mode],
            "rgb_divided"
        )
        
        print(f"PSD file saved: {filename}")
        print(f"Created {len(color_regions)} color region layers")
        
        # コンポジット画像を作成（プレビュー用）
        composite = base_color_cv.copy()
        if line_blend_mode == "multiply":
            # 乗算合成
            line_rgb = line_art_cv[:, :, :3].astype(np.float32) / 255.0
            composite_rgb = composite[:, :, :3].astype(np.float32) / 255.0
            composite[:, :, :3] = (composite_rgb * line_rgb * 255).astype(np.uint8)
        elif line_blend_mode == "normal":
            # 線画のアルファを考慮して合成
            alpha = line_art_cv[:, :, 3:4].astype(np.float32) / 255.0
            composite[:, :, :3] = (
                line_art_cv[:, :, :3] * alpha + 
                composite[:, :, :3] * (1 - alpha)
            ).astype(np.uint8)
        
        # 出力
        return (
            to_comfy_img(composite),
            to_comfy_img(base_color_cv),
            len(color_regions),
            filename
        )


# ノードマッピング用の辞書を作成
RGB_NODE_CLASS_MAPPINGS = {
    "RGBLineArtDivider": RGBLineArtDivider,
}

RGB_NODE_DISPLAY_NAME_MAPPINGS = {
    "RGBLineArtDivider": "RGB Line Art Divider",
}
