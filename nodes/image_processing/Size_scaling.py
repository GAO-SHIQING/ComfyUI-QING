# -*- coding: utf-8 -*-
import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import math
import comfy.utils


class Imagesizescaling:
    """
    图像缩放节点 - 实现图像和遮罩的高级缩放功能
    
    功能:
    - 同时处理图像和遮罩的缩放
    - 支持多种缩放方式：拉伸、裁剪、填充、保持比例
    - 支持多种插值方法：nearest、bilinear、bicubic、area、nearest-exact、lanczos
    - 支持多种缩放定义：无、最长边、最短边、宽度、高度、百分比、总像素
    - 支持图像倍数约束
    - 输出最终的图像、遮罩和尺寸信息
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scale_mode": (["keep_ratio", "stretch", "crop", "pad"], {
                    "default": "keep_ratio"
                }),
                "interpolation": (["lanczos", "nearest", "bilinear", "bicubic", "area", "nearest-exact"], {
                    "default": "lanczos"
                }),
                "scale_definition": (["none", "longest_side", "shortest_side", "width", "height", "percentage", "total_pixels"], {
                    "default": "longest_side"
                }),
                "definition_value": ("INT", {
                    "default": 1024,
                    "min": 1,
                    "max": 999999999,
                    "step": 1
                }),
                "multiple_of": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 256,
                    "step": 1
                }),
            },
            "optional": {
                "image": ("IMAGE",),
                "mask": ("MASK",),
                "width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999999,
                    "step": 1
                }),
                "height": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999999,
                    "step": 1
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("image", "mask", "width", "height")
    FUNCTION = "scale_image"
    CATEGORY = "🎨QING/图像处理"
    
    def scale_image(self, scale_mode, interpolation, scale_definition, definition_value, multiple_of,
                   width=0, height=0, image=None, mask=None):
        """
        主处理函数：实现图像和遮罩的缩放
        
        参数:
            scale_mode: 缩放方式
            interpolation: 插值方法
            scale_definition: 缩放定义
            definition_value: 定义调整值
            multiple_of: 图像倍数
            image: 输入图像（可选）
            mask: 输入遮罩（可选）
            width: 目标宽度（可选）
            height: 目标高度（可选）
            
        返回:
            tuple: (缩放后的图像, 缩放后的遮罩, 最终宽度, 最终高度)
        """
        
        # 验证输入
        if image is None and mask is None:
            raise ValueError("至少需要提供图像或遮罩中的一个")
        
        # 获取原始尺寸
        if image is not None:
            orig_height, orig_width = self._get_image_size(image)
        elif mask is not None:
            orig_height, orig_width = self._get_mask_size(mask)
        else:
            orig_height, orig_width = 512, 512  # 默认尺寸
        
        # 计算目标尺寸
        target_width, target_height = self._calculate_target_size(
            orig_width, orig_height, width, height, scale_mode, 
            scale_definition, definition_value, multiple_of
        )
        
        # 缩放图像
        scaled_image = None
        if image is not None:
            scaled_image = self._scale_image_tensor(
                image, target_width, target_height, scale_mode, interpolation
            )
        else:
            # 创建空图像
            scaled_image = self._create_empty_image(target_width, target_height)
        
        # 缩放遮罩
        scaled_mask = None
        if mask is not None:
            scaled_mask = self._scale_mask_tensor(
                mask, target_width, target_height, interpolation
            )
        else:
            # 创建白色遮罩
            scaled_mask = self._create_white_mask(target_width, target_height)
        
        return (scaled_image, scaled_mask, target_width, target_height)
    
    def _get_image_size(self, image):
        """获取图像尺寸"""
        if image.dim() == 4:  # (B, H, W, C)
            return image.shape[1], image.shape[2]
        elif image.dim() == 3:  # (H, W, C)
            return image.shape[0], image.shape[1]
        else:
            raise ValueError(f"不支持的图像维度: {image.dim()}")
    
    def _get_mask_size(self, mask):
        """获取遮罩尺寸"""
        if mask.dim() == 3:  # (B, H, W)
            return mask.shape[1], mask.shape[2]
        elif mask.dim() == 2:  # (H, W)
            return mask.shape[0], mask.shape[1]
        else:
            raise ValueError(f"不支持的遮罩维度: {mask.dim()}")
    
    def _calculate_target_size(self, orig_width, orig_height, width, height, 
                              scale_mode, scale_definition, definition_value, multiple_of):
        """计算目标尺寸"""
        
        # 如果直接指定了宽高，优先使用
        if width > 0 and height > 0:
            target_width, target_height = width, height
        elif width > 0:
            target_width = width
            if scale_mode == "pad":
                # pad模式：如果只指定宽度，高度保持原始值（不缩放）
                target_height = orig_height
            elif scale_mode == "keep_ratio":
                target_height = max(1, int(orig_height * (width / orig_width)))
            else:
                target_height = orig_height
        elif height > 0:
            target_height = height
            if scale_mode == "pad":
                # pad模式：如果只指定高度，宽度保持原始值（不缩放）
                target_width = orig_width
            elif scale_mode == "keep_ratio":
                target_width = max(1, int(orig_width * (height / orig_height)))
            else:
                target_width = orig_width
        else:
            # 根据缩放定义计算尺寸
            target_width, target_height = self._calculate_by_definition(
                orig_width, orig_height, scale_definition, definition_value, scale_mode
            )
        
        # 应用倍数约束
        if multiple_of > 1:
            # 使用就近舍入模式，减少不必要的尺寸变化
            target_width = round(target_width / multiple_of) * multiple_of
            target_height = round(target_height / multiple_of) * multiple_of
        
        # 确保最小尺寸
        target_width = max(1, target_width)
        target_height = max(1, target_height)
        
        return target_width, target_height
    
    def _calculate_by_definition(self, orig_width, orig_height, scale_definition, 
                                definition_value, scale_mode):
        """根据缩放定义计算目标尺寸"""
        
        if scale_definition == "none":
            return orig_width, orig_height
        
        elif scale_definition == "longest_side":
            if orig_width >= orig_height:
                target_width = definition_value
                if scale_mode in ["keep_ratio", "pad"]:
                    target_height = max(1, int(orig_height * (definition_value / orig_width)))
                else:
                    target_height = orig_height
            else:
                target_height = definition_value
                if scale_mode in ["keep_ratio", "pad"]:
                    target_width = max(1, int(orig_width * (definition_value / orig_height)))
                else:
                    target_width = orig_width
        
        elif scale_definition == "shortest_side":
            if orig_width <= orig_height:
                target_width = definition_value
                if scale_mode in ["keep_ratio", "pad"]:
                    target_height = max(1, int(orig_height * (definition_value / orig_width)))
                else:
                    target_height = orig_height
            else:
                target_height = definition_value
                if scale_mode in ["keep_ratio", "pad"]:
                    target_width = max(1, int(orig_width * (definition_value / orig_height)))
                else:
                    target_width = orig_width
        
        elif scale_definition == "width":
            target_width = definition_value
            if scale_mode in ["keep_ratio", "pad"]:
                target_height = max(1, int(orig_height * (definition_value / orig_width)))
            else:
                target_height = orig_height
        
        elif scale_definition == "height":
            target_height = definition_value
            if scale_mode in ["keep_ratio", "pad"]:
                target_width = max(1, int(orig_width * (definition_value / orig_height)))
            else:
                target_width = orig_width
        
        elif scale_definition == "percentage":
            scale_factor = definition_value / 100.0
            target_width = max(1, int(orig_width * scale_factor))
            target_height = max(1, int(orig_height * scale_factor))
        
        elif scale_definition == "total_pixels":
            if scale_mode in ["keep_ratio", "pad"]:
                aspect_ratio = orig_width / orig_height
                target_height = max(1, int(math.sqrt(definition_value / aspect_ratio)))
                target_width = max(1, int(target_height * aspect_ratio))
            else:
                # 非保持比例时，平均分配像素
                side_length = max(1, int(math.sqrt(definition_value)))
                target_width = side_length
                target_height = side_length
        
        else:
            target_width, target_height = orig_width, orig_height
        
        return target_width, target_height
    
    def _scale_image_tensor(self, image, target_width, target_height, scale_mode, interpolation):
        """缩放图像张量"""
        
        # 确保图像是4维 (B, H, W, C)
        if image.dim() == 3:
            image = image.unsqueeze(0)
        
        device = image.device
        dtype = image.dtype
        
        # 获取原始尺寸
        batch_size, orig_height, orig_width, channels = image.shape
        
        if scale_mode == "stretch":
            # 直接拉伸到目标尺寸
            return self._resize_image(image, target_width, target_height, interpolation)
        
        elif scale_mode == "keep_ratio":
            # 保持比例缩放，可能会有黑边
            scale_x = target_width / orig_width
            scale_y = target_height / orig_height
            scale = min(scale_x, scale_y)
            
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            
            # 先缩放到合适大小
            scaled = self._resize_image(image, new_width, new_height, interpolation)
            
            # 然后填充到目标尺寸
            return self._pad_image(scaled, target_width, target_height)
        
        elif scale_mode == "crop":
            # 保持比例缩放，裁剪多余部分
            scale_x = target_width / orig_width
            scale_y = target_height / orig_height
            scale = max(scale_x, scale_y)
            
            new_width = int(orig_width * scale)
            new_height = int(orig_height * scale)
            
            # 先缩放到合适大小
            scaled = self._resize_image(image, new_width, new_height, interpolation)
            
            # 然后居中裁剪
            return self._center_crop_image(scaled, target_width, target_height)
        
        elif scale_mode == "pad":
            # pad模式：保持原始尺寸，直接填充到目标尺寸
            # 不进行任何缩放，直接将原图放置在目标画布中心
            return self._pad_image(image, target_width, target_height)
        
        else:
            return self._resize_image(image, target_width, target_height, interpolation)
    
    def _scale_mask_tensor(self, mask, target_width, target_height, interpolation):
        """缩放遮罩张量"""
        
        # 确保遮罩是3维 (B, H, W)
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)
        
        device = mask.device
        dtype = mask.dtype
        
        # 遮罩始终使用最近邻或双线性插值，不使用复杂的插值方法
        if interpolation in ["nearest", "nearest-exact"]:
            mode = "nearest"
        else:
            mode = "bilinear"
        
        # 转换为float进行插值
        mask_float = mask.float().unsqueeze(1)  # (B, 1, H, W)
        
        # 使用F.interpolate进行缩放
        scaled_mask = F.interpolate(
            mask_float,
            size=(target_height, target_width),
            mode=mode,
            align_corners=False if mode != "nearest" else None
        ).squeeze(1)  # (B, H, W)
        
        # 转回原始数据类型并限制范围
        scaled_mask = torch.clamp(scaled_mask, 0.0, 1.0)
        if dtype != torch.float32:
            scaled_mask = scaled_mask.to(dtype)
        
        return scaled_mask
    
    def _resize_image(self, image, target_width, target_height, interpolation):
        """使用指定插值方法缩放图像"""
        
        device = image.device
        dtype = image.dtype
        
        if interpolation == "lanczos":
            # 使用PIL进行Lanczos插值
            return self._resize_image_pil(image, target_width, target_height, Image.LANCZOS)
        
        elif interpolation == "area":
            # 使用PIL进行区域插值（适合缩小）
            return self._resize_image_pil(image, target_width, target_height, Image.BOX)
        
        elif interpolation == "nearest-exact":
            # 精确最近邻插值
            return self._resize_image_pil(image, target_width, target_height, Image.NEAREST)
        
        else:
            # 使用PyTorch的F.interpolate
            mode_map = {
                "nearest": "nearest",
                "bilinear": "bilinear",
                "bicubic": "bicubic"
            }
            mode = mode_map.get(interpolation, "bilinear")
            
            # 转换维度 (B, H, W, C) -> (B, C, H, W)
            image_transposed = image.permute(0, 3, 1, 2)
            
            # 缩放
            scaled = F.interpolate(
                image_transposed,
                size=(target_height, target_width),
                mode=mode,
                align_corners=False if mode != "nearest" else None
            )
            
            # 转换回 (B, H, W, C)
            return scaled.permute(0, 2, 3, 1)
    
    def _resize_image_pil(self, image, target_width, target_height, pil_method):
        """使用PIL进行图像缩放"""
        
        device = image.device
        dtype = image.dtype
        batch_size = image.shape[0]
        
        scaled_images = []
        for i in range(batch_size):
            # 转换为PIL图像
            img_np = (image[i].cpu().numpy() * 255).astype(np.uint8)
            if img_np.shape[2] == 1:
                pil_img = Image.fromarray(img_np[:, :, 0], mode='L')
            elif img_np.shape[2] == 3:
                pil_img = Image.fromarray(img_np, mode='RGB')
            elif img_np.shape[2] == 4:
                pil_img = Image.fromarray(img_np, mode='RGBA')
            else:
                # 不支持的通道数，取前3个通道
                pil_img = Image.fromarray(img_np[:, :, :3], mode='RGB')
            
            # 缩放
            resized_pil = pil_img.resize((target_width, target_height), pil_method)
            
            # 转换回张量
            resized_np = np.array(resized_pil).astype(np.float32) / 255.0
            if resized_np.ndim == 2:
                resized_np = resized_np[:, :, np.newaxis]  # 添加通道维度
            elif resized_np.ndim == 3 and resized_np.shape[2] != image.shape[3]:
                # 调整通道数以匹配原始图像
                if image.shape[3] == 3 and resized_np.shape[2] == 4:
                    resized_np = resized_np[:, :, :3]  # 移除alpha通道
                elif image.shape[3] == 4 and resized_np.shape[2] == 3:
                    # 添加alpha通道
                    alpha = np.ones((resized_np.shape[0], resized_np.shape[1], 1), dtype=np.float32)
                    resized_np = np.concatenate([resized_np, alpha], axis=2)
                elif image.shape[3] == 1:
                    resized_np = resized_np.mean(axis=2, keepdims=True)  # 转为灰度
            
            resized_tensor = torch.from_numpy(resized_np).to(device=device, dtype=dtype)
            scaled_images.append(resized_tensor)
        
        return torch.stack(scaled_images)
    
    def _pad_image(self, image, target_width, target_height):
        """填充图像到目标尺寸"""
        
        batch_size, orig_height, orig_width, channels = image.shape
        
        if orig_width == target_width and orig_height == target_height:
            return image
        
        device = image.device
        dtype = image.dtype
        
        # 创建目标尺寸的黑色图像
        padded = torch.zeros((batch_size, target_height, target_width, channels), 
                           device=device, dtype=dtype)
        
        # 计算居中位置和裁剪/填充参数
        if orig_width <= target_width and orig_height <= target_height:
            # 原图小于目标尺寸，需要填充
            start_x = (target_width - orig_width) // 2
            start_y = (target_height - orig_height) // 2
            
            # 复制整个原图到目标位置
            padded[:, start_y:start_y+orig_height, start_x:start_x+orig_width, :] = image
        else:
            # 原图大于目标尺寸，需要居中裁剪然后放置
            # 计算原图的裁剪区域
            crop_start_x = max(0, (orig_width - target_width) // 2)
            crop_start_y = max(0, (orig_height - target_height) // 2)
            
            # 计算实际复制的尺寸
            copy_width = min(orig_width, target_width)
            copy_height = min(orig_height, target_height)
            
            # 计算在目标图像中的放置位置
            pad_start_x = max(0, (target_width - copy_width) // 2)
            pad_start_y = max(0, (target_height - copy_height) // 2)
            
            # 从原图裁剪并复制到目标位置
            padded[:, pad_start_y:pad_start_y+copy_height, pad_start_x:pad_start_x+copy_width, :] = \
                image[:, crop_start_y:crop_start_y+copy_height, crop_start_x:crop_start_x+copy_width, :]
        
        return padded
    
    def _center_crop_image(self, image, target_width, target_height):
        """居中裁剪图像"""
        
        batch_size, orig_height, orig_width, channels = image.shape
        
        if orig_width == target_width and orig_height == target_height:
            return image
        
        # 计算裁剪起始位置
        start_x = (orig_width - target_width) // 2
        start_y = (orig_height - target_height) // 2
        
        # 确保不会越界
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(start_x + target_width, orig_width)
        end_y = min(start_y + target_height, orig_height)
        
        # 裁剪图像
        cropped = image[:, start_y:end_y, start_x:end_x, :]
        
        # 如果裁剪后尺寸不足，需要填充
        actual_height, actual_width = cropped.shape[1], cropped.shape[2]
        if actual_width < target_width or actual_height < target_height:
            cropped = self._pad_image(cropped, target_width, target_height)
        
        return cropped
    
    def _create_empty_image(self, width, height):
        """创建空的黑色图像"""
        return torch.zeros((1, height, width, 3), dtype=torch.float32)
    
    def _create_white_mask(self, width, height):
        """创建白色遮罩"""
        return torch.ones((1, height, width), dtype=torch.float32)


class MaskScale:
    """
    遮罩缩放节点 - 专门处理遮罩的缩放功能
    
    功能:
    - 专注于遮罩的高质量缩放
    - 支持多种缩放定义方式
    - 支持保持比例或自由缩放
    - 高效的插值算法
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "scale_definition": (["width", "height", "longest_side", "shortest_side", "total_pixels"], {
                    "default": "longest_side"
                }),
                "definition_value": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 999999999,
                    "step": 1
                }),
                "interpolation": (["nearest", "bilinear", "bicubic", "lanczos"], {
                    "default": "lanczos"
                }),
                "keep_proportions": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999999,
                    "step": 1
                }),
                "height": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999999999,
                    "step": 1
                }),
            }
        }
    
    # 返回类型与名称（统一中文显示）
    RETURN_TYPES = ("MASK", "INT", "INT")
    RETURN_NAMES = ("mask", "width", "height")
    FUNCTION = "scale_mask"
    CATEGORY = "🎨QING/遮罩处理"
    
    def scale_mask(self, mask, scale_definition, definition_value, interpolation, keep_proportions, width=0, height=0):
        """
        缩放遮罩尺寸
        - 遮罩: 输入遮罩 (Tensor: [B,H,W])
        - scale_definition: 缩放定义：width/height/longest_side/shortest_side/total_pixels
        - definition_value: 定义数值（与 scale_definition 对应）
        - interpolation: interpolation：nearest/bilinear/bicubic/lanczos
        - keep_proportions: 是否保持纵横比
        - width/height: 指定目标尺寸（优先于 scale_definition）
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
        if width > 0 and height > 0:
            target_width = max(1, width)
            target_height = max(1, height)
        else:
            # 根据缩放方式计算目标尺寸
            orig_pixels = orig_height * orig_width
            
            if scale_definition == "width":
                target_width = definition_value
                if keep_proportions:
                    target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                else:
                    target_height = orig_height
                    
            elif scale_definition == "height":
                target_height = definition_value
                if keep_proportions:
                    target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                else:
                    target_width = orig_width
                    
            elif scale_definition == "longest_side":
                if orig_height >= orig_width:
                    target_height = definition_value
                    if keep_proportions:
                        target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                    else:
                        target_width = orig_width
                else:
                    target_width = definition_value
                    if keep_proportions:
                        target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                    else:
                        target_height = orig_height
                        
            elif scale_definition == "shortest_side":
                if orig_height <= orig_width:
                    target_height = definition_value
                    if keep_proportions:
                        target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                    else:
                        target_width = orig_width
                else:
                    target_width = definition_value
                    if keep_proportions:
                        target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                    else:
                        target_height = orig_height
                        
            elif scale_definition == "total_pixels":
                # 依据总像素计算缩放因子
                scale_factor = (definition_value / orig_pixels) ** 0.5
                target_width = max(1, int(round(orig_width * scale_factor)))
                target_height = max(1, int(round(orig_height * scale_factor)))
                
                # 若keep_proportions，细调以更接近目标像素
                if keep_proportions:
                    actual_pixels = target_width * target_height
                    if abs(actual_pixels - definition_value) / definition_value > 0.1:
                        alternative_width = max(1, int(round((definition_value * orig_width / orig_height) ** 0.5)))
                        alternative_height = max(1, int(round(definition_value / alternative_width)))
                        if abs(alternative_width * alternative_height - definition_value) < abs(actual_pixels - definition_value):
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


# 节点注册
NODE_CLASS_MAPPINGS = {
    "Imagesizescaling": Imagesizescaling,
    "MaskScale": MaskScale
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Imagesizescaling": "图像缩放",
    "MaskScale": "遮罩缩放"
}
