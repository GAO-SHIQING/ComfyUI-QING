import torch
import numpy as np
from scipy import ndimage

class MaskFill:
    """
    遮罩填充节点
    功能：填充遮罩中的孔洞和漏洞，使遮罩区域更加完整
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK", {"tooltip": "输入遮罩"}),
                "invert_fill": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "反转填充：填充外部区域而非内部孔洞"
                }),
                "size_info": (["original", "mask_content"], {
                    "default": "mask_content",
                    "tooltip": "尺寸信息：original(原始张量尺寸) 或 mask_content(遮罩内容区域尺寸)"
                }),
            },
        }

    CATEGORY = "🎨QING/遮罩处理"
    RETURN_TYPES = ("MASK", "INT", "INT")
    RETURN_NAMES = ("mask", "width", "height")
    FUNCTION = "fill_mask"
    OUTPUT_NODE = False

    def fill_mask(self, mask, invert_fill=False, size_info="mask_content"):
        """
        主处理函数：执行遮罩填充操作
        
        参数:
            mask: 输入遮罩张量
            invert_fill: 是否反转填充
            size_info: 尺寸信息类型（original/mask_content）
            
        返回:
            tuple: (填充后的遮罩, 宽度, 高度)
        """
        # 检查输入是否有效
        if mask is None or mask.numel() == 0:
            raise ValueError("输入遮罩不能为空")
        
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
            processed_mask = self._process_single_mask(single_mask, invert_fill)
            processed_masks.append(processed_mask)
        
        # 合并结果
        result = np.stack(processed_masks, axis=0)
        
        # 根据选择计算尺寸信息
        if size_info == "original":
            # 原始张量尺寸
            height = int(result.shape[1])
            width = int(result.shape[2])
        else:  # mask_content
            # 遮罩内容区域尺寸（边界框）
            width, height = self._get_mask_content_size(result)
        
        # 转换回torch张量
        result_tensor = torch.from_numpy(result).to(device)
        
        return (result_tensor, width, height)
    
    def _process_single_mask(self, mask, invert_fill):
        """
        处理单个遮罩
        
        参数:
            mask: 单个遮罩数组
            invert_fill: 是否反转填充（填充外部区域而非内部孔洞）
            
        返回:
            处理后的遮罩数组
        """
        # 二值化遮罩
        binary_mask = (mask > 0.5).astype(np.uint8)
        
        # 使用二值填充方法填充所有封闭孔洞
        filled_mask = ndimage.binary_fill_holes(binary_mask).astype(np.uint8)
        
        # 如果需要反转填充，对填充结果进行反转
        # 这样可以填充外部区域而非内部孔洞
        if invert_fill:
            filled_mask = 1 - filled_mask
        
        return filled_mask.astype(np.float32)
    
    def _get_mask_content_size(self, mask_array):
        """
        获取遮罩内容区域的尺寸（边界框）
        
        参数:
            mask_array: 遮罩数组 (可能是批次)
            
        返回:
            tuple: (宽度, 高度) - 遮罩非零区域的边界框尺寸
        """
        # 如果是批次，取第一个遮罩
        if len(mask_array.shape) == 3:
            mask_2d = mask_array[0]
        else:
            mask_2d = mask_array
        
        # 二值化遮罩
        binary_mask = (mask_2d > 0.5).astype(np.uint8)
        
        # 查找非零区域
        rows = np.any(binary_mask, axis=1)
        cols = np.any(binary_mask, axis=0)
        
        # 如果遮罩完全为空，返回0
        if not np.any(rows) or not np.any(cols):
            return 0, 0
        
        # 获取边界
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        
        # 计算宽度和高度
        width = int(xmax - xmin + 1)
        height = int(ymax - ymin + 1)
        
        return width, height


# 节点注册
NODE_CLASS_MAPPINGS = {
    "MaskFill": MaskFill
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskFill": "遮罩填充"
}
