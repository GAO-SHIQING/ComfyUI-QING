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
        
        # 默认配置（支持多平台API密钥）- 生成用户友好的配置文件
        self.default_config = {
            "//": "════════════════════════════════════════════════════════════════════════════════",
            "// ": "                    🎨QING 多平台API密钥配置文件                                ",
            "//  ": "════════════════════════════════════════════════════════════════════════════════",
            "//   ": "📝 使用说明：在下方 api_settings 各平台的 value 字段填写您的API密钥",
            "//    ": "⚠️  注意：只需要填写 value 字段，其他注释请勿删除",
            "//     ": "════════════════════════════════════════════════════════════════════════════════",
            
            "api_settings": {
                "// ": "┌─────────────────────────────────────────────────────────────────────────────┐",
                "//  ": "│                          📋 API密钥配置区域                                │",
                "//   ": "│                    请在下方各平台的 value 字段填写密钥                     │",
                "//    ": "└─────────────────────────────────────────────────────────────────────────────┘",
                
                "glm_api_key": {
                    "// ": "🤖 智谱AI GLM模型",
                    "描述": "智谱AI的API密钥，用于GLM语言和视觉模型调用",
                    "格式示例": "glm-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "获取地址": "https://open.bigmodel.cn/usercenter/apikeys",
                    "🔑 请在此填写": "👇👇👇 在下方value字段填写您的智谱AI API密钥 👇👇👇",
                    "value": ""
                },
                
                "volcengine_api_key": {
                    "// ": "🌋 火山引擎平台",
                    "描述": "火山引擎平台的API密钥，用于DeepSeek模型调用",
                    "格式示例": "ak-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "获取地址": "https://console.volcengine.com/ark",
                    "🔑 请在此填写": "👇👇👇 在下方value字段填写您的火山引擎API密钥 👇👇👇",
                    "value": ""
                },
                
                "dashscope_api_key": {
                    "// ": "☁️ 阿里云百炼平台",
                    "描述": "阿里云百炼平台的API密钥，用于DeepSeek模型调用",
                    "格式示例": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "获取地址": "https://bailian.console.aliyun.com",
                    "🔑 请在此填写": "👇👇👇 在下方value字段填写您的阿里云百炼API密钥 👇👇👇",
                    "value": ""
                },
                
                "siliconflow_api_key": {
                    "// ": "💎 硅基流动平台",
                    "描述": "硅基流动平台的API密钥，用于DeepSeek模型调用",
                    "格式示例": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "获取地址": "https://cloud.siliconflow.cn/account/ak",
                    "🔑 请在此填写": "👇👇👇 在下方value字段填写您的硅基流动API密钥 👇👇👇",
                    "value": ""
                },
                
                "//      ": "═══════════════════════════════════════════════════════════════════════════════",
                "__system_info": {
                    "// ": "⚠️ 系统信息 - 请勿手动修改",
                    "last_updated": "",
                    "source": "manual",
                    "sync_count": 0
                }
            },
            
            "//       ": "═══════════════════════════════════════════════════════════════════════════════",
            "sync_settings": {
                "// ": "🔧 同步设置 - 通常无需修改",
                "auto_sync": True,
                "check_interval": 2000,
                "enable_logging": False
            },
            
            "version": "2.0.0",
            "//        ": "═══════════════════════════════════════════════════════════════════════════════",
            "//         ": "✅ 配置完成后，保存文件即可自动同步到ComfyUI设置",
            "//          ": "🔄 支持实时双向同步，在ComfyUI设置中修改也会同步到此文件",
            "//           ": "═══════════════════════════════════════════════════════════════════════════════"
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
    
    def get_api_key(self, config_key: str = "glm_api_key") -> str:
        """
        获取API密钥
        
        Args:
            config_key: 配置键名（glm_api_key, volcengine_api_key, dashscope_api_key, siliconflow_api_key）
        
        Returns:
            str: API密钥
        """
        config = self.load_config()
        api_settings = config.get("api_settings", {})
        
        # 兼容新旧配置格式
        key_config = api_settings.get(config_key, "")
        if isinstance(key_config, dict):
            # 新格式：返回value字段
            return key_config.get("value", "")
        else:
            # 旧格式：直接返回字符串值
            return str(key_config) if key_config else ""
    
    def update_api_key(self, api_key: str, source: str = "unknown", config_key: str = "glm_api_key") -> bool:
        """
        更新API密钥
        
        Args:
            api_key: API密钥
            source: 来源
            config_key: 配置键名
        
        Returns:
            bool: 是否更新成功
        """
        config = self.load_config()
        
        if "api_settings" not in config:
            config["api_settings"] = {}
        
        # 获取或创建API密钥配置
        if config_key not in config["api_settings"]:
            config["api_settings"][config_key] = {}
        
        # 兼容新旧格式
        key_config = config["api_settings"][config_key]
        if isinstance(key_config, dict):
            # 新格式：更新value字段
            key_config["value"] = api_key
        else:
            # 迁移到新格式
            config["api_settings"][config_key] = {
                "__comment": f"{config_key} API密钥",
                "value": api_key
            }
        
        # 更新系统信息
        if "__system_info" not in config["api_settings"]:
            config["api_settings"]["__system_info"] = {}
        
        system_info = config["api_settings"]["__system_info"]
        system_info["last_updated"] = self._get_current_timestamp()
        system_info["source"] = source
        system_info["sync_count"] = system_info.get("sync_count", 0) + 1
        
        return self.save_config(config)
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"

# 全局配置管理器实例
qing_config_manager = QingConfigManager()

# 便捷函数
def get_qing_api_key_improved(config_key: str = "glm_api_key") -> str:
    """
    获取API密钥的便捷函数
    
    Args:
        config_key: 配置键名
    
    Returns:
        str: API密钥
    """
    return qing_config_manager.get_api_key(config_key)

def set_qing_api_key_improved(api_key: str, source: str = "unknown", config_key: str = "glm_api_key") -> bool:
    """
    设置API密钥的便捷函数
    
    Args:
        api_key: API密钥
        source: 来源
        config_key: 配置键名
    
    Returns:
        bool: 是否设置成功
    """
    return qing_config_manager.update_api_key(api_key, source, config_key)