# -*- coding: utf-8 -*-
import torch

class ImageDataAnalyzer:
    """图像数据分析节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "image": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = ("批次", "宽度", "高度", "通道", "信息")
    FUNCTION = "analyze_image_data"
    CATEGORY = "🎨QING/数据工具"

    def analyze_image_data(self, image=None):
        if image is None:
            return (0, 0, 0, 0, "无图像输入")
        
        # 解析图像维度
        if len(image.shape) == 4:
            batch_size, height, width, channels = image.shape
        elif len(image.shape) == 3:
            height, width, channels = image.shape
            batch_size = 1
        else:
            return (0, 0, 0, 0, f"不支持的维度: {image.shape}")
        
        # 计算统计信息
        total_pixels = batch_size * height * width * channels
        memory_mb = total_pixels * 4 / (1024 * 1024)  # 假设float32
        min_val = float(image.min())
        max_val = float(image.max())
        mean_val = float(image.mean())
        
        # 生成详细信息
        info_lines = [
            f"图像维度: {image.shape}",
            f"设备: {image.device}",
            f"数据类型: {image.dtype}",
            f"总像素数: {total_pixels:,}",
            f"内存占用: {memory_mb:.2f} MB",
            f"数值范围: [{min_val:.4f}, {max_val:.4f}]",
            f"平均值: {mean_val:.4f}",
        ]
        
        # 判断图像类型
        if min_val >= 0 and max_val <= 1.001:
            info_lines.append("类型: 标准化图像 (0-1)")
        elif min_val >= 0 and max_val <= 255.1:
            info_lines.append("类型: 8位图像 (0-255)")
        else:
            info_lines.append("类型: 自定义范围")
        
        more_info = "\n".join(info_lines)
        
        return (int(batch_size), int(width), int(height), int(channels), more_info)


class MaskDataAnalyzer:
    """遮罩数据分析节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("批次", "宽度", "高度", "覆盖率", "信息")
    FUNCTION = "analyze_mask_data"
    CATEGORY = "🎨QING/数据工具"

    def analyze_mask_data(self, mask=None):
        if mask is None:
            return (0, 0, 0, 0.0, "无遮罩输入")
        
        # 解析遮罩维度
        if len(mask.shape) == 3:
            batch_size, height, width = mask.shape
        elif len(mask.shape) == 2:
            height, width = mask.shape
            batch_size = 1
        else:
            return (0, 0, 0, 0.0, f"不支持的维度: {mask.shape}")
        
        # 计算统计信息
        total_pixels = batch_size * height * width
        memory_mb = total_pixels * 4 / (1024 * 1024)  # 假设float32
        coverage_ratio = (mask > 0.5).float().mean().item()
        covered_pixels = int(coverage_ratio * total_pixels)
        min_val = float(mask.min())
        max_val = float(mask.max())
        mean_val = float(mask.mean())
        
        # 生成详细信息
        info_lines = [
            f"遮罩维度: {mask.shape}",
            f"设备: {mask.device}",
            f"数据类型: {mask.dtype}",
            f"总像素数: {total_pixels:,}",
            f"内存占用: {memory_mb:.2f} MB",
            f"数值范围: [{min_val:.4f}, {max_val:.4f}]",
            f"平均值: {mean_val:.4f}",
            f"覆盖像素: {covered_pixels:,}",
            f"覆盖比例: {coverage_ratio:.4f} ({coverage_ratio*100:.2f}%)",
        ]
        
        # 判断遮罩类型
        if min_val >= 0 and max_val <= 1.001:
            info_lines.append("类型: 标准化遮罩 (0-1)")
        elif min_val >= 0 and max_val <= 255.1:
            info_lines.append("类型: 8位遮罩 (0-255)")
        else:
            info_lines.append("类型: 自定义范围")
        
        # 遮罩质量评估
        if coverage_ratio < 0.01:
            info_lines.append("质量: 几乎空白")
        elif coverage_ratio < 0.1:
            info_lines.append("质量: 稀疏覆盖")
        elif coverage_ratio < 0.5:
            info_lines.append("质量: 部分覆盖")
        elif coverage_ratio < 0.9:
            info_lines.append("质量: 大面积覆盖")
        else:
            info_lines.append("质量: 几乎全覆盖")
        
        more_info = "\n".join(info_lines)
        
        return (int(batch_size), int(width), int(height), float(coverage_ratio), more_info)


class TextCompare:
    """文本比较节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "case_sensitive": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "text_1": ("STRING", {"default": ""}),
                "compare_1": ("STRING", {"default": ""}),
                "text_2": ("STRING", {"default": ""}),
                "compare_2": ("STRING", {"default": ""}),
                "text_3": ("STRING", {"default": ""}),
                "compare_3": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("BOOLEAN", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("结果1", "结果2", "结果3")
    FUNCTION = "compare_texts"
    CATEGORY = "🎨QING/数据工具"
    OUTPUT_NODE = True
    
    def compare_texts(self, case_sensitive=False, **kwargs):
        results = []
        for i in range(1, 4):
            text = kwargs.get(f"text_{i}", "")
            compare = kwargs.get(f"compare_{i}", "")
            
            if case_sensitive:
                result = text == compare
            else:
                result = text.lower() == compare.lower()
            results.append(result)
        
        return tuple(results)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageDataAnalyzer": ImageDataAnalyzer,
    "MaskDataAnalyzer": MaskDataAnalyzer,
    "TextCompare": TextCompare
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageDataAnalyzer": "图像数据",
    "MaskDataAnalyzer": "遮罩数据",
    "TextCompare": "文本对比"
}
