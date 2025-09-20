import os
import numpy as np
from PIL import Image
import torch
import folder_paths
import comfy.utils
from io import BytesIO
import cairosvg
import xml.etree.ElementTree as ET
import math
import re

class SVGToImage:
    """
    SVG 转图片（PNG/JPG）节点：提供高级缩放方式与尺寸输出
    - 支持按最长边/最短边/宽/高/总像素定义缩放
    - 支持设置DPI、输出质量、背景色、尺寸对齐倍数
    - 输出图片张量、遮罩、最终宽高
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "svg_input": ("STRING", {
                    "multiline": True,
                    "default": "<svg width='100' height='100' xmlns='http://www.w3.org/2000/svg'><rect width='100' height='100' fill='red'/></svg>"
                }),
                "adjust_size": ("STRING", {
                    "default": "1024",
                    "description": "目标尺寸，WxH 或单个数值（正方形）"
                }),
                "keep_aspect_ratio": (["true", "false"], {
                    "default": "true"
                }),
                "scale_definition": (["longest_side", "shortest_side", "width", "height", "total_pixels"], {
                    "default": "longest_side",
                    "description": "缩放参考定义"
                }),
                "scale_method": (["lanczos", "bicubic", "hamming", "bilinear", "box", "nearest"], {
                    "default": "lanczos"
                }),
                "dpi": ("INT", {
                    "default": 100,
                    "min": 10,
                    "max": 1200,
                    "step": 10
                }),
                "output_format": (["png", "jpg"], {
                    "default": "png"
                }),
                "quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "display": "slider"
                }),
                "background_color": ("STRING", {
                    "default": "",
                    "description": "背景色十六进制，如#FFFFFF；留空为透明"
                }),
            },
            "optional": {
                "multiple_of": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 256,
                    "step": 8,
                    "description": "将宽高约束为该整数倍（0为禁用）"
                }),
                "target_pixels": ("INT", {
                    "default": 1048576,
                    "min": 256,
                    "max": 16777216,  # 4096x4096
                    "step": 1024,
                    "description": "目标总像素（用于 total_pixels 缩放定义）"
                }),
            }
        }

    # 返回类型与中文显示名
    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("图像", "遮罩", "宽度", "高度")
    FUNCTION = "convert_svg"
    CATEGORY = "图像/转换"

    def parse_size_string(self, size_str):
        """解析尺寸字符串（WxH 或单个数值），返回宽和高"""
        try:
            # Handle empty string
            if not size_str or not size_str.strip():
                return 1024, 1024  # Changed from 512, 512
                
            # Remove any whitespace
            size_str = size_str.strip()
            
            # Handle format with 'x' separator
            if 'x' in size_str:
                parts = size_str.split('x')
                if len(parts) == 2:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    return max(16, min(16384, width)), max(16, min(16384, height))
            
            # Handle format with ',' separator
            if ',' in size_str:
                parts = size_str.split(',')
                if len(parts) == 2:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    return max(16, min(16384, width)), max(16, min(16384, height))
            
            # Handle format with '*' separator
            if '*' in size_str:
                parts = size_str.split('*')
                if len(parts) == 2:
                    width = int(parts[0].strip())
                    height = int(parts[1].strip())
                    return max(16, min(16384, width)), max(16, min(16384, height))
            
            # If format is invalid, try to parse as single number
            try:
                size = int(size_str)
                size = max(16, min(16384, size))
                return size, size
            except:
                pass
                
        except Exception as e:
            print(f"Size parsing failed: {str(e)}")
            
        # Fallback to default size
        return 1024, 1024  # Changed from 512, 512

    def parse_svg_dimensions(self, svg_content):
        """直接解析SVG获取原始尺寸（不渲染）"""
        try:
            # Try to parse SVG as XML to get dimensions
            # Remove any XML declarations or doctypes that might cause issues
            cleaned_svg = re.sub(r'<\?xml[^>]*\?>', '', svg_content)
            cleaned_svg = re.sub(r'<!DOCTYPE[^>]*>', '', cleaned_svg)
            
            # Handle malformed SVG with proper error handling
            try:
                root = ET.fromstring(cleaned_svg)
            except ET.ParseError:
                # If XML parsing fails, try to extract dimensions using regex
                width_match = re.search(r'width\s*[=:]\s*["\']?([0-9.]+)', svg_content, re.IGNORECASE)
                height_match = re.search(r'height\s*[=:]\s*["\']?([0-9.]+)', svg_content, re.IGNORECASE)
                
                if width_match and height_match:
                    width = float(width_match.group(1))
                    height = float(height_match.group(1))
                    return max(1, int(width)), max(1, int(height))
                else:
                    return 100, 100
            
            width_attr = root.get('width', '100')
            height_attr = root.get('height', '100')
            viewbox_attr = root.get('viewBox', '')
            
            # Handle viewBox if present (format: "min-x min-y width height")
            if viewbox_attr:
                viewbox_parts = viewbox_attr.split()
                if len(viewbox_parts) >= 4:
                    # Use width and height from viewBox
                    width_attr = viewbox_parts[2]
                    height_attr = viewbox_parts[3]
            
            # Extract numeric values from attributes (handle units like px, pt, etc.)
            width_match = re.search(r'([0-9.]+)', str(width_attr))
            height_match = re.search(r'([0-9.]+)', str(height_attr))
            
            width = float(width_match.group(1)) if width_match else 100.0
            height = float(height_match.group(1)) if height_match else 100.0
            
            # Ensure reasonable minimum dimensions
            width = max(1.0, width)
            height = max(1.0, height)
            
            return int(round(width)), int(round(height))
            
        except Exception as e:
            # Fallback: return default dimensions if parsing fails
            print(f"SVG dimension parsing failed, using defaults: {str(e)}")
            return 100, 100

    def calculate_target_dimensions(self, original_width, original_height, width, height, 
                                  keep_aspect_ratio, scale_definition, target_pixels=None):
        """依据缩放定义计算目标尺寸"""
        if not keep_aspect_ratio == "true":
            return max(1, width), max(1, height)
        
        # Ensure original dimensions are valid
        original_width = max(1, original_width)
        original_height = max(1, original_height)
        
        try:
            if scale_definition == "width":
                # Scale based on width only
                ratio = width / original_width
                target_width = width
                target_height = int(original_height * ratio)
            
            elif scale_definition == "height":
                # Scale based on height only
                ratio = height / original_height
                target_width = int(original_width * ratio)
                target_height = height
            
            elif scale_definition == "longest_side":
                # Scale based on the longest side
                if original_width >= original_height:
                    ratio = width / original_width
                    target_width = width
                    target_height = int(original_height * ratio)
                else:
                    ratio = height / original_height
                    target_width = int(original_width * ratio)
                    target_height = height
            
            elif scale_definition == "shortest_side":
                # Scale based on the shortest side
                if original_width <= original_height:
                    ratio = width / original_width
                    target_width = width
                    target_height = int(original_height * ratio)
                else:
                    ratio = height / original_height
                    target_width = int(original_width * ratio)
                    target_height = height
            
            elif scale_definition == "total_pixels" and target_pixels:
                # Scale based on total pixel count
                aspect_ratio = original_width / original_height
                target_height = int(math.sqrt(target_pixels / aspect_ratio))
                target_width = int(target_height * aspect_ratio)
            
            else:
                # Default: use the standard method (fit within width x height)
                ratio = min(width / original_width, height / original_height)
                target_width = int(original_width * ratio)
                target_height = int(original_height * ratio)
            
            # Ensure dimensions are not zero and at least 1
            target_width = max(1, target_width)
            target_height = max(1, target_height)
            
            # Ensure dimensions don't exceed reasonable limits
            target_width = min(16384, target_width)
            target_height = min(16384, target_height)
            
            return target_width, target_height
            
        except Exception as e:
            print(f"Dimension calculation failed, using fallback: {str(e)}")
            # Fallback to standard method
            ratio = min(width / original_width, height / original_height)
            target_width = max(1, int(original_width * ratio))
            target_height = max(1, int(original_height * ratio))
            return target_width, target_height

    def parse_background_color(self, color_str):
        """解析背景色字符串为RGBA元组"""
        if not color_str or not color_str.strip():
            return None
            
        try:
            color_str = color_str.strip()
            
            # Handle hex colors (e.g., #FFFFFF, #FFF, #FFFFFF80)
            if color_str.startswith('#'):
                hex_color = color_str[1:]
                
                # Handle shorthand (3-digit) hex
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                
                # Handle 6-digit hex (RGB)
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return (r, g, b, 255)
                
                # Handle 8-digit hex (RGBA)
                if len(hex_color) == 8:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    a = int(hex_color[6:8], 16)
                    return (r, g, b, a)
            
            # Handle named colors (basic support)
            color_lower = color_str.lower()
            if color_lower == "white":
                return (255, 255, 255, 255)
            elif color_lower == "black":
                return (0, 0, 0, 255)
            elif color_lower == "transparent":
                return None
                
        except Exception as e:
            print(f"Background color parsing failed: {str(e)}")
            
        return None

    def convert_svg(self, svg_input, adjust_size, keep_aspect_ratio, scale_definition, 
                   scale_method, dpi, output_format, quality, background_color="", 
                   multiple_of=0, target_pixels=1048576):
        # 参数校验
        if not svg_input or not svg_input.strip():
            raise ValueError("SVG输入不能为空")
            
        # 解析尺寸字符串
        width, height = self.parse_size_string(adjust_size)
        
        # 限定参数范围
        dpi = max(10, min(1200, dpi))
        quality = max(1, min(100, quality))
        target_pixels = max(256, min(16777216, target_pixels))

        # 尺寸对齐倍数（可选）
        if multiple_of > 0:
            multiple_of = max(1, min(256, multiple_of))
            width = max(multiple_of, (width // multiple_of) * multiple_of)
            height = max(multiple_of, (height // multiple_of) * multiple_of)

        # 获取原始SVG尺寸（不渲染）
        original_width, original_height = self.parse_svg_dimensions(svg_content=svg_input)
        
        # 计算目标尺寸
        target_width, target_height = self.calculate_target_dimensions(
            original_width, original_height, width, height, 
            keep_aspect_ratio, scale_definition, target_pixels
        )

        # 将SVG字符串转换为PNG字节流
        try:
            png_data = cairosvg.svg2png(
                bytestring=svg_input.encode('utf-8'),
                output_width=target_width,
                output_height=target_height,
                dpi=dpi
            )
        except Exception as e:
            raise Exception(f"SVG conversion failed: {str(e)}")

        # PNG字节流转PIL图像
        try:
            image = Image.open(BytesIO(png_data))
        except Exception as e:
            raise Exception(f"Failed to parse SVG conversion result: {str(e)}")
        
        # 判断是否有Alpha通道
        has_alpha = image.mode == 'RGBA'
        
        # 解析并应用背景色（若提供）
        bg_color = self.parse_background_color(background_color)
        if bg_color and has_alpha:
            try:
                # 创建背景图
                background = Image.new('RGBA', image.size, bg_color)
                # 覆盖合成
                image = Image.alpha_composite(background, image)
                has_alpha = False  # After compositing, alpha is no longer needed
            except Exception as e:
                print(f"Failed to apply background color: {str(e)}")
        
        # 转为目标输出模式
        try:
            if output_format == "jpg" or not has_alpha:
                rgb_image = image.convert("RGB")
            else:
                rgb_image = image.convert("RGBA")
        except Exception as e:
            raise Exception(f"Image format conversion failed: {str(e)}")
        
        # 最终尺寸
        final_width, final_height = rgb_image.size
        
        # 基于Alpha生成遮罩（若有）
        try:
            if has_alpha:
                alpha_channel = image.getchannel("A")
                mask_np = np.array(alpha_channel).astype(np.float32) / 255.0
                mask = torch.from_numpy(mask_np)
            else:
                # 无透明则输出白遮罩
                mask = torch.ones((final_height, final_width), dtype=torch.float32)
        except Exception as e:
            # 兜底：失败则使用白遮罩
            print(f"Mask creation failed, using white mask: {str(e)}")
            mask = torch.ones((final_height, final_width), dtype=torch.float32)
        
        # 转为ComfyUI张量格式
        try:
            image_np = np.array(rgb_image.convert("RGB")).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_np)[None,]
        except Exception as e:
            raise Exception(f"Image conversion failed: {str(e)}")
        
        # 尝试保存输出图像（非必需）
        try:
            output_dir = folder_paths.get_output_directory()
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            filename = f"svg_converted_{comfy.utils.get_datetime_string()}.{output_format}"
            output_path = os.path.join(output_dir, filename)
            
            if output_format == "jpg":
                rgb_image.convert("RGB").save(output_path, "JPEG", quality=quality, optimize=True)
            else:
                if has_alpha and rgb_image.mode == 'RGBA':
                    rgb_image.save(output_path, "PNG", optimize=True)
                else:
                    rgb_image.convert("RGB").save(output_path, "PNG", optimize=True)
                    
            print(f"SVG converted and saved to: {output_path}")
        except Exception as e:
            print(f"Failed to save image: {str(e)}")
            # Don't raise exception as main function (returning tensors) still succeeds
        
        # 返回图像、遮罩与宽高
        return (image_tensor, mask.unsqueeze(0), final_width, final_height)

# Node registration
NODE_CLASS_MAPPINGS = {
    "SVGToImage": SVGToImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SVGToImage": "SVG to Image"
}
