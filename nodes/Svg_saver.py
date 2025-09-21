import os
import re
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import time
import uuid
import folder_paths

# SVG到PNG转换函数（用于预览）
def svg_to_png(svg_string, size=(256, 256)):
    """
    将SVG字符串转换为PNG图像用于预览
    """
    # SVG转换开始
    
    try:
        # 尝试使用cairosvg进行转换（更准确）
        try:
            import cairosvg
            # 使用 cairosvg 转换
            
            # 取消SVG体积限制，直接使用原始SVG内容
            # 处理SVG内容
            
            png_data = cairosvg.svg2png(
                bytestring=svg_string.encode('utf-8', errors='ignore'), 
                output_width=size[0], 
                output_height=size[1],
                dpi=72  # 降低DPI提高速度
            )
            image = Image.open(io.BytesIO(png_data))
            # cairosvg 转换成功
            return image
            
        except ImportError:
            # cairosvg 不可用，尝试 svglib
            # 回退到SVG2
            try:
                from svglib.svglib import svg2rlg
                from reportlab.graphics import renderPM
                
                drawing = svg2rlg(io.BytesIO(svg_string.encode('utf-8')))
                if drawing is None:
                    raise ValueError("无法解析SVG字符串")
                
                # 调整大小
                drawing.width, drawing.height = size
                png_data = renderPM.drawToString(drawing, fmt="PNG")
                image = Image.open(io.BytesIO(png_data))
                # svglib 转换成功
                return image
                
            except ImportError:
                # svglib 也不可用，使用回退图像
                # 如果所有库都不可用，创建一个简单的替代图像
                return create_fallback_image(size, "SVG库未安装")
                
    except Exception as e:
        # 如果所有方法都失败了，创建一个错误图像
        # SVG转换错误
        return create_fallback_image(size, f"转换错误")

def _parse_numeric(value):
    """从类似 '1024', '1024px', '100.5px' 中解析数值，无法解析返回 None"""
    if value is None:
        return None
    try:
        match = re.match(r"^\s*([0-9]*\.?[0-9]+)\s*(px)?\s*$", str(value))
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return None

def _extract_svg_aspect_ratio(svg_string):
    """从 <svg> 的 width/height 或 viewBox 推断宽高与比例，返回 (w, h) 或 (None, None)。"""
    try:
        # 抓取 <svg ...> 标签内容
        svg_tag_match = re.search(r"<svg[^>]*>", svg_string, re.IGNORECASE | re.DOTALL)
        if not svg_tag_match:
            return (None, None)
        svg_tag = svg_tag_match.group(0)

        # width / height 属性
        width_match = re.search(r"\bwidth\s*=\s*\"([^\"]+)\"|\bwidth\s*=\s*'([^']+)'", svg_tag, re.IGNORECASE)
        height_match = re.search(r"\bheight\s*=\s*\"([^\"]+)\"|\bheight\s*=\s*'([^']+)'", svg_tag, re.IGNORECASE)
        width_str = width_match.group(1) if width_match and width_match.group(1) is not None else (width_match.group(2) if width_match else None)
        height_str = height_match.group(1) if height_match and height_match.group(1) is not None else (height_match.group(2) if height_match else None)
        width_val = _parse_numeric(width_str)
        height_val = _parse_numeric(height_str)

        if width_val and height_val and width_val > 0 and height_val > 0:
            return (width_val, height_val)

        # 使用 viewBox 推断比例
        viewbox_match = re.search(r"\bviewBox\s*=\s*\"([^\"]+)\"|\bviewBox\s*=\s*'([^']+)'", svg_tag, re.IGNORECASE)
        viewbox_str = viewbox_match.group(1) if viewbox_match and viewbox_match.group(1) is not None else (viewbox_match.group(2) if viewbox_match else None)
        if viewbox_str:
            parts = re.split(r"\s+|,", viewbox_str.strip())
            if len(parts) == 4:
                try:
                    vb_w = float(parts[2])
                    vb_h = float(parts[3])
                    if vb_w > 0 and vb_h > 0:
                        return (vb_w, vb_h)
                except Exception:
                    pass
    except Exception:
        pass
    return (None, None)

def _fit_size_by_aspect(max_size, src_w, src_h):
    """在不超过 max_size 的前提下，按比例缩放 (src_w, src_h)，返回整数 (w, h)。"""
    try:
        src_w = float(src_w)
        src_h = float(src_h)
        if src_w <= 0 or src_h <= 0:
            raise ValueError
        aspect = src_w / src_h
        if aspect >= 1.0:
            w = int(max_size)
            h = max(1, int(round(max_size / aspect)))
        else:
            h = int(max_size)
            w = max(1, int(round(max_size * aspect)))
        return (w, h)
    except Exception:
        return (max_size, max_size)

