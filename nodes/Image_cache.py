# -*- coding: utf-8 -*-
import os
import time
import json
import uuid
import shutil
from datetime import datetime
from PIL import Image
import torch
import numpy as np
import folder_paths

class ImageCache:
    """
    图像缓存节点
    功能：
    - 缓存输入的图像，支持最多99张图像缓存
    - 提供图像预览，显示所有缓存图像（数量与实际缓存数量相等）
    - 达到99张上限时自动保存到实例专用子文件夹并清空缓存
    - 支持自定义保存路径和文件名前缀
    - 支持保存时包含/排除元数据
    - 每个节点实例有独立的目录结构：
      * 保存路径：自定义路径优先，否则保存到output/image_cache_{实例ID}/
      * 预览路径：output/image_cache_{实例ID}/previews/
    """
    
    # 类级别的缓存存储，用于在不同执行之间保持状态
    _cache_storage = {}
    _cache_counter = {}
    
    def __init__(self):
        # 为每个实例生成唯一ID
        self.instance_id = str(uuid.uuid4())[:8]
        
        # 初始化实例缓存
        if self.instance_id not in self._cache_storage:
            self._cache_storage[self.instance_id] = []
            self._cache_counter[self.instance_id] = 0
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "metadata": ("BOOLEAN", {
                    "default": False, 
                    "label_on": "包含", 
                    "label_off": "不包含",
                    "tooltip": "控制保存图像时是否包含生成元数据"
                }),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI", 
                    "multiline": False,
                    "tooltip": "保存图像的文件名前缀"
                }),
                "custom_path": ("STRING", {
                    "default": "", 
                    "multiline": False,
                    "tooltip": "自定义保存路径，留空则使用ComfyUI默认output目录。注意：只有图像达到上限99张之后才会触发保存机制"
                }),
                "clear_cache": ("BOOLEAN", {
                    "default": False,
                    "label_on": "清理缓存", 
                    "label_off": "保持缓存",
                    "tooltip": "点击开启后将清空当前实例的所有缓存和预览图像"
                }),
            }
        }
    
    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "cache_image"
    CATEGORY = "图像/缓存"
    OUTPUT_NODE = True
    
    def cache_image(self, image, metadata=False, filename_prefix="ComfyUI", custom_path="", clear_cache=False):
        """
        缓存图像的主要处理函数
        """
        try:
            # 获取当前实例的缓存
            cache = self._cache_storage[self.instance_id]
            
            # 检查是否需要清理缓存
            if clear_cache:
                return self._handle_clear_cache()
            
            # 将图像添加到缓存
            cache_item = {
                "image": image.clone(),
                "timestamp": time.time(),
                "metadata": metadata,
                "filename_prefix": filename_prefix,
                "custom_path": custom_path
            }
            cache.append(cache_item)
            
            # 检查是否达到缓存上限
            if len(cache) >= 99:
                self._save_cached_images()
                cache.clear()  # 清空缓存
                self._cleanup_current_instance_previews()  # 清理当前实例的预览文件
            
            # 生成预览
            preview_result = self._generate_preview()
            
            return preview_result
            
        except Exception as e:
            print(f"图像缓存节点错误: {e}")
            return {"ui": {"text": [f"错误: {str(e)}"]}}
    
    def _handle_clear_cache(self):
        """
        处理清理缓存的操作
        """
        try:
            # 清空当前实例的内存缓存
            cache = self._cache_storage[self.instance_id]
            cache.clear()
            
            # 清理当前实例的所有预览文件
            self._cleanup_current_instance_previews()
            
            # 清理整个实例目录（如果存在的话）
            self._cleanup_instance_directory()
            
            print(f"实例 {self.instance_id} 的缓存和预览已全部清理")
            
            return {
                "ui": {
                    "text": ["✅ 缓存已清理完成！所有预览图像和缓存数据已删除。"]
                }
            }
            
        except Exception as e:
            print(f"清理缓存失败: {e}")
            return {"ui": {"text": [f"清理失败: {str(e)}"]}}
    
    def _cleanup_instance_directory(self):
        """
        清理当前实例的整个目录（预览目录）
        """
        try:
            output_dir = folder_paths.get_output_directory()
            instance_dir = os.path.join(output_dir, f"image_cache_{self.instance_id}")
            preview_dir = os.path.join(instance_dir, "previews")
            
            # 清理预览目录
            if os.path.exists(preview_dir):
                import shutil
                shutil.rmtree(preview_dir)
                print(f"已删除预览目录: {preview_dir}")
            
            # 如果实例目录为空，也可以删除（但保留以备将来使用）
            # 这里我们选择保留目录结构，只清理内容
            
        except Exception as e:
            print(f"清理实例目录失败: {e}")
    
    def _save_cached_images(self):
        """
        保存缓存中的所有图像
        """
        try:
            cache = self._cache_storage[self.instance_id]
            if not cache:
                return
            
            # 使用第一个图像的参数作为保存参数
            first_item = cache[0]
            custom_path = first_item["custom_path"].strip()
            filename_prefix = first_item["filename_prefix"]
            include_metadata = first_item["metadata"]
            
            # 确定保存目录
            if custom_path and os.path.isabs(custom_path):
                # 使用自定义绝对路径
                save_dir = custom_path
                os.makedirs(save_dir, exist_ok=True)
            else:
                # 使用ComfyUI默认目录下的实例专用子文件夹 (output/image_cache_实例ID)
                output_dir = folder_paths.get_output_directory()
                save_dir = os.path.join(output_dir, f"image_cache_{self.instance_id}")
                os.makedirs(save_dir, exist_ok=True)
            
            # 获取当前时间戳作为批次标识
            batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            saved_count = 0
            for i, item in enumerate(cache):
                try:
                    # 转换tensor为PIL图像
                    pil_image = self._tensor_to_pil(item["image"])
                    if pil_image is None:
                        continue
                    
                    # 生成文件名
                    filename = f"{filename_prefix}_{batch_timestamp}_{i+1:03d}.png"
                    filepath = os.path.join(save_dir, filename)
                    
                    # 保存图像
                    save_kwargs = {"format": "PNG"}
                    if not include_metadata:
                        save_kwargs["pnginfo"] = None
                    
                    pil_image.save(filepath, **save_kwargs)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"保存第{i+1}张图像失败: {e}")
                    continue
            
            print(f"成功保存 {saved_count} 张缓存图像到: {save_dir}")
            
        except Exception as e:
            print(f"保存缓存图像失败: {e}")
    
    def _generate_preview(self):
        """
        生成缓存图像的预览
        """
        try:
            cache = self._cache_storage[self.instance_id]
            cache_count = len(cache)
            
            if cache_count == 0:
                return {"ui": {"text": ["缓存为空"]}}
            
            # 创建预览图像列表
            preview_images = []
            
            # 清理旧的临时预览文件
            self._cleanup_old_preview_files()
            
            # 检查并生成缺失的预览图像（增量保存）
            preview_images = self._get_or_create_preview_images(cache_count)
            
            # 准备UI结果
            ui_result = {
                "text": [f"缓存图像数量: {cache_count}/99"],
            }
            
            # ComfyUI预览图像需要特定格式
            if preview_images:
                formatted_images = []
                for rel_path in preview_images:
                    if rel_path:  # 确保路径不为空
                        # 分离文件名和子文件夹
                        filename = os.path.basename(rel_path)
                        subfolder = os.path.dirname(rel_path)
                        
                        formatted_images.append({
                            "filename": filename,
                            "subfolder": subfolder,
                            "type": "output"
                        })
                ui_result["images"] = formatted_images
            
            return {"ui": ui_result}
            
        except Exception as e:
            print(f"生成预览失败: {e}")
            return {"ui": {"text": [f"预览生成失败: {str(e)}"]}}
    
    def _tensor_to_pil(self, tensor):
        """
        将tensor转换为PIL图像
        """
        try:
            if tensor is None:
                return None
            
            # 确保tensor在CPU上
            if tensor.device.type != 'cpu':
                tensor = tensor.cpu()
            
            # 处理批次维度
            if tensor.dim() == 4 and tensor.shape[0] > 0:
                tensor = tensor[0]  # 取第一张图像
            elif tensor.dim() != 3:
                return None
            
            # 转换为numpy数组
            if tensor.dtype != torch.uint8:
                # 假设tensor值在0-1范围内
                tensor = (tensor * 255).clamp(0, 255).to(torch.uint8)
            
            numpy_image = tensor.numpy()
            
            # 转换为PIL图像
            if numpy_image.shape[2] == 3:  # RGB
                pil_image = Image.fromarray(numpy_image, 'RGB')
            elif numpy_image.shape[2] == 4:  # RGBA
                pil_image = Image.fromarray(numpy_image, 'RGBA')
            else:
                return None
            
            return pil_image
            
        except Exception as e:
            print(f"tensor转PIL失败: {e}")
            return None
    
    def _get_preview_dir(self):
        """
        获取当前实例专用的预览图像子目录
        """
        output_dir = folder_paths.get_output_directory()
        preview_dir = os.path.join(output_dir, f"image_cache_{self.instance_id}", "previews")
        os.makedirs(preview_dir, exist_ok=True)
        return preview_dir
    
    def _get_or_create_preview_images(self, cache_count):
        """
        增量生成预览图像，只生成缺失的预览
        """
        preview_images = []
        preview_dir = self._get_preview_dir()
        cache = self._cache_storage[self.instance_id]
        
        for i in range(cache_count):
            # 生成预览文件名（不包含时间戳，固定命名）
            preview_filename = f"cache_preview_{self.instance_id}_{i:03d}.png"
            preview_path = os.path.join(preview_dir, preview_filename)
            
            # 检查预览文件是否已存在
            if not os.path.exists(preview_path):
                try:
                    # 生成缺失的预览图像
                    pil_image = self._tensor_to_pil(cache[i]["image"])
                    if pil_image:
                        # 调整预览图像大小
                        pil_image.thumbnail((256, 256), Image.Resampling.LANCZOS)
                        # 保存预览图像
                        pil_image.save(preview_path, "PNG", optimize=True, quality=95)
                        print(f"生成新预览: {preview_filename}")
                except Exception as e:
                    print(f"生成第{i+1}张预览失败: {e}")
                    continue
            
            # 添加到预览列表（无论是否新生成）
            if os.path.exists(preview_path):
                # 返回相对于output目录的路径
                rel_path = os.path.relpath(preview_path, folder_paths.get_output_directory())
                preview_images.append(rel_path.replace('\\', '/'))
        
        return preview_images
    
    def _cleanup_old_preview_files(self, max_age=1800):
        """
        智能清理预览子目录中的临时预览文件
        - 保护当前实例的活跃缓存预览文件
        - 清理其他实例或超过30分钟的文件
        """
        try:
            preview_dir = self._get_preview_dir()
            if not os.path.exists(preview_dir):
                return
                
            current_time = time.time()
            current_instance_prefix = f"cache_preview_{self.instance_id}_"
            
            for filename in os.listdir(preview_dir):
                # 只处理我们的临时预览文件
                if filename.startswith("cache_preview_"):
                    filepath = os.path.join(preview_dir, filename)
                    if os.path.isfile(filepath):
                        try:
                            # 检查是否是当前实例的预览文件
                            is_current_instance = filename.startswith(current_instance_prefix)
                            file_age = current_time - os.path.getmtime(filepath)
                            
                            # 当前实例的预览文件：只有在缓存为空时才清理
                            if is_current_instance:
                                cache = self._cache_storage.get(self.instance_id, [])
                                # 如果缓存为空，清理所有当前实例的预览文件
                                if len(cache) == 0 and file_age > 300:  # 5分钟后清理空缓存的预览
                                    os.remove(filepath)
                            else:
                                # 其他实例的预览文件：超过30分钟就清理
                                if file_age > max_age:
                                    os.remove(filepath)
                                    
                        except Exception:
                            pass
        except Exception:
            pass
    
    def _cleanup_current_instance_previews(self):
        """
        清理当前实例的所有预览文件（用于缓存清空后）
        """
        try:
            preview_dir = self._get_preview_dir()
            if not os.path.exists(preview_dir):
                return
                
            current_instance_prefix = f"cache_preview_{self.instance_id}_"
            
            for filename in os.listdir(preview_dir):
                if filename.startswith(current_instance_prefix):
                    filepath = os.path.join(preview_dir, filename)
                    try:
                        if os.path.isfile(filepath):
                            os.remove(filepath)
                            print(f"清理预览文件: {filename}")
                    except Exception:
                        pass
        except Exception:
            pass
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """
        确保每次都重新执行（用于缓存功能）
        当清理缓存按钮被点击时，强制刷新节点
        """
        clear_cache = kwargs.get("clear_cache", False)
        if clear_cache:
            # 当清理缓存被触发时，返回唯一值强制刷新
            return time.time()
        return float("nan")

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageCache": ImageCache
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageCache": "图像缓存"
}
