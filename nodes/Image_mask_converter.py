import torch
import numpy as np

class ImageMaskConverter:
    """
    图像与遮罩转换节点
    功能：自动检测输入类型，实现图像与遮罩之间的相互转换
    """
    
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

    CATEGORY = "image/processing"
    RETURN_TYPES = ("MASK", "MASK", "IMAGE", "IMAGE")
    RETURN_NAMES = ("mask1", "mask2", "image1", "image2")
    FUNCTION = "convert"
    OUTPUT_NODE = False

    def convert(self, channel, image1=None, image2=None, mask1=None, mask2=None):
        """
        主转换函数：根据输入类型自动执行转换
        """
        # 处理第一组输入
        result_1 = self._process_single_pair(image1, mask1, channel)
        
        # 处理第二组输入
        result_2 = self._process_single_pair(image2, mask2, channel)
        
        return (result_1[1], result_2[1], result_1[0], result_2[0])
    
    def _process_single_pair(self, image, mask, channel):
        """
        处理单组图像/遮罩输入
        """
        if image is not None and mask is not None:
            # 同时有图像和遮罩输入，返回原样
            return (image, mask)
        elif image is not None:
            # 只有图像输入，转换为遮罩
            converted_mask = self.image_to_mask(image, channel)
            return (image, converted_mask)
        elif mask is not None:
            # 只有遮罩输入，转换为图像
            converted_image = self.mask_to_image(mask, channel)
            return (converted_image, mask)
        else:
            # 没有有效输入，返回空张量
            empty_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            empty_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
            return (empty_image, empty_mask)
    
    def image_to_mask(self, image, channel):
        """
        将图像转换为遮罩
        """
        # 确保图像在CPU上并转换为numpy数组
        image_np = image.cpu().numpy()
        
        # 确定通道索引
        channel_map = {"red": 0, "green": 1, "blue": 2, "alpha": 3}
        channel_idx = channel_map[channel]
        
        # 检查通道是否存在
        if channel_idx == 3 and image_np.shape[3] < 4:
            # 没有alpha通道，创建全白遮罩
            masks = np.ones(image_np.shape[:3], dtype=np.float32)
        elif channel_idx < image_np.shape[3]:
            # 提取指定通道
            masks = image_np[:, :, :, channel_idx].astype(np.float32)
        else:
            # 通道不存在，使用红色通道作为备用
            masks = image_np[:, :, :, 0].astype(np.float32)
        
        # 转换为torch张量并确保正确的设备
        return torch.from_numpy(masks).to(image.device)
    
    def mask_to_image(self, mask, channel):
        """
        将遮罩转换为图像
        """
        # 确保遮罩在CPU上并转换为numpy数组
        mask_np = mask.cpu().numpy()
        
        # 处理遮罩维度
        if len(mask_np.shape) == 4 and mask_np.shape[1] == 1:
            mask_np = mask_np[:, 0, :, :]
        
        # 确定通道索引
        channel_map = {"red": 0, "green": 1, "blue": 2, "alpha": 3}
        channel_idx = channel_map[channel]
        
        # 获取形状信息
        batch_size, height, width = mask_np.shape
        
        # 创建RGBA图像
        images = np.zeros((batch_size, height, width, 4), dtype=np.float32)
        
        # 将遮罩值复制到指定通道
        images[:, :, :, channel_idx] = mask_np
        
        # 非alpha通道时设置alpha为不透明
        if channel_idx != 3:
            images[:, :, :, 3] = 1.0
        
        # 转换为torch张量并确保正确的设备
        return torch.from_numpy(images).to(mask.device)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageMaskConverter": ImageMaskConverter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMaskConverter": "图像与遮罩转换"
}