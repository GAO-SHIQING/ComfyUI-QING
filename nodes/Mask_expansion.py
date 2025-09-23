import torch
import torch.nn.functional as F
import numpy as np
import cv2
from scipy import ndimage

class MaskExpansion:
    """
    遮罩扩张节点
    功能：遮罩的扩张和收缩，支持方向性扩张、feather、反转等操作
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK", {"tooltip": "输入遮罩"}),
                "expansion": ("INT", {
                    "default": 15,
                    "min": -100,
                    "max": 100,
                    "step": 1,
                    "display": "slider",
                    "tooltip": "expansion：正数扩张，负数收缩"
                }),
                "feather": ("INT", {
                    "default": 8,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "display": "slider",
                    "tooltip": "羽化强度：数值越大边缘越平滑"
                }),
                "invert_mask": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "invert_mask：处理前后反转遮罩"
                }),
            },
            "optional": {
                "direction_up": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "向上扩张"
                }),
                "direction_down": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "向下扩张"
                }),
                "direction_left": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "向左扩张"
                }),
                "direction_right": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "向右扩张"
                }),
            }
        }

    CATEGORY = "QING/遮罩处理"
    RETURN_TYPES = ("MASK",)
    RETURN_NAMES = ("mask",)
    FUNCTION = "expand_mask"
    OUTPUT_NODE = False

    def expand_mask(self, mask, expansion, feather, invert_mask, 
                   direction_up=True, direction_down=True, direction_left=True, direction_right=True):
        """
        主处理函数：执行遮罩扩张操作
        """
        # 确保遮罩在CPU上处理
        device = mask.device
        mask_np = mask.cpu().numpy()
        
        # 处理批次维度
        if len(mask_np.shape) == 4:
            mask_np = mask_np[:, 0, :, :]  # 移除通道维度
        elif len(mask_np.shape) == 2:
            mask_np = mask_np[np.newaxis, :, :]  # 添加批次维度
        
        # 处理每个遮罩
        processed_masks = []
        for i in range(mask_np.shape[0]):
            single_mask = mask_np[i]
            processed_mask = self._process_single_mask(
                single_mask, expansion, feather, invert_mask,
                direction_up, direction_down, direction_left, direction_right
            )
            processed_masks.append(processed_mask)
        
        # 合并结果
        result = np.stack(processed_masks, axis=0)
        
        # 转换回torch张量
        result_tensor = torch.from_numpy(result).to(device)
        
        return (result_tensor,)
    
    def _process_single_mask(self, mask, expansion, feather, invert_mask,
                           direction_up, direction_down, direction_left, direction_right):
        """
        处理单个遮罩
        """
        # invert_mask
        if invert_mask:
            mask = 1.0 - mask
        
        # 二值化遮罩
        binary_mask = (mask > 0.5).astype(np.uint8)
        
        # 方向性扩张
        if expansion != 0:
            mask = self._directional_expansion(
                binary_mask, expansion,
                direction_up, direction_down, direction_left, direction_right
            )
        
        # 羽化处理
        if feather > 0:
            mask = self._apply_feathering(mask, feather)
        
        return mask.astype(np.float32)
    
    def _directional_expansion(self, mask, expansion, up, down, left, right):
        """
        方向性扩张处理
        """
        if expansion == 0:
            return mask
        
        # 检查是否有方向选择
        has_direction_selected = any([up, down, left, right])
        
        if has_direction_selected:
            # 有方向选择，使用方向扩张
            return self._standard_directional_expansion(mask, expansion, up, down, left, right)
        else:
            # 没有方向选择，使用全方向扩张
            return self._full_directional_expansion(mask, expansion)
    
    def _standard_directional_expansion(self, mask, expansion, up, down, left, right):
        """
        标准方向性扩张 - 按字面意思执行方向
        """
        result = mask.copy()
        
        # 直接按照选择的方向进行扩张或收缩
        if up:
            result = self._expand_in_direction(result, expansion, 'up')
        if down:
            result = self._expand_in_direction(result, expansion, 'down')
        if left:
            result = self._expand_in_direction(result, expansion, 'left')
        if right:
            result = self._expand_in_direction(result, expansion, 'right')
        
        return result
    
    def _expand_in_direction(self, mask, expansion, direction):
        """
        在指定方向进行扩张/收缩 - 使用固定3x3核迭代实现方向性
        """
        if expansion == 0:
            return mask
        
        abs_expansion = abs(expansion)
        is_dilate = expansion > 0
        
        # 为扩张和收缩分别设计核，确保方向一致
        if is_dilate:
            # 扩张核：反向核设计 - 要向哪个方向扩张，核就在相反方向
            if direction == 'up':
                kernel = np.array([[0, 0, 0],
                                 [0, 1, 0],
                                 [0, 1, 0]], dtype=np.uint8)
                
            elif direction == 'down':
                kernel = np.array([[0, 1, 0],
                                 [0, 1, 0],
                                 [0, 0, 0]], dtype=np.uint8)
                
            elif direction == 'left':
                kernel = np.array([[0, 0, 0],
                                 [0, 1, 1],
                                 [0, 0, 0]], dtype=np.uint8)
                
            elif direction == 'right':
                kernel = np.array([[0, 0, 0],
                                 [1, 1, 0],
                                 [0, 0, 0]], dtype=np.uint8)
            else:
                return mask
        else:
            # 收缩核：同向核设计 - 要向哪个方向收缩，核就在那个方向
            if direction == 'up':
                kernel = np.array([[0, 1, 0],
                                 [0, 1, 0],
                                 [0, 0, 0]], dtype=np.uint8)
                
            elif direction == 'down':
                kernel = np.array([[0, 0, 0],
                                 [0, 1, 0],
                                 [0, 1, 0]], dtype=np.uint8)
                
            elif direction == 'left':
                kernel = np.array([[0, 0, 0],
                                 [1, 1, 0],
                                 [0, 0, 0]], dtype=np.uint8)
                
            elif direction == 'right':
                kernel = np.array([[0, 0, 0],
                                 [0, 1, 1],
                                 [0, 0, 0]], dtype=np.uint8)
            else:
                return mask
        
        # 逐步迭代以获得精确的扩张/收缩距离，强度提升30%
        result = mask.copy()
        enhanced_expansion = int(abs_expansion * 1.3)
        for _ in range(enhanced_expansion):
            if is_dilate:
                result = cv2.dilate(result, kernel, iterations=1)
            else:
                result = cv2.erode(result, kernel, iterations=1)
        
        return result
    
    def _full_directional_expansion(self, mask, expansion):
        """
        全方向扩张（当没有选择任何方向时使用）
        """
        if expansion == 0:
            return mask
            
        abs_expansion = abs(expansion)
        is_dilate = expansion > 0
        
        # 使用固定的3x3圆形核，通过迭代实现大扩张
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        
        result = mask.copy()
        enhanced_expansion = int(abs_expansion * 1.3)
        for _ in range(enhanced_expansion):
            if is_dilate:
                result = cv2.dilate(result, kernel, iterations=1)
            else:
                result = cv2.erode(result, kernel, iterations=1)
        
        return result
    
    def _apply_feathering(self, mask, feather_radius):
        """
        应用羽化效果
        """
        if feather_radius <= 0:
            return mask
        
        # 使用高斯模糊进行羽化
        kernel_size = feather_radius * 2 + 1
        sigma = feather_radius / 3.0
        
        # 应用高斯模糊
        feathered = cv2.GaussianBlur(mask.astype(np.float32), (kernel_size, kernel_size), sigma)
        
        return feathered

# 节点注册
NODE_CLASS_MAPPINGS = {
    "MaskExpansion": MaskExpansion
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskExpansion": "遮罩扩张"
}
