# -*- coding: utf-8 -*-
"""
GLM Language API节点 - 基于通用框架
调用GLM语言模型API进行文本推理
支持多平台：智谱AI、其他兼容OpenAI格式的服务端
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseLanguageAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class StandardGLMAdapter(BasePlatformAdapter):
    """标准GLM平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 应用token限制（如果有）
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        return params


class GLMLanguageAPI(BaseLanguageAPINode):
    """
    GLM语言模型API调用节点 - 框架版本
    支持多个服务平台的GLM模型调用
    """
    
    # 节点信息
    NODE_NAME = "GLMLanguageAPI"
    DISPLAY_NAME = "GLM_语言丨API"
    
    # GLM模型列表 (按版本和功能有序排列)
    GLM_MODELS = [
        # GLM-4.5 系列（最新版本）
        "GLM-4.5-Flash",
        "GLM-4.5",
        "GLM-4.5-X",
        "GLM-4.5-Air",
        "GLM-4.5-AirX",
        
        # GLM-4 系列（经典版本）
        "GLM-4-Flash",
        "GLM-4-Flash-250414",
        "GLM-4-FlashX",
        "GLM-4-Plus",
        "GLM-4",
        "GLM-4-0520", 
        "GLM-4-Long",
        "GLM-4-Air",
        "GLM-4-AirX",
        
        # GLM-3 系列（早期版本）
        "GLM-3-Turbo"
    ]
    
    # 硅基流动GLM模型列表
    SILICONFLOW_GLM_MODELS = [
        "GLM-4.5",
        "GLM-4.5-Air", 
        "GLM-Z1-32B-0414",
        "GLM-4-32B-0414",
        "GLM-Z1-9B-0414",
        "GLM-4-9B-0414"
    ]
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "智谱AI": PlatformConfig(
            name="智谱AI",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            api_key_env="ZHIPUAI_API_KEY",
            config_key="glm_api_key",
            platform_key="zhipuai",
            models=GLM_MODELS,
            model_mapping={
                "GLM-4.5-Flash": "glm-4.5-flash",
                "GLM-4.5": "glm-4.5",
                "GLM-4.5-X": "glm-4.5-x",
                "GLM-4.5-Air": "glm-4.5-air",
                "GLM-4.5-AirX": "glm-4.5-airx",
                "GLM-4-Flash": "glm-4-flash",
                "GLM-4-Flash-250414": "glm-4-flash-250414",
                "GLM-4-FlashX": "glm-4-flashx",
                "GLM-4-Plus": "glm-4-plus",
                "GLM-4": "glm-4",
                "GLM-4-0520": "glm-4-0520",
                "GLM-4-Long": "glm-4-long",
                "GLM-4-Air": "glm-4-air",
                "GLM-4-AirX": "glm-4-airx",
                "GLM-3-Turbo": "glm-3-turbo"
            },
            supports_frequency_penalty=True
        ),
        "硅基流动": PlatformConfig(
            name="硅基流动",
            base_url="https://api.siliconflow.cn/v1",
            api_key_env="SILICONFLOW_API_KEY",
            config_key="siliconflow_api_key",
            platform_key="glm_siliconflow",
            models=SILICONFLOW_GLM_MODELS,
            model_mapping={
                "GLM-4.5": "zai-org/GLM-4.5",
                "GLM-4.5-Air": "zai-org/GLM-4.5-Air",
                "GLM-Z1-32B-0414": "THUDM/GLM-Z1-32B-0414",
                "GLM-4-32B-0414": "THUDM/GLM-4-32B-0414", 
                "GLM-Z1-9B-0414": "THUDM/GLM-Z1-9B-0414",
                "GLM-4-9B-0414": "THUDM/GLM-4-9B-0414"
            },
            max_tokens_limit=4096,
            supports_frequency_penalty=True
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "智谱AI": StandardGLMAdapter,
        "硅基流动": StandardGLMAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加GLM特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义GLM的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给GLM模型的文本内容，GLM擅长中文理解、逻辑推理和创意写作"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的GLM模型
📋 智谱AI模型特点：
🔸 GLM-4.5-Flash：最新快速版本，响应迅速，适合日常对话
🔸 GLM-4.5：最新标准版本，平衡性能和质量
🔸 GLM-4：经典版本，稳定可靠
🔸 GLM-4-Long：长文本版本，支持超长上下文
🔸 GLM-4-FlashX：超快响应版本

📋 硅基流动模型特点：
🔸 GLM-4.5：高性能版本，适合复杂推理
🔸 GLM-4.5-Air：轻量级版本，快速响应
🔸 GLM-Z1-32B-0414：大参数版本，强大的理解能力
🔸 GLM-4-32B-0414：经典大参数版本
💡 GLM模型在中文理解、创意写作、代码生成方面表现优异"""
        
        # 调整GLM的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.7
        base_types["optional"]["top_p"][1]["default"] = 0.9
        base_types["required"]["history"][1]["default"] = 10
        base_types["required"]["max_tokens"][1]["default"] = 4096
        
        return base_types


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "GLMLanguageAPI": GLMLanguageAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GLMLanguageAPI": "GLM_语言丨API"
}