# -*- coding: utf-8 -*-
import torch
import numpy as np

class ImageDataAnalyzer:
    """
    图像数据分析节点
    
    功能：
    - 分析输入图像的各种信息参数
    - 输出批次数、宽度、高度、通道数等基本信息
    - 提供详细的图像数据信息
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "image": ("IMAGE", {"description": "要分析的图像"}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT", "STRING")
    RETURN_NAMES = ("批次", "宽度", "高度", "通道", "更多")
    FUNCTION = "analyze_image_data"
    CATEGORY = "QING/数据类型"
    OUTPUT_NODE = False

    def analyze_image_data(self, image=None):
        """
        分析图像数据并返回各种信息
        
        参数:
            image: 输入图像张量 (通常是 B×H×W×C 格式，可选)
            
        返回:
            tuple: (批次数, 宽度, 高度, 通道数, 详细信息字符串)
        """
        try:
            # 验证输入
            if image is None:
                return self._create_no_input_result_image()
            if not isinstance(image, torch.Tensor):
                return self._create_error_result("无效的图像输入")
            
            # 检测是否为默认的空图像（通常是全零张量）
            if self._is_empty_default_image(image):
                return self._create_no_input_result_image()
            
            # 获取图像维度信息
            shape = image.shape
            device = image.device
            dtype = image.dtype
            
            # 根据常见的ComfyUI图像格式解析维度
            if len(shape) == 4:
                # 标准格式: (B, H, W, C)
                batch_size, height, width, channels = shape
            elif len(shape) == 3:
                # 可能是单张图像: (H, W, C)
                height, width, channels = shape
                batch_size = 1
            elif len(shape) == 2:
                # 可能是灰度图: (H, W)
                height, width = shape
                channels = 1
                batch_size = 1
            else:
                return self._create_error_result(f"不支持的图像维度: {shape}")
            
            # 计算数据统计信息
            total_pixels = batch_size * height * width * channels
            memory_usage_mb = total_pixels * 4 / (1024 * 1024)  # 假设float32
            
            # 计算数值范围
            min_val = float(torch.min(image))
            max_val = float(torch.max(image))
            mean_val = float(torch.mean(image))
            
            # 生成详细信息
            more_info = self._generate_detailed_info(
                shape, device, dtype, total_pixels, memory_usage_mb,
                min_val, max_val, mean_val
            )
            
            return (int(batch_size), int(width), int(height), int(channels), more_info)
            
        except Exception as e:
            error_msg = f"图像数据分析失败: {str(e)}"
            return self._create_error_result(error_msg)
    
    def _generate_detailed_info(self, shape, device, dtype, total_pixels, memory_mb, min_val, max_val, mean_val):
        """生成详细的图像信息字符串"""
        info_lines = [
            f"图像维度: {shape}",
            f"设备: {device}",
            f"数据类型: {dtype}",
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
        
        return "\n".join(info_lines)
    
    def _create_error_result(self, error_msg):
        """创建错误结果"""
        return (0, 0, 0, 0, f"错误: {error_msg}")
    
    def _create_no_input_result_image(self):
        """创建无输入结果（图像）"""
        return (0, 0, 0, 0, "无图像输入")
    
    def _is_empty_default_image(self, image):
        """
        检测是否为默认的空图像
        判断条件：
        1. 全零张量
        2. 或者数值极小（接近零）
        3. 或者是ComfyUI常见的默认尺寸且值很小
        """
        try:
            # 计算图像的统计信息
            image_sum = torch.sum(image).item()
            image_max = torch.max(image).item()
            image_mean = torch.mean(image).item()
            
            # 条件1：完全为零
            if image_sum == 0.0 and image_max == 0.0:
                return True
            
            # 条件2：数值极小（可能是浮点精度误差）
            if image_max < 1e-6 and image_mean < 1e-6:
                return True
            
            # 条件3：检查是否为默认尺寸的近似空图像
            shape = image.shape
            total_pixels = 1
            for dim in shape:
                total_pixels *= dim
            
            # 如果是常见的默认尺寸且平均值很小
            common_sizes = [64*64*3, 1*64*64*3, 64*64*3*1, 128*128*3, 1*128*128*3]
            if total_pixels in common_sizes and image_mean < 0.01:
                return True
            
            return False
            
        except Exception:
            # 如果检测过程出错，保守地认为不是空图像
            return False


class MaskDataAnalyzer:
    """
    遮罩数据分析节点
    
    功能：
    - 分析输入遮罩的各种信息参数
    - 输出批次数、宽度、高度、覆盖比例等信息
    - 提供详细的遮罩数据信息
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "optional": {
                "mask": ("MASK", {"description": "要分析的遮罩"}),
            }
        }

    RETURN_TYPES = ("INT", "INT", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("批次", "宽度", "高度", "比例", "更多")
    FUNCTION = "analyze_mask_data"
    CATEGORY = "QING/数据类型"
    OUTPUT_NODE = False

    def analyze_mask_data(self, mask=None):
        """
        分析遮罩数据并返回各种信息
        
        参数:
            mask: 输入遮罩张量 (通常是 B×H×W 格式，可选)
            
        返回:
            tuple: (批次数, 宽度, 高度, 覆盖比例, 详细信息字符串)
        """
        try:
            # 验证输入
            if mask is None:
                return self._create_no_input_result()
            if not isinstance(mask, torch.Tensor):
                return self._create_error_result("无效的遮罩输入")
            
            # 检测是否为默认的空遮罩（通常是全零张量）
            if self._is_empty_default_mask(mask):
                return self._create_no_input_result()
            
            # 获取遮罩维度信息
            shape = mask.shape
            device = mask.device
            dtype = mask.dtype
            
            # 根据常见的ComfyUI遮罩格式解析维度
            if len(shape) == 3:
                # 标准格式: (B, H, W)
                batch_size, height, width = shape
            elif len(shape) == 2:
                # 单张遮罩: (H, W)
                height, width = shape
                batch_size = 1
            elif len(shape) == 4:
                # 可能是 (B, H, W, 1) 格式
                if shape[3] == 1:
                    batch_size, height, width, _ = shape
                else:
                    return self._create_error_result(f"不支持的遮罩维度: {shape}")
            else:
                return self._create_error_result(f"不支持的遮罩维度: {shape}")
            
            # 计算遮罩统计信息
            total_pixels = batch_size * height * width
            memory_usage_mb = total_pixels * 4 / (1024 * 1024)  # 假设float32
            
            # 计算数值范围和覆盖比例
            min_val = float(torch.min(mask))
            max_val = float(torch.max(mask))
            mean_val = float(torch.mean(mask))
            
            # 计算覆盖比例（假设遮罩值>0.5表示前景）
            if len(shape) == 3:
                threshold_mask = mask > 0.5
            elif len(shape) == 2:
                threshold_mask = mask > 0.5
            else:  # shape[3] == 1
                threshold_mask = mask.squeeze(-1) > 0.5
            
            covered_pixels = torch.sum(threshold_mask).item()
            coverage_ratio = covered_pixels / total_pixels if total_pixels > 0 else 0.0
            
            # 生成详细信息
            more_info = self._generate_detailed_info(
                shape, device, dtype, total_pixels, memory_usage_mb,
                min_val, max_val, mean_val, coverage_ratio, covered_pixels
            )
            
            return (int(batch_size), int(width), int(height), float(coverage_ratio), more_info)
            
        except Exception as e:
            error_msg = f"遮罩数据分析失败: {str(e)}"
            return self._create_error_result(error_msg)
    
    def _generate_detailed_info(self, shape, device, dtype, total_pixels, memory_mb, 
                              min_val, max_val, mean_val, coverage_ratio, covered_pixels):
        """生成详细的遮罩信息字符串"""
        info_lines = [
            f"遮罩维度: {shape}",
            f"设备: {device}",
            f"数据类型: {dtype}",
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
        
        return "\n".join(info_lines)
    
    def _create_error_result(self, error_msg):
        """创建错误结果"""
        return (0, 0, 0, 0.0, f"错误: {error_msg}")
    
    def _create_no_input_result(self):
        """创建无输入结果"""
        return (0, 0, 0, 0.0, "无遮罩输入")
    
    def _is_empty_default_mask(self, mask):
        """
        检测是否为默认的空遮罩
        判断条件：
        1. 全零张量
        2. 或者数值极小（接近零）
        3. 或者是ComfyUI常见的默认尺寸（如64×64）且值很小
        """
        try:
            # 计算遮罩的统计信息
            mask_sum = torch.sum(mask).item()
            mask_max = torch.max(mask).item()
            mask_mean = torch.mean(mask).item()
            
            # 条件1：完全为零
            if mask_sum == 0.0 and mask_max == 0.0:
                return True
            
            # 条件2：数值极小（可能是浮点精度误差）
            if mask_max < 1e-6 and mask_mean < 1e-6:
                return True
            
            # 条件3：检查是否为默认尺寸的近似空遮罩
            shape = mask.shape
            total_pixels = 1
            for dim in shape:
                total_pixels *= dim
            
            # 如果是常见的默认尺寸（如64×64，1×64×64等）且平均值很小
            common_sizes = [64*64, 1*64*64, 64*64*1, 128*128, 1*128*128]
            if total_pixels in common_sizes and mask_mean < 0.01:
                return True
            
            return False
            
        except Exception:
            # 如果检测过程出错，保守地认为不是空遮罩
            return False


# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageDataAnalyzer": ImageDataAnalyzer,
    "MaskDataAnalyzer": MaskDataAnalyzer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageDataAnalyzer": "图像数据",
    "MaskDataAnalyzer": "遮罩数据",
}
