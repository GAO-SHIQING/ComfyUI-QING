import os
from datetime import datetime
import re
import numpy as np
from PIL import Image
import torch
import folder_paths
import comfy.utils
from io import BytesIO
import cv2
import xml.etree.ElementTree as ET
from xml.dom import minidom
 

class ImageToSVG:
    """
    图像转SVG节点：将图像转换为SVG格式
    - 支持多种转换模式：边缘检测、颜色量化、剪影和海报化
    - 预设模式：简单、详细、艺术
    - 输出SVG字符串、宽度、高度、遮罩和预览图像
    - 功能与SVGToImage节点保持对称
    """
    
    # 预设配置
    PRESETS = {
        "simple": {
            "precision": 50,
            "simplify_tolerance": 2.0,
            "min_area": 20,
            "edge_threshold1": 50,
            "edge_threshold2": 150,
            "stroke_width": 1.5,
            "minify_svg": True,
            "decimal_precision": 1
        },
        "detailed": {
            "precision": 150,
            "simplify_tolerance": 0.5,
            "min_area": 5,
            "edge_threshold1": 30,
            "edge_threshold2": 120,
            "stroke_width": 0.8,
            "minify_svg": True,
            "decimal_precision": 2
        },
        "artistic": {
            "precision": 80,
            "simplify_tolerance": 3.0,
            "min_area": 50,
            "edge_threshold1": 80,
            "edge_threshold2": 200,
            "stroke_width": 2.0,
            "minify_svg": True,
            "decimal_precision": 1
        }
    }

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "conversion_mode": (["edge_detection", "color_quantization", "silhouette", "posterize"], {
                    "default": "edge_detection",
                    "description": "转换模式：边缘检测、颜色量化、剪影或海报化"
                }),
                "precision": ("INT", {
                    "default": 100,
                    "min": 1,
                    "max": 200,
                    "step": 1,
                    "description": "SVG精度（越高越详细）",
                    "display": "slider"
                }),
                "preset": (["custom", "simple", "detailed", "artistic"], {
                    "default": "simple",
                    "description": "预设模式：简单、详细、艺术或自定义"
                }),
                "edge_threshold1": ("INT", {
                    "default": 50,
                    "min": 1,
                    "max": 200,
                    "step": 1,
                    "description": "边缘检测阈值1",
                    "display": "slider"
                }),
                "edge_threshold2": ("INT", {
                    "default": 150,
                    "min": 1,
                    "max": 300,
                    "step": 1,
                    "description": "边缘检测阈值2",
                    "display": "slider"
                }),
                "simplify_tolerance": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 10.0,
                    "step": 0.1,
                    "description": "轮廓简化容忍度（越高越简化）",
                    "display": "slider"
                }),
                "min_area": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 1000,
                    "step": 1,
                    "description": "最小区域大小（小于此值的区域将被忽略）"
                }),
            },
            "optional": {
                "mask": ("MASK", {
                    "description": "可选遮罩，用于限制转换区域"
                }),
                "edge_auto_threshold": ("BOOLEAN", {
                    "default": True,
                    "description": "自动计算Canny双阈值"
                }),
                "preserve_aspect_ratio": ("BOOLEAN", {
                    "default": True,
                    "description": "保持图像比例（设置SVG preserveAspectRatio）"
                }),
                "background_color": ("STRING", {
                    "default": "#FFFFFF",
                    "description": "SVG背景色十六进制，如#FFFFFF"
                }),
                "stroke_color": ("STRING", {
                    "default": "#000000",
                    "description": "描边颜色十六进制，如#000000"
                }),
                "stroke_width": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 10.0,
                    "step": 0.1,
                    "description": "描边宽度"
                }),
                "silhouette_auto_threshold": ("BOOLEAN", {
                    "default": True,
                    "description": "剪影阈值自动(Otsu)"
                }),
                "silhouette_threshold": ("INT", {
                    "default": 127,
                    "min": 0,
                    "max": 255,
                    "step": 1,
                    "description": "剪影手动阈值(当关闭自动时有效)"
                }),
                "preview_max_size": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 2048,
                    "step": 16,
                    "description": "预览最长边像素"
                }),
                "minify_svg": ("BOOLEAN", {
                    "default": True,
                    "description": "最小化SVG以减小体积"
                }),
                "decimal_precision": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 6,
                    "step": 1,
                    "description": "坐标与数值小数位数"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "INT", "INT", "MASK", "IMAGE")
    RETURN_NAMES = ("svg_content", "width", "height", "mask", "preview")
    FUNCTION = "convert_image"
    CATEGORY = "🎨QING/SVG处理"
    
    def apply_preset(self, preset, **kwargs):
        """应用预设配置，用户自定义参数会覆盖预设"""
        if preset in self.PRESETS:
            # 从预设开始
            config = self.PRESETS[preset].copy()
            # 用户参数覆盖预设
            config.update({k: v for k, v in kwargs.items() if v is not None})
            return config
        else:
            # custom 模式，使用用户提供的参数
            return kwargs

    # ===== 工具方法 =====
    
    def safe_update_progress(self, progress, message):
        """安全调用进度更新，兼容没有 update_progress 的环境"""
        try:
            if hasattr(comfy.utils, "update_progress"):
                comfy.utils.update_progress(progress, message)
        except Exception:
            pass

    def minify_svg_string(self, svg_content, decimal_precision=2):
        """简单最小化：裁剪小数位、压缩多余空白。"""
        try:
            # 抽出 XML 声明，避免被数值裁剪破坏
            decl_match = re.match(r"^\s*<\?xml[^>]*\?>", svg_content)
            decl = decl_match.group(0) if decl_match else ""
            body = svg_content[len(decl):] if decl_match else svg_content

            # 裁剪浮点小数位（仅作用于主体内容）
            def round_num(m):
                num = float(m.group(0))
                s = f"{num:.{decimal_precision}f}" if decimal_precision >= 0 else str(num)
                s = re.sub(r"\.0+$", "", s)
                s = re.sub(r"(\.[0-9]*?)0+$", r"\1", s)
                return s
            body = re.sub(r"-?\d+\.\d+", round_num, body)
            # 压缩标签间空白
            body = re.sub(r">\s+<", "><", body)
            body = re.sub(r"\s{2,}", " ", body)
            # 规范化 XML 声明
            normalized_decl = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            return f"{normalized_decl}{body}"
        except Exception:
            return svg_content

    # ===== 图像处理方法 =====
    
    def tensor_to_pil(self, tensor):
        """将PyTorch张量转换为PIL图像 - 性能优化版"""
        try:
            # 优化：减少不必要的复制操作
            if len(tensor.shape) == 4:
                tensor = tensor[0]
            
            # 优化：直接在CPU上操作，避免重复转换
            if tensor.device != torch.device('cpu'):
                tensor = tensor.cpu()
            
            image_np = tensor.numpy()
            
            # 优化：更高效的维度检查和转换
            if image_np.ndim == 3:
                if image_np.shape[0] in (3, 4):  # CHW格式
                    image_np = np.transpose(image_np, (1, 2, 0))
                elif image_np.shape[2] not in (1, 3, 4):  # 无效格式
                    raise ValueError(f"不支持的图像通道数: {image_np.shape}")
            
            # 优化：使用更快的数据类型转换
            if image_np.dtype != np.uint8:
                image_np = np.clip(image_np * 255, 0, 255).astype(np.uint8)
            
            # 优化：处理不同通道数
            if image_np.ndim == 2:  # 灰度图
                pil_img = Image.fromarray(image_np, mode='L').convert('RGB')
            elif image_np.shape[2] == 1:  # 单通道
                pil_img = Image.fromarray(image_np[:, :, 0], mode='L').convert('RGB')
            elif image_np.shape[2] == 3:  # RGB
                pil_img = Image.fromarray(image_np, mode='RGB')
            elif image_np.shape[2] == 4:  # RGBA
                pil_img = Image.fromarray(image_np, mode='RGBA').convert('RGB')
            else:
                raise ValueError(f"不支持的图像形状: {image_np.shape}")
                
            return pil_img
            
        except Exception as e:
            # 图像转换失败
            # 返回一个小的默认图像
            return Image.new('RGB', (64, 64), color=(128, 128, 128))

    def pil_to_tensor(self, image):
        """将PIL图像转换为PyTorch张量"""
        image_np = np.array(image).astype(np.float32) / 255.0
        if image_np.ndim == 2:  # 灰度图
            image_np = np.repeat(image_np[..., None], 3, axis=2)
        if image_np.shape[2] == 4:  # 带Alpha通道
            image_np = image_np[:, :, :3]
        # 返回 BHWC（ComfyUI 标准）
        return torch.from_numpy(image_np)[None, ...]

    def parse_background_color(self, color_str):
        """解析背景色字符串为RGBA元组"""
        if not color_str or not color_str.strip():
            return (255, 255, 255, 255)  # 默认白色
            
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
                return (0, 0, 0, 0)
                
        except Exception as e:
            # Background color parsing failed
            pass
            
        return (255, 255, 255, 255)  # 默认白色

    # ===== SVG创建方法 =====
    
    def create_svg_from_edges(self, image, precision, simplify_tolerance, min_area, bg_color, stroke_color, stroke_width, threshold1, threshold2, auto_threshold, preserve_aspect_ratio):
        """通过边缘检测创建SVG"""
        # 转换为灰度图
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        # 应用高斯模糊减少噪声
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 应用边缘检测（支持自动阈值）
        if auto_threshold:
            # 以中位数为基准的自动阈值策略
            v = np.median(blurred)
            t1 = int(max(0, 0.66 * v))
            t2 = int(min(255, 1.33 * v))
            edges = cv2.Canny(blurred, t1, t2)
        else:
            edges = cv2.Canny(blurred, threshold1, threshold2)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # 使用原始图像尺寸（output_scale = 1.0）
        scaled_width = image.width
        scaled_height = image.height
        
        # 创建SVG根元素
        svg_root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg")
        svg_root.set("width", str(scaled_width))
        svg_root.set("height", str(scaled_height))
        svg_root.set("viewBox", f"0 0 {scaled_width} {scaled_height}")
        svg_root.set("preserveAspectRatio", "xMidYMid meet" if preserve_aspect_ratio else "none")
        
        # 添加背景矩形
        if bg_color[3] > 0:  # 如果背景不透明
            bg_rect = ET.SubElement(svg_root, "rect")
            bg_rect.set("x", "0")
            bg_rect.set("y", "0")
            bg_rect.set("width", str(scaled_width))
            bg_rect.set("height", str(scaled_height))
            bg_rect.set("fill", f"rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})")
            if bg_color[3] < 255:
                bg_rect.set("fill-opacity", str(bg_color[3] / 255.0))
        
        # 添加路径
        for contour in contours:
            # 简化轮廓
            epsilon = max(0.0001, simplify_tolerance * 0.01) * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # 计算轮廓面积
            area = cv2.contourArea(approx)
            if area < min_area:
                continue
            
            # 创建路径
            path_data = "M "
            for i, point in enumerate(approx):
                x, y = point[0]
                # 使用原始坐标（不再缩放）
                path_data += f"{x} {y} "
                if i == 0:
                    path_data += "L "
            path_data += "Z"
            
            # 添加路径元素到SVG
            path_element = ET.SubElement(svg_root, "path")
            path_element.set("d", path_data)
            path_element.set("fill", "none")
            # 确保颜色值是整数
            stroke_r = int(stroke_color[0]) if len(stroke_color) > 0 else 0
            stroke_g = int(stroke_color[1]) if len(stroke_color) > 1 else 0
            stroke_b = int(stroke_color[2]) if len(stroke_color) > 2 else 0
            path_element.set("stroke", f"rgb({stroke_r},{stroke_g},{stroke_b})")
            path_element.set("stroke-width", str(stroke_width))
        
        # 转换为字符串
        rough_string = ET.tostring(svg_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def create_svg_from_colors(self, image, precision, min_area, bg_color, simplify_tolerance, preserve_aspect_ratio):
        """通过颜色量化创建SVG - 性能优化版本"""
        try:
            # 优化：智能颜色量化
            if precision < 100:
                num_colors = max(2, min(32, int(precision / 5)))  # 限制最大颜色数
                # 优化：对大图像先缩放再量化，提高速度
                original_size = image.size
                if max(original_size) > 800:  # 大图像优化
                    scale_factor = 800 / max(original_size)
                    temp_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                    temp_image = image.resize(temp_size, Image.Resampling.LANCZOS)
                    quantized_temp = temp_image.convert("P", palette=Image.ADAPTIVE, colors=num_colors)
                    quantized = quantized_temp.resize(original_size, Image.Resampling.NEAREST).convert("RGB")
                else:
                    quantized = image.convert("P", palette=Image.ADAPTIVE, colors=num_colors).convert("RGB")
            else:
                quantized = image
        except Exception as e:
            # 颜色量化失败
            quantized = image
        
        # 转换为numpy数组
        img_array = np.array(quantized)
        height, width, _ = img_array.shape
        
        # 使用原始图像尺寸（output_scale = 1.0）
        scaled_width = width
        scaled_height = height
        
        # 创建SVG根元素
        svg_root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg")
        svg_root.set("width", str(scaled_width))
        svg_root.set("height", str(scaled_height))
        svg_root.set("viewBox", f"0 0 {scaled_width} {scaled_height}")
        svg_root.set("preserveAspectRatio", "xMidYMid meet" if preserve_aspect_ratio else "none")
        
        # 添加背景矩形
        if bg_color[3] > 0:  # 如果背景不透明
            bg_rect = ET.SubElement(svg_root, "rect")
            bg_rect.set("x", "0")
            bg_rect.set("y", "0")
            bg_rect.set("width", str(scaled_width))
            bg_rect.set("height", str(scaled_height))
            bg_rect.set("fill", f"rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})")
            if bg_color[3] < 255:
                bg_rect.set("fill-opacity", str(bg_color[3] / 255.0))
        
        # 使用更高效的方法检测颜色区域
        # 转换为Lab颜色空间以获得更好的颜色分割
        lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
        
        try:
            # 优化：使用更高效的K-means聚类
            pixel_values = lab.reshape((-1, 3)).astype(np.float32)
            k_clusters = min(8, max(2, int(precision/25)))
            
            # 优化：更激进的采样以提高速度
            max_samples = min(5000, len(pixel_values))  # 减少采样数量
            if len(pixel_values) > max_samples:
                sample_indices = np.random.choice(len(pixel_values), max_samples, replace=False)
                sample_pixels = pixel_values[sample_indices]
            else:
                sample_pixels = pixel_values
            
            # 减少迭代次数和尝试次数以提高速度
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, sample_labels, centers = cv2.kmeans(sample_pixels, k_clusters, None, criteria, 3, cv2.KMEANS_RANDOM_CENTERS)
            
            # 为所有像素分配标签
            if len(pixel_values) > 10000:
                distances = np.linalg.norm(pixel_values[:, np.newaxis] - centers, axis=2)
                labels = np.argmin(distances, axis=1)
            else:
                labels = sample_labels.flatten()
                
        except Exception as e:
            # K-means聚类失败，使用简化方法
            # 回退到简单的颜色量化
            labels = np.zeros(height * width, dtype=np.int32)
            centers = np.array([[128, 0, 0]], dtype=np.float32)  # Lab空间的灰色
        
        # 转换回RGB - 增强错误处理
        try:
            centers = np.uint8(centers)
            centers_rgb = cv2.cvtColor(np.array([centers]), cv2.COLOR_LAB2RGB)[0]
            # 颜色中心转换成功
        except Exception as e:
            # 颜色空间转换失败
            # 使用原始图像的主要颜色作为回退
            centers_rgb = np.array([[128, 128, 128], [64, 64, 64], [192, 192, 192]], dtype=np.uint8)
            # 使用回退颜色
        
        # 为每个颜色簇基于掩码提取真实边界（支持孔洞）
        labels_2d = labels.reshape(height, width)
        for i, color in enumerate(centers_rgb):
            mask_i = (labels_2d == i).astype(np.uint8) * 255
            if int(mask_i.sum() // 255) < min_area:
                continue

            contours, hierarchy = cv2.findContours(mask_i, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
            if hierarchy is None:
                continue

            hierarchy = hierarchy[0]

            def build_path(idx):
                # 从一个顶层轮廓出发，组合自身与所有子孔洞，形成 even-odd 多子路径
                parts = []
                def add_subpath(contour_idx):
                    cnt = contours[contour_idx]
                    eps = max(0.0001, simplify_tolerance * 0.01) * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, eps, True)
                    if len(approx) < 3:
                        return
                    part = "M "
                    for k, pt in enumerate(approx):
                        x, y = pt[0]
                        # 使用原始坐标（不再缩放）
                        part += f"{x} {y} "
                        if k == 0:
                            part += "L "
                    part += "Z"
                    parts.append(part)
                    # 子孔洞
                    child = hierarchy[contour_idx][2]
                    while child != -1:
                        add_subpath(child)
                        child = hierarchy[child][0]
                add_subpath(idx)
                return " ".join(parts)

            # 遍历顶层轮廓（父索引为-1）
            for idx, h in enumerate(hierarchy):
                if h[3] == -1:
                    path_data = build_path(idx)
                    if not path_data:
                        continue
                    path_element = ET.SubElement(svg_root, "path")
                    path_element.set("d", path_data)
                    path_element.set("fill", f"rgb({color[0]},{color[1]},{color[2]})")
                    path_element.set("stroke", "none")
                    path_element.set("fill-rule", "evenodd")
        
        # 转换为字符串
        rough_string = ET.tostring(svg_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def create_silhouette_svg(self, image, precision, simplify_tolerance, min_area, bg_color, stroke_color, stroke_width, auto_threshold, manual_threshold, preserve_aspect_ratio):
        """创建剪影SVG"""
        # 转换为灰度图
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
        
        # 应用阈值处理创建剪影（支持自动 Otsu 或手动阈值）
        if auto_threshold:
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            _, thresh = cv2.threshold(gray, int(manual_threshold), 255, cv2.THRESH_BINARY)
        
        # 查找轮廓（支持孔洞）
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        
        # 使用原始图像尺寸（output_scale = 1.0）
        scaled_width = image.width
        scaled_height = image.height
        
        # 创建SVG根元素
        svg_root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg")
        svg_root.set("width", str(scaled_width))
        svg_root.set("height", str(scaled_height))
        svg_root.set("viewBox", f"0 0 {scaled_width} {scaled_height}")
        svg_root.set("preserveAspectRatio", "xMidYMid meet" if preserve_aspect_ratio else "none")
        
        # 添加背景矩形
        if bg_color[3] > 0:  # 如果背景不透明
            bg_rect = ET.SubElement(svg_root, "rect")
            bg_rect.set("x", "0")
            bg_rect.set("y", "0")
            bg_rect.set("width", str(scaled_width))
            bg_rect.set("height", str(scaled_height))
            bg_rect.set("fill", f"rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})")
            if bg_color[3] < 255:
                bg_rect.set("fill-opacity", str(bg_color[3] / 255.0))
        
        # 添加剪影路径（even-odd 填充以支持孔洞）
        if hierarchy is not None:
            hierarchy = hierarchy[0]
            def build_path(idx):
                parts = []
                def add_subpath(contour_idx):
                    cnt = contours[contour_idx]
                    eps = max(0.0001, simplify_tolerance * 0.01) * cv2.arcLength(cnt, True)
                    approx = cv2.approxPolyDP(cnt, eps, True)
                    if len(approx) < 3:
                        return
                    # 面积过滤
                    if abs(cv2.contourArea(approx)) < min_area:
                        return
                    part = "M "
                    for k, pt in enumerate(approx):
                        x, y = pt[0]
                        # 使用原始坐标（不再缩放）
                        part += f"{x} {y} "
                        if k == 0:
                            part += "L "
                    part += "Z"
                    parts.append(part)
                    child = hierarchy[contour_idx][2]
                    while child != -1:
                        add_subpath(child)
                        child = hierarchy[child][0]
                add_subpath(idx)
                return " ".join(parts)

            for idx, h in enumerate(hierarchy):
                if h[3] == -1:
                    path_data = build_path(idx)
                    if not path_data:
                        continue
                    path_element = ET.SubElement(svg_root, "path")
                    path_element.set("d", path_data)
                    # 确保颜色值是整数
                    fill_r = int(stroke_color[0]) if len(stroke_color) > 0 else 0
                    fill_g = int(stroke_color[1]) if len(stroke_color) > 1 else 0
                    fill_b = int(stroke_color[2]) if len(stroke_color) > 2 else 0
                    path_element.set("fill", f"rgb({fill_r},{fill_g},{fill_b})")
                    path_element.set("stroke", "none")
                    path_element.set("fill-rule", "evenodd")
        
        # 转换为字符串
        rough_string = ET.tostring(svg_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def create_poster_svg(self, image, precision, min_area, bg_color, preserve_aspect_ratio):
        """创建海报化SVG"""
        # 转换为numpy数组
        img_array = np.array(image)
        height, width, _ = img_array.shape
        
        # 使用原始图像尺寸（output_scale = 1.0）
        scaled_width = width
        scaled_height = height
        
        # 创建SVG根元素
        svg_root = ET.Element("svg", xmlns="http://www.w3.org/2000/svg")
        svg_root.set("width", str(scaled_width))
        svg_root.set("height", str(scaled_height))
        svg_root.set("viewBox", f"0 0 {scaled_width} {scaled_height}")
        svg_root.set("preserveAspectRatio", "xMidYMid meet" if preserve_aspect_ratio else "none")
        
        # 添加背景矩形
        if bg_color[3] > 0:  # 如果背景不透明
            bg_rect = ET.SubElement(svg_root, "rect")
            bg_rect.set("x", "0")
            bg_rect.set("y", "0")
            bg_rect.set("width", str(scaled_width))
            bg_rect.set("height", str(scaled_height))
            bg_rect.set("fill", f"rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})")
            if bg_color[3] < 255:
                bg_rect.set("fill-opacity", str(bg_color[3] / 255.0))
        
        # 重新设计的海报效果 - 大幅减少矩形数量
        # 根据precision智能计算网格大小，避免生成过多矩形
        if precision <= 25:
            grid_size = 32  # 低精度：大网格，少矩形
        elif precision <= 50:
            grid_size = 16  # 中等精度
        elif precision <= 100:
            grid_size = 8   # 高精度
        else:
            grid_size = 4   # 超高精度
        
        # 进一步限制最大矩形数量
        max_rects = 5000  # 最多5000个矩形
        total_grids = (height // grid_size) * (width // grid_size)
        if total_grids > max_rects:
            # 重新计算网格大小以限制矩形数量
            grid_size = max(grid_size, int((height * width / max_rects) ** 0.5))
            # 限制矩形数量，调整网格大小
        
        # 超高效的向量化海报化算法
        # 海报化网格配置
        
        # 使用numpy向量化操作，一次性处理所有网格
        y_indices = np.arange(0, height, grid_size)
        x_indices = np.arange(0, width, grid_size)
        
        # 预分配数组以提高性能
        rect_count = len(y_indices) * len(x_indices)
        rect_data = []
        
        # 批量处理所有网格（向量化）
        for i, y in enumerate(y_indices):
            y_end = min(y + grid_size, height)
            for j, x in enumerate(x_indices):
                x_end = min(x + grid_size, width)
                
                # 高效的区域平均颜色计算
                region = img_array[y:y_end, x:x_end]
                if region.size > 0:
                    # 使用更快的平均值计算
                    avg_color = region.mean(axis=(0, 1)).astype(np.uint8)
                    rect_data.append((x, y, x_end - x, y_end - y, avg_color))
        
        # 优化：合并相邻的同色矩形（可选，进一步减少元素数量）
        if len(rect_data) > 1000:  # 只在矩形太多时启用合并
            rect_data = self._merge_adjacent_rects(rect_data)
            # 矩形合并完成
        
        # 批量创建SVG元素（最小化DOM操作）
        for x, y, w, h, color in rect_data:
            rect_element = ET.SubElement(svg_root, "rect")
            rect_element.set("x", str(x))
            rect_element.set("y", str(y))  
            rect_element.set("width", str(w))
            rect_element.set("height", str(h))
            rect_element.set("fill", f"rgb({color[0]},{color[1]},{color[2]})")
        
        # 转换为字符串
        rough_string = ET.tostring(svg_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def _merge_adjacent_rects(self, rect_data):
        """合并相邻的同色矩形以减少SVG元素数量"""
        if len(rect_data) < 2:
            return rect_data
        
        # 简化版合并：只合并水平相邻的同色矩形
        merged = []
        rect_data.sort(key=lambda r: (r[1], r[0]))  # 按y,x排序
        
        i = 0
        while i < len(rect_data):
            current = list(rect_data[i])  # [x, y, w, h, color]
            
            # 尝试向右合并
            j = i + 1
            while j < len(rect_data):
                next_rect = rect_data[j]
                # 检查是否可以合并：同行、相邻、同色、同高
                if (next_rect[1] == current[1] and  # 同一行
                    next_rect[0] == current[0] + current[2] and  # 水平相邻
                    next_rect[3] == current[3] and  # 同高
                    np.array_equal(next_rect[4], current[4])):  # 同色
                    # 合并矩形
                    current[2] += next_rect[2]  # 扩展宽度
                    j += 1
                else:
                    break
            
            merged.append(tuple(current))
            i = j if j > i + 1 else i + 1
        
        return merged

    def create_preview_image(self, svg_content, width, height, preview_max_size=512, conversion_mode="edge_detection"):
        """创建SVG预览图像 - 性能优化版"""
        try:
            # 延迟导入cairosvg
            import cairosvg
            
            # 智能尺寸计算
            if width <= 0 or height <= 0:
                target_w = target_h = min(256, preview_max_size)
            else:
                max_size = max(64, min(1024, int(preview_max_size)))
                scale = min(max_size / width, max_size / height, 1.0)
                target_w = max(16, int(width * scale))
                target_h = max(16, int(height * scale))
            
            # 快速验证SVG内容
            if not svg_content.strip() or not re.search(r'<svg[^>]*>', svg_content, re.IGNORECASE):
                return self._create_fallback_preview(width, height, preview_max_size)
            
            # 高效的SVG转PNG
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8', errors='ignore'),
                output_width=target_w,
                output_height=target_h,
                dpi=72
            )
            
            preview_image = Image.open(BytesIO(png_data))
            
            # 确保RGB格式
            if preview_image.mode != 'RGB':
                preview_image = preview_image.convert('RGB')
            
            # 简化的灰度检测（仅对问题模式）
            if conversion_mode in ["color_quantization", "posterize"]:
                img_array = np.array(preview_image)
                if self._is_grayscale_image(img_array):
                    # 灰度预览检测
                    pass
            
            return self.pil_to_tensor(preview_image)
            
        except ImportError:
            # cairosvg未安装
            return self._create_fallback_preview(width, height, preview_max_size)
        except Exception as e:
            # 预览创建失败
            return self._create_fallback_preview(width, height, preview_max_size)
    
    def _is_grayscale_image(self, img_array):
        """检查图像是否为灰度图像"""
        if len(img_array.shape) != 3 or img_array.shape[2] != 3:
            return True
        
        # 检查 R、G、B 通道是否相等
        r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
        return np.array_equal(r, g) and np.array_equal(g, b)
    
    def _create_fallback_preview(self, width, height, preview_max_size):
        """创建回退预览图像 - 高性能版"""
        try:
            size = min(max(64, preview_max_size), 512)
            # 简化的回退图像，不使用PIL绘图操作
            return torch.ones((1, size, size, 3), dtype=torch.float32) * 0.7  # 浅灰色
        except Exception:
            return torch.ones((1, 64, 64, 3), dtype=torch.float32) * 0.7

    def convert_image(self, image, conversion_mode, precision, preset, simplify_tolerance, min_area, 
                     mask=None, edge_auto_threshold=True, background_color="#FFFFFF", stroke_color="#000000", stroke_width=1.0,
                     edge_threshold1=50, edge_threshold2=150,
                     silhouette_auto_threshold=True, silhouette_threshold=127,
                     preserve_aspect_ratio=True, preview_max_size=512, minify_svg=True, decimal_precision=2):
        
        # 输入验证和健壮性检查
        try:
            # 验证图像输入
            if image is None:
                raise ValueError("输入图像不能为空")
            if not isinstance(image, torch.Tensor):
                raise TypeError("输入图像必须是PyTorch张量")
            if len(image.shape) < 3:
                raise ValueError("输入图像维度不足")
                
            # 验证参数范围
            precision = max(1, min(200, int(precision)))
            min_area = max(1, int(min_area))
            simplify_tolerance = max(0.1, min(10.0, float(simplify_tolerance)))
            preview_max_size = max(64, min(2048, int(preview_max_size)))
            stroke_width = max(0.1, min(20.0, float(stroke_width)))
            
            # 验证转换模式
            valid_modes = ["edge_detection", "color_quantization", "silhouette", "posterize"]
            if conversion_mode not in valid_modes:
                # 无效的转换模式，使用默认模式
                conversion_mode = "edge_detection"
                
        except Exception as e:
            # 参数验证失败，使用默认值
            # 使用安全的默认值
            precision = 100
            min_area = 10
            simplify_tolerance = 1.0
            conversion_mode = "edge_detection"
        
        # 应用预设配置（无进度更新以提高速度）
        config = self.apply_preset(preset, 
            precision=precision,
            simplify_tolerance=simplify_tolerance,
            min_area=min_area,
            edge_threshold1=edge_threshold1,
            edge_threshold2=edge_threshold2,
            stroke_width=stroke_width,
            minify_svg=minify_svg,
            decimal_precision=decimal_precision
        )
        
        # 从配置中获取最终参数
        final_precision = config.get('precision', precision)
        final_simplify_tolerance = config.get('simplify_tolerance', simplify_tolerance)
        final_min_area = config.get('min_area', min_area)
        final_edge_threshold1 = config.get('edge_threshold1', edge_threshold1)
        final_edge_threshold2 = config.get('edge_threshold2', edge_threshold2)
        final_stroke_width = config.get('stroke_width', stroke_width)
        final_minify_svg = config.get('minify_svg', minify_svg)
        final_decimal_precision = config.get('decimal_precision', decimal_precision)

        # 处理输入图像
        pil_image = self.tensor_to_pil(image)
        width, height = pil_image.size
        
        # 解析背景色和描边色
        try:
            bg_color = self.parse_background_color(background_color)
            stroke_rgb = self.parse_background_color(stroke_color)
        except Exception as e:
            bg_color = (255, 255, 255, 255)  # 默认白色
            stroke_rgb = (0, 0, 0, 255)     # 默认黑色
        
        # 应用遮罩（如果有）
        result_mask = None
        if mask is not None:
            if len(mask.shape) == 3:
                mask = mask[0]
            mask_np = (mask.numpy() * 255).astype(np.uint8)
            mask_pil = Image.fromarray(mask_np).resize((width, height))
            
            # 应用遮罩
            pil_image.putalpha(mask_pil)
            # 转回 RGB，避免下游 OpenCV 使用 RGBA 导致报错
            pil_image = pil_image.convert("RGB")
            result_mask = mask
        else:
            # 如果没有提供遮罩，创建一个全白遮罩（形状：1 x H x W）
            result_mask = torch.ones((1, height, width), dtype=torch.float32)
        # 开始转换
        
        # 根据模式创建SVG
        try:
            if conversion_mode == "edge_detection":
                # 边缘检测转换
                svg_content = self.create_svg_from_edges(
                    pil_image, final_precision, final_simplify_tolerance, final_min_area, 
                    bg_color, stroke_rgb, final_stroke_width,
                    final_edge_threshold1, final_edge_threshold2, edge_auto_threshold, preserve_aspect_ratio
                )
            elif conversion_mode == "color_quantization":
                # 颜色量化转换
                svg_content = self.create_svg_from_colors(
                    pil_image, final_precision, final_min_area, bg_color, final_simplify_tolerance, preserve_aspect_ratio
                )
            elif conversion_mode == "silhouette":
                # 剪影转换
                svg_content = self.create_silhouette_svg(
                    pil_image, final_precision, final_simplify_tolerance, final_min_area, 
                    bg_color, stroke_rgb, final_stroke_width,
                    silhouette_auto_threshold, silhouette_threshold, preserve_aspect_ratio
                )
            else:  # posterize
                # 海报化转换
                svg_content = self.create_poster_svg(
                    pil_image, final_precision, final_min_area, bg_color, preserve_aspect_ratio
                )
            # 转换完成
            
            # 简化的SVG内容验证（减少调试输出以提高性能）
            if svg_content:
                # 只计算元素数量，不输出内容
                if conversion_mode == "posterize":
                    rect_count = svg_content.count('<rect')
                    # 海报化元素统计
                else:
                    path_count = svg_content.count('<path')
                    # 路径元素统计
            else:
                # SVG内容为空
                pass
            
            # 调试SVG文件保存已禁用以提高性能
            # 如需调试可手动启用此功能
            pass
        except Exception as e:
            # 转换模式执行失败
            import traceback
            traceback.print_exc()
            # 使用默认的边缘检测作为回退
            try:
                svg_content = self.create_svg_from_edges(
                    pil_image, 50, 2.0, 20, 
                    bg_color, stroke_rgb, 1.0,
                    50, 150, True, preserve_aspect_ratio
                )
                # 使用回退的边缘检测
            except Exception as fallback_error:
                # 回退方案失败
                # 最终回退：创建一个简单的SVG
                svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
                <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
                <rect width="100%" height="100%" fill="rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})"/>
                <text x="50%" y="50%" text-anchor="middle" fill="#666" font-size="16">转换失败</text>
                </svg>'''
        
        # 使用原始图像尺寸（不再缩放）
        scaled_width = width
        scaled_height = height
        
        # 创建预览图像（移除不必要的进度更新）
        if final_minify_svg:
            svg_content = self.minify_svg_string(svg_content, decimal_precision=final_decimal_precision)
        
        # 根据转换模式调整预览创建策略
        preview_tensor = self.create_preview_image(svg_content, scaled_width, scaled_height, 
                                                 preview_max_size=preview_max_size, 
                                                 conversion_mode=conversion_mode)
        
        # 调试输出
        # 返回结果
        
        # 验证SVG内容
        if not svg_content or not svg_content.strip():
            # 返回的SVG内容为空
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
            <svg width="{scaled_width}" height="{scaled_height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="rgb({bg_color[0]},{bg_color[1]},{bg_color[2]})"/>
            <text x="50%" y="50%" text-anchor="middle" fill="#666" font-size="16">SVG内容为空</text>
            </svg>'''
        
        # 验证SVG格式
        if not re.search(r'<svg[^>]*>', svg_content, re.IGNORECASE):
            # 返回的不是有效的SVG格式
            pass
        
        # 返回结果
        return (svg_content, scaled_width, scaled_height, result_mask, preview_tensor)
    
    def convert_image_safe(self, *args, **kwargs):
        """安全的转换包装器，提供完整的错误处理"""
        try:
            return self.convert_image(*args, **kwargs)
        except Exception as e:
            # 图像转SVG转换失败
            # 返回安全的默认结果
            default_svg = '''<?xml version="1.0" encoding="UTF-8"?>
            <svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f0f0f0"/>
            <text x="50%" y="50%" text-anchor="middle" fill="#666">转换失败</text>
            </svg>'''
            default_mask = torch.ones((1, 100, 100), dtype=torch.float32)
            default_preview = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            return (default_svg, 100, 100, default_mask, default_preview)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageToSVG": ImageToSVG
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageToSVG": "Image to SVG"
}
