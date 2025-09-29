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
        "glm-4.5-flash",
        "glm-4.5",
        "glm-4.5-x",
        "glm-4.5-air",
        "glm-4.5-airx",
        
        # GLM-4 系列（经典版本）
        "glm-4-flash",
        "glm-4-flash-250414",
        "glm-4-flashx",
        "glm-4-plus",
        "glm-4",
        "glm-4-0520", 
        "glm-4-long",
        "glm-4-air",
        "glm-4-airx",
        
        # GLM-3 系列（早期版本）
        "glm-3-turbo"
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
            model_mapping={model: model for model in GLM_MODELS},  # GLM模型名称不需要映射
            supports_frequency_penalty=True
    ),
    # 后续可以添加其他支持GLM模型的平台
    # "其他平台": PlatformConfig(...)
}
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "智谱AI": StandardGLMAdapter,
        # 后续添加的平台也使用StandardGLMAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加GLM特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义GLM的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给GLM模型的文本内容，GLM擅长中文理解、逻辑推理和创意写作"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的GLM模型
📋 模型特点：
🔸 glm-4.5-flash：最新快速版本，响应迅速，适合日常对话
🔸 glm-4.5：最新标准版本，平衡性能和质量
🔸 glm-4：经典版本，稳定可靠
🔸 glm-4-long：长文本版本，支持超长上下文
🔸 GLM-4-FlashX：超快响应版本
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