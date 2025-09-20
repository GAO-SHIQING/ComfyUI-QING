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
    - 可调整SVG精度和质量
    - 输出SVG字符串、宽度、高度、遮罩和预览图像
    - 功能与SVGToImage节点保持对称
    """

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
                "output_scale": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.1,
                    "max": 10.0,
                    "step": 0.1,
                    "description": "输出SVG的缩放比例"
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
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "step": 1,
                    "randomize": True,
                    "description": "改变以打破缓存，强制重新执行"
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
    RETURN_NAMES = ("SVG", "宽度", "高度", "遮罩", "预览")
    FUNCTION = "convert_image"
    CATEGORY = "图像/转换"

    def safe_update_progress(self, progress, message):
        """安全调用进度更新，兼容没有 update_progress 的环境"""
        try:
            if hasattr(comfy.utils, "update_progress"):
                comfy.utils.update_progress(progress, message)
        except Exception:
            pass

    def ensure_utils_datetime(self):
        """为旧环境添加 get_datetime_string 以避免其他节点报错"""
        try:
            if not hasattr(comfy.utils, "get_datetime_string"):
                def _dt():
                    return datetime.now().strftime("%Y%m%d_%H%M%S")
                setattr(comfy.utils, "get_datetime_string", _dt)
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

    def tensor_to_pil(self, tensor):
        """将PyTorch张量转换为PIL图像"""
        if len(tensor.shape) == 4:
            tensor = tensor[0]
        tensor = tensor.clone().detach().cpu()
        image_np = tensor.numpy()
        # 支持两种格式：CHW 或 HWC
        if image_np.ndim == 3 and image_np.shape[0] in (3, 4):  # CHW
            image_np = image_np.transpose(1, 2, 0)
        image_np = (image_np * 255).astype(np.uint8)
        pil_img = Image.fromarray(image_np)
        # 统一转换为 RGB，避免后续 OpenCV 颜色转换报错
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        return pil_img

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
            print(f"Background color parsing failed: {str(e)}")
            
        return (255, 255, 255, 255)  # 默认白色

    def create_svg_from_edges(self, image, precision, simplify_tolerance, min_area, output_scale, bg_color, stroke_color, stroke_width, threshold1, threshold2, auto_threshold, preserve_aspect_ratio):
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
        
        # 计算缩放后的尺寸
        scaled_width = int(image.width * output_scale)
        scaled_height = int(image.height * output_scale)
        
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
                # 应用缩放
                x = int(x * output_scale)
                y = int(y * output_scale)
                path_data += f"{x} {y} "
                if i == 0:
                    path_data += "L "
            path_data += "Z"
            
            # 添加路径元素到SVG
            path_element = ET.SubElement(svg_root, "path")
            path_element.set("d", path_data)
            path_element.set("fill", "none")
            path_element.set("stroke", f"rgb({stroke_color[0]},{stroke_color[1]},{stroke_color[2]})")
            path_element.set("stroke-width", str(max(1, int(stroke_width * output_scale))))
        
        # 转换为字符串
        rough_string = ET.tostring(svg_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def create_svg_from_colors(self, image, precision, min_area, output_scale, bg_color, simplify_tolerance, preserve_aspect_ratio):
        """通过颜色量化创建SVG - 优化版本"""
        # 简化颜色 - 使用更高效的量化方法
        if precision < 100:
            num_colors = max(2, int(precision / 10))
            # 使用更高效的量化方法
            quantized = image.convert("P", palette=Image.ADAPTIVE, colors=num_colors).convert("RGB")
        else:
            quantized = image
        
        # 转换为numpy数组
        img_array = np.array(quantized)
        height, width, _ = img_array.shape
        
        # 计算缩放后的尺寸
        scaled_width = int(width * output_scale)
        scaled_height = int(height * output_scale)
        
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
        
        # 使用K-means聚类进行颜色量化
        pixel_values = lab.reshape((-1, 3)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixel_values, min(8, max(2, int(precision/25))), None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 转换回RGB
        centers = np.uint8(centers)
        centers_rgb = cv2.cvtColor(np.array([centers]), cv2.COLOR_LAB2RGB)[0]
        
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
                        x = int(x * output_scale)
                        y = int(y * output_scale)
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

    def create_silhouette_svg(self, image, precision, simplify_tolerance, min_area, output_scale, bg_color, stroke_color, stroke_width, auto_threshold, manual_threshold, preserve_aspect_ratio):
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
        
        # 计算缩放后的尺寸
        scaled_width = int(image.width * output_scale)
        scaled_height = int(image.height * output_scale)
        
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
                        x = int(x * output_scale)
                        y = int(y * output_scale)
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
                    path_element.set("fill", f"rgb({stroke_color[0]},{stroke_color[1]},{stroke_color[2]})")
                    path_element.set("stroke", "none")
                    path_element.set("fill-rule", "evenodd")
        
        # 转换为字符串
        rough_string = ET.tostring(svg_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def create_poster_svg(self, image, precision, min_area, output_scale, bg_color, preserve_aspect_ratio):
        """创建海报化SVG"""
        # 转换为numpy数组
        img_array = np.array(image)
        height, width, _ = img_array.shape
        
        # 计算缩放后的尺寸
        scaled_width = int(width * output_scale)
        scaled_height = int(height * output_scale)
        
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
        
        # 使用简单的方法创建海报效果 - 将图像分割为网格
        grid_size = max(1, int(20 - (precision / 10)))
        
        for y in range(0, height, grid_size):
            for x in range(0, width, grid_size):
                # 获取网格区域
                y_end = min(y + grid_size, height)
                x_end = min(x + grid_size, width)
                
                # 计算网格的平均颜色
                grid_region = img_array[y:y_end, x:x_end]
                if grid_region.size == 0:
                    continue
                    
                avg_color = np.mean(grid_region, axis=(0, 1)).astype(int)
                
                # 添加矩形元素
                rect_element = ET.SubElement(svg_root, "rect")
                rect_element.set("x", str(int(x * output_scale)))
                rect_element.set("y", str(int(y * output_scale)))
                rect_element.set("width", str(int((x_end - x) * output_scale)))
                rect_element.set("height", str(int((y_end - y) * output_scale)))
                rect_element.set("fill", f"rgb({avg_color[0]},{avg_color[1]},{avg_color[2]})")
        
        # 转换为字符串
        rough_string = ET.tostring(svg_root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def create_preview_image(self, svg_content, width, height, preview_max_size=512):
        """创建SVG预览图像"""
        try:
            # 使用cairosvg创建预览
            import cairosvg
            # 计算与 SVG 输出一致比例的预览尺寸，最长边不超过 512
            if width <= 0 or height <= 0:
                target_w, target_h = min(256, preview_max_size), min(256, preview_max_size)
            else:
                max_size = max(64, int(preview_max_size))
                scale = min(max_size / float(width), max_size / float(height), 1.0)
                target_w = max(1, int(round(width * scale)))
                target_h = max(1, int(round(height * scale)))

            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=target_w,
                output_height=target_h
            )
            preview_image = Image.open(BytesIO(png_data))
            return self.pil_to_tensor(preview_image)
        except Exception as e:
            print(f"Preview creation failed: {str(e)}")
            # 返回一个黑色图像作为后备
            return torch.zeros((1, 64, 64, 3), dtype=torch.float32)

    def convert_image(self, image, conversion_mode, precision, simplify_tolerance, min_area, output_scale, 
                     mask=None, edge_auto_threshold=True, seed=0, background_color="#FFFFFF", stroke_color="#000000", stroke_width=1.0,
                     edge_threshold1=50, edge_threshold2=150,
                     silhouette_auto_threshold=True, silhouette_threshold=127,
                     preserve_aspect_ratio=True, preview_max_size=512, minify_svg=True, decimal_precision=2):
        # 添加进度指示
        self.safe_update_progress(0.1, "正在处理图像...")
        
        # 使用 seed 影响节点哈希（不改变算法，仅防缓存复用）
        _ = (int(seed) * 1664525 + 1013904223) & 0xFFFFFFFF

        # 处理输入图像
        pil_image = self.tensor_to_pil(image)
        width, height = pil_image.size
        
        self.safe_update_progress(0.3, "正在解析颜色...")
        # 解析背景色和描边色
        bg_color = self.parse_background_color(background_color)
        stroke_rgb = self.parse_background_color(stroke_color)
        
        # 应用遮罩（如果有）
        result_mask = None
        if mask is not None:
            self.safe_update_progress(0.4, "正在应用遮罩...")
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
        
        self.safe_update_progress(0.6, "正在生成SVG...")
        # 根据模式创建SVG
        if conversion_mode == "edge_detection":
            svg_content = self.create_svg_from_edges(
                pil_image, precision, simplify_tolerance, min_area, 
                output_scale, bg_color, stroke_rgb, stroke_width,
                edge_threshold1, edge_threshold2, edge_auto_threshold, preserve_aspect_ratio
            )
        elif conversion_mode == "color_quantization":
            svg_content = self.create_svg_from_colors(
                pil_image, precision, min_area, output_scale, bg_color, simplify_tolerance, preserve_aspect_ratio
            )
        elif conversion_mode == "silhouette":
            svg_content = self.create_silhouette_svg(
                pil_image, precision, simplify_tolerance, min_area, 
                output_scale, bg_color, stroke_rgb, stroke_width,
                silhouette_auto_threshold, silhouette_threshold, preserve_aspect_ratio
            )
        else:  # posterize
            svg_content = self.create_poster_svg(
                pil_image, precision, min_area, output_scale, bg_color, preserve_aspect_ratio
            )
        
        self.safe_update_progress(0.8, "正在处理输出...")
        # 计算缩放后的尺寸
        scaled_width = int(width * output_scale)
        scaled_height = int(height * output_scale)
        
        # 创建预览图像
        if minify_svg:
            svg_content = self.minify_svg_string(svg_content, decimal_precision=decimal_precision)
        preview_tensor = self.create_preview_image(svg_content, scaled_width, scaled_height, preview_max_size=preview_max_size)
        
        # 不再自动保存到磁盘，仅返回SVG字符串与预览
        
        self.safe_update_progress(1.0, "完成!")
        
        # 返回结果
        return (svg_content, scaled_width, scaled_height, result_mask, preview_tensor)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageToSVG": ImageToSVG
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageToSVG": "Image to SVG"
}
