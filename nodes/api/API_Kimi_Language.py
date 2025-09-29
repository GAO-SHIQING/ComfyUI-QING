# -*- coding: utf-8 -*-
"""
Kimi Language API节点 - 基于通用框架
调用Kimi语言模型API进行文本推理
支持多平台：月之暗面、火山引擎、阿里云百炼、硅基流动
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseLanguageAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class StandardKimiAdapter(BasePlatformAdapter):
    """标准Kimi平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 应用token限制（如果有）
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        return params


class KimiLanguageAPI(BaseLanguageAPINode):
    """
    Kimi语言模型API调用节点 - 框架版本
    支持多个服务平台的Kimi模型调用
    """
    
    # 节点信息
    NODE_NAME = "KimiLanguageAPI"
    DISPLAY_NAME = "Kimi_语言丨API"
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "月之暗面": PlatformConfig(
            name="月之暗面",
            base_url="https://api.moonshot.cn/v1",
            api_key_env="MOONSHOT_API_KEY",
            config_key="moonshot_api_key",
            platform_key="moonshot",
            models=["kimi-k2-0905", "kimi-k2-0711", "kimi-k2-turbo"],
            model_mapping={
                "kimi-k2-0905": "kimi-k2-0905-preview",
                "kimi-k2-0711": "kimi-k2-0711-preview", 
                "kimi-k2-turbo": "kimi-k2-turbo-preview"
            },
            supports_frequency_penalty=True
        ),
        "火山引擎": PlatformConfig(
            name="火山引擎",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key_env="VOLCENGINE_API_KEY",
            config_key="volcengine_api_key",
            platform_key="volcengine",
            models=["kimi-k2-0905"],
            model_mapping={
                "kimi-k2-0905": "kimi-k2-250905"
            },
            supports_frequency_penalty=True
        ),
        "阿里云百炼": PlatformConfig(
            name="阿里云百炼",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="DASHSCOPE_API_KEY", 
            config_key="dashscope_api_key",
            platform_key="dashscope",
            models=["kimi-k2-0905"],
            model_mapping={
                "kimi-k2-0905": "Moonshot-Kimi-K2-Instruct"
            },
            supports_frequency_penalty=True
        ),
        "硅基流动": PlatformConfig(
            name="硅基流动",
            base_url="https://api.siliconflow.cn/v1",
            api_key_env="SILICONFLOW_API_KEY",
            config_key="siliconflow_api_key",
            platform_key="siliconflow",
            models=["kimi-k2-0905"],
            model_mapping={
                "kimi-k2-0905": "moonshotai/Kimi-K2-Instruct-0905"
            },
            supports_frequency_penalty=True
        )
    }
    
    # 所有平台使用相同的适配器
    PLATFORM_ADAPTERS = {
        "月之暗面": StandardKimiAdapter,
        "火山引擎": StandardKimiAdapter,
        "阿里云百炼": StandardKimiAdapter,
        "硅基流动": StandardKimiAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加Kimi特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义Kimi的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给Kimi模型的文本内容，Kimi擅长长文档分析、联网搜索和复杂推理"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的Kimi模型
📋 模型特点：
🔸 kimi-k2-0905：最新版本，200万字超长上下文，擅长长文档分析和复杂推理
🔸 kimi-k2-0711：稳定版本，平衡性能和成本
🔸 kimi-k2-turbo：快速响应版本，适合简单对话
💡 Kimi模型具备联网搜索能力，特别适合需要实时信息的任务"""
        
        # 调整Kimi的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.8
        base_types["optional"]["top_p"][1]["default"] = 0.95
        base_types["required"]["history"][1]["default"] = 12
        
        return base_types


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "KimiLanguageAPI": KimiLanguageAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KimiLanguageAPI": "Kimi_语言丨API"
}
