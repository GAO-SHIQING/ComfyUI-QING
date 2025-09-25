import os
import importlib
import inspect
from pathlib import Path

# 导入API密钥管理服务
try:
    from .nodes.api import api_key_server
    from .nodes.api import config_server
except ImportError:
    pass


def _discover_and_register_nodes():
    """
    自动发现并注册nodes目录下的所有节点类
    从各个节点文件中自动提取显示名称，实现完全自动化的节点注册
    """
    node_classes = {}
    display_names = {}
    failed_imports = []
    
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
                module_node_count = 0
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # 只处理在当前模块中定义的类（排除导入的类）
                    if obj.__module__ == module.__name__:
                        # 检查类是否具有ComfyUI节点的基本属性
                        if hasattr(obj, 'INPUT_TYPES') and hasattr(obj, 'FUNCTION'):
                            node_classes[name] = obj
                            # 优先使用模块中定义的显示名称，否则使用类名
                            display_names[name] = module_display_names.get(name, name)
                            module_node_count += 1
        except ImportError as e:
            error_msg = f"模块导入失败 {py_file.relative_to(nodes_dir)}: {e}"
            failed_imports.append(error_msg)
        except Exception as e:
            error_msg = f"处理模块时出错 {py_file.relative_to(nodes_dir)}: {e}"
            failed_imports.append(error_msg)
    
    return node_classes, display_names


def get_node_count():
    """获取已注册的节点数量"""
    return len(_NODE_CLASSES) if '_NODE_CLASSES' in globals() else 0


def get_registered_nodes():
    """获取已注册的节点列表（用于调试）"""
    if '_NODE_CLASSES' not in globals():
        return {}
    return {name: cls.__module__ for name, cls in _NODE_CLASSES.items()}


# 使用动态发现机制注册所有节点（包括子目录中的节点）
_NODE_CLASSES, _DISPLAY_NAMES = _discover_and_register_nodes()

# 按照官方文档加载翻译系统
# 参考：https://docs.comfy.org/zh-CN/custom-nodes/i18n
# 官方示例：https://github.com/comfyui-wiki/ComfyUI-i18n-demo
try:
    from comfy.utils import load_translation
    load_translation(__file__)
except ImportError:
    # 当前 ComfyUI 版本不支持官方 i18n API
    # 使用 NODE_DISPLAY_NAME_MAPPINGS 作为回退方案
    pass

# 使用动态注册的节点类和显示名称
NODE_CLASS_MAPPINGS = _NODE_CLASSES
NODE_DISPLAY_NAME_MAPPINGS = _DISPLAY_NAMES

# JavaScript扩展目录
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]