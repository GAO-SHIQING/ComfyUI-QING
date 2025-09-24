import os
import importlib
import inspect
from pathlib import Path


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
        print(f"❌ 错误：nodes目录不存在: {nodes_dir}")
        return node_classes, display_names
    
    # 遍历nodes目录下的所有Python文件
    for py_file in nodes_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue
            
        try:
            # 构建模块名
            module_name = f"nodes.{py_file.stem}"
            
            # 动态导入模块
            module = importlib.import_module(f".{module_name}", package=__package__)
            
            # 首先尝试从模块的NODE_DISPLAY_NAME_MAPPINGS中获取显示名称
            module_display_names = getattr(module, 'NODE_DISPLAY_NAME_MAPPINGS', {})
            
            # 检查模块中的所有类
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
            
            # 调试信息：显示每个模块加载的节点数
            if module_node_count > 0:
                display_info = f"✅ 从 {py_file.name} 加载了 {module_node_count} 个节点"
                if module_display_names:
                    display_info += f"（含 {len(module_display_names)} 个显示名称）"
                print(display_info)
                        
        except ImportError as e:
            error_msg = f"模块导入失败 {py_file.name}: {e}"
            failed_imports.append(error_msg)
            print(f"⚠️  {error_msg}")
        except Exception as e:
            error_msg = f"处理模块时出错 {py_file.name}: {e}"
            failed_imports.append(error_msg)
            print(f"❌ {error_msg}")
    
    # 如果有失败的导入，在调试模式下显示详细信息
    if failed_imports and os.environ.get('COMFYUI_QING_DEBUG', '').lower() in ('true', '1', 'yes'):
        print(f"\n⚠️  共有 {len(failed_imports)} 个模块导入失败:")
        for error in failed_imports:
            print(f"   {error}")
    
    return node_classes, display_names


def get_node_count():
    """获取已注册的节点数量"""
    return len(_NODE_CLASSES) if '_NODE_CLASSES' in globals() else 0


def get_registered_nodes():
    """获取已注册的节点列表（用于调试）"""
    if '_NODE_CLASSES' not in globals():
        return {}
    return {name: cls.__module__ for name, cls in _NODE_CLASSES.items()}


# 使用动态发现机制注册所有节点
_NODE_CLASSES, _DISPLAY_NAMES = _discover_and_register_nodes()

# 调试信息：打印已注册的节点数量
print(f"🎨QING节点包：成功注册了 {len(_NODE_CLASSES)} 个节点")

# 可选：打印详细的节点信息（仅在调试模式下）
DEBUG_MODE = os.environ.get('COMFYUI_QING_DEBUG', '').lower() in ('true', '1', 'yes')
if DEBUG_MODE:
    print("已注册的节点列表:")
    for node_name in sorted(_NODE_CLASSES.keys()):
        print(f"  - {node_name} ({_DISPLAY_NAMES.get(node_name, node_name)})")


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
