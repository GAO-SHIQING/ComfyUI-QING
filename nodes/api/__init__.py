# -*- coding: utf-8 -*-
"""
🎨QING API模块
提供现代化的API密钥管理功能
节点类由各自的文件中的NODE_CLASS_MAPPINGS定义，主模块会自动发现并导入

注意：旧版API密钥管理已废弃，请使用新版配置系统：
- settings_approach.py: 多平台配置管理
- config_server.py: HTTP端点配置服务
- base_api_framework.py: 框架集成的API密钥管理
"""

# 现代化API密钥管理（推荐使用）
try:
    from .utils.settings_approach import get_qing_api_key_improved, set_qing_api_key_improved
    from .utils.config_server import get_api_key_by_platform, set_api_key_by_platform
    MODERN_API_AVAILABLE = True
except ImportError:
    MODERN_API_AVAILABLE = False

# 为了向后兼容，提供旧版接口的替代实现
def get_qing_api_key() -> str:
    """
    向后兼容的API密钥获取函数
    现在使用新版配置系统
    """
    if MODERN_API_AVAILABLE:
        return get_qing_api_key_improved("glm_api_key")
    return ""

def set_qing_api_key(api_key: str) -> bool:
    """
    向后兼容的API密钥设置函数
    现在使用新版配置系统
    """
    if MODERN_API_AVAILABLE:
        return set_qing_api_key_improved(api_key, "compatibility_layer", "glm_api_key")
    return False

__all__ = [
    "get_qing_api_key",
    "set_qing_api_key",
    # 现代化接口（推荐）
    "get_qing_api_key_improved", 
    "set_qing_api_key_improved",
    "get_api_key_by_platform",
    "set_api_key_by_platform"
]
