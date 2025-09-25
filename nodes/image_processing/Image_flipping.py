# -*- coding: utf-8 -*-
import torch
import numpy as np
from PIL import Image


class ImageRotation:
    """
    图像旋转节点
    功能：对输入图像进行旋转操作，支持多种旋转模式、角度控制、插值算法和填充选项
    透明度处理：当"是否填充"设置为透明时，输出带有透明通道的RGBA图像
    """
    
    def __init__(self):
        """初始化颜色映射"""
        # 定义九种填充颜色 (RGB值，范围0-255)
        self.fill_colors = {
            "黑": (0, 0, 0),          # 黑色
            "白": (255, 255, 255),    # 白色
            "赤": (255, 0, 0),        # 红色
            "橙": (255, 128, 0),      # 橙色
            "黄": (255, 255, 0),      # 黄色
            "绿": (0, 255, 0),        # 绿色
            "青": (0, 255, 255),      # 青色
            "蓝": (0, 0, 255),        # 蓝色
            "紫": (204, 0, 255),      # 紫色
        }
        
        # PIL插值算法映射
        self.resample_methods = {
            "lanczos": Image.Resampling.LANCZOS,
            "bicubic": Image.Resampling.BICUBIC,
            "hamming": Image.Resampling.HAMMING,
            "bilinear": Image.Resampling.BILINEAR,
            "box": Image.Resampling.BOX,
            "nearest": Image.Resampling.NEAREST,
        }
    
    @classmethod
    def INPUT_TYPES(cls):
        """定义节点的输入参数"""
        return {
            "required": {
                "image": ("IMAGE",),
                "rotation_mode": (["正向旋转", "反向旋转"], {
                    "default": "正向旋转"
                }),
                "rotation_angle": ("INT", {
                    "default": 90,
                    "min": 0,
                    "max": 360,
                    "step": 1,
                    "display": "slider"
                }),
                "interpolation": (["lanczos", "bicubic", "hamming", "bilinear", "box", "nearest"], {
                    "default": "lanczos"
                }),
                "enable_fill": ("BOOLEAN", {
                    "default": False,
                    "label_on": "填充",
                    "label_off": "透明"
                }),
                "fill_color": (["黑", "白", "赤", "橙", "黄", "绿", "青", "蓝", "紫"], {
                    "default": "黑"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "rotate_image"
    CATEGORY = "🎨QING/图像处理"

    def rotate_image(self, image, rotation_mode, rotation_angle, interpolation, enable_fill, fill_color):
        """
        旋转图像
        
        参数:
            image: 输入图像张量 [batch, height, width, channels]
            rotation_mode: 旋转模式 ("正向旋转" 或 "反向旋转")
            rotation_angle: 旋转角度 (0-360)
            interpolation: 插值算法
            enable_fill: 是否启用填充
            fill_color: 填充颜色
            
        返回:
            tuple: (旋转后的图像张量, 填充区域遮罩张量)
        """
        try:
            # 如果角度为0或360，直接返回原图像和全零遮罩
            if rotation_angle % 360 == 0:
                # 创建全零遮罩（无填充区域）
                batch_size, height, width = image.shape[:3]
                zero_mask = torch.zeros((batch_size, height, width), dtype=torch.float32, device=image.device)
                return (image, zero_mask)
            
            # 转换输入张量为PIL图像列表
            batch_size = image.shape[0]
            rotated_images = []
            rotation_masks = []
            
            # 确定实际旋转角度
            # PIL的rotate()默认是逆时针旋转，为了让"正向旋转"表现为顺时针，需要取负值
            if rotation_mode == "反向旋转":
                actual_angle = rotation_angle  # 反向旋转 = 逆时针 = PIL的正角度
            else:
                actual_angle = -rotation_angle  # 正向旋转 = 顺时针 = PIL的负角度
            
            # 标准化角度到 -180 到 180 范围，提高旋转精度
            actual_angle = actual_angle % 360
            if actual_angle > 180:
                actual_angle -= 360
            
            # 获取插值方法，处理LANCZOS兼容性问题
            resample_method = self.resample_methods.get(interpolation, Image.Resampling.BICUBIC)
            
            # 对于某些PIL版本，LANCZOS可能不支持某些操作，fallback到BICUBIC
            if interpolation == "lanczos":
                try:
                    # 测试LANCZOS是否可用
                    test_img = Image.new('RGB', (10, 10))
                    test_img.rotate(1, resample=Image.Resampling.LANCZOS)
                    resample_method = Image.Resampling.LANCZOS
                except:
                    resample_method = Image.Resampling.BICUBIC
            
            # 处理每张图像
            for i in range(batch_size):
                # 将张量转换为PIL图像 [H, W, C] -> PIL Image
                img_tensor = image[i]  # [H, W, C]
                
                # 确保张量在0-1范围内，然后转换为0-255
                if img_tensor.max() <= 1.0:
                    img_array = (img_tensor * 255).clamp(0, 255).cpu().numpy().astype(np.uint8)
                else:
                    img_array = img_tensor.clamp(0, 255).cpu().numpy().astype(np.uint8)
                
                # 转换为PIL图像
                if img_array.shape[2] == 3:  # RGB
                    pil_img = Image.fromarray(img_array, 'RGB')
                elif img_array.shape[2] == 4:  # RGBA
                    pil_img = Image.fromarray(img_array, 'RGBA')
                else:
                    # 单通道转换为RGB
                    img_array = np.repeat(img_array, 3, axis=2)
                    pil_img = Image.fromarray(img_array, 'RGB')
                
                # 生成遮罩：首先创建原图对应的全白遮罩
                original_mask = Image.new('L', pil_img.size, 255)  # 全白遮罩表示原图区域
                
                # 旋转原图遮罩以获得填充区域
                rotated_mask = original_mask.rotate(
                    actual_angle,
                    resample=resample_method,
                    expand=True,
                    fillcolor=0  # 填充区域用黑色(0)表示
                )
                
                # 执行旋转
                if enable_fill:
                    # 使用指定颜色填充
                    fill_rgb = self.fill_colors[fill_color]
                    # 如果原图有alpha通道，添加alpha=255
                    if pil_img.mode == 'RGBA':
                        fillcolor = fill_rgb + (255,)
                    else:
                        fillcolor = fill_rgb
                    
                    rotated_pil = pil_img.rotate(
                        actual_angle, 
                        resample=resample_method,
                        expand=True,
                        fillcolor=fillcolor
                    )
                else:
                    # 使用透明填充（alpha通道）
                    if pil_img.mode != 'RGBA':
                        pil_img = pil_img.convert('RGBA')
                    
                    rotated_pil = pil_img.rotate(
                        actual_angle, 
                        resample=resample_method,
                        expand=True,
                        fillcolor=(0, 0, 0, 0)  # 透明填充
                    )
                
                # 处理输出格式（保持透明度或转换为RGB）
                if rotated_pil.mode == 'RGBA':
                    if not enable_fill:
                        # 保持RGBA格式以保留透明度信息
                        rotated_array = np.array(rotated_pil).astype(np.float32) / 255.0
                        rotated_tensor = torch.from_numpy(rotated_array)
                    else:
                        # 填充模式：转换为RGB
                        rotated_pil = rotated_pil.convert('RGB')
                        rotated_array = np.array(rotated_pil).astype(np.float32) / 255.0
                        rotated_tensor = torch.from_numpy(rotated_array)
                else:
                    # 确保为RGB格式
                    if rotated_pil.mode != 'RGB':
                        rotated_pil = rotated_pil.convert('RGB')
                    rotated_array = np.array(rotated_pil).astype(np.float32) / 255.0
                    rotated_tensor = torch.from_numpy(rotated_array)
                
                # 处理遮罩：将遮罩转换为张量
                # 注意：我们需要反转遮罩，使填充区域为白色(1.0)，原图区域为黑色(0.0)
                mask_array = np.array(rotated_mask).astype(np.float32) / 255.0
                # 反转遮罩：原图区域(白色255->1.0)变为0.0，填充区域(黑色0->0.0)变为1.0
                mask_array = 1.0 - mask_array
                mask_tensor = torch.from_numpy(mask_array)
                
                # 确保遮罩与图像在同一设备上
                mask_tensor = mask_tensor.to(device=image.device)
                
                
                rotated_images.append(rotated_tensor)
                rotation_masks.append(mask_tensor)
            
            # 合并批次
            result_tensor = torch.stack(rotated_images, dim=0)
            mask_tensor = torch.stack(rotation_masks, dim=0)
            
            return (result_tensor, mask_tensor)
            
        except Exception as e:
            print(f"图像旋转错误: {e}")
            # 返回原图像和全零遮罩作为fallback
            batch_size, height, width = image.shape[:3]
            fallback_mask = torch.zeros((batch_size, height, width), dtype=torch.float32, device=image.device)
            return (image, fallback_mask)


class ImageFlipping:
    """
    图像翻转节点
    功能：对输入图像进行翻转操作，支持水平翻转和垂直翻转，以及多种插值算法
    透明度处理：自动保持原始图像的透明度信息（如果存在）
    """
    
    def __init__(self):
        """初始化插值算法映射"""
        # PIL插值算法映射
        self.resample_methods = {
            "lanczos": Image.Resampling.LANCZOS,
            "bicubic": Image.Resampling.BICUBIC,
            "hamming": Image.Resampling.HAMMING,
            "bilinear": Image.Resampling.BILINEAR,
            "box": Image.Resampling.BOX,
            "nearest": Image.Resampling.NEAREST,
        }
    
    @classmethod
    def INPUT_TYPES(cls):
        """定义节点的输入参数"""
        return {
            "required": {
                "image": ("IMAGE",),
                "flip_mode": (["水平翻转", "垂直翻转"], {
                    "default": "水平翻转"
                }),
                "interpolation": (["lanczos", "bicubic", "hamming", "bilinear", "box", "nearest"], {
                    "default": "lanczos"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "flip_image"
    CATEGORY = "🎨QING/图像处理"

    def flip_image(self, image, flip_mode, interpolation):
        """
        翻转图像
        
        参数:
            image: 输入图像张量 [batch, height, width, channels]
            flip_mode: 翻转模式 ("水平翻转" 或 "垂直翻转")
            interpolation: 插值算法
            
        返回:
            tuple: (翻转后的图像张量,)
        """
        try:
            # 转换输入张量为PIL图像列表
            batch_size = image.shape[0]
            flipped_images = []
            
            # 获取插值方法（注意：翻转操作本身不需要插值，但为了保持一致性保留此参数）
            resample_method = self.resample_methods.get(interpolation, Image.Resampling.LANCZOS)
            
            # 处理每张图像
            for i in range(batch_size):
                # 将张量转换为PIL图像 [H, W, C] -> PIL Image
                img_tensor = image[i]  # [H, W, C]
                
                # 确保张量在0-1范围内，然后转换为0-255
                if img_tensor.max() <= 1.0:
                    img_array = (img_tensor * 255).clamp(0, 255).cpu().numpy().astype(np.uint8)
                else:
                    img_array = img_tensor.clamp(0, 255).cpu().numpy().astype(np.uint8)
                
                # 转换为PIL图像
                if img_array.shape[2] == 3:  # RGB
                    pil_img = Image.fromarray(img_array, 'RGB')
                elif img_array.shape[2] == 4:  # RGBA
                    pil_img = Image.fromarray(img_array, 'RGBA')
                else:
                    # 单通道转换为RGB
                    img_array = np.repeat(img_array, 3, axis=2)
                    pil_img = Image.fromarray(img_array, 'RGB')
                
                # 执行翻转
                if flip_mode == "水平翻转":
                    flipped_pil = pil_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                elif flip_mode == "垂直翻转":
                    flipped_pil = pil_img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                else:
                    # 默认水平翻转
                    flipped_pil = pil_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                
                # 处理输出格式（保持原始格式的透明度信息）
                if flipped_pil.mode == 'RGBA':
                    # 保持RGBA格式以保留透明度信息
                    flipped_array = np.array(flipped_pil).astype(np.float32) / 255.0
                    flipped_tensor = torch.from_numpy(flipped_array)
                else:
                    # 确保为RGB格式
                    if flipped_pil.mode != 'RGB':
                        flipped_pil = flipped_pil.convert('RGB')
                    flipped_array = np.array(flipped_pil).astype(np.float32) / 255.0
                    flipped_tensor = torch.from_numpy(flipped_array)
                
                flipped_images.append(flipped_tensor)
            
            # 合并批次
            result_tensor = torch.stack(flipped_images, dim=0)
            
            return (result_tensor,)
            
        except Exception as e:
            print(f"图像翻转错误: {e}")
            # 返回原图像作为fallback
            return (image,)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageRotation": ImageRotation,
    "ImageFlipping": ImageFlipping,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageRotation": "图像旋转",
    "ImageFlipping": "图像翻转",
}
