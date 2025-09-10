import os
import numpy as np
from PIL import Image
import torch
import folder_paths
import comfy.utils
from io import BytesIO
import cairosvg

class SVGToImage:
    """
    SVG to PNG/JPG conversion node for ComfyUI with transparency mask support
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "svg_input": ("STRING", {
                    "multiline": True,
                    "default": "<svg width='100' height='100' xmlns='http://www.w3.org/2000/svg'><rect width='100' height='100' fill='red'/></svg>"
                }),
                "width": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 8192,
                    "step": 64
                }),
                "height": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 8192,
                    "step": 64
                }),
                "keep_aspect_ratio": (["true", "false"], {
                    "default": "true"
                }),
                "scale_method": (["lanczos", "bicubic", "hamming", "bilinear", "box", "nearest"], {
                    "default": "lanczos"
                }),
                "multiple_of": (["none", "8", "16", "32", "64", "128"], {
                    "default": "none"
                }),
                "dpi": ("INT", {
                    "default": 96,
                    "min": 72,
                    "max": 600,
                    "step": 1
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
                "use_cuda": (["enabled", "disabled"], {
                    "default": "disabled"
                }),
                "mask_type": (["auto", "white", "alpha"], {
                    "default": "auto"
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "convert_svg"
    CATEGORY = "image/conversion"

    def convert_svg(self, svg_input, width, height, keep_aspect_ratio, scale_method, multiple_of, dpi, output_format, quality, use_cuda, mask_type):
        # Validate input parameters
        if not svg_input.strip():
            raise ValueError("SVG input cannot be empty")
            
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be greater than 0")
            
        # Handle multiple of constraint
        if multiple_of != "none":
            multiple = int(multiple_of)
            width = max(multiple, (width // multiple) * multiple)
            height = max(multiple, (height // multiple) * multiple)

        # Convert SVG string to PNG bytes
        try:
            # First, convert SVG to get the original dimensions
            png_data_original = cairosvg.svg2png(
                bytestring=svg_input.encode('utf-8'),
                dpi=dpi
            )
            
            # Get original image to calculate aspect ratio
            original_image = Image.open(BytesIO(png_data_original))
            original_width, original_height = original_image.size
            
            # Calculate target dimensions while preserving aspect ratio if needed
            if keep_aspect_ratio == "true":
                ratio = min(width / original_width, height / original_height)
                target_width = int(original_width * ratio)
                target_height = int(original_height * ratio)
                
                # Ensure dimensions are not zero
                target_width = max(1, target_width)
                target_height = max(1, target_height)
                
                # Convert with target dimensions
                png_data = cairosvg.svg2png(
                    bytestring=svg_input.encode('utf-8'),
                    output_width=target_width,
                    output_height=target_height,
                    dpi=dpi
                )
            else:
                # Convert with specified dimensions
                png_data = cairosvg.svg2png(
                    bytestring=svg_input.encode('utf-8'),
                    output_width=width,
                    output_height=height,
                    dpi=dpi
                )
                
        except Exception as e:
            raise Exception(f"SVG conversion failed: {str(e)}")

        # Convert PNG bytes to PIL Image
        try:
            image = Image.open(BytesIO(png_data))
        except Exception as e:
            raise Exception(f"Failed to parse SVG conversion result: {str(e)}")
        
        # Check if image has alpha channel
        has_alpha = image.mode == 'RGBA'
        
        # Convert to RGB or RGBA depending on output format
        if output_format == "jpg" or not has_alpha:
            rgb_image = image.convert("RGB")
        else:
            rgb_image = image.convert("RGBA")
        
        # Create mask
        try:
            if mask_type == "white":
                # White mask
                mask = torch.ones((rgb_image.height, rgb_image.width), dtype=torch.float32)
            elif mask_type == "alpha" and has_alpha:
                # Use alpha channel as mask
                alpha_channel = image.getchannel("A")
                mask_np = np.array(alpha_channel).astype(np.float32) / 255.0
                mask = torch.from_numpy(mask_np)
            else:
                # Auto selection: use alpha if available, otherwise use white mask
                if has_alpha:
                    alpha_channel = image.getchannel("A")
                    mask_np = np.array(alpha_channel).astype(np.float32) / 255.0
                    mask = torch.from_numpy(mask_np)
                else:
                    mask = torch.ones((rgb_image.height, rgb_image.width), dtype=torch.float32)
        except Exception as e:
            # If mask creation fails, use white mask as fallback
            print(f"Mask creation failed, using white mask: {str(e)}")
            mask = torch.ones((rgb_image.height, rgb_image.width), dtype=torch.float32)
        
        # Convert to ComfyUI format
        try:
            image_np = np.array(rgb_image.convert("RGB")).astype(np.float32) / 255.0
        except Exception as e:
            raise Exception(f"Image conversion failed: {str(e)}")
        
        # Use CUDA acceleration (if enabled and available)
        cuda_available = torch.cuda.is_available() and use_cuda == "enabled"
        device = torch.device("cuda") if cuda_available else torch.device("cpu")
        
        try:
            image_tensor = torch.from_numpy(image_np).to(device)[None,]
            mask = mask.to(device)
        except Exception as e:
            # Fall back to CPU if CUDA memory is insufficient
            if "CUDA" in str(e).upper():
                print(f"CUDA memory insufficient, falling back to CPU: {str(e)}")
                device = torch.device("cpu")
                image_tensor = torch.from_numpy(image_np)[None,]
                mask = mask.cpu() if mask.is_cuda else mask
            else:
                raise Exception(f"Tensor creation failed: {str(e)}")
        
        # Save output image
        try:
            output_dir = folder_paths.get_output_directory()
            filename = f"svg_converted_{comfy.utils.get_datetime_string()}.{output_format}"
            output_path = os.path.join(output_dir, filename)
            
            if output_format == "jpg":
                rgb_image.convert("RGB").save(output_path, "JPEG", quality=quality)
            else:
                if has_alpha and rgb_image.mode == 'RGBA':
                    rgb_image.save(output_path, "PNG")
                else:
                    rgb_image.convert("RGB").save(output_path, "PNG")
        except Exception as e:
            print(f"Failed to save image: {str(e)}")
            # Don't raise exception as main function (returning tensors) still succeeds
        
        return (image_tensor, mask.unsqueeze(0))

# Node registration
NODE_CLASS_MAPPINGS = {
    "SVGToImage": SVGToImage
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SVGToImage": "SVG to Image"
}