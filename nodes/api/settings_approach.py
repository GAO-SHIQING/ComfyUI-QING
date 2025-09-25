# -*- coding: utf-8 -*-
"""
改进的ComfyUI设置方法
参考comfyui_prompt_assistant项目的最佳实践
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

class QingConfigManager:
    """🎨QING配置管理器 - 参考comfyui_prompt_assistant的最佳实践"""
    
    def __init__(self):
        # 插件目录和配置文件路径
        self.dir_path = Path(__file__).parent
        
        # 创建config目录
        self.config_dir = self.dir_path / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_path = self.config_dir / "config.json"
        
        # 默认配置
        self.default_config = {
            "__comment": "🎨QING项目配置文件",
            "api_settings": {
                "glm_api_key": "",
                "last_updated": "",
                "source": "manual"
            },
            "sync_settings": {
                "auto_sync": True,
                "check_interval": 2000
            },
            "version": "1.0.0"
        }
        
        # 确保配置文件存在
        self._ensure_config_exists()
    
    def _ensure_config_exists(self):
        """确保配置文件存在，不存在则创建默认配置"""
        if not self.config_path.exists():
            self.save_config(self.default_config)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.default_config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        config = self.load_config()
        return config.get("api_settings", {}).get("glm_api_key", "")
    
    def update_api_key(self, api_key: str, source: str = "unknown") -> bool:
        """更新API密钥"""
        config = self.load_config()
        
        if "api_settings" not in config:
            config["api_settings"] = {}
        
        config["api_settings"]["glm_api_key"] = api_key
        config["api_settings"]["last_updated"] = self._get_current_timestamp()
        config["api_settings"]["source"] = source
        
        return self.save_config(config)
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"

# 全局配置管理器实例
qing_config_manager = QingConfigManager()

# 便捷函数
def get_qing_api_key_improved() -> str:
    """获取API密钥的便捷函数"""
    return qing_config_manager.get_api_key()

def set_qing_api_key_improved(api_key: str, source: str = "unknown") -> bool:
    """设置API密钥的便捷函数"""
    return qing_config_manager.update_api_key(api_key, source)