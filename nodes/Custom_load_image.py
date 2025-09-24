# -*- coding: utf-8 -*-
import folder_paths
from PIL import Image, ImageOps, ImageSequence
import numpy as np
import torch
import os
import hashlib
import traceback

# 定义特殊占位符类
class NoOutput:
    """特殊占位符，表示无输出"""
    def __str__(self):
        return "NO_OUTPUT"
    
    def __repr__(self):
        return "NO_OUTPUT"
    
    def __bool__(self):
        return False

# 创建特殊占位符实例
NO_OUTPUT = NoOutput()

# 定义支持的图像格式映射
SUPPORTED_FORMATS = {
    '.png': 'PNG',
    '.jpg': 'JPEG',
    '.jpeg': 'JPEG',
    '.gif': 'GIF',
    '.webp': 'WEBP',
    '.bmp': 'BMP',
    '.tiff': 'TIFF',
    '.tif': 'TIFF',
    '.svg': 'SVG',
    '.ico': 'ICO'
}

class CustomLoadImageWithFormat:
    """
    自定义图像加载器：支持多种格式（含SVG）
    - 对于位图格式，输出 图像/遮罩，SVG口置为占位符
    - 对于SVG格式，输出 SVG 文本，图像/遮罩口置为占位符
    - 额外输出格式信息
    """
    
    @classmethod
    def INPUT_TYPES(s):
        try:
            input_dir = folder_paths.get_input_directory()
            files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
            return {
                "required": {
                    "image": (sorted(files), {"image_upload": True}),
                },
            }
        except Exception as e:
            # Error getting input files
            return {
                "required": {
                    "image": ([], {"image_upload": True}),
                },
            }
    
    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("image", "mask", "svg_content", "format_info")
    FUNCTION = "load_image"
    CATEGORY = "🎨QING/输入输出"
    OUTPUT_NODE = True
    
    
    def load_image(self, image):
        """
        加载图像并根据文件类型决定输出端口
        - 位图：返回(IMAGE, MASK, NO_OUTPUT, FORMAT)
        - SVG：返回(NO_OUTPUT, NO_OUTPUT, SVG_STRING, "SVG")
        """
        try:
            # 获取图像完整路径
            image_path = folder_paths.get_annotated_filepath(image)
            
            if not os.path.exists(image_path):
                return self._create_error_result(f"File not found: {image_path}")
            
            # 获取文件扩展名以确定格式
            file_extension = os.path.splitext(image_path)[1].lower()
            format_info = self._get_format_info(file_extension, image_path)
            
            # 特殊处理SVG格式
            if file_extension == '.svg':
                # 读取SVG文件内容
                try:
                    with open(image_path, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                    
                    # 验证SVG内容
                    if not self._is_valid_svg(svg_content):
                        return self._create_error_result(f"Invalid SVG content: {image_path}", format_info)
                    
                    # 对于SVG，SVG端口输出内容，图像和遮罩端口输出特殊占位符
                    return (NO_OUTPUT, NO_OUTPUT, svg_content, format_info)
                except Exception as e:
                    # Failed to read SVG file
                    return self._create_error_result(f"Failed to read SVG file: {str(e)}", format_info)
            else:
                # 处理其他图像格式
                try:
                    img = Image.open(image_path)
                    # 验证图像
                    img.verify()  # 验证图像完整性
                    img = Image.open(image_path)  # 重新打开已验证的图像
                    
                    # 获取实际格式信息（如果PIL能识别）
                    actual_format = img.format or format_info
                    
                    image_tensor, mask_tensor = self._load_other_formats(img)
                    # 对于非SVG格式，图像和遮罩端口输出内容，SVG端口输出特殊占位符
                    return (image_tensor, mask_tensor, NO_OUTPUT, actual_format)
                except Exception as e:
                    # Failed to load image
                    return self._create_error_result(f"Failed to load image: {str(e)}", format_info)
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            # Error occurred
            traceback.print_exc()
            return self._create_error_result(error_msg, "UNKNOWN")
    
    def _get_format_info(self, file_extension, image_path):
        """获取文件格式信息"""
        format_info = SUPPORTED_FORMATS.get(file_extension, f"UNKNOWN({file_extension})")
        
        # 尝试从文件内容获取更准确的格式信息
        if file_extension in ['.jpg', '.jpeg']:
            # 对于JPEG，可能需要额外检查
            try:
                with open(image_path, 'rb') as f:
                    header = f.read(10)
                    if header.startswith(b'\xff\xd8\xff'):
                        format_info = "JPEG"
                    else:
                        format_info = f"JPEG(?)"
            except:
                pass
        
        return format_info
    
    def _is_valid_svg(self, svg_content):
        """验证SVG内容是否有效"""
        if not svg_content or not isinstance(svg_content, str):
            return False
        
        # 基本检查：包含SVG标签
        svg_content_lower = svg_content.lower()
        return '<svg' in svg_content_lower and '</svg>' in svg_content_lower
    
    def _load_other_formats(self, img):
        """处理非SVG格式的图像"""
        output_images = []
        output_masks = []
        
        # 处理动画图像的所有帧
        for i in ImageSequence.Iterator(img):
            i = ImageOps.exif_transpose(i)
            
            # 处理特殊格式
            if i.mode == 'I':
                i = i.point(lambda p: p * 0.0039215686)  # 将16位转换为8位
            
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            
            # 处理透明度/遮罩
            if 'transparency' in i.info:
                mask = np.array(i.convert('RGBA'))[:,:,3].astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            elif i.mode == 'RGBA':
                mask = np.array(i)[:,:,3].astype(np.float32) / 255.0
                mask = torch.from_numpy(mask)
            elif i.mode == 'LA':
                mask = np.array(i.convert('RGBA'))[:,:,3].astype(np.float32) / 255.0
                mask = torch.from_numpy(mask)
            else:
                mask = torch.zeros((image.shape[1], image.shape[2]), dtype=torch.float32)
            
            output_images.append(image)
            output_masks.append(mask.unsqueeze(0))
        
        if len(output_images) > 1:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]
        
        return (output_image, output_mask)
    
    def _create_error_result(self, error_msg, format_info="UNKNOWN"):
        """创建错误返回结果"""
        print(f"加载错误: {error_msg}")
        # 创建空的图像和遮罩张量
        empty_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
        empty_mask = torch.zeros((1, 64, 64), dtype=torch.float32)
        return (empty_image, empty_mask, NO_OUTPUT, f"ERROR: {error_msg} (Format: {format_info})")
    
    @classmethod
    def IS_CHANGED(s, image):
        try:
            image_path = folder_paths.get_annotated_filepath(image)
            m = hashlib.sha256()
            with open(image_path, 'rb') as f:
                m.update(f.read())
            return m.digest().hex()
        except:
            return str(os.path.getmtime(folder_paths.get_annotated_filepath(image))) if folder_paths.exists_annotated_filepath(image) else ""
    
    @classmethod
    def VALIDATE_INPUTS(s, image):
        if not folder_paths.exists_annotated_filepath(image):
            return "Invalid image: {}".format(image)
        return True

# 节点注册
NODE_CLASS_MAPPINGS = {
    "CustomLoadImageWithFormat": CustomLoadImageWithFormat
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomLoadImageWithFormat": "加载图像(支持SVG)"
}