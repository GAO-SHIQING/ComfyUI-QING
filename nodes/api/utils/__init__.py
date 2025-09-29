# -*- coding: utf-8 -*-
"""
🎨QING API工具模块
提供API密钥管理、配置服务等工具功能
"""

# 导入现代化API管理工具
from .settings_approach import (
    QingConfigManager, 
    get_config_manager,
    get_qing_api_key_improved, 
    set_qing_api_key_improved
)

from .config_server import (
    get_api_key_by_platform,
    set_api_key_by_platform,
    register_endpoints
)

__all__ = [
    # 配置管理
    "QingConfigManager",
    "get_config_manager", 
    "get_qing_api_key_improved",
    "set_qing_api_key_improved",
    
    # HTTP配置服务
    "get_api_key_by_platform",
    "set_api_key_by_platform", 
    "register_endpoints"
]
