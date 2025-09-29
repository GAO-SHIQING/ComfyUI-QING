import importlib
import inspect
import time
from pathlib import Path

# 导入新版API配置服务
try:
    from .nodes.api.utils import config_server
except ImportError:
    pass


def _discover_and_register_nodes():
    """
    自动发现并注册nodes目录下的所有节点类
    从各个节点文件中自动提取显示名称，实现完全自动化的节点注册
    """
    start_time = time.time()
    node_classes = {}
    display_names = {}
    
    # 获取nodes目录路径
    nodes_dir = Path(__file__).parent / "nodes"
    
    if not nodes_dir.exists():
        return node_classes, display_names
    
    # 递归遍历nodes目录下的所有Python文件（包括子目录）
    for py_file in nodes_dir.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        
        try:
            # 构建相对于nodes目录的模块路径
            relative_path = py_file.relative_to(nodes_dir)
            module_parts = ["nodes"] + list(relative_path.with_suffix("").parts)
            module_name = ".".join(module_parts)
            
            # 动态导入模块
            module = importlib.import_module(f".{module_name}", package=__package__)
            
            # 检查模块是否有NODE_CLASS_MAPPINGS（这是ComfyUI节点的标准定义方式）
            module_node_classes = getattr(module, 'NODE_CLASS_MAPPINGS', {})
            module_display_names = getattr(module, 'NODE_DISPLAY_NAME_MAPPINGS', {})
            
            if module_node_classes:
                # 直接使用模块定义的节点映射
                node_classes.update(module_node_classes)
                display_names.update(module_display_names)
            else:
                # 回退到原来的类检查方式（为了兼容性）
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # 只处理在当前模块中定义的类（排除导入的类）
                    if obj.__module__ == module.__name__:
                        # 跳过标记为基类的类
                        if hasattr(obj, '_IS_BASE_CLASS') and obj._IS_BASE_CLASS:
                            continue
                        # 检查类是否具有ComfyUI节点的基本属性
                        if hasattr(obj, 'INPUT_TYPES') and hasattr(obj, 'FUNCTION'):
                            node_classes[name] = obj
                            # 优先使用模块中定义的显示名称，否则使用类名
                            display_names[name] = module_display_names.get(name, name)
                
        except (ImportError, Exception):
            # 静默跳过无法导入或处理的模块
            continue
    
    # 简洁的加载完成信息
    load_time = time.time() - start_time
    print(f"🎨QING: 节点加载完成 - 用时 {load_time:.2f}s")
    
    return node_classes, display_names


def get_node_count():
    """获取已注册的节点数量"""
    return len(_NODE_CLASSES) if '_NODE_CLASSES' in globals() else 0


def get_registered_nodes():
    """获取已注册的节点列表（用于调试）"""
    if '_NODE_CLASSES' not in globals():
        return {}
    return {name: cls.__module__ for name, cls in _NODE_CLASSES.items()}


def get_node_stats():
    """获取节点统计信息"""
    if '_NODE_CLASSES' not in globals() or not _NODE_CLASSES:
        return {"total_nodes": 0, "api_nodes": 0, "processing_nodes": 0, "other_nodes": 0}
    
    stats = {"api_nodes": 0, "processing_nodes": 0, "other_nodes": 0}
    for name, cls in _NODE_CLASSES.items():
        module_name = cls.__module__.lower()
        if "api" in module_name:
            stats["api_nodes"] += 1
        elif any(keyword in module_name for keyword in ["image", "mask", "video", "svg"]):
            stats["processing_nodes"] += 1
        else:
            stats["other_nodes"] += 1
    
    stats["total_nodes"] = sum(stats.values())
    return stats


# 使用动态发现机制注册所有节点（包括子目录中的节点）
try:
    _NODE_CLASSES, _DISPLAY_NAMES = _discover_and_register_nodes()
except Exception:
    _NODE_CLASSES, _DISPLAY_NAMES = {}, {}

# 按照官方文档加载翻译系统
# 参考：https://docs.comfy.org/zh-CN/custom-nodes/i18n
# 官方示例：https://github.com/comfyui-wiki/ComfyUI-i18n-demo
try:
    from comfy.utils import load_translation
    load_translation(__file__)
except ImportError:
    pass

# 使用动态注册的节点类和显示名称
NODE_CLASS_MAPPINGS = _NODE_CLASSES
NODE_DISPLAY_NAME_MAPPINGS = _DISPLAY_NAMES

# JavaScript扩展目录
WEB_DIRECTORY = "./js"

# 导出的公共接口
__all__ = [
    "NODE_CLASS_MAPPINGS", 
    "NODE_DISPLAY_NAME_MAPPINGS", 
    "WEB_DIRECTORY",
    "get_node_count",
    "get_registered_nodes", 
    "get_node_stats"
]