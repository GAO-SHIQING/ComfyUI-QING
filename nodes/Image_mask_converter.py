import torch
import numpy as np

class ImageMaskConverter:
    """
    图像与遮罩转换节点
    功能：独立的双向转换，每个输入对应特定输出
    - image1 → mask1 (提取指定通道)
    - image2 → mask2 (提取指定通道)  
    - mask1 → image1 (转换为灰度图像)
    - mask2 → image2 (转换为灰度图像)
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

    CATEGORY = "自定义/图像"
    RETURN_TYPES = ("MASK", "MASK", "IMAGE", "IMAGE")
    RETURN_NAMES = ("mask1", "mask2", "image1", "image2")
    FUNCTION = "convert"
    OUTPUT_NODE = False

    def convert(self, channel, image1=None, image2=None, mask1=None, mask2=None):
        """
        主转换函数：实现独立的输入输出对应关系
        - image1 → mask1 (图像转遮罩)
        - image2 → mask2 (图像转遮罩)  
        - mask1 → image1 (遮罩转图像)
        - mask2 → image2 (遮罩转图像)
        """
        # 验证channel参数
        valid_channels = ["red", "green", "blue", "alpha"]
        if channel not in valid_channels:
            raise ValueError(f"无效的通道参数: {channel}，必须是 {valid_channels} 中的一个")
        
        # 独立处理每个输入，生成对应的输出
        # image1 → mask1
        output_mask1 = self._convert_image_to_mask(image1, channel) if image1 is not None else self._create_empty_mask()
        
        # image2 → mask2  
        output_mask2 = self._convert_image_to_mask(image2, channel) if image2 is not None else self._create_empty_mask()
        
        # mask1 → image1
        output_image1 = self._convert_mask_to_image(mask1, channel) if mask1 is not None else self._create_empty_image()
        
        # mask2 → image2
        output_image2 = self._convert_mask_to_image(mask2, channel) if mask2 is not None else self._create_empty_image()
        
        return (output_mask1, output_mask2, output_image1, output_image2)
    
    def _convert_image_to_mask(self, image, channel):
        """将图像转换为遮罩"""
        return self.image_to_mask(image, channel)
    
    def _convert_mask_to_image(self, mask, channel):
        """将遮罩转换为黑白图像（不使用通道参数）"""
        return self.mask_to_grayscale_image(mask)
    
    def _create_empty_mask(self):
        """创建空遮罩"""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        return torch.zeros((1, 64, 64), dtype=torch.float32, device=device)
    
    def _create_empty_image(self):
        """创建空图像"""
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        return torch.zeros((1, 64, 64, 3), dtype=torch.float32, device=device)
    
    def image_to_mask(self, image, channel):
        """
        将图像转换为遮罩
        """
        # 验证输入
        if image is None or image.numel() == 0:
            raise ValueError("输入图像不能为空")
        
        # 验证数据类型
        if not torch.is_floating_point(image):
            raise ValueError("输入图像必须是浮点类型")
        
        # 验证值范围（ComfyUI图像通常在0-1范围内）
        if torch.any(image < 0) or torch.any(image > 1):
            # 警告但不抛出异常，因为有些图像可能超出0-1范围
            print(f"警告：图像值超出标准范围 [0,1]，实际范围 [{image.min():.3f}, {image.max():.3f}]")
        
        # 保存原始设备信息
        original_device = image.device
        
        # 确保图像在CPU上并转换为numpy数组
        image_np = image.cpu().numpy()
        
        # 验证图像维度
        if len(image_np.shape) != 4:
            raise ValueError(f"图像必须是4维张量 (batch, height, width, channels)，当前维度: {image_np.shape}")
        
        # 确定通道索引
        channel_map = {"red": 0, "green": 1, "blue": 2, "alpha": 3}
        channel_idx = channel_map[channel]
        
        batch_size, height, width, num_channels = image_np.shape
        
        # 检查通道是否存在
        if channel_idx == 3 and num_channels < 4:
            # 没有alpha通道，创建全白遮罩
            masks = np.ones((batch_size, height, width), dtype=np.float32)
        elif channel_idx < num_channels:
            # 提取指定通道
            masks = image_np[:, :, :, channel_idx].astype(np.float32)
        else:
            # 通道不存在的处理
            if num_channels > 0:
                # 使用灰度转换作为备用方案
                if num_channels >= 3:
                    # RGB图像：使用标准灰度转换公式 (0.299*R + 0.587*G + 0.114*B)
                    masks = (0.299 * image_np[:, :, :, 0] + 
                            0.587 * image_np[:, :, :, 1] + 
                            0.114 * image_np[:, :, :, 2]).astype(np.float32)
                else:
                    # 单通道图像：直接使用该通道
                    masks = image_np[:, :, :, 0].astype(np.float32)
            else:
                # 完全没有通道，创建零遮罩
                masks = np.zeros((batch_size, height, width), dtype=np.float32)
        
        # 转换为torch张量并确保正确的设备
        return torch.from_numpy(masks).to(original_device)
    
    def mask_to_image(self, mask, channel):
        """
        将遮罩转换为图像
        """
        # 验证输入
        if mask is None or mask.numel() == 0:
            raise ValueError("输入遮罩不能为空")
        
        # 验证数据类型
        if not torch.is_floating_point(mask):
            raise ValueError("输入遮罩必须是浮点类型")
        
        # 验证值范围（遮罩应该在0-1范围内）
        if torch.any(mask < 0) or torch.any(mask > 1):
            print(f"警告：遮罩值超出标准范围 [0,1]，实际范围 [{mask.min():.3f}, {mask.max():.3f}]")
        
        # 保存原始设备信息
        original_device = mask.device
        
        # 确保遮罩在CPU上并转换为numpy数组
        mask_np = mask.cpu().numpy()
        
        # 标准化遮罩维度为3维 (batch, height, width)
        if len(mask_np.shape) == 2:
            # 添加批次维度
            mask_np = mask_np[np.newaxis, :, :]
        elif len(mask_np.shape) == 4:
            # 移除多余的通道维度
            if mask_np.shape[1] == 1:
                mask_np = mask_np[:, 0, :, :]
            elif mask_np.shape[3] == 1:
                mask_np = mask_np[:, :, :, 0]
            else:
                raise ValueError(f"不支持的4维遮罩形状: {mask_np.shape}")
        elif len(mask_np.shape) != 3:
            raise ValueError(f"遮罩维度必须是2、3或4维，当前维度: {mask_np.shape}")
        
        # 确定通道索引
        channel_map = {"red": 0, "green": 1, "blue": 2, "alpha": 3}
        channel_idx = channel_map[channel]
        
        # 获取形状信息
        batch_size, height, width = mask_np.shape
        
        if channel_idx < 3:
            # RGB通道：创建RGB图像，只在指定通道设置值
            images = np.zeros((batch_size, height, width, 3), dtype=np.float32)
            images[:, :, :, channel_idx] = mask_np
        else:
            # Alpha通道：创建RGBA图像或灰度效果
            # 由于ComfyUI通常使用RGB格式，这里创建灰度图像
            images = np.zeros((batch_size, height, width, 3), dtype=np.float32)
            # 将遮罩值复制到所有RGB通道创建灰度效果
            for i in range(3):
                images[:, :, :, i] = mask_np
        
        # 转换为torch张量并确保正确的设备
        return torch.from_numpy(images).to(original_device)

    def mask_to_grayscale_image(self, mask):
        """
        将遮罩转换为灰度图像（黑白图像）
        """
        # 验证输入
        if mask is None or mask.numel() == 0:
            raise ValueError("输入遮罩不能为空")
        
        # 验证数据类型
        if not torch.is_floating_point(mask):
            raise ValueError("输入遮罩必须是浮点类型")
        
        # 验证值范围（遮罩应该在0-1范围内）
        if torch.any(mask < 0) or torch.any(mask > 1):
            print(f"警告：遮罩值超出标准范围 [0,1]，实际范围 [{mask.min():.3f}, {mask.max():.3f}]")
        
        # 保存原始设备信息
        original_device = mask.device
        
        # 确保遮罩在CPU上并转换为numpy数组
        mask_np = mask.cpu().numpy()
        
        # 标准化遮罩维度为3维 (batch, height, width)
        if len(mask_np.shape) == 2:
            # 添加批次维度
            mask_np = mask_np[np.newaxis, :, :]
        elif len(mask_np.shape) == 4:
            # 移除多余的通道维度
            if mask_np.shape[1] == 1:
                mask_np = mask_np[:, 0, :, :]
            elif mask_np.shape[3] == 1:
                mask_np = mask_np[:, :, :, 0]
            else:
                raise ValueError(f"不支持的4维遮罩形状: {mask_np.shape}")
        elif len(mask_np.shape) != 3:
            raise ValueError(f"遮罩维度必须是2、3或4维，当前维度: {mask_np.shape}")
        
        # 获取形状信息
        batch_size, height, width = mask_np.shape
        
        # 创建灰度图像：所有RGB通道都设置为相同的遮罩值
        images = np.zeros((batch_size, height, width, 3), dtype=np.float32)
        for i in range(3):
            images[:, :, :, i] = mask_np
        
        # 转换为torch张量并确保正确的设备
        return torch.from_numpy(images).to(original_device)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageMaskConverter": ImageMaskConverter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMaskConverter": "图像与遮罩转换"
}