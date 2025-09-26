import numpy as np
import torch
import cv2
from collections import defaultdict
from scipy import ndimage
from skimage import measure

class MaskSplitter:
    """
    遮罩拆分Q：高效可靠的遮罩拆分工具
    - 支持最小组件过滤、小区域合并/移除/保留
    - 提供文字/结构保护的智能合并
    - 输出组件遮罩列表（可保留原始像素值）
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "min_component_size": ("INT", {
                    "default": 100,
                    "min": 1,
                    "max": 10000,
                    "step": 10,
                    "display": "slider|min_component_size (像素数)"
                }),
                "small_region_handling": (["merge", "remove", "keep"], {
                    "default": "merge",
                    "display": "small_region_handling"
                }),
                "merge_distance_ratio": ("FLOAT", {
                    "default": 2.0,
                    "min": 0.1,
                    "max": 10.0,
                    "step": 0.1,
                    "display": "slider|merge_distance_ratio"
                }),
                "text_preservation": (["auto", "aggressive", "chinese_optimized", "disabled"], {
                    "default": "chinese_optimized",
                    "display": "text_preservation"
                }),
                "structure_preservation": (["disabled", "auto", "enhanced"], {
                    "default": "auto",
                    "display": "structure_preservation"
                }),
                "output_all_components": ("BOOLEAN", {
                    "default": True,
                    "label_on": "启用",
                    "label_off": "禁用",
                    "display": "output_all_components"
                }),
                "preserve_original_values": ("BOOLEAN", {
                    "default": True,
                    "label_on": "启用",
                    "label_off": "禁用",
                    "display": "preserve_original_values"
                }),
            },
            "optional": {
                "reference_image": ("IMAGE", {
                    "display": "reference_image (可选)"
                }),
            }
        }

    # 保留 INPUT_NAMES 作为备份
    INPUT_NAMES = {
        "mask": "输入遮罩",
        "min_component_size": "min_component_size (像素数)",
        "small_region_handling": "small_region_handling",
        "merge_distance_ratio": "merge_distance_ratio",
        "text_preservation": "text_preservation",
        "structure_preservation": "structure_preservation",
        "output_all_components": "output_all_components",
        "preserve_original_values": "preserve_original_values",
        "reference_image": "reference_image (可选)",
    }

    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask_list",)
    FUNCTION = "split"
    OUTPUT_IS_LIST = (True,)
    CATEGORY = "🎨QING/遮罩处理"

    def split(self, mask, min_component_size=100, small_region_handling="merge", 
              merge_distance_ratio=2.0, text_preservation="auto", 
              structure_preservation="auto", output_all_components=True,
              preserve_original_values=True, reference_image=None):
        
        # 转换mask为numpy数组
        mask_np = self.mask_to_numpy(mask)
        original_mask_np = mask_np.copy()  # 保存原始遮罩值
        
        # 二值化用于分析，但保留原始值用于输出
        _, binary_mask = cv2.threshold(mask_np, 0.5, 1, cv2.THRESH_BINARY)
        binary_mask = binary_mask.astype(np.uint8)
        
        # 形态学预处理：针对文字优化
        if text_preservation != "disabled":
            binary_mask = self.preprocess_for_text(binary_mask)
        
        # 使用连通组件分析确保所有区域都被找到
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary_mask, connectivity=8
        )
        
        # 收集所有组件
        components = []
        for i in range(1, num_labels):  # 跳过背景(0)
            area = stats[i, cv2.CC_STAT_AREA]
            component_mask = (labels == i).astype(np.uint8)
            
            # 保存原始像素值
            if preserve_original_values:
                component_original_values = original_mask_np * component_mask
            else:
                component_original_values = component_mask.astype(np.float32)
                
            components.append((i, component_original_values, area, centroids[i]))
        
        # 处理小区域
        if small_region_handling != "keep":
            components = self.handle_small_regions(components, min_component_size, 
                                                 small_region_handling, merge_distance_ratio,
                                                 binary_mask.shape)
        
        # 如果启用了文字保护，尝试合并可能是文字的组件
        if text_preservation != "disabled" and len(components) > 1:
            components = self.preserve_text_components(components, binary_mask, text_preservation)
        
        # 如果启用了结构保护，尝试合并可能属于同一结构的组件
        if structure_preservation != "disabled" and len(components) > 1:
            components = self.preserve_structure_components(components, binary_mask, structure_preservation)
        
        # 确保所有内容都被输出
        if output_all_components:
            # 创建一个包含所有组件的综合遮罩，确保没有遗漏
            combined_mask = np.zeros_like(binary_mask, dtype=np.float32)
            for comp in components:
                if len(comp) == 4:
                    _, comp_mask, _, _ = comp
                else:
                    _, comp_mask, _, _, _ = comp
                combined_mask = np.maximum(combined_mask, comp_mask)
            
            # 检查是否有遗漏的像素
            missing_pixels = np.sum(binary_mask) - np.sum(combined_mask > 0)
            if missing_pixels > 0:
                # 创建一个额外的组件包含所有遗漏的像素
                missing_mask = (binary_mask - (combined_mask > 0).astype(np.uint8))
                missing_mask[missing_mask < 0] = 0
                
                if preserve_original_values:
                    missing_values = original_mask_np * missing_mask
                else:
                    missing_values = missing_mask.astype(np.float32)
                    
                components.append((num_labels, missing_values, np.sum(missing_mask), (0, 0)))
        
        # 转换为输出格式
        output_masks = []
        for comp in components:
            if len(comp) == 4:
                _, comp_mask, _, _ = comp
            else:
                _, comp_mask, _, _, _ = comp
            output_masks.append(torch.from_numpy(comp_mask).unsqueeze(0))
        
        # 如果没有找到任何组件，返回原始遮罩
        if len(output_masks) == 0:
            output_masks = [mask]
        
        return (output_masks,)
    
    def mask_to_numpy(self, mask):
        """将各种格式的mask转换为numpy数组"""
        if len(mask.shape) == 4:  # (B, H, W, 1)
            return mask[0, :, :, 0].cpu().numpy()
        elif len(mask.shape) == 3:
            if mask.shape[0] == 1:  # (1, H, W)
                return mask[0].cpu().numpy()
            else:  # (H, W, 1) or (H, W)
                return mask[:, :, 0].cpu().numpy() if mask.shape[2] == 1 else mask.cpu().numpy()
        else:  # (H, W)
            return mask.cpu().numpy()
    
    def handle_small_regions(self, components, min_size, handling_method, distance_ratio, mask_shape):
        """处理小区域：合并、移除或保留"""
        if len(components) <= 1:
            return components
        
        # 分离大小组件
        large_components = []
        small_components = []
        
        for comp in components:
            if len(comp) == 4:
                comp_id, comp_mask, area, centroid = comp
            else:
                comp_id, comp_mask, area, centroid, _ = comp
                
            if area >= min_size:
                large_components.append((comp_id, comp_mask, area, centroid))
            else:
                small_components.append((comp_id, comp_mask, area, centroid))
        
        # 如果没有小区域，直接返回
        if not small_components:
            return components
            
        # 根据处理方式处理小区域
        if handling_method == "remove":
            # 直接移除小区域
            return large_components
        elif handling_method == "merge" and large_components:
            # 合并小区域到最近的大区域
            return self.merge_small_regions(large_components, small_components, distance_ratio, mask_shape)
        else:
            # 保留所有区域
            return large_components + small_components
    
    def merge_small_regions(self, large_comps, small_comps, distance_ratio, mask_shape):
        """合并小区域到最近的大区域"""
        if not large_comps or not small_comps:
            return large_comps + small_comps
            
        # 计算平均组件大小，用于确定合并距离
        avg_height = mask_shape[0] * 0.05  # 使用图像高度的5%作为基准
        merge_distance = avg_height * distance_ratio
        
        # 为每个大组件创建KD树（简化版，使用列表）
        large_centroids = [centroid for _, _, _, centroid in large_comps]
        
        # 处理每个小区域
        merged_components = large_comps.copy()
        
        for small_id, small_mask, small_area, small_centroid in small_comps:
            # 找到最近的大组件
            min_distance = float('inf')
            nearest_index = -1
            
            for i, (_, _, _, large_centroid) in enumerate(merged_components):
                dx = small_centroid[0] - large_centroid[0]
                dy = small_centroid[1] - large_centroid[1]
                distance = np.sqrt(dx*dx + dy*dy)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_index = i
            
            # 如果距离在阈值内，合并到最近的大组件
            if min_distance <= merge_distance and nearest_index >= 0:
                # 获取大组件
                large_id, large_mask, large_area, large_centroid = merged_components[nearest_index]
                
                # 合并遮罩
                merged_mask = np.maximum(large_mask, small_mask)
                
                # 更新组件
                merged_components[nearest_index] = (large_id, merged_mask, large_area + small_area, large_centroid)
            else:
                # 距离太远，保留为独立组件
                merged_components.append((small_id, small_mask, small_area, small_centroid))
        
        return merged_components
    
    def preserve_text_components(self, components, original_mask, mode):
        """尝试保持文字组件的完整性"""
        if len(components) <= 1:
            return components
        
        # 统一组件格式
        unified_components = []
        for idx, comp in enumerate(components):
            if len(comp) == 4:
                comp_id, comp_mask, area, centroid = comp
                unified_components.append((comp_id, comp_mask, area, centroid, idx))
            else:
                comp_id, comp_mask, area, centroid, _ = comp
                unified_components.append((comp_id, comp_mask, area, centroid, idx))
        
        # 计算组件之间的空间关系
        text_candidates = []
        non_text_components = []
        
        for i, (comp_id, comp_mask, area, centroid, idx) in enumerate(unified_components):
            # 使用简单的启发式方法识别可能是文字的组件
            is_text = self.is_likely_text(comp_mask, area)
            if is_text:
                text_candidates.append((comp_id, comp_mask, area, centroid, idx))
            else:
                non_text_components.append((comp_id, comp_mask, area, centroid, idx))
        
        # 如果没有文字候选，直接返回所有组件
        if not text_candidates:
            return components
        
        # 根据模式合并文字组件
        if mode == "aggressive":
            # 将所有文字组件合并为一个
            merged_text_mask = np.zeros_like(original_mask, dtype=np.float32)
            for comp_id, comp_mask, _, _, _ in text_candidates:
                merged_text_mask = np.maximum(merged_text_mask, comp_mask)
            
            # 创建一个新的合并组件
            merged_area = np.sum(merged_text_mask > 0)
            merged_centroid = self.calculate_centroid((merged_text_mask > 0).astype(np.uint8))
            
            # 创建新的组件列表
            new_components = [(0, merged_text_mask, merged_area, merged_centroid)]
            for comp_id, comp_mask, area, centroid, idx in non_text_components:
                new_components.append((comp_id, comp_mask, area, centroid))
            
            return new_components
        elif mode == "chinese_optimized":
            # 专门针对中文字符优化的处理模式
            return self.chinese_optimized_grouping(text_candidates, non_text_components, original_mask)
        else:  # auto mode
            # 尝试将空间上接近的文字组件分组
            text_groups = self.group_text_components(text_candidates)
            
            # 合并每组文字组件
            merged_components = []
            for group in text_groups:
                if len(group) == 1:
                    comp_id, comp_mask, area, centroid, idx = group[0]
                    merged_components.append((comp_id, comp_mask, area, centroid))
                else:
                    # 合并组内的所有组件
                    merged_mask = np.zeros_like(original_mask, dtype=np.float32)
                    for comp_id, comp_mask, _, _, _ in group:
                        merged_mask = np.maximum(merged_mask, comp_mask)
                    
                    merged_area = np.sum(merged_mask > 0)
                    merged_centroid = self.calculate_centroid((merged_mask > 0).astype(np.uint8))
                    merged_components.append((0, merged_mask, merged_area, merged_centroid))
            
            # 添加非文字组件
            for comp_id, comp_mask, area, centroid, idx in non_text_components:
                merged_components.append((comp_id, comp_mask, area, centroid))
            
            return merged_components
    
    def preserve_structure_components(self, components, original_mask, mode):
        """
        尝试保持图形结构的完整性
        新增函数：用于处理非文字但属于同一结构的情况
        """
        if len(components) <= 1:
            return components

        # 统一组件格式
        unified_components = []
        for idx, comp in enumerate(components):
            if len(comp) == 4:
                comp_id, comp_mask, area, centroid = comp
                unified_components.append((comp_id, comp_mask, area, centroid, idx))
            else:
                comp_id, comp_mask, area, centroid, _ = comp
                unified_components.append((comp_id, comp_mask, area, centroid, idx))

        # 计算每个组件的特征，用于判断是否可能属于同一结构
        processed_components = []
        used_indices = set()

        # 计算原图的高度，用于距离阈值判断
        image_height = original_mask.shape[0]
        distance_threshold = image_height * 0.05  # 距离阈值设为图像高度的5%

        for i, (comp_id, comp_mask, area, centroid, idx) in enumerate(unified_components):
            if i in used_indices:
                continue

            current_group = [(comp_id, comp_mask, area, centroid, idx)]
            used_indices.add(i)

            # 计算当前组件的特征
            binary_comp_mask = (comp_mask > 0).astype(np.uint8)
            current_contour = self.get_largest_contour(binary_comp_mask)
            current_hu_moments = cv2.HuMoments(cv2.moments(current_contour)).flatten() if current_contour is not None else np.zeros(7)

            for j, (other_id, other_mask, other_area, other_centroid, other_idx) in enumerate(unified_components):
                if j in used_indices or i == j:
                    continue

                binary_other_mask = (other_mask > 0).astype(np.uint8)
                other_contour = self.get_largest_contour(binary_other_mask)
                if other_contour is None:
                    continue

                # 计算两个组件之间的距离
                dx = centroid[0] - other_centroid[0]
                dy = centroid[1] - other_centroid[1]
                distance = np.sqrt(dx*dx + dy*dy)

                # 如果距离太远，则不太可能属于同一结构
                if distance > distance_threshold:
                    continue

                # 计算Hu矩相似性（形状相似性）
                other_hu_moments = cv2.HuMoments(cv2.moments(other_contour)).flatten()
                shape_similarity = np.linalg.norm(current_hu_moments - other_hu_moments)

                # 计算面积比例
                area_ratio = max(area, other_area) / min(area, other_area) if min(area, other_area) > 0 else float('inf')

                # 判断是否可能属于同一结构的条件
                if (shape_similarity < 0.5 and  # 形状相似
                    area_ratio < 10 and         # 面积相差不太大
                    distance < distance_threshold):  # 距离接近

                    current_group.append((other_id, other_mask, other_area, other_centroid, other_idx))
                    used_indices.add(j)

            # 根据模式决定是否合并组内的组件
            if mode == "enhanced" or (mode == "auto" and len(current_group) > 1):
                # 合并组内的所有组件
                merged_mask = np.zeros_like(original_mask, dtype=np.float32)
                for comp_data in current_group:
                    _, comp_mask, _, _, _ = comp_data
                    merged_mask = np.maximum(merged_mask, comp_mask)
                
                merged_area = np.sum(merged_mask > 0)
                merged_centroid = self.calculate_centroid((merged_mask > 0).astype(np.uint8))
                processed_components.append((0, merged_mask, merged_area, merged_centroid))
            else:
                # 不合并，保持原样
                for comp_data in current_group:
                    comp_id, comp_mask, area, centroid, idx = comp_data
                    processed_components.append((comp_id, comp_mask, area, centroid))

        # 添加未分组的组件
        for i, (comp_id, comp_mask, area, centroid, idx) in enumerate(unified_components):
            if i not in used_indices:
                processed_components.append((comp_id, comp_mask, area, centroid))

        return processed_components

    def is_likely_text(self, mask, area):
        """改进的文字识别算法，特别优化中文字符识别"""
        # 创建二值掩码用于轮廓检测
        binary_mask = (mask > 0).astype(np.uint8)
        
        # 计算轮廓
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        
        # 获取最大轮廓（主要轮廓）
        main_contour = max(contours, key=cv2.contourArea)
        
        # 获取外接矩形和轮廓特征
        x, y, w, h = cv2.boundingRect(main_contour)
        contour_area = cv2.contourArea(main_contour)
        
        # 计算各种特征
        aspect_ratio = w / max(h, 1)
        fill_ratio = area / (w * h) if w * h > 0 else 0
        contour_fill_ratio = contour_area / area if area > 0 else 0
        
        # 计算轮廓的复杂度（周长与面积的比值）
        perimeter = cv2.arcLength(main_contour, True)
        complexity = perimeter / max(np.sqrt(contour_area), 1) if contour_area > 0 else 0
        
        # 计算轮廓的凸性缺陷（文字通常有一些凹陷）
        hull = cv2.convexHull(main_contour, returnPoints=False)
        defects = cv2.convexityDefects(main_contour, hull)
        defect_count = len(defects) if defects is not None else 0
        
        # 计算边界框的紧密度
        rect_area = w * h
        bbox_fill_ratio = contour_area / rect_area if rect_area > 0 else 0
        
        # 多重判断条件，特别适合中文字符
        # 条件1: 基本形状特征
        basic_text_features = (
            0.3 < aspect_ratio < 3.0 and      # 中文字符通常接近正方形
            0.3 < fill_ratio < 0.95 and       # 填充率不能太低或太高
            0.4 < bbox_fill_ratio < 0.9        # 边界框填充率
        )
        
        # 条件2: 复杂度特征（文字有一定复杂度但不会过于复杂）
        complexity_features = (
            3 < complexity < 15 and           # 适中的复杂度
            defect_count >= 2                 # 有一定的凹陷特征
        )
        
        # 条件3: 尺寸特征（排除过小或过大的组件）
        size_features = (
            area > 50 and                     # 最小面积阈值
            area < 50000 and                  # 最大面积阈值
            min(w, h) > 8                     # 最小尺寸
        )
        
        # 条件4: 特殊的中文字符特征
        chinese_features = (
            0.6 < aspect_ratio < 1.4 and      # 中文字符接近正方形
            0.4 < fill_ratio < 0.8 and        # 中文字符的典型填充率
            defect_count >= 1                 # 中文字符通常有笔画间隙
        )
        
        # 综合判断：满足基本特征和尺寸特征，并且满足复杂度特征或中文特征
        is_text = (basic_text_features and size_features and 
                  (complexity_features or chinese_features))
        
        return is_text
    
    def group_text_components(self, text_components):
        """智能文字分组算法，特别优化中文字符处理"""
        if len(text_components) <= 1:
            return [text_components]
        
        # 计算组件的详细特征
        component_features = []
        for comp_id, comp_mask, area, centroid, idx in text_components:
            binary_mask = (comp_mask > 0).astype(np.uint8)
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                x, y, w, h = cv2.boundingRect(contours[0])
                component_features.append({
                    'id': comp_id,
                    'mask': comp_mask,
                    'area': area,
                    'centroid': centroid,
                    'idx': idx,
                    'bbox': (x, y, w, h),
                    'width': w,
                    'height': h,
                    'aspect_ratio': w / max(h, 1)
                })
        
        if not component_features:
            return [text_components]
        
        # 计算全局统计信息
        heights = [f['height'] for f in component_features]
        widths = [f['width'] for f in component_features]
        areas = [f['area'] for f in component_features]
        
        avg_height = np.mean(heights)
        median_height = np.median(heights)
        avg_width = np.mean(widths)
        median_area = np.median(areas)
        
        # 使用更智能的分组策略
        groups = []
        used_indices = set()
        
        for i, feat1 in enumerate(component_features):
            if i in used_indices:
                continue
                
            group = [feat1]
            used_indices.add(i)
            
            for j, feat2 in enumerate(component_features):
                if j in used_indices or i == j:
                    continue
                
                # 多维度相似性判断
                should_group = self.should_group_characters(feat1, feat2, avg_height, avg_width, median_area)
                
                if should_group:
                    group.append(feat2)
                    used_indices.add(j)
            
            # 转换回原始格式
            group_converted = []
            for feat in group:
                group_converted.append((feat['id'], feat['mask'], feat['area'], feat['centroid'], feat['idx']))
            
            groups.append(group_converted)
        
        return groups
    
    def should_group_characters(self, feat1, feat2, avg_height, avg_width, median_area):
        """判断两个字符组件是否应该分组（合并）"""
        # 计算距离
        dx = feat1['centroid'][0] - feat2['centroid'][0]
        dy = feat1['centroid'][1] - feat2['centroid'][1]
        distance = np.sqrt(dx*dx + dy*dy)
        
        # 计算尺寸相似性
        height_ratio = max(feat1['height'], feat2['height']) / max(min(feat1['height'], feat2['height']), 1)
        width_ratio = max(feat1['width'], feat2['width']) / max(min(feat1['width'], feat2['width']), 1)
        area_ratio = max(feat1['area'], feat2['area']) / max(min(feat1['area'], feat2['area']), 1)
        
        # 计算位置关系
        horizontal_distance = abs(dx)
        vertical_distance = abs(dy)
        
        # 判断是否在同一行（中文字符通常在同一水平线上）
        is_same_line = vertical_distance < avg_height * 0.3
        
        # 判断水平间距是否合理（不能太远也不能太近）
        reasonable_spacing = avg_width * 0.1 < horizontal_distance < avg_width * 2.0
        
        # 中文字符特有的判断条件
        chinese_grouping_conditions = (
            is_same_line and                    # 在同一水平线上
            reasonable_spacing and              # 合理的水平间距
            height_ratio < 2.0 and             # 高度相似
            area_ratio < 3.0                   # 面积相似
        )
        
        # 通用的分组条件（适用于被错误分割的字符）
        broken_character_conditions = (
            distance < avg_height * 1.5 and    # 距离很近
            height_ratio < 1.8 and             # 高度比较相似
            (vertical_distance < avg_height * 0.5 or horizontal_distance < avg_width * 0.8)  # 垂直或水平距离很近
        )
        
        # 避免过度合并：如果两个组件都比较大且距离较远，不合并
        both_large = feat1['area'] > median_area and feat2['area'] > median_area
        far_apart = distance > avg_height * 1.2
        
        if both_large and far_apart:
            return False
        
        # 最终判断：满足中文分组条件或者是被分割字符的条件
        return chinese_grouping_conditions or broken_character_conditions
    
    def chinese_optimized_grouping(self, text_candidates, non_text_components, original_mask):
        """专门针对中文字符优化的分组算法"""
        if not text_candidates:
            return [(comp_id, comp_mask, area, centroid) for comp_id, comp_mask, area, centroid, idx in non_text_components]
        
        # 分析文字组件的特征，识别可能的中文字符
        chinese_components = []
        other_text_components = []
        
        for comp_id, comp_mask, area, centroid, idx in text_candidates:
            if self.is_likely_chinese_character(comp_mask, area):
                chinese_components.append((comp_id, comp_mask, area, centroid, idx))
            else:
                other_text_components.append((comp_id, comp_mask, area, centroid, idx))
        
        # 对中文组件进行特殊处理
        final_components = []
        
        if chinese_components:
            # 使用专门的中文字符分组逻辑
            chinese_groups = self.group_chinese_characters(chinese_components)
            
            for group in chinese_groups:
                if len(group) == 1:
                    # 单个字符，直接保留
                    comp_id, comp_mask, area, centroid, idx = group[0]
                    final_components.append((comp_id, comp_mask, area, centroid))
                else:
                    # 多个组件，判断是否应该合并
                    should_merge = self.should_merge_chinese_group(group)
                    
                    if should_merge:
                        # 合并为一个字符
                        merged_mask = np.zeros_like(original_mask, dtype=np.float32)
                        for comp_id, comp_mask, _, _, _ in group:
                            merged_mask = np.maximum(merged_mask, comp_mask)
                        
                        merged_area = np.sum(merged_mask > 0)
                        merged_centroid = self.calculate_centroid((merged_mask > 0).astype(np.uint8))
                        final_components.append((0, merged_mask, merged_area, merged_centroid))
                    else:
                        # 保持分离
                        for comp_id, comp_mask, area, centroid, idx in group:
                            final_components.append((comp_id, comp_mask, area, centroid))
            
            # 后处理：对剩余的小组件进行强制合并
            final_components = self.post_process_small_fragments(final_components, original_mask)
        
        # 处理其他文字组件
        for comp_id, comp_mask, area, centroid, idx in other_text_components:
            final_components.append((comp_id, comp_mask, area, centroid))
        
        # 添加非文字组件
        for comp_id, comp_mask, area, centroid, idx in non_text_components:
            final_components.append((comp_id, comp_mask, area, centroid))
        
        return final_components
    
    def is_likely_chinese_character(self, mask, area):
        """判断组件是否可能是中文字符或其部分（降低阈值以捕获分散部分）"""
        binary_mask = (mask > 0).astype(np.uint8)
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return False
        
        main_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(main_contour)
        
        # 中文字符特征（放宽条件以捕获分散的部分）
        aspect_ratio = w / max(h, 1)
        
        # 放宽宽高比范围，包括可能的字符片段
        is_reasonable_shape = 0.2 <= aspect_ratio <= 5.0  # 更宽的范围
        
        # 大幅降低面积阈值，包括小的字符片段
        reasonable_size = 20 <= area <= 50000  # 降低最小面积从100到20
        
        # 放宽复杂度要求
        perimeter = cv2.arcLength(main_contour, True)
        complexity = perimeter / max(np.sqrt(area), 1) if area > 0 else 0
        has_some_complexity = 2 <= complexity <= 30  # 放宽复杂度范围
        
        # 额外检查：如果是小面积但形状合理，也认为是字符片段
        is_small_fragment = (
            20 <= area <= 200 and 
            0.3 <= aspect_ratio <= 3.0 and
            complexity >= 1.5
        )
        
        # 主要条件或小片段条件
        main_condition = is_reasonable_shape and reasonable_size and has_some_complexity
        
        return main_condition or is_small_fragment
    
    def group_chinese_characters(self, chinese_components):
        """对中文字符进行分组，使用更积极的合并策略"""
        if len(chinese_components) <= 1:
            return [chinese_components]
        
        # 计算字符间的平均尺寸和统计信息
        heights = []
        widths = []
        areas = []
        bboxes = []
        
        for comp_id, comp_mask, area, centroid, idx in chinese_components:
            binary_mask = (comp_mask > 0).astype(np.uint8)
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                x, y, w, h = cv2.boundingRect(contours[0])
                heights.append(h)
                widths.append(w)
                areas.append(area)
                bboxes.append((x, y, w, h))
        
        if not heights:
            return [chinese_components]
        
        avg_height = np.mean(heights)
        avg_width = np.mean(widths)
        median_area = np.median(areas)
        max_dimension = max(avg_height, avg_width)
        
        
        # 使用更积极的分组策略
        groups = []
        used_indices = set()
        
        for i, (comp_id1, comp_mask1, area1, centroid1, idx1) in enumerate(chinese_components):
            if i in used_indices:
                continue
            
            group = [(comp_id1, comp_mask1, area1, centroid1, idx1)]
            used_indices.add(i)
            
            # 递归查找可能属于同一字符的所有组件
            self._find_related_components(i, chinese_components, group, used_indices, 
                                        avg_height, avg_width, median_area, max_dimension)
            
            groups.append(group)
        
        return groups
    
    def _find_related_components(self, base_idx, all_components, current_group, used_indices, 
                               avg_height, avg_width, median_area, max_dimension):
        """递归查找与当前组相关的组件"""
        base_comp = all_components[base_idx]
        base_centroid = base_comp[3]
        base_area = base_comp[2]
        
        for j, (comp_id2, comp_mask2, area2, centroid2, idx2) in enumerate(all_components):
            if j in used_indices or j == base_idx:
                continue
            
            # 计算距离
            dx = base_centroid[0] - centroid2[0]
            dy = base_centroid[1] - centroid2[1]
            distance = np.sqrt(dx*dx + dy*dy)
            
            # 多重判断条件（更宽松的合并条件）
            should_merge = False
            
            # 条件1: 非常接近的组件（可能是同一字符的不同部分）
            very_close = distance < max_dimension * 1.2  # 增大距离阈值
            
            # 条件2: 尺寸兼容性检查（放宽要求）
            area_ratio = max(base_area, area2) / max(min(base_area, area2), 1)
            size_compatible = area_ratio < 5.0  # 放宽面积比例要求
            
            # 条件3: 位置合理性（在合理的字符范围内）
            reasonable_position = (
                abs(dx) < max_dimension * 2.0 and  # 水平距离不超过2个字符宽度
                abs(dy) < max_dimension * 2.0      # 垂直距离不超过2个字符高度
            )
            
            # 条件4: 特殊情况 - 小片段更容易合并
            is_small_fragment = min(base_area, area2) < median_area * 0.5
            if is_small_fragment:
                fragment_close = distance < max_dimension * 1.8  # 小片段允许更大距离
                should_merge = fragment_close and reasonable_position
            else:
                should_merge = very_close and size_compatible and reasonable_position
            
            if should_merge:
                current_group.append((comp_id2, comp_mask2, area2, centroid2, idx2))
                used_indices.add(j)
                
                # 递归查找与新加入组件相关的其他组件
                self._find_related_components(j, all_components, current_group, used_indices,
                                            avg_height, avg_width, median_area, max_dimension)
    
    def should_merge_chinese_group(self, group):
        """判断中文字符组是否应该合并（更积极的策略）"""
        if len(group) <= 1:
            return False
        
        # 更积极的合并策略：
        # 1. 如果组内有多个组件，很可能是同一字符的分散部分
        # 2. 只要不是明显的多个独立字符就合并
        
        if len(group) <= 5:  # 允许合并最多5个组件
            # 计算组内组件的空间分布
            centroids = [comp[3] for comp in group]  # 提取质心
            areas = [comp[2] for comp in group]      # 提取面积
            
            # 计算边界框
            min_x = min(c[0] for c in centroids)
            max_x = max(c[0] for c in centroids)
            min_y = min(c[1] for c in centroids)
            max_y = max(c[1] for c in centroids)
            
            bbox_width = max_x - min_x
            bbox_height = max_y - min_y
            
            # 计算平均组件尺寸
            avg_area = np.mean(areas)
            estimated_char_size = np.sqrt(avg_area)
            
            # 判断是否在合理的字符尺寸范围内
            reasonable_bbox = (
                bbox_width <= estimated_char_size * 2.5 and  # 宽度不超过2.5个字符
                bbox_height <= estimated_char_size * 2.5     # 高度不超过2.5个字符
            )
            
            
            # 如果在合理范围内，合并
            if reasonable_bbox:
                return True
            
            # 即使边界框稍大，如果组件数量不多也合并（可能是复杂字符）
            return len(group) <= 3
        
        # 组件太多，可能是多个字符，不合并
        return False
    
    def post_process_small_fragments(self, components, original_mask):
        """后处理：强制合并剩余的小片段到最近的大组件"""
        if len(components) <= 1:
            return components
        
        # 计算组件的面积统计
        areas = [comp[2] for comp in components]
        median_area = np.median(areas)
        
        # 分离大组件和小片段
        large_components = []
        small_fragments = []
        
        for comp in components:
            comp_id, comp_mask, area, centroid = comp
            if area >= median_area * 0.3:  # 面积大于中位数30%的认为是主要组件
                large_components.append(comp)
            else:
                small_fragments.append(comp)
        
        if not small_fragments or not large_components:
            return components
        
        
        # 将小片段合并到最近的大组件
        final_components = []
        
        for large_comp in large_components:
            large_id, large_mask, large_area, large_centroid = large_comp
            merged_mask = large_mask.copy()
            
            # 查找需要合并到这个大组件的小片段
            fragments_to_merge = []
            for small_comp in small_fragments[:]:  # 使用切片复制，允许修改原列表
                small_id, small_mask, small_area, small_centroid = small_comp
                
                # 计算距离
                dx = large_centroid[0] - small_centroid[0]
                dy = large_centroid[1] - small_centroid[1]
                distance = np.sqrt(dx*dx + dy*dy)
                
                # 估计字符尺寸
                estimated_size = np.sqrt(large_area)
                
                # 如果小片段距离大组件很近，合并它
                if distance < estimated_size * 1.5:  # 距离阈值
                    fragments_to_merge.append(small_comp)
                    small_fragments.remove(small_comp)  # 从待处理列表中移除
            
            # 合并找到的片段
            for fragment in fragments_to_merge:
                _, frag_mask, _, _ = fragment
                merged_mask = np.maximum(merged_mask, frag_mask)
            
            # 更新组件信息
            merged_area = np.sum(merged_mask > 0)
            merged_centroid = self.calculate_centroid((merged_mask > 0).astype(np.uint8))
            final_components.append((large_id, merged_mask, merged_area, merged_centroid))
        
        # 添加未被合并的小片段（距离所有大组件都太远）
        for remaining_fragment in small_fragments:
            final_components.append(remaining_fragment)
        
        return final_components

    def get_largest_contour(self, mask):
        """获取遮罩中最大的轮廓"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)
    
    def preprocess_for_text(self, binary_mask):
        """针对文字的形态学预处理，更积极地连接分散的字符部分"""
        # 多级形态学处理策略
        
        # 第一级：使用小核进行基础连接
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        processed = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_small, iterations=1)
        
        # 第二级：使用中等大小的核进行更强的连接
        kernel_medium = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel_medium, iterations=1)
        
        # 第三级：针对文字特点，使用水平和垂直核分别处理
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 3))
        kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 7))
        
        # 水平连接（连接左右分离的部分）
        h_processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel_horizontal, iterations=1)
        # 垂直连接（连接上下分离的部分）
        v_processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel_vertical, iterations=1)
        
        # 合并两个方向的处理结果
        processed = cv2.bitwise_or(h_processed, v_processed)
        
        # 清理小噪声
        kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel_clean, iterations=1)
        
        # 检查处理效果
        original_components = self.count_components(binary_mask)
        processed_components = self.count_components(processed)
        
        
        # 如果组件数量减少太多（超过80%），可能过度连接了，使用更保守的策略
        if processed_components < original_components * 0.2:
            # 回退到更温和的处理
            kernel_gentle = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4, 4))
            processed = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_gentle, iterations=2)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel_clean, iterations=1)
        
        return processed
    
    def count_components(self, binary_mask):
        """计算二值图像中的连通组件数量"""
        num_labels, _, _, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
        return num_labels - 1  # 减去背景组件
    
    def calculate_centroid(self, mask):
        """计算遮罩的质心"""
        # 确保mask是数值类型，而不是布尔类型
        if mask.dtype == bool:
            mask = mask.astype(np.uint8)
        
        moments = cv2.moments(mask)
        if moments["m00"] == 0:
            return (0, 0)
        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        return (cx, cy)

# 让ComfyUI识别这个节点
NODE_CLASS_MAPPINGS = {
    "MaskSplitter": MaskSplitter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskSplitter": "遮罩拆分"
}
