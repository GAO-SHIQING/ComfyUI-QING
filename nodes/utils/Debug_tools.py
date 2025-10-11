# -*- coding: utf-8 -*-
"""
QING调试工具节点集合
包含LetMeSee和ShowMePure两个核心调试节点
支持任意数据类型的调试显示和透传
"""

import json
import time
import sys
from datetime import datetime

# 可选依赖，如果不存在则使用基础功能
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# 定义通用类型代理，允许接受任何类型的输入
class AlwaysEqualProxy(str):
    """代理类，允许接受任何类型的输入"""
    def __eq__(self, _):
        return True
    
    def __ne__(self, _):
        return False


# 创建任意类型的实例
any_type = AlwaysEqualProxy("*")


class LetMeSee:
    """
    我想看看 - 通用调试工具
    显示任何类型数据的详细分析，包含数据类型、运行时长、系统资源使用等信息
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {}, 
            "optional": {"source": (any_type, {})},
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"}
        }
    
    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ('source',)
    INPUT_IS_LIST = True
    OUTPUT_NODE = True
    FUNCTION = "show_data"
    CATEGORY = "🎨QING/调试工具"
    
    def show_data(self, unique_id=None, extra_pnginfo=None, **kwargs):
        """
        处理输入数据并在UI中显示，包含系统信息统计
        """
        start_time = time.time()
        
        # 获取系统信息
        system_info = self._get_system_info()
        
        # 收集UI显示内容和原始输出数据
        ui_values = []
        output_data = []
        
        if "source" in kwargs:
            for val in kwargs['source']:
                try:
                    # 生成分析报告用于UI显示
                    analysis_result = self._analyze_data(val, start_time, system_info)
                    ui_values.append(analysis_result)
                    # 保存原始数据用于输出端口
                    output_data.append(val)
                except Exception:
                    ui_values.append(str(val))
                    output_data.append(val)

        # 更新工作流信息（UI显示用）
        if not extra_pnginfo:
            pass
        elif (not isinstance(extra_pnginfo[0], dict) or "workflow" not in extra_pnginfo[0]):
            pass
        else:
            workflow = extra_pnginfo[0]["workflow"]
            node = next((x for x in workflow["nodes"] if str(x["id"]) == unique_id[0]), None)
            if node:
                node["widgets_values"] = [ui_values]
        
        # 返回结果：UI显示分析报告，输出端口传递原始数据
        if isinstance(output_data, list) and len(output_data) == 1:
            result = {"ui": {"text": ui_values}, "result": (output_data[0],), }
        else:
            result = {"ui": {"text": ui_values}, "result": (output_data,), }
            
        return result

    def _get_system_info(self):
        """获取系统信息"""
        info = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # 内存信息
        if HAS_PSUTIL:
            try:
                memory = psutil.virtual_memory()
                info["memory_mb"] = memory.used / 1024 / 1024
                info["memory_percent"] = memory.percent
            except:
                info["memory_mb"] = 0
                info["memory_percent"] = 0
        else:
            info["memory_mb"] = 0
            info["memory_percent"] = 0
        
        # GPU信息
        if HAS_TORCH:
            try:
                import torch
                if torch.cuda.is_available():
                    info["gpu_memory_mb"] = torch.cuda.memory_allocated() / 1024 / 1024
                    info["gpu_memory_cached_mb"] = torch.cuda.memory_reserved() / 1024 / 1024
                    info["gpu_count"] = torch.cuda.device_count()
                    info["gpu_name"] = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown"
                else:
                    info["gpu_memory_mb"] = 0
                    info["gpu_memory_cached_mb"] = 0
                    info["gpu_count"] = 0
                    info["gpu_name"] = "No GPU"
            except:
                info["gpu_memory_mb"] = 0
                info["gpu_memory_cached_mb"] = 0
                info["gpu_count"] = 0
                info["gpu_name"] = "No GPU"
        else:
            info["gpu_memory_mb"] = 0
            info["gpu_memory_cached_mb"] = 0
            info["gpu_count"] = 0
            info["gpu_name"] = "No GPU"
            
        return info

    def _analyze_data(self, data, start_time, system_info):
        """分析数据并生成精简报告"""
        current_time = time.time()
        execution_time = current_time - start_time
        
        # 基础数据信息
        data_type = type(data).__name__
        data_size = sys.getsizeof(data)
        
        # 构建精简报告
        report_lines = [
            "📊 数据分析",
            f"🕒 {system_info['timestamp']} | ⚡ {execution_time:.3f}s",
            "",
            f"类型: {data_type} | 大小: {data_size/1024:.1f}KB",
        ]
        
        # Tensor信息（精简版）
        if HAS_TORCH and 'torch' in str(type(data)):
            try:
                import torch
                if isinstance(data, torch.Tensor):
                    shape_str = "x".join(map(str, data.shape))
                    report_lines.append(f"形状: {shape_str} | 设备: {data.device} | 类型: {data.dtype}")
                    
                    # 简化数值统计
                    if data.numel() > 0 and data.dtype in [torch.float32, torch.float64, torch.float16]:
                        try:
                            min_val = data.min().item()
                            max_val = data.max().item()
                            mean_val = data.mean().item()
                            report_lines.append(f"范围: {min_val:.3f}~{max_val:.3f} | 均值: {mean_val:.3f}")
                        except:
                            pass
            except:
                pass
        
        # 容器类型信息
        elif hasattr(data, '__len__'):
            try:
                report_lines.append(f"长度: {len(data)}")
            except:
                pass
        
        # 精简系统资源信息
        report_lines.extend([
            "",
            f"💻 内存: {system_info['memory_mb']:.0f}MB ({system_info['memory_percent']:.0f}%)",
            f"🖥️ GPU: {system_info['gpu_memory_mb']:.0f}MB | {system_info['gpu_name']}",
            "",
            "📄 内容:",
        ])
        
        # 完整数据内容显示（无截断）
        try:
            if isinstance(data, str):
                content = data
            elif isinstance(data, (int, float, bool)):
                content = str(data)
            elif isinstance(data, list):
                content = str(data)
            else:
                content = json.dumps(data, ensure_ascii=False, indent=1, default=str)
        except:
            content = str(data)
            
        report_lines.append(content)
        
        return "\n".join(report_lines)


class ShowMePure:
    """
    让我看看 - 极简内容显示工具
    直接输出原始数据内容，无任何格式化或额外信息
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {}, 
            "optional": {"source": (any_type, {})},
            "hidden": {"unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"}
        }
    
    RETURN_TYPES = (any_type,)
    RETURN_NAMES = ('source',)
    INPUT_IS_LIST = True
    OUTPUT_NODE = True
    FUNCTION = "show_pure_data"
    CATEGORY = "🎨QING/调试工具"
    
    def show_pure_data(self, unique_id=None, extra_pnginfo=None, **kwargs):
        """
        处理输入数据并在UI中显示纯净内容，无系统分析
        """
        # 收集UI显示内容和原始输出数据
        ui_values = []
        output_data = []
        
        if "source" in kwargs:
            for val in kwargs['source']:
                try:
                    # 生成纯净内容显示
                    pure_content = self._show_pure_content(val)
                    ui_values.append(pure_content)
                    # 保存原始数据用于输出端口
                    output_data.append(val)
                except Exception:
                    ui_values.append(str(val))
                    output_data.append(val)

        # 更新工作流信息（UI显示用）
        if not extra_pnginfo:
            pass
        elif (not isinstance(extra_pnginfo[0], dict) or "workflow" not in extra_pnginfo[0]):
            pass
        else:
            workflow = extra_pnginfo[0]["workflow"]
            node = next((x for x in workflow["nodes"] if str(x["id"]) == unique_id[0]), None)
            if node:
                node["widgets_values"] = [ui_values]
        
        # 返回结果：UI显示纯净内容，输出端口传递原始数据
        if isinstance(output_data, list) and len(output_data) == 1:
            result = {"ui": {"text": ui_values}, "result": (output_data[0],), }
        else:
            result = {"ui": {"text": ui_values}, "result": (output_data,), }
            
        return result

    def _show_pure_content(self, data):
        """显示纯净数据内容，完全无格式化"""
        # 直接返回数据内容，无任何额外信息
        try:
            if isinstance(data, str):
                return data
            elif isinstance(data, (int, float, bool)):
                return str(data)
            elif isinstance(data, list):
                return str(data)
            else:
                return json.dumps(data, ensure_ascii=False, indent=1, default=str)
        except:
            return str(data)


# 节点注册
NODE_CLASS_MAPPINGS = {
    "LetMeSee": LetMeSee,
    "ShowMePure": ShowMePure
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LetMeSee": "我想看看",
    "ShowMePure": "让我看看"
}
