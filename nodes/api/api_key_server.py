# -*- coding: utf-8 -*-
"""
🎨QING API密钥管理服务器
提供API密钥的存储和获取服务
"""

import os
import json
import threading
from pathlib import Path

class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self):
        self._api_key = ""
        self._lock = threading.Lock()
        self._config_file = Path(__file__).parent / ".qing_api_key.json"
        self._load_from_file()
    
    def set_api_key(self, api_key: str):
        """设置API密钥"""
        with self._lock:
            self._api_key = api_key.strip() if api_key else ""
            self._save_to_file()
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        with self._lock:
            return self._api_key
    
    def _load_from_file(self):
        """从文件加载API密钥"""
        try:
            if self._config_file.exists():
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._api_key = data.get('api_key', '')
        except Exception:
            # 如果加载失败，使用空字符串
            self._api_key = ""
    
    def _save_to_file(self):
        """保存API密钥到文件"""
        try:
            data = {'api_key': self._api_key}
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

# 全局API密钥管理器实例
_api_key_manager = APIKeyManager()

def get_qing_api_key() -> str:
    """
    获取🎨QING设置中的API密钥
    
    优先级（参考comfyui_prompt_assistant最佳实践）：
    1. 🎨QING改进配置管理器（本地JSON文件）- 最高优先级
    2. 环境变量ZHIPUAI_API_KEY
    3. 🎨QING本地文件存储（向后兼容）
    
    Returns:
        str: API密钥
    """
    # 方法0: 从🎨QING改进配置管理器获取（最高优先级）
    try:
        from .settings_approach import get_qing_api_key_improved
        improved_key = get_qing_api_key_improved()
        if improved_key:
            return improved_key
    except ImportError:
        pass
    
    # 方法1: 从环境变量获取
    env_api_key = os.getenv('ZHIPUAI_API_KEY', '')
    if env_api_key:
        return env_api_key
    
    # 方法2: 回退到本地文件存储（向后兼容）
    return _api_key_manager.get_api_key()

def set_qing_api_key(api_key: str):
    """设置API密钥"""
    _api_key_manager.set_api_key(api_key)