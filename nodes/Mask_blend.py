import torch
import torch.nn.functional as F
import time
from enum import Enum

class BlendMode(Enum):
    """blend_mode（精简常用）"""
    ADD = "add"
    SUBTRACT = "subtract"
    INTERSECT = "intersect"
    XOR = "xor"
    INVERT = "invert"
    MAX = "max"
    MIN = "min"
    SCREEN = "screen"

class GradientType(Enum):
    """渐变类型枚举"""
    NONE = "none"
    LINEAR = "linear"
    RADIAL = "radial"
    ANGULAR = "angular"
    DIAMOND = "diamond"

class GradientDirection(Enum):
    """渐变方向枚举"""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    DIAGONAL = "diagonal"
    RADIAL_IN = "radial_in"
    RADIAL_OUT = "radial_out"

class StrokePosition(Enum):
    """描边位置枚举"""
    CENTER = "center"
    INSIDE = "inside"
    OUTSIDE = "outside"

class MaskBlend:
    """
    MaskBlend节点 - 多遮罩混合处理
    
    功能:
    - 支持多种混合模式: 相加、相减、交集、异或等
    - 边缘效果: 羽化、渐变、描边
    - 阈值控制和反转选项
    
    使用示例:
    1. 将两个遮罩相加并添加羽化效果
    2. 使用交集模式创建精确选区
    3. 添加描边效果突出显示边缘
    
    注意事项:
    - 所有输入遮罩会自动调整到相同尺寸
    - 大半径羽化可能会增加处理时间
    """
    
    def __init__(self):
        """初始化，预计算常用核和渐变"""
        self.precomputed_kernels = {}
        self.precomputed_gradients = {}
        self.debug_info = {}

    # ------------------------------
    # 参数校验与规范化
    # ------------------------------
    def _normalize_bool_str(self, value, default="false"):
        if isinstance(value, str):
            v = value.lower()
            return "true" if v in ("1", "true", "yes", "y") else "false"
        if isinstance(value, (int, float)):
            return "true" if value else "false"
        return default

    def _validate_and_normalize_params(self,
                                       blend_mode,
                                       feather_radius,
                                       invert_mask,
                                       threshold,
                                       gradient_type,
                                       gradient_direction,
                                       gradient_intensity,
                                       stroke_width,
                                       stroke_position):
        # 校验枚举
        valid_blend = {m.value for m in BlendMode}
        blend_mode = blend_mode if blend_mode in valid_blend else BlendMode.ADD.value

        valid_grad_type = {g.value for g in GradientType}
        gradient_type = gradient_type if gradient_type in valid_grad_type else GradientType.NONE.value

        valid_grad_dir = {d.value for d in GradientDirection}
        gradient_direction = gradient_direction if gradient_direction in valid_grad_dir else GradientDirection.HORIZONTAL.value

        valid_stroke_pos = {s.value for s in StrokePosition}
        stroke_position = stroke_position if stroke_position in valid_stroke_pos else StrokePosition.CENTER.value

        # 数值范围
        def clamp_int(v, lo, hi):
            try:
                return int(max(lo, min(hi, int(v))))
            except Exception:
                return lo

        def clamp_float(v, lo, hi):
            try:
                return float(max(lo, min(hi, float(v))))
            except Exception:
                return lo

        feather_radius = clamp_int(feather_radius, 0, 100)
        threshold = clamp_int(threshold, 0, 100)
        stroke_width = clamp_int(stroke_width, 0, 50)
        gradient_intensity = clamp_float(gradient_intensity, 0.0, 2.0)

        invert_mask = self._normalize_bool_str(invert_mask)

        return {
            "blend_mode": blend_mode,
            "feather_radius": feather_radius,
            "invert_mask": invert_mask,
            "threshold": threshold,
            "gradient_type": gradient_type,
            "gradient_direction": gradient_direction,
            "gradient_intensity": gradient_intensity,
            "stroke_width": stroke_width,
            "stroke_position": stroke_position,
        }
    
    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点的输入参数，添加详细描述和滑块显示（按功能分组排序）
        """
        blend_modes = [mode.value for mode in BlendMode]
        gradient_types = [gt.value for gt in GradientType]
        gradient_directions = [gd.value for gd in GradientDirection]
        stroke_positions = [sp.value for sp in StrokePosition]

        return {
            "required": {
                # 基础输入
                "mask1": ("MASK", {
                    "default": None,
                    "description": "第一个遮罩（基准尺寸）"
                }),

                # 混合设置
                "blend_mode": (blend_modes, {
                    "default": BlendMode.ADD.value,
                    "description": "blend_mode"
                }),
                "feather_radius": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "display": "slider",
                    "description": "feather_radius（像素）"
                }),
                "invert_mask": (["false", "true"], {
                    "default": "false",
                    "description": "是否反转输出遮罩"
                }),
                "threshold": ("INT", {
                    "default": 50,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "display": "slider",
                    "description": "二值阈值（%）。50 为常规半阈值"
                }),
            },
            "optional": {
                # 模式：专家模式
                "expert_mode": (["false", "true"], {
                    "default": "false",
                    "description": "专家模式：开启后显示并启用进阶参数"
                }),
                # 其他遮罩输入
                "mask2": ("MASK", {
                    "default": None,
                    "description": "第二个遮罩（可选）"
                }),
                "mask3": ("MASK", {
                    "default": None,
                    "description": "第三个遮罩（可选）"
                }),
                "mask4": ("MASK", {
                    "default": None,
                    "description": "第四个遮罩（可选）"
                }),
                "mask5": ("MASK", {
                    "default": None,
                    "description": "第五个遮罩（可选）"
                }),
                # 边缘与效果（进阶，需 expert_mode=true）
                "stroke_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 50,
                    "step": 1,
                    "display": "slider",
                    "description": "描边宽度（像素，专家模式）"
                }),
                "stroke_position": (stroke_positions, {
                    "default": StrokePosition.CENTER.value,
                    "description": "描边位置（专家模式）"
                }),
                # 渐变
                "gradient_type": (gradient_types, {
                    "default": GradientType.NONE.value,
                    "description": "渐变类型（专家模式）"
                }),
                "gradient_direction": (gradient_directions, {
                    "default": GradientDirection.HORIZONTAL.value,
                    "description": "渐变方向（专家模式）"
                }),
                "gradient_intensity": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider",
                    "description": "渐变强度（专家模式）"
                }),
            },
        }

    # 节点信息
    RETURN_TYPES = ("MASK", "IMAGE", "MASK")  # 返回遮罩、图像和原始混合结果
    RETURN_NAMES = ("mask", "image", "raw_mask")
    FUNCTION = "blend_masks"
    CATEGORY = "QING/遮罩处理"

    def blend_masks(self, mask1, blend_mode, feather_radius, invert_mask, threshold, 
                   mask2=None, mask3=None, mask4=None, mask5=None, gradient_type=GradientType.NONE.value, 
                   gradient_direction=GradientDirection.HORIZONTAL.value, gradient_intensity=1.0,
                   stroke_width=0, stroke_position=StrokePosition.CENTER.value,
                   expert_mode="false"):
        """
        主处理函数：混合多个遮罩并应用指定的效果
        
        参数:
            mask1: 第一个遮罩张量
            blend_mode: blend_mode
            feather_radius: feather_radius
            invert_mask: 是否反转遮罩
            threshold: 混合阈值(0-100)
            mask2: 可选第二个遮罩
            mask3: 可选第三个遮罩
            gradient_type: 渐变类型
            gradient_direction: 渐变方向
            gradient_intensity: 渐变强度
            stroke_width: 描边宽度
            stroke_position: 描边位置
            
        返回:
            tuple: 处理后的遮罩、图像和原始混合结果
        """
        # 记录开始时间
        start_time = time.time()
        self.debug_info = {}
        
        # 验证输入
        if mask1 is None:
            raise ValueError("至少需要提供一个遮罩输入")
        
        # 检查遮罩尺寸
        if mask1.numel() == 0:
            raise ValueError("输入遮罩不能为空")
        
        # 检查遮罩维度
        if mask1.dim() < 2 or mask1.dim() > 4:
            raise ValueError(f"遮罩维度必须在2-4之间，当前为{mask1.dim()}")

        # 规范化参数
        params = self._validate_and_normalize_params(
            blend_mode, feather_radius, invert_mask, threshold,
            gradient_type, gradient_direction, gradient_intensity,
            stroke_width, stroke_position,
        )
        # 专家模式：关闭时屏蔽进阶参数
        expert_mode = self._normalize_bool_str(expert_mode)
        if expert_mode != "true":
            params["gradient_type"] = GradientType.NONE.value
            params["stroke_width"] = 0
        blend_mode = params["blend_mode"]
        feather_radius = params["feather_radius"]
        invert_mask = params["invert_mask"]
        threshold = params["threshold"]
        gradient_type = params["gradient_type"]
        gradient_direction = params["gradient_direction"]
        gradient_intensity = params["gradient_intensity"]
        stroke_width = params["stroke_width"]
        stroke_position = params["stroke_position"]
        
        # 确保遮罩在同一个设备上
        device = mask1.device
        
        # 收集所有遮罩并批量调整尺寸（以第一个遮罩为基准）
        masks = [mask1]
        if mask2 is not None:
            masks.append(mask2.to(device))
        if mask3 is not None:
            masks.append(mask3.to(device))
        if mask4 is not None:
            masks.append(mask4.to(device))
        if mask5 is not None:
            masks.append(mask5.to(device))

        # 标准化形状到 (N,1,H,W)
        target_size = mask1.shape[-2:] if mask1.dim() > 2 else mask1.shape
        normalized = []
        for m in masks:
            t = m
            # 确保浮点 0-1
            if not torch.is_floating_point(t):
                t = t.float()
            t = torch.clamp(t, 0, 1)
            if t.dim() == 2:
                t = t.unsqueeze(0)
            if t.dim() == 3:
                t = t.unsqueeze(1)
            normalized.append(t)

        batched = torch.cat(normalized, dim=0)
        if batched.shape[-2:] != target_size:
            batched = F.interpolate(batched, size=target_size, mode='bilinear', align_corners=False)

        # 还原到列表 (可能有批维度)
        resized_masks = [batched[i] for i in range(batched.shape[0])]
        resized_masks = [t.squeeze(1) for t in resized_masks]
        
        # 应用混合模式
        if len(resized_masks) == 1:
            blended_mask = resized_masks[0]
        else:
            blended_mask = self.apply_blend_mode(resized_masks, blend_mode, threshold/100.0)
        
        # 保存原始混合结果
        raw_blended = blended_mask.clone()
        
        # 确保遮罩值在0-1范围内
        blended_mask = torch.clamp(blended_mask, 0, 1)
        
        # 应用边缘效果
        effect_params = {
            "feather_radius": feather_radius,
            "gradient_type": gradient_type,
            "gradient_direction": gradient_direction,
            "gradient_intensity": gradient_intensity,
            "stroke_width": stroke_width,
            "stroke_position": stroke_position,
        }
        
        blended_mask = self.apply_edge_effects(blended_mask, effect_params)
        
        # 应用阈值（二值化）
        # 注意：如果用户想要保持原始灰度值，可以设置阈值为0
        if threshold > 0:
            threshold_value = threshold / 100.0
            blended_mask = (blended_mask > threshold_value).float()
        
        # 应用反转
        if invert_mask == "true":
            blended_mask = 1 - blended_mask
        
        # 创建图像输出
        image_output = self.mask_to_image(blended_mask)
        
        # 记录处理时间（保留在 debug_info，不打印）
        processing_time = (time.time() - start_time) * 1000
        self.debug_info = {
            "input_count": len(masks),
            "output_size": blended_mask.shape,
            "processing_time_ms": processing_time
        }

        return (blended_mask, image_output, raw_blended)

    # 预设功能已移除

    def apply_blend_mode(self, masks, mode, threshold):
        """
        应用指定的混合模式到多个遮罩，使用更高效的张量操作
        """
        # 将所有遮罩堆叠到一个张量中
        stacked = torch.stack(masks, dim=0)
        
        if mode == BlendMode.ADD.value:
            result = torch.clamp(torch.sum(stacked, dim=0), 0, 1)

        elif mode == BlendMode.SUBTRACT.value:
            if stacked.shape[0] == 1:
                result = stacked[0]
            else:
                result = stacked[0]
                for i in range(1, stacked.shape[0]):
                    result = torch.clamp(result - stacked[i], 0, 1)
                result = torch.clamp(result, 0, 1)

        elif mode == BlendMode.INTERSECT.value:
            result = torch.min(stacked, dim=0)[0]

        elif mode == BlendMode.XOR.value:
            if stacked.shape[0] == 1:
                result = stacked[0]
            elif stacked.shape[0] == 2:
                # 标准XOR：两个遮罩的异或
                result = torch.abs(stacked[0] - stacked[1])
            else:
                # 多个遮罩的XOR：使用奇偶性规则
                result = stacked[0]
                for i in range(1, stacked.shape[0]):
                    # 使用逻辑XOR：(A + B) - 2*(A * B)
                    result = result + stacked[i] - 2 * result * stacked[i]

        elif mode == BlendMode.INVERT.value:
            result = 1 - stacked[0]
            
        elif mode == BlendMode.MAX.value:
            result = torch.max(stacked, dim=0)[0]
            
        elif mode == BlendMode.MIN.value:
            result = torch.min(stacked, dim=0)[0]
            
        elif mode == BlendMode.SCREEN.value:
            result = 1 - torch.prod(1 - stacked, dim=0)
            
        else:
            result = stacked[0]  # 默认使用第一个遮罩
            
        return torch.clamp(result, 0, 1)

    def _soft_light_g(self, x):
        """软光模式的辅助函数"""
        return torch.where(x < 0.25, 
                          ((16 * x - 12) * x + 4) * x,
                          torch.sqrt(x))

    def apply_edge_effects(self, mask, effects):
        """
        应用多种边缘效果
        """
        result = mask.clone()
        
        # 羽化
        if effects.get("feather_radius", 0) > 0:
            result = self.apply_feathering(result, effects["feather_radius"])
        
        # 渐变
        if effects.get("gradient_type", GradientType.NONE.value) != GradientType.NONE.value:
            result = self.apply_gradient(
                result, 
                effects["gradient_type"], 
                effects.get("gradient_direction", GradientDirection.HORIZONTAL.value),
                effects.get("gradient_intensity", 1.0)
            )
        
        # 描边
        if effects.get("stroke_width", 0) > 0:
            result = self.apply_stroke(
                result, 
                effects["stroke_width"], 
                effects.get("stroke_position", StrokePosition.CENTER.value)
            )
        
        # 斜面效果
        # 已移除 bevel/texture 功能（简化节点）
        
        return result

    def apply_feathering(self, mask, radius):
        """
        应用羽化效果到遮罩边缘，使用优化方法
        """
        if radius == 0:
            return mask
        
        # 统一使用分离高斯卷积（GPU/CPU 通用，缓存核）
        kernel_1d = self.get_gaussian_kernel(radius, device=mask.device, dtype=mask.dtype)

        if mask.dim() == 2:
            mask = mask.unsqueeze(0).unsqueeze(0)
        elif mask.dim() == 3:
            mask = mask.unsqueeze(1)

        # 横向卷积 (1,1,1,K)
        kx = kernel_1d.view(1, 1, 1, -1)
        blurred = F.conv2d(mask, kx, padding=(0, radius))

        # 纵向卷积 (1,1,K,1)
        ky = kernel_1d.view(1, 1, -1, 1)
        blurred = F.conv2d(blurred, ky, padding=(radius, 0))

        # 恢复原始维度
        if blurred.dim() == 4:
            blurred = blurred.squeeze(1)
        elif blurred.dim() == 3:
            blurred = blurred.squeeze(0)

        return blurred

    def get_gaussian_kernel(self, radius, device='cpu', dtype=torch.float32):
        """生成并缓存一维高斯核（按半径与设备/精度缓存）"""
        cache_key = (int(radius), str(device), str(dtype))
        if cache_key in self.precomputed_kernels:
            return self.precomputed_kernels[cache_key]

        if radius <= 0:
            k = torch.tensor([1.0], device=device, dtype=dtype)
            self.precomputed_kernels[cache_key] = k
            return k

        kernel_size = radius * 2 + 1
        x = torch.arange(kernel_size, device=device, dtype=dtype) - radius
        sigma = max(radius / 2.0, 1e-6)
        kernel = torch.exp(-x * x / (2 * sigma * sigma))
        kernel = kernel / kernel.sum()
        self.precomputed_kernels[cache_key] = kernel
        return kernel

    def _compute_gradient(self, gradient_type, gradient_direction, height, width, device):
        """计算渐变矩阵"""
        if gradient_type == GradientType.LINEAR.value:
            if gradient_direction == GradientDirection.HORIZONTAL.value:
                gradient = torch.linspace(0, 1, width, device=device)
                gradient = gradient.unsqueeze(0).repeat(height, 1)
            elif gradient_direction == GradientDirection.VERTICAL.value:
                gradient = torch.linspace(0, 1, height, device=device)
                gradient = gradient.unsqueeze(1).repeat(1, width)
            elif gradient_direction == GradientDirection.DIAGONAL.value:
                x = torch.linspace(0, 1, width, device=device)
                y = torch.linspace(0, 1, height, device=device)
                X, Y = torch.meshgrid(x, y, indexing='xy')
                gradient = (X + Y) / 2
            else:
                gradient = torch.linspace(0, 1, width, device=device)
                gradient = gradient.unsqueeze(0).repeat(height, 1)
                
        elif gradient_type == GradientType.RADIAL.value:
            center_x, center_y = width // 2, height // 2
            x = torch.arange(width, device=device).float() - center_x
            y = torch.arange(height, device=device).float() - center_y
            x = x / max(center_x, 1)
            y = y / max(center_y, 1)
            X, Y = torch.meshgrid(x, y, indexing='xy')
            
            if gradient_direction == GradientDirection.RADIAL_IN.value:
                gradient = torch.sqrt(X**2 + Y**2)
                gradient = gradient / gradient.max()
                gradient = 1 - gradient
            else:
                gradient = torch.sqrt(X**2 + Y**2)
                gradient = gradient / gradient.max()
                
        elif gradient_type == GradientType.ANGULAR.value:
            center_x, center_y = width // 2, height // 2
            x = torch.arange(width, device=device).float() - center_x
            y = torch.arange(height, device=device).float() - center_y
            X, Y = torch.meshgrid(x, y, indexing='xy')
            gradient = torch.atan2(Y, X)
            gradient = (gradient + torch.pi) / (2 * torch.pi)
            
        elif gradient_type == GradientType.DIAMOND.value:
            center_x, center_y = width // 2, height // 2
            x = torch.arange(width, device=device).float() - center_x
            y = torch.arange(height, device=device).float() - center_y
            x = torch.abs(x) / max(center_x, 1)
            y = torch.abs(y) / max(center_y, 1)
            X, Y = torch.meshgrid(x, y, indexing='xy')
            gradient = X + Y
            gradient = gradient / gradient.max()
        else:
            gradient = torch.ones(height, width, device=device)
            
        return gradient

    def apply_gradient(self, mask, gradient_type, gradient_direction, intensity=1.0):
        """
        应用渐变效果，支持多种类型和方向
        """
        if mask.numel() == 0:
            return mask
            
        height, width = mask.shape[-2:]
        if height <= 0 or width <= 0:
            return mask
            
        device = mask.device
        
        # 如果没有渐变效果，直接返回
        if gradient_type == GradientType.NONE.value:
            return mask
        
        # 检查是否有缓存的渐变
        gradient_key = (gradient_type, gradient_direction, height, width, str(device))
        if gradient_key in self.precomputed_gradients:
            gradient = self.precomputed_gradients[gradient_key]
        else:
            # 计算并缓存渐变
            gradient = self._compute_gradient(gradient_type, gradient_direction, height, width, device)
            self.precomputed_gradients[gradient_key] = gradient
        
        # 应用渐变强度
        gradient = gradient ** intensity
        
        # 应用渐变到遮罩
        if mask.dim() == 3:
            gradient = gradient.unsqueeze(0)
        
        return mask * gradient

    def apply_stroke(self, mask, stroke_width, stroke_position):
        """
        应用描边效果，支持不同位置
        """
        if stroke_width == 0:
            return mask
        
        # 使用膨胀和腐蚀操作创建描边
        if mask.dim() == 2:
            mask = mask.unsqueeze(0).unsqueeze(0)
        elif mask.dim() == 3:
            mask = mask.unsqueeze(1)
        
        # 创建卷积核
        kernel_size = stroke_width * 2 + 1
        kernel = torch.ones(1, 1, kernel_size, kernel_size, device=mask.device)
        
        # 使用形态学操作：膨胀和腐蚀
        # 膨胀：卷积后判断是否大于0
        dilated = F.conv2d(mask, kernel, padding=stroke_width)
        dilated = (dilated > 0).float()
        
        # 腐蚀：先反转遮罩，膨胀后再反转
        inverted_mask = 1 - mask
        eroded_inv = F.conv2d(inverted_mask, kernel, padding=stroke_width)
        eroded = 1 - (eroded_inv > 0).float()
        
        # 根据位置计算描边
        if stroke_position == StrokePosition.CENTER.value:
            # 中心描边（膨胀区域减去腐蚀区域）
            stroke = dilated - eroded
        elif stroke_position == StrokePosition.INSIDE.value:
            # 内部描边（原始遮罩减去腐蚀区域）
            stroke = mask - eroded
        else:  # OUTSIDE
            # 外部描边（膨胀区域减去原始遮罩）
            stroke = dilated - mask
        
        # 合并原始遮罩和描边
        result = torch.clamp(mask + stroke, 0, 1)
        
        # 恢复原始维度
        if result.dim() == 4:
            result = result.squeeze(1)
        elif result.dim() == 3:
            result = result.squeeze(0)
            
        return result

    # 已移除 apply_bevel（功能下线）

    # 已移除 apply_texture（功能下线）

    def mask_to_image(self, mask):
        """
        将遮罩转换为图像张量
        """
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)
        
        # 重复通道以创建RGB图像
        if mask.dim() == 3:
            image = mask.unsqueeze(-1).repeat(1, 1, 1, 3)
        else:
            image = mask.unsqueeze(0).repeat(1, 1, 1, 3)
        
        return image

# 注册节点
NODE_CLASS_MAPPINGS = {
    "MaskBlend": MaskBlend
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskBlend": "Mask Blend"
}