# -*- coding: utf-8 -*-
import torch

class ImageMaskConverter:
    """图像与遮罩转换节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "channel": (["red", "green", "blue", "alpha"], {"default": "red"}),
            },
            "optional": {
                "image1": ("IMAGE",),
                "image2": ("IMAGE",),
                "mask1": ("MASK",),
                "mask2": ("MASK",),
            }
        }

    CATEGORY = "🎨QING/图像处理"
    RETURN_TYPES = ("MASK", "MASK", "IMAGE", "IMAGE")
    RETURN_NAMES = ("遮罩1", "遮罩2", "图像1", "图像2")
    FUNCTION = "convert"

    def convert(self, channel, image1=None, image2=None, mask1=None, mask2=None):
        """主转换函数"""
        # 图像转遮罩
        output_mask1 = self._image_to_mask(image1, channel) if image1 is not None else self._empty_mask()
        output_mask2 = self._image_to_mask(image2, channel) if image2 is not None else self._empty_mask()
        
        # 遮罩转图像
        output_image1 = self._mask_to_image(mask1) if mask1 is not None else self._empty_image()
        output_image2 = self._mask_to_image(mask2) if mask2 is not None else self._empty_image()
        
        return (output_mask1, output_mask2, output_image1, output_image2)
    
    def _image_to_mask(self, image, channel):
        """图像转遮罩"""
        if len(image.shape) == 4:
            image = image[0]  # 取第一张
        
        height, width, channels = image.shape
        
        if channel == "red" and channels >= 1:
            return image[:, :, 0]
        elif channel == "green" and channels >= 2:
            return image[:, :, 1]  
        elif channel == "blue" and channels >= 3:
            return image[:, :, 2]
        elif channel == "alpha":
            if channels >= 4:
                return image[:, :, 3]
            else:
                # 没有alpha通道时，基于亮度创建遮罩
                if channels >= 3:
                    # RGB转灰度：0.299*R + 0.587*G + 0.114*B
                    gray = 0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]
                    return gray
                else:
                    # 单通道图像直接使用
                    return image[:, :, 0]
        else:
            # 默认返回全白遮罩
            return torch.ones((height, width), dtype=torch.float32, device=image.device)
    
    def _mask_to_image(self, mask):
        """遮罩转灰度图像"""
        if len(mask.shape) == 3:
            mask = mask[0]  # 取第一张
        
        # 创建RGB图像，所有通道都是遮罩值
        height, width = mask.shape
        image = torch.stack([mask, mask, mask], dim=2)
        
        return image.unsqueeze(0)  # 添加batch维度
    
    def _empty_mask(self):
        """空遮罩"""
        return torch.zeros((1, 64, 64), dtype=torch.float32)
    
    def _empty_image(self):
        """空图像"""
        return torch.zeros((1, 64, 64, 3), dtype=torch.float32)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageMaskConverter": ImageMaskConverter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMaskConverter": "图像遮罩转换"
}