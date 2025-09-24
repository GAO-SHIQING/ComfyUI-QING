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
                "text_preservation": (["auto", "aggressive", "disabled"], {
                    "default": "auto",
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
                print(f"警告: 有 {missing_pixels} 个像素未被任何组件包含，已创建额外组件")
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
            print("警告: 未找到任何组件，返回原始遮罩")
        
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
        """简单启发式方法判断组件是否可能是文字"""
        # 创建二值掩码用于轮廓检测
        binary_mask = (mask > 0).astype(np.uint8)
        
        # 计算轮廓
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return False
        
        # 获取外接矩形
        x, y, w, h = cv2.boundingRect(contours[0])
        
        # 计算宽高比和填充率
        aspect_ratio = w / max(h, 1)
        fill_ratio = area / (w * h) if w * h > 0 else 0
        
        # 文字通常具有特定的宽高比和填充率
        return (0.1 < aspect_ratio < 10 and  # 合理的宽高比范围
                0.2 < fill_ratio < 0.9)      # 合理的填充率范围
    
    def group_text_components(self, text_components):
        """将空间上接近的文字组件分组"""
        if len(text_components) <= 1:
            return [text_components]
        
        # 计算组件之间的平均高度
        heights = []
        for comp_id, comp_mask, area, centroid, idx in text_components:
            binary_mask = (comp_mask > 0).astype(np.uint8)
            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                x, y, w, h = cv2.boundingRect(contours[0])
                heights.append(h)
        
        avg_height = np.mean(heights) if heights else 50
        
        # 根据空间接近度分组
        groups = []
        used_indices = set()
        
        for i, (comp_id1, comp_mask1, area1, centroid1, idx1) in enumerate(text_components):
            if i in used_indices:
                continue
                
            group = [(comp_id1, comp_mask1, area1, centroid1, idx1)]
            used_indices.add(i)
            
            for j, (comp_id2, comp_mask2, area2, centroid2, idx2) in enumerate(text_components):
                if j in used_indices or i == j:
                    continue
                
                # 计算组件之间的距离
                dx = centroid1[0] - centroid2[0]
                dy = centroid1[1] - centroid2[1]
                distance = np.sqrt(dx*dx + dy*dy)
                
                # 如果距离小于平均高度的两倍，认为是同一文字的一部分
                if distance < avg_height * 2:
                    group.append((comp_id2, comp_mask2, area2, centroid2, idx2))
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups

    def get_largest_contour(self, mask):
        """获取遮罩中最大的轮廓"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        return max(contours, key=cv2.contourArea)
    
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
    "MaskSplitter": "Mask Splitter"
}
