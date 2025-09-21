# -*- coding: utf-8 -*-
import torch
import numpy as np
from PIL import Image
import comfy.utils

class MaskScale:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "scale_by": (["width", "height", "longest_side", "shortest_side", "total_pixels"], {
                    "default": "longest_side"
                }),
                "target_value": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1
                }),
                "interpolation": (["nearest", "bilinear", "bicubic", "lanczos"], {
                    "default": "lanczos"
                }),
                "keep_proportions": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "target_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1
                }),
                "target_height": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1
                }),
            }
        }
    
    # 返回类型与名称（统一中文显示）
    RETURN_TYPES = ("MASK", "INT", "INT")
    RETURN_NAMES = ("mask", "width", "height")
    FUNCTION = "scale_mask"
    CATEGORY = "图像/遮罩"
    
    
    def scale_mask(self, mask, scale_by, target_value, interpolation, keep_proportions, target_width=0, target_height=0):
        """
        缩放遮罩尺寸
        - 遮罩: 输入遮罩 (Tensor: [B,H,W])
        - scale_by: scale_by：width/height/longest_side/shortest_side/total_pixels
        - target_value: target_value（与 scale_by 对应）
        - interpolation: interpolation：nearest/bilinear/bicubic/lanczos
        - keep_proportions: 是否保持纵横比
        - 目标宽度/目标高度: 指定目标尺寸（优先于 scale_by）
        返回：缩放后的遮罩，以及目标宽高
        """
        # 输入校验
        if mask is None:
            raise ValueError("Input mask cannot be None")
        
        # Ensure input is 2D or 3D tensor
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)
        elif mask.dim() != 3:
            raise ValueError(f"Mask dimension should be 2 or 3, got {mask.dim()}")
        
        # 获取当前遮罩尺寸
        batch_size, orig_height, orig_width = mask.shape
        
        # 若显式提供目标尺寸，则优先使用
        if target_width > 0 and target_height > 0:
            target_width = max(1, target_width)
            target_height = max(1, target_height)
        else:
            # 根据缩放方式计算目标尺寸
            orig_pixels = orig_height * orig_width
            
            if scale_by == "width":
                target_width = target_value
                if keep_proportions:
                    target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                else:
                    target_height = orig_height
                    
            elif scale_by == "height":
                target_height = target_value
                if keep_proportions:
                    target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                else:
                    target_width = orig_width
                    
            elif scale_by == "longest_side":
                if orig_height >= orig_width:
                    target_height = target_value
                    if keep_proportions:
                        target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                    else:
                        target_width = orig_width
                else:
                    target_width = target_value
                    if keep_proportions:
                        target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                    else:
                        target_height = orig_height
                        
            elif scale_by == "shortest_side":
                if orig_height <= orig_width:
                    target_height = target_value
                    if keep_proportions:
                        target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                    else:
                        target_width = orig_width
                else:
                    target_width = target_value
                    if keep_proportions:
                        target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                    else:
                        target_height = orig_height
                        
            elif scale_by == "total_pixels":
                # 依据总像素计算缩放因子
                scale_factor = (target_value / orig_pixels) ** 0.5
                target_width = max(1, int(round(orig_width * scale_factor)))
                target_height = max(1, int(round(orig_height * scale_factor)))
                
                # 若keep_proportions，细调以更接近目标像素
                if keep_proportions:
                    actual_pixels = target_width * target_height
                    if abs(actual_pixels - target_value) / target_value > 0.1:
                        alternative_width = max(1, int(round((target_value * orig_width / orig_height) ** 0.5)))
                        alternative_height = max(1, int(round(target_value / alternative_width)))
                        if abs(alternative_width * alternative_height - target_value) < abs(actual_pixels - target_value):
                            target_width, target_height = alternative_width, alternative_height
        
        # 保证目标尺寸至少为 1x1
        target_width = max(1, target_width)
        target_height = max(1, target_height)
        
        # 记录原始设备与数据类型
        device = mask.device
        dtype = mask.dtype
        
        # 当选择 Lanczos 时，使用 PIL 获得更高质量
        if interpolation == "lanczos":
            scaled_masks = []
            for i in range(batch_size):
                # 转为 PIL 图像
                mask_np = mask[i].cpu().numpy() * 255
                mask_pil = Image.fromarray(mask_np.astype(np.uint8), mode='L')
                
                # Lanczos 插值缩放
                mask_pil = mask_pil.resize((target_width, target_height), Image.LANCZOS)
                
                # 转回张量
                mask_np = np.array(mask_pil).astype(np.float32) / 255.0
                mask_tensor = torch.from_numpy(mask_np).to(device=device, dtype=dtype)
                scaled_masks.append(mask_tensor)
            
            scaled_mask = torch.stack(scaled_masks)
        else:
            # 选择 PyTorch 的插值模式
            if interpolation == "nearest":
                mode = "nearest"
            elif interpolation == "bilinear":
                mode = "bilinear"
            else:  # bicubic
                mode = "bicubic"
            
            # 转为 float 以便插值
            mask_float = mask.float()
            
            # 进行尺寸变换
            scaled_mask = torch.nn.functional.interpolate(
                mask_float.unsqueeze(1),
                size=(target_height, target_width),
                mode=mode,
                align_corners=False if mode != "nearest" else None
            ).squeeze(1)
            
            # 转回原 dtype
            if dtype != torch.float32:
                scaled_mask = scaled_mask.to(dtype)
        
        # 保证数值在 0-1 范围
        scaled_mask = torch.clamp(scaled_mask, 0.0, 1.0)
        
        return (scaled_mask, target_width, target_height)

# Node registration
NODE_CLASS_MAPPINGS = {
    "MaskScale": MaskScale
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskScale": "Mask Scale"
}
