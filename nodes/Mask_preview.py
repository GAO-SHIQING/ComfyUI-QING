import torch
import torch.nn.functional as F
import numpy as np
import os
import time
import folder_paths
from PIL import Image

class ImageMaskPreview:
    """
    遮罩预览节点 - 实现图像和遮罩的混合预览
    
    功能:
    - 支持图像和遮罩的混合预览
    - 可设置遮罩的透明程度 (0-100)
    - 可自由选择遮罩的呈现颜色 (黑白赤橙黄绿青蓝紫)
    - 支持单端口输入模式
    
    使用场景:
    1. 只输入图像: 显示原始图像
    2. 只输入遮罩: 显示彩色遮罩预览
    3. 同时输入图像和遮罩: 显示混合预览效果
    """
    
    def __init__(self):
        """初始化颜色映射"""
        # 定义九种颜色 (RGB值，范围0-1)
        self.color_map = {
            "黑": [0.0, 0.0, 0.0],      # 黑色
            "白": [1.0, 1.0, 1.0],      # 白色
            "赤": [1.0, 0.0, 0.0],      # 红色
            "橙": [1.0, 0.5, 0.0],      # 橙色
            "黄": [1.0, 1.0, 0.0],      # 黄色
            "绿": [0.0, 1.0, 0.0],      # 绿色
            "青": [0.0, 1.0, 1.0],      # 青色
            "蓝": [0.0, 0.0, 1.0],      # 蓝色
            "紫": [0.8, 0.0, 1.0],      # 紫色
        }
    
    @classmethod
    def INPUT_TYPES(cls):
        """定义节点的输入参数"""
        return {
            "required": {
                # 遮罩透明程度 (0-100)
                "mask_alpha": ("INT", {
                    "default": 50,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "display": "slider",
                    "description": "遮罩透明程度 (0=完全透明, 100=完全不透明)"
                }),
                # 遮罩颜色选择
                "mask_color": (["黑", "白", "赤", "橙", "黄", "绿", "青", "蓝", "紫"], {
                    "default": "紫",
                    "description": "遮罩显示颜色"
                }),
            },
            "optional": {
                # 图像输入 (可选)
                "image": ("IMAGE", {
                    "default": None,
                    "description": "输入图像"
                }),
                # 遮罩输入 (可选)
                "mask": ("MASK", {
                    "default": None,
                    "description": "输入遮罩"
                }),
            },
        }
    
    # 节点信息
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("preview",)
    FUNCTION = "preview_mask"
    CATEGORY = "QING/遮罩处理"
    OUTPUT_NODE = True  # 输出节点，具备预览功能
    
    def preview_mask(self, mask_alpha, mask_color, image=None, mask=None):
        """
        主处理函数：实现遮罩预览功能
        
        参数:
            mask_alpha: 遮罩透明程度 (0-100)
            mask_color: 遮罩颜色选择
            image: 输入图像 (可选)
            mask: 输入遮罩 (可选)
            
        返回:
            dict: 包含输出图像和UI预览信息
        """
        # 调试信息：记录输入状态（可以注释掉）
        # print(f"遮罩预览节点输入状态: image={'有' if image is not None else '无'}, mask={'有' if mask is not None else '无'}")
        # if mask is not None:
        #     print(f"接收到的遮罩信息: 类型={type(mask)}, 形状={mask.shape if hasattr(mask, 'shape') else '未知'}")
        
        # 验证输入
        if image is None and mask is None:
            # 创建一个带提示的占位符图像
            preview_tensor = self._create_placeholder_image("无输入")
        else:
            # 验证和清理参数
            mask_alpha = max(0, min(100, int(mask_alpha)))  # 确保在有效范围内
            if mask_color not in self.color_map:
                mask_color = "紫"
            color_rgb = self.color_map[mask_color]
            
            # 转换透明程度 (0-100 -> 0.0-1.0)
            alpha = mask_alpha / 100.0
            
            # 处理不同的输入组合
            if image is not None and mask is not None:
                # 同时有图像和遮罩 - 显示混合预览
                preview_tensor = self._preview_image_mask_blend(image, mask, color_rgb, alpha, mask_color, mask_alpha)
                
            elif image is not None:
                # 只有图像 - 显示原始图像
                preview_tensor = self._preview_image_only(image)
                
            elif mask is not None:
                # 只有遮罩 - 显示彩色遮罩预览
                preview_tensor = self._preview_mask_only(mask, color_rgb, mask_color)
            else:
                # 默认情况 - 不应该到达这里
                preview_tensor = self._create_placeholder_image("错误")
        
        # 生成预览UI
        preview_ui = self._generate_preview_ui(preview_tensor)
        
        # 返回结果：输出图像 + UI预览信息
        return {"ui": preview_ui, "result": (preview_tensor,)}
    
    def _preview_image_mask_blend(self, image, mask, color_rgb, alpha, mask_color, mask_alpha):
        """处理图像和遮罩的混合预览"""
        try:
            # 确保图像和遮罩在同一设备上
            device = image.device
            mask = mask.to(device)
            
            # 标准化图像到 [0, 1] 范围
            if image.dtype != torch.float32:
                image = image.float()
            if image.max() > 1.0:
                image = image / 255.0
            
            # 标准化遮罩到 [0, 1] 范围
            if mask.dtype != torch.float32:
                mask = mask.float()
            if mask.max() > 1.0:
                mask = mask / 255.0
            
            # 调整遮罩尺寸以匹配图像
            if image.dim() == 4:  # (B, H, W, C)
                batch_size, height, width, channels = image.shape
                
                # 安全地处理不同维度的遮罩
                if mask.dim() == 2:  # (H, W)
                    mask = mask.unsqueeze(0).unsqueeze(-1)  # (1, H, W, 1)
                elif mask.dim() == 3:  # (B, H, W) 或 (H, W, 1)
                    if mask.shape[0] == batch_size and len(mask.shape) == 3:
                        mask = mask.unsqueeze(-1)  # (B, H, W, 1)
                    else:
                        mask = mask.unsqueeze(-1)  # (H, W, 1) -> (H, W, 1, 1)
                        mask = mask.unsqueeze(0)   # (1, H, W, 1)
                elif mask.dim() == 4:  # 已经是正确格式
                    pass
                else:
                    return self._create_placeholder_image("遮罩格式错误")
                
                # 调整遮罩尺寸
                if mask.shape[1] != height or mask.shape[2] != width:
                    mask = F.interpolate(
                        mask.permute(0, 3, 1, 2),  # (B, 1, H, W)
                        size=(height, width),
                        mode='bilinear',
                        align_corners=False
                    ).permute(0, 2, 3, 1)  # (B, H, W, 1)
                
                # 创建彩色遮罩，匹配图像的通道数
                color_tensor = torch.tensor(color_rgb, device=device, dtype=torch.float32)
                
                if channels == 4:  # RGBA图像
                    # 分离RGB和Alpha通道
                    image_rgb = image[:, :, :, :3]  # RGB部分
                    image_alpha = image[:, :, :, 3:4]  # Alpha部分
                    
                    # 创建RGB彩色遮罩
                    colored_mask_rgb = mask * color_tensor  # (B, H, W, 3)
                    
                    # 混合RGB部分
                    blended_rgb = image_rgb * (1 - mask * alpha) + colored_mask_rgb * (mask * alpha)
                    
                    # 保持原始alpha通道（遮罩区域可能需要调整透明度）
                    # 选项1：保持原始alpha
                    blended_alpha = image_alpha
                    
                    # 选项2：在遮罩区域增加不透明度（取消注释使用）
                    # mask_alpha_effect = mask * (1.0 - alpha) + alpha  # 遮罩区域变更不透明
                    # blended_alpha = image_alpha * mask_alpha_effect
                    
                    # 合并RGB和Alpha
                    blended = torch.cat([blended_rgb, blended_alpha], dim=3)
                    
                    # ComfyUI可能需要RGB输出，因此提供选项转换
                    # 如果预览异常，可以尝试转换为RGB
                    use_rgb_output = True  # 设为True强制输出RGB，False保持RGBA
                    
                    if use_rgb_output:
                        # 使用alpha混合将RGBA转换为RGB
                        alpha_channel = blended[:, :, :, 3:4]
                        rgb_part = blended[:, :, :, :3]
                        
                        # 选择转换方案
                        use_alpha_enhancement = False  # 设为True使用alpha增强，False直接使用RGB
                        
                        if use_alpha_enhancement:
                            # 方案1：强制遮罩区域为不透明，避免被白色背景稀释
                            enhanced_alpha = torch.where(mask > 0.1, torch.ones_like(alpha_channel), alpha_channel)
                            # Alpha混合公式：result = foreground * alpha + background * (1 - alpha)
                            blended = rgb_part * enhanced_alpha + torch.ones_like(rgb_part) * (1 - enhanced_alpha)
                        else:
                            # 方案2：直接跳过alpha混合，保持RGB结果（推荐）
                            blended = rgb_part
                    
                elif channels == 3:  # RGB图像
                    # 为RGB图像创建3通道彩色遮罩
                    colored_mask = mask * color_tensor  # (B, H, W, 3)
                    
                    # 混合图像和遮罩
                    blended = image * (1 - mask * alpha) + colored_mask * (mask * alpha)
                else:
                    return self._create_placeholder_image("不支持的图像通道数")
                
                # 确保输出在 [0, 1] 范围内
                blended = torch.clamp(blended, 0.0, 1.0)
                return blended
                
            else:
                return self._create_placeholder_image("图像格式错误")
                
        except Exception as e:
            return self._create_placeholder_image("处理失败")
    
    def _preview_image_only(self, image):
        """处理只有图像的情况"""
        try:
            if image.dim() == 4:  # (B, H, W, C)
                # 确保图像在 [0, 1] 范围内
                if image.max() > 1.0:
                    image = image / 255.0
                image = torch.clamp(image, 0.0, 1.0)
                
                # 检查是否为RGBA图像，如果是则转换为RGB以便显示
                batch_size, height, width, channels = image.shape
                
                if channels == 4:  # RGBA图像
                    # 使用alpha混合将RGBA转换为RGB（白色背景）
                    alpha_channel = image[:, :, :, 3:4]
                    rgb_part = image[:, :, :, :3]
                    # Alpha混合公式：result = foreground * alpha + background * (1 - alpha)
                    image = rgb_part * alpha_channel + torch.ones_like(rgb_part) * (1 - alpha_channel)
                elif channels == 3:  # RGB图像
                    pass  # 直接返回
                else:
                    return self._create_placeholder_image("不支持的图像通道数")
                
                return image
            else:
                return self._create_placeholder_image("图像维度错误")
                
        except Exception as e:
            return self._create_placeholder_image("图像处理失败")
    
    def _preview_mask_only(self, mask, color_rgb, mask_color):
        """处理只有遮罩的情况"""
        try:
            # 确保遮罩在同一设备上
            device = mask.device
            
            # 标准化遮罩到 [0, 1] 范围
            if mask.dtype != torch.float32:
                mask = mask.float()
            if mask.max() > 1.0:
                mask = mask / 255.0
            
            # 检测是否为全零遮罩或极小值遮罩
            mask_max = torch.max(mask).item()
            mask_sum = torch.sum(mask).item()
            mask_mean = torch.mean(mask).item()
            
            # 更严格的全零检测
            is_effectively_zero = (mask_max < 1e-6 and mask_sum < 1e-6 and mask_mean < 1e-6)
            
            if is_effectively_zero:
                # 全零遮罩：创建一个带说明的可视化图像
                return self._create_empty_mask_visualization(mask.shape, device, mask_color)
            
            # 获取遮罩尺寸并转换为 (B, H, W, C) 格式
            if mask.dim() == 2:  # (H, W)
                height, width = mask.shape
                mask = mask.unsqueeze(0).unsqueeze(-1)  # (1, H, W, 1)
            elif mask.dim() == 3:  # (H, W, 1) 或 (1, H, W)
                if mask.shape[0] == 1:
                    height, width = mask.shape[1], mask.shape[2]
                    mask = mask.permute(1, 2, 0).unsqueeze(0)  # (1, H, W, 1)
                else:
                    height, width = mask.shape[0], mask.shape[1]
                    mask = mask.unsqueeze(0).unsqueeze(-1)  # (1, H, W, 1)
            else:
                pass  # 处理不常见的遮罩维度
            
            # 创建彩色遮罩
            color_tensor = torch.tensor(color_rgb, device=device, dtype=torch.float32)
            colored_mask = mask * color_tensor  # (1, H, W, 3)
            
            # 确保输出在 [0, 1] 范围内
            colored_mask = torch.clamp(colored_mask, 0.0, 1.0)
            
            # 如果着色后仍然是全零，使用备用可视化
            if torch.max(colored_mask).item() < 1e-6:
                return self._create_empty_mask_visualization(mask.shape, device, mask_color)
            
            return colored_mask
            
        except Exception as e:
            return self._create_placeholder_image("遮罩处理失败")
    
    def _generate_preview_ui(self, preview_tensor):
        """生成预览UI信息"""
        try:
            # 将tensor转换为可预览的图像
            preview_image = self._tensor_to_pil(preview_tensor)
            
            # 保存临时预览图像
            temp_path, subfolder = self._save_temp_preview(preview_image)
            
            # 返回UI结构
            return {"images": [{"filename": os.path.basename(temp_path), "subfolder": subfolder, "type": "output"}]}
            
        except Exception as e:
            return {"images": []}
    
    def _tensor_to_pil(self, tensor):
        """将tensor转换为PIL图像"""
        try:
            # 确保tensor在CPU上
            if tensor.is_cuda:
                tensor = tensor.cpu()
            
            # 转换为numpy数组
            if tensor.dim() == 4:
                # (B, H, W, C) -> (H, W, C)
                array = tensor[0].numpy()
            else:
                array = tensor.numpy()
            
            # 确保值在[0, 1]范围内
            array = np.clip(array, 0.0, 1.0)
            
            # 转换为0-255范围
            array = (array * 255).astype(np.uint8)
            
            # 创建PIL图像
            return Image.fromarray(array, 'RGB')
            
        except Exception as e:
            # 返回一个64x64的黑色图像
            return Image.new('RGB', (64, 64), (0, 0, 0))
    
    def _create_placeholder_image(self, text="占位符"):
        """创建带文字的占位符图像"""
        try:
            # 创建一个128x128的灰色图像
            device = torch.device("cpu")
            size = 128
            
            # 创建灰色背景 (RGB: 0.5, 0.5, 0.5)
            placeholder = torch.full((1, size, size, 3), 0.5, dtype=torch.float32, device=device)
            
            return placeholder
            
        except Exception as e:
            # 最后的备用方案
            return torch.zeros((1, 64, 64, 3), dtype=torch.float32)
    
    def _create_empty_mask_visualization(self, mask_shape, device, mask_color):
        """为全零遮罩创建可视化图像"""
        try:
            # 获取遮罩的实际尺寸
            if len(mask_shape) == 2:  # (H, W)
                height, width = mask_shape
            elif len(mask_shape) == 3:  # (B, H, W) 或 (H, W, 1)
                if mask_shape[0] == 1:
                    height, width = mask_shape[1], mask_shape[2]
                else:
                    height, width = mask_shape[0], mask_shape[1]
            else:
                # 使用默认尺寸
                height, width = 256, 256
            
            # 创建一个棋盘格模式来表示"空遮罩"
            # 使用低对比度的棋盘格，便于区分和占位符图像
            checkboard_size = max(8, min(height, width) // 16)  # 动态调整棋盘格大小
            
            # 创建棋盘格模式
            y_indices = torch.arange(height, device=device).float()
            x_indices = torch.arange(width, device=device).float()
            
            y_grid = (y_indices // checkboard_size) % 2
            x_grid = (x_indices // checkboard_size) % 2
            
            # 创建棋盘格：XOR操作产生交替模式
            checkboard = (y_grid.unsqueeze(1) + x_grid.unsqueeze(0)) % 2
            
            # 创建低对比度的灰色棋盘格 (0.3 和 0.4 之间)
            checkboard_intensity = 0.3 + checkboard * 0.1
            
            # 转换为 (1, H, W, 3) 格式
            visualization = checkboard_intensity.unsqueeze(0).unsqueeze(-1).repeat(1, 1, 1, 3)
            
            # 添加边框指示这是空遮罩
            border_width = max(1, min(height, width) // 64)
            if border_width > 0:
                # 上下边框
                visualization[0, :border_width, :, :] = 0.6
                visualization[0, -border_width:, :, :] = 0.6
                # 左右边框
                visualization[0, :, :border_width, :] = 0.6
                visualization[0, :, -border_width:, :] = 0.6
            
            return visualization.to(device)
            
        except Exception as e:
            # 如果出错，返回简单的灰色图像
            return torch.full((1, 128, 128, 3), 0.4, dtype=torch.float32, device=device)
    
    def _save_temp_preview(self, pil_image):
        """保存临时预览图像（仅用于UI显示）"""
        try:
            # 获取ComfyUI的输出目录
            output_dir = folder_paths.get_output_directory()
            
            # 确保目录存在
            if not os.path.exists(output_dir):
                return "", ""
            
            # 创建唯一的临时文件名
            timestamp = int(time.time() * 1000)
            instance_id = id(self) % 10000  # 简化ID
            temp_filename = f"mask_preview_{timestamp}_{instance_id}.png"
            temp_path = os.path.join(output_dir, temp_filename)
            
            # 保存预览图像
            pil_image.save(temp_path, "PNG", optimize=True, quality=95)
            
            return temp_path, ""
            
        except Exception as e:
            return "", ""

# 注册节点
NODE_CLASS_MAPPINGS = {
    "ImageMaskPreview": ImageMaskPreview
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageMaskPreview": "图像遮罩预览"
}
