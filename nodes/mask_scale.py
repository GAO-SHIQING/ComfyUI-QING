# -*- coding: utf-8 -*-
import torch
import numpy as np
from PIL import Image
import comfy.utils

class MaskScale:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mask": ("MASK",),
                "scale_by": (["width", "height", "longest_side", "shortest_side", "total_pixels"], {
                    "default": "longest_side"
                }),
                "target_value": ("INT", {
                    "default": 512,
                    "min": 1,
                    "max": 8192,
                    "step": 1
                }),
                "interpolation": (["nearest", "bilinear", "bicubic", "lanczos"], {
                    "default": "lanczos"
                }),
                "keep_proportions": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "target_width": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1
                }),
                "target_height": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 8192,
                    "step": 1
                }),
            }
        }
    
    RETURN_TYPES = ("MASK", "INT", "INT")
    RETURN_NAMES = ("mask", "width", "height")
    FUNCTION = "scale_mask"
    CATEGORY = "image/mask"
    
    def scale_mask(self, mask, scale_by, target_value, interpolation, keep_proportions, target_width=0, target_height=0):
        # Input validation
        if mask is None:
            raise ValueError("Input mask cannot be None")
        
        # Ensure input is 2D or 3D tensor
        if mask.dim() == 2:
            mask = mask.unsqueeze(0)
        elif mask.dim() != 3:
            raise ValueError(f"Mask dimension should be 2 or 3, got {mask.dim()}")
        
        # Get current mask dimensions
        batch_size, orig_height, orig_width = mask.shape
        
        # If explicit target dimensions are provided, use them
        if target_width > 0 and target_height > 0:
            target_width = max(1, target_width)
            target_height = max(1, target_height)
        else:
            # Calculate target dimensions based on scaling method
            orig_pixels = orig_height * orig_width
            
            if scale_by == "width":
                target_width = target_value
                if keep_proportions:
                    target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                else:
                    target_height = orig_height
                    
            elif scale_by == "height":
                target_height = target_value
                if keep_proportions:
                    target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                else:
                    target_width = orig_width
                    
            elif scale_by == "longest_side":
                if orig_height >= orig_width:
                    target_height = target_value
                    if keep_proportions:
                        target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                    else:
                        target_width = orig_width
                else:
                    target_width = target_value
                    if keep_proportions:
                        target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                    else:
                        target_height = orig_height
                        
            elif scale_by == "shortest_side":
                if orig_height <= orig_width:
                    target_height = target_value
                    if keep_proportions:
                        target_width = max(1, int(round(orig_width * (target_height / orig_height))))
                    else:
                        target_width = orig_width
                else:
                    target_width = target_value
                    if keep_proportions:
                        target_height = max(1, int(round(orig_height * (target_width / orig_width))))
                    else:
                        target_height = orig_height
                        
            elif scale_by == "total_pixels":
                # Calculate scaling factor to achieve target pixel count
                scale_factor = (target_value / orig_pixels) ** 0.5
                target_width = max(1, int(round(orig_width * scale_factor)))
                target_height = max(1, int(round(orig_height * scale_factor)))
                
                # If keeping proportions, fine-tune to get closer to target
                if keep_proportions:
                    actual_pixels = target_width * target_height
                    if abs(actual_pixels - target_value) / target_value > 0.1:
                        alternative_width = max(1, int(round((target_value * orig_width / orig_height) ** 0.5)))
                        alternative_height = max(1, int(round(target_value / alternative_width)))
                        if abs(alternative_width * alternative_height - target_value) < abs(actual_pixels - target_value):
                            target_width, target_height = alternative_width, alternative_height
        
        # Ensure dimensions are at least 1x1
        target_width = max(1, target_width)
        target_height = max(1, target_height)
        
        # Get original device and dtype
        device = mask.device
        dtype = mask.dtype
        
        # Use PIL for high-quality scaling, especially for Lanczos
        if interpolation == "lanczos":
            scaled_masks = []
            for i in range(batch_size):
                # Convert to PIL image
                mask_np = mask[i].cpu().numpy() * 255
                mask_pil = Image.fromarray(mask_np.astype(np.uint8), mode='L')
                
                # Resize with Lanczos interpolation
                mask_pil = mask_pil.resize((target_width, target_height), Image.LANCZOS)
                
                # Convert back to tensor
                mask_np = np.array(mask_pil).astype(np.float32) / 255.0
                mask_tensor = torch.from_numpy(mask_np).to(device=device, dtype=dtype)
                scaled_masks.append(mask_tensor)
            
            scaled_mask = torch.stack(scaled_masks)
        else:
            # Choose PyTorch interpolation mode
            if interpolation == "nearest":
                mode = "nearest"
            elif interpolation == "bilinear":
                mode = "bilinear"
            else:  # bicubic
                mode = "bicubic"
            
            # Ensure data type is suitable for interpolation
            mask_float = mask.float()
            
            # Resize mask
            scaled_mask = torch.nn.functional.interpolate(
                mask_float.unsqueeze(1),
                size=(target_height, target_width),
                mode=mode,
                align_corners=False if mode != "nearest" else None
            ).squeeze(1)
            
            # Convert back to original dtype
            if dtype != torch.float32:
                scaled_mask = scaled_mask.to(dtype)
        
        # Ensure mask values are in 0-1 range
        scaled_mask = torch.clamp(scaled_mask, 0.0, 1.0)
        
        return (scaled_mask, target_width, target_height)

# Node registration
NODE_CLASS_MAPPINGS = {
    "MaskScale": MaskScale
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MaskScale": "Mask Scale"
}