def create_fallback_image(size, text):
    """创建一个简单的回退图像"""
    image = Image.new("RGB", size, (240, 240, 240))
    draw = ImageDraw.Draw(image)
    
    # 尝试使用默认字体
    try:
        font = ImageFont.load_default()
    except:
        font = None
    
    # 居中绘制文本
    text_width = draw.textlength(text, font=font) if font else len(text) * 6
    text_position = ((size[0] - text_width) // 2, (size[1] - 10) // 2)
    draw.text(text_position, text, fill=(100, 100, 100), font=font)
    
    return image

# 主节点类
class SVGSaver:
    def __init__(self):
        self.output_dir = self.get_output_directory()
    
    def get_output_directory(self):
        """获取输出目录，可自定义修改"""
        # 默认输出目录：使用 ComfyUI 全局输出目录下的 svg 子目录
        try:
            base_output = folder_paths.get_output_directory()
        except Exception:
            base_output = os.path.dirname(os.path.abspath(__file__))
        # 若 base_output 已经是 svg 目录，则直接使用，否则拼接 svg
        base_norm = os.path.normpath(base_output)
        if os.path.basename(base_norm).lower() == "svg":
            default_dir = base_norm
        else:
            default_dir = os.path.join(base_output, "svg")
        
        # 检查是否设置了自定义目录环境变量
        custom_dir = os.environ.get("COMFY_SVG_OUTPUT", "")
        if custom_dir and os.path.isabs(custom_dir):
            return custom_dir
        
        return default_dir
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "svg_content": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
                "filename_prefix": ("STRING", {"default": "comfy_svg"}),
            },
            "optional": {
                "save_dir": ("STRING", {"default": "", "multiline": False, "placeholder": "自定义保存目录（留空使用默认）"}),
                "overwrite": (["enable", "disable"], {"default": "disable"}),
                "preview_max_size": ("INT", {"default": 512, "min": 64, "max": 2048, "step": 16}),
            }
        }
    
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "save_svg"
    CATEGORY = "自定义/SVG"
    OUTPUT_NODE = True
    
    def save_svg(self, svg_content, filename_prefix, save_dir="", overwrite="enable", preview_max_size=512):
        # 确保有有效的SVG内容
        if not svg_content.strip():
            # 创建一个空SVG提示图像
            preview_image = create_fallback_image((256, 256), "SVG内容为空")
            # 保存预览并返回 UI 引用
            preview_path, preview_subfolder = self.save_preview_temp_image(preview_image, filename_prefix)
            return {"ui": {"images": [{"filename": os.path.basename(preview_path), "subfolder": preview_subfolder, "type": "output"}]}}
        
        # 验证是否是有效的SVG
        if not re.search(r'<svg[^>]*>', svg_content, re.IGNORECASE):
            # 创建一个无效SVG提示图像
            preview_image = create_fallback_image((256, 256), "无效SVG格式")
            preview_path, preview_subfolder = self.save_preview_temp_image(preview_image, filename_prefix)
            return {"ui": {"images": [{"filename": os.path.basename(preview_path), "subfolder": preview_subfolder, "type": "output"}]}}
        
        # 处理文件名
        if not filename_prefix.lower().endswith('.svg'):
            filename_prefix += '.svg'
        
        # 创建子文件夹路径：
        # - 空或相对路径: 保存到 output/svg 下
        # - 绝对路径: 按用户指定绝对路径保存
        if save_dir and save_dir.strip():
            candidate = save_dir.strip()
            if os.path.isabs(candidate):
                full_output_dir = candidate
            else:
                full_output_dir = os.path.join(self.output_dir, candidate)
        else:
            full_output_dir = self.output_dir
        
        # 确保目录存在
        os.makedirs(full_output_dir, exist_ok=True)
        
        # 处理文件覆盖
        filepath = os.path.join(full_output_dir, filename_prefix)
        if os.path.exists(filepath) and overwrite == "disable":
            counter = 1
            base_name = filename_prefix[:-4]  # 移除.svg扩展名
            while os.path.exists(os.path.join(full_output_dir, f"{base_name}_{counter}.svg")):
                counter += 1
            filepath = os.path.join(full_output_dir, f"{base_name}_{counter}.svg")
            filename_prefix = f"{base_name}_{counter}.svg"
        
        # 保存SVG文件
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            # SVG保存成功
        except Exception as e:
            # 保存SVG文件时出错
            # 创建错误预览图像（保存到临时预览目录）
            preview_image = create_fallback_image((256, 256), "保存失败")
            preview_path, preview_subfolder = self.save_preview_temp_image(preview_image, filename_prefix)
            return {"ui": {"images": [{"filename": os.path.basename(preview_path), "subfolder": preview_subfolder, "type": "output"}]}}
        
        # 生成预览图像
        preview_image = self.generate_preview(svg_content, max_size=preview_max_size)
        # 保存到临时预览目录（自动清理），并返回 UI 引用
        preview_path, preview_subfolder = self.save_preview_temp_image(preview_image, filename_prefix)
        
        # SVGSaver 预览信息
        
        return {"ui": {"images": [{"filename": os.path.basename(preview_path), "subfolder": preview_subfolder, "type": "output"}]}}
    
    def generate_preview(self, svg_string, max_size=512):
        """生成预览图像"""
        try:
            max_size = max(64, int(max_size))
            
            # 验证SVG内容并生成预览
            if not svg_string.strip():
                return create_fallback_image((max_size, max_size), "SVG内容为空").convert("RGB")
            
            if not re.search(r'<svg[^>]*>', svg_string, re.IGNORECASE):
                return create_fallback_image((max_size, max_size), "无效SVG格式").convert("RGB")
            
            src_w, src_h = _extract_svg_aspect_ratio(svg_string)
            if src_w and src_h:
                target_size = _fit_size_by_aspect(max_size, src_w, src_h)
            else:
                target_size = (max_size, max_size)
            
            png_image = svg_to_png(svg_string, size=target_size)
            return png_image.convert("RGB")
            
        except Exception as e:
            # 生成预览时出错
            error_image = create_fallback_image((max_size, max_size), "预览生成失败")
            return error_image.convert("RGB")

    def save_preview_image(self, pil_image, filename_prefix, save_dir):
        """保存预览PNG到输出目录，返回路径与相对子目录。"""
        # 解析输出目录（与 SVG 相同逻辑）
        if save_dir and save_dir.strip():
            candidate = save_dir.strip()
            if os.path.isabs(candidate):
                full_output_dir = candidate
            else:
                full_output_dir = os.path.join(self.output_dir, candidate)
        else:
            full_output_dir = self.output_dir
        os.makedirs(full_output_dir, exist_ok=True)
        base_name = filename_prefix[:-4] if filename_prefix.lower().endswith('.svg') else filename_prefix
        preview_name = f"{base_name}.preview.png"
        preview_path = os.path.join(full_output_dir, preview_name)
        try:
            pil_image.save(preview_path, format="PNG")
        except Exception as e:
            # 保存预览失败
            pass
        # 计算相对子目录（相对于全局输出目录）
        try:
            base_output = folder_paths.get_output_directory()
        except Exception:
            base_output = self.output_dir
        rel_subfolder = os.path.relpath(full_output_dir, base_output)
        if rel_subfolder == ".":
            rel_subfolder = ""
        return preview_path, rel_subfolder

    def _get_temp_preview_dir(self):
        """获取临时预览目录（位于 svg 输出目录内）"""
        temp_dir = os.path.join(self.output_dir, ".tmp_preview")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

    def _cleanup_old_previews(self, directory, max_age_seconds=1800):
        """清理目录中早于 max_age_seconds 的文件。"""
        now = time.time()
        try:
            for name in os.listdir(directory):
                path = os.path.join(directory, name)
                try:
                    if os.path.isfile(path):
                        mtime = os.path.getmtime(path)
                        if now - mtime > max_age_seconds:
                            os.remove(path)
                except Exception:
                    pass
        except Exception:
            pass

    def save_preview_temp_image(self, pil_image, filename_prefix):
        """保存预览到临时目录（自动清理），返回路径与相对子目录。"""
        temp_dir = self._get_temp_preview_dir()
        # 执行一次清理（>30分钟）
        self._cleanup_old_previews(temp_dir, max_age_seconds=1800)

        base_name = filename_prefix[:-4] if filename_prefix.lower().endswith('.svg') else filename_prefix
        unique = uuid.uuid4().hex[:8]
        preview_name = f"{base_name}.{unique}.preview.png"
        preview_path = os.path.join(temp_dir, preview_name)
        try:
            pil_image.save(preview_path, format="PNG")
        except Exception as e:
            # 保存预览失败
            pass

        # 相对子目录相对于全局输出目录
        try:
            base_output = folder_paths.get_output_directory()
        except Exception:
            base_output = self.output_dir
        rel_subfolder = os.path.relpath(temp_dir, base_output)
        if rel_subfolder == ".":
            rel_subfolder = ""
        return preview_path, rel_subfolder

# 节点映射
NODE_CLASS_MAPPINGS = {
    "SVGSaver": SVGSaver
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SVGSaver": "SVG Saver"
}
