"""
Fill Space Debug Node for ComfyUI
デバッグ用ノード - 入力画像の値を確認
"""

import torch
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont
import cv2
import folder_paths
import os

comfy_path = os.path.dirname(folder_paths.__file__)
layer_divider_path = f'{comfy_path}/custom_nodes/ComfyUI-fixableflow'
output_dir = f"{layer_divider_path}/output"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)


def tensor_to_pil(tensor):
    """ComfyUIのテンソル形式をPIL Imageに変換"""
    image_np = tensor.cpu().detach().numpy()
    if len(image_np.shape) == 4:
        image_np = image_np[0]  # バッチの最初の画像を取得
    image_np = (image_np * 255).astype(np.uint8)
    
    if image_np.shape[2] == 3:
        mode = 'RGB'
    elif image_np.shape[2] == 4:
        mode = 'RGBA'
    else:
        mode = 'L'
    
    return Image.fromarray(image_np, mode=mode)


def pil_to_tensor(image):
    """PIL ImageをComfyUIのテンソル形式に変換"""
    image_np = np.array(image).astype(np.float32) / 255.0
    image_np = np.expand_dims(image_np, axis=0)
    return torch.from_numpy(image_np)


def analyze_image(image_pil):
    """画像の値を分析"""
    # グレースケールに変換
    if image_pil.mode != 'L':
        gray_pil = image_pil.convert('L')
    else:
        gray_pil = image_pil
    
    array = np.array(gray_pil)
    
    # ユニークな値とその頻度を取得
    unique_values, counts = np.unique(array, return_counts=True)
    
    # 統計情報
    stats = {
        'min': array.min(),
        'max': array.max(),
        'mean': array.mean(),
        'std': array.std(),
        'unique_values': unique_values,
        'counts': counts,
        'shape': array.shape
    }
    
    # 値の分布をヒストグラムで確認
    hist_values = {}
    for val, count in zip(unique_values, counts):
        hist_values[int(val)] = int(count)
    
    return stats, hist_values, array


def create_visualization(original, binary, stats, hist_values, threshold=128):
    """分析結果の可視化"""
    width = original.width
    height = original.height
    
    # 可視化画像（4パネル）
    viz = Image.new('RGB', (width * 2, height * 2), (255, 255, 255))
    
    # 1. オリジナル画像
    viz.paste(original.convert('RGB'), (0, 0))
    
    # 2. 二値化画像（閾値処理後）
    binary_gray = binary.convert('L') if binary.mode != 'L' else binary
    viz.paste(binary_gray.convert('RGB'), (width, 0))
    
    # 3. 値の分布ヒートマップ
    array = np.array(binary_gray)
    
    # ヒートマップ作成
    heatmap = np.zeros((height, width, 3), dtype=np.uint8)
    # 0 (黒) -> 青
    # 128 (中間) -> 緑
    # 255 (白) -> 赤
    heatmap[:, :, 0] = 255 - array  # Blue channel
    heatmap[:, :, 1] = 128 - np.abs(array - 128) * 2  # Green channel
    heatmap[:, :, 2] = array  # Red channel
    
    heatmap_pil = Image.fromarray(heatmap)
    viz.paste(heatmap_pil, (0, height))
    
    # 4. 統計情報パネル
    info_panel = Image.new('RGB', (width, height), (240, 240, 240))
    draw = ImageDraw.Draw(info_panel)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 統計情報を描画
    y_pos = 10
    line_height = 20
    
    draw.text((10, y_pos), f"Image Statistics:", fill=(0, 0, 0), font=font)
    y_pos += line_height * 1.5
    
    draw.text((10, y_pos), f"Min: {stats['min']}", fill=(0, 0, 0), font=font_small)
    y_pos += line_height
    
    draw.text((10, y_pos), f"Max: {stats['max']}", fill=(0, 0, 0), font=font_small)
    y_pos += line_height
    
    draw.text((10, y_pos), f"Mean: {stats['mean']:.2f}", fill=(0, 0, 0), font=font_small)
    y_pos += line_height
    
    draw.text((10, y_pos), f"Std: {stats['std']:.2f}", fill=(0, 0, 0), font=font_small)
    y_pos += line_height
    
    draw.text((10, y_pos), f"Unique values: {len(stats['unique_values'])}", fill=(0, 0, 0), font=font_small)
    y_pos += line_height * 1.5
    
    # 主要な値の頻度を表示
    draw.text((10, y_pos), "Value Distribution:", fill=(0, 0, 0), font=font)
    y_pos += line_height
    
    # 最も頻度の高い値を表示
    sorted_values = sorted(hist_values.items(), key=lambda x: x[1], reverse=True)
    for i, (val, count) in enumerate(sorted_values[:10]):
        percentage = (count / sum(hist_values.values())) * 100
        draw.text((10, y_pos), f"  {val}: {count} ({percentage:.1f}%)", fill=(0, 0, 0), font=font_small)
        y_pos += line_height
        if y_pos > height - 20:
            break
    
    # 問題の可能性を表示
    y_pos = height - 100
    draw.text((10, y_pos), "Potential Issues:", fill=(255, 0, 0), font=font)
    y_pos += line_height
    
    # 中間値の存在をチェック
    intermediate_values = [v for v in stats['unique_values'] if v not in [0, 255]]
    if len(intermediate_values) > 0:
        draw.text((10, y_pos), f"⚠ Found {len(intermediate_values)} intermediate values", fill=(255, 0, 0), font=font_small)
        y_pos += line_height
        draw.text((10, y_pos), f"  Values: {intermediate_values[:10]}", fill=(255, 0, 0), font=font_small)
    else:
        draw.text((10, y_pos), "✓ Image is properly binarized", fill=(0, 128, 0), font=font_small)
    
    viz.paste(info_panel, (width, height))
    
    # ラベルを追加
    draw = ImageDraw.Draw(viz)
    draw.text((10, 10), "Original", fill=(255, 255, 255), font=font)
    draw.text((width + 10, 10), "Binary Input", fill=(255, 255, 255), font=font)
    draw.text((10, height + 10), "Value Heatmap", fill=(255, 255, 255), font=font)
    draw.text((width + 10, height + 10), "Statistics", fill=(0, 0, 0), font=font)
    
    return viz


