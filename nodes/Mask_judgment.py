import torch
import numpy as np
from comfy.model_patcher import ModelPatcher

class MaskJudgment:
    """
    遮罩判断节点
    功能：根据输入的遮罩判断是否存在有效遮罩
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
            },
            "optional": {
                "threshold": ("FLOAT", {"default": 0.01, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("has_mask", "mask_flag", "mask_ratio", "mask_info")
    FUNCTION = "judge_mask"
    CATEGORY = "自定义/遮罩"

    def judge_mask(self, mask, threshold=0.01):
        """
        判断遮罩是否存在
        
        参数:
            mask: 输入的遮罩张量
            threshold: 遮罩有效阈值（占比多少算有效）
            
        返回:
            tuple: (布尔值, 整数标志, 浮点比例, 信息字符串)
        """
        # 初始化默认值
        has_mask = False
        mask_flag = 0
        mask_ratio = 0.0
        mask_info = "无遮罩对象"
        real_mask_ratio = 0.0
        
        # 精确检查遮罩状态
        if mask is None:
            # 完全没有遮罩输入
            mask_info = "无遮罩对象"
        elif not hasattr(mask, 'numel') or mask.numel() == 0:
            # 遮罩对象无效或为空张量
            mask_info = "无遮罩对象"
        else:
            # 将遮罩转换为numpy数组以便处理
            mask_np = mask.cpu().numpy() if hasattr(mask, 'cpu') else np.array(mask)
            
            # 检查张量形状是否有效
            if mask_np.size == 0:
                mask_info = "无遮罩对象"
            else:
                # 计算遮罩中非零像素的比例
                total_pixels = mask_np.size
                non_zero_pixels = np.count_nonzero(mask_np)
                real_mask_ratio = non_zero_pixels / total_pixels
                
                # 检查遮罩最大值，如果最大值接近0，可能是无效遮罩
                max_value = np.max(mask_np) if mask_np.size > 0 else 0
                
                # 精确判断遮罩状态
                if non_zero_pixels == 0 or max_value < 1e-6:
                    # 判断是真正的无遮罩还是空内容遮罩
                    # 如果张量很小或者看起来像默认空值，认为是无遮罩
                    if mask_np.size <= 4 or (mask_np.shape[0] == 1 and np.allclose(mask_np, 0)):
                        mask_info = "无遮罩对象"
                    else:
                        mask_info = "遮罩对象存在但无内容 (全为零值)"
                elif real_mask_ratio >= threshold:
                    # 遮罩存在且满足阈值要求
                    has_mask = True
                    mask_flag = 1
                    mask_ratio = 1.0
                    
                    # 计算遮罩的边界框
                    rows = np.any(mask_np, axis=1)
                    cols = np.any(mask_np, axis=0)
                    ymin, ymax = np.where(rows)[0][[0, -1]] if np.any(rows) else (0, 0)
                    xmin, xmax = np.where(cols)[0][[0, -1]] if np.any(cols) else (0, 0)
                    
                    # 计算边界框尺寸
                    bbox_width = xmax - xmin + 1
                    bbox_height = ymax - ymin + 1
                    
                    mask_info = f"遮罩覆盖率: {real_mask_ratio:.2%}\n"
                    mask_info += f"非零像素: {non_zero_pixels}/{total_pixels}\n"
                    mask_info += f"边界框: [{xmin}, {ymin}] - [{xmax}, {ymax}]\n"
                    mask_info += f"边界框尺寸: {bbox_width}×{bbox_height}"
                    
                    # 添加质量评估
                    if real_mask_ratio > 0.8:
                        mask_info += "\n质量评估: 高质量遮罩"
                    elif real_mask_ratio > 0.3:
                        mask_info += "\n质量评估: 中等质量遮罩"
                    else:
                        mask_info += "\n质量评估: 稀疏遮罩"
                else:
                    # 遮罩存在且有内容，但覆盖率低于阈值
                    has_mask = False
                    mask_flag = 0
                    mask_ratio = 0.0
                    mask_info = f"遮罩存在但覆盖率低于阈值 ({real_mask_ratio:.2%} < {threshold:.2%})"
        
        # 返回结果
        return (bool(has_mask), mask_flag, float(mask_ratio), mask_info)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "MaskJudgment": MaskJudgment
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskJudgment": "MaskJudgment"
}