class FillSpaceDebugNode:
    """
    FillSpace用デバッグノード
    入力画像の値を分析して問題を特定
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "binary_image": ("IMAGE",),
                "flat_image": ("IMAGE",),
                "analysis_threshold": ("INT", {
                    "default": 128,
                    "min": 0,
                    "max": 255,
                    "step": 1,
                    "display": "slider",
                    "display_label": "Analysis Threshold"
                }),
                "save_debug_info": ("BOOLEAN", {
                    "default": True,
                    "display_label": "Save Debug Info to File"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("debug_visualization", "analysis_report")
    
    FUNCTION = "execute"
    
    CATEGORY = "LayerDivider/Debug"
    
    def execute(self, binary_image, flat_image, analysis_threshold=128, save_debug_info=True):
        """
        入力画像を分析してデバッグ情報を生成
        """
        
        # テンソルをPIL Imageに変換
        binary_pil = tensor_to_pil(binary_image)
        flat_pil = tensor_to_pil(flat_image)
        
        # バイナリ画像の分析
        stats, hist_values, array = analyze_image(binary_pil)
        
        # レポート生成
        report = "=== Fill Space Debug Analysis ===\n\n"
        report += f"Binary Image Shape: {stats['shape']}\n"
        report += f"Min Value: {stats['min']}\n"
        report += f"Max Value: {stats['max']}\n"
        report += f"Mean Value: {stats['mean']:.2f}\n"
        report += f"Std Dev: {stats['std']:.2f}\n"
        report += f"Unique Values Count: {len(stats['unique_values'])}\n\n"
        
        report += "Value Distribution:\n"
        sorted_values = sorted(hist_values.items(), key=lambda x: x[1], reverse=True)
        total_pixels = sum(hist_values.values())
        for val, count in sorted_values[:10]:
            percentage = (count / total_pixels) * 100
            report += f"  Value {val}: {count} pixels ({percentage:.2f}%)\n"
        
        # 問題の診断
        report += "\n=== Diagnosis ===\n"
        intermediate_values = [v for v in stats['unique_values'] if v not in [0, 255]]
        
        if len(intermediate_values) > 0:
            report += f"⚠ WARNING: Found {len(intermediate_values)} intermediate values!\n"
            report += f"  These values: {intermediate_values}\n"
            report += "  This may cause the mottled/spotted pattern in FillSpace.\n"
            report += "\nRecommended Solutions:\n"
            report += "  1. Apply proper binarization before FillSpace\n"
            report += "  2. Use threshold value to convert to pure black/white\n"
            report += f"  3. Suggested threshold based on mean: {int(stats['mean'])}\n"
        else:
            report += "✓ Image is properly binarized (only 0 and 255 values)\n"
            
            # 白黒の比率をチェック
            if 0 in hist_values and 255 in hist_values:
                black_ratio = hist_values[0] / total_pixels * 100
                white_ratio = hist_values[255] / total_pixels * 100
                report += f"\nPixel Distribution:\n"
                report += f"  Black (0): {black_ratio:.2f}%\n"
                report += f"  White (255): {white_ratio:.2f}%\n"
                
                if white_ratio < 10:
                    report += "\n⚠ Very few white pixels - might not have much to fill\n"
                elif black_ratio < 10:
                    report += "\n⚠ Very few black pixels - might not have enough reference points\n"
        
        # 可視化を作成
        viz = create_visualization(flat_pil, binary_pil, stats, hist_values, analysis_threshold)
        
        # デバッグ情報をファイルに保存
        if save_debug_info:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # レポートを保存
            report_path = os.path.join(output_dir, f"fillspace_debug_{timestamp}.txt")
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # 画像を保存
            viz_path = os.path.join(output_dir, f"fillspace_debug_{timestamp}.png")
            viz.save(viz_path)
            
            # 配列データも保存（詳細分析用）
            np_path = os.path.join(output_dir, f"fillspace_debug_{timestamp}.npy")
            np.save(np_path, array)
            
            report += f"\n\nDebug files saved to:\n"
            report += f"  Report: {report_path}\n"
            report += f"  Visualization: {viz_path}\n"
            report += f"  Array data: {np_path}\n"
        
        # ComfyUIのテンソル形式に変換
        viz_tensor = pil_to_tensor(viz)
        
        return (viz_tensor, report)


# ノードクラスのマッピング
NODE_CLASS_MAPPINGS = {
    "FillSpaceDebug": FillSpaceDebugNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FillSpaceDebug": "Fill Space Debug",
}
