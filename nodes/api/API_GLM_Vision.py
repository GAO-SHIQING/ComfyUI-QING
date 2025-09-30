# -*- coding: utf-8 -*-
"""
GLM Vision API节点 - 基于通用框架
调用GLM视觉模型API进行图像理解和分析
支持智谱AI平台
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseVisionAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class StandardGLMVisionAdapter(BasePlatformAdapter):
    """标准GLM视觉平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数（如果支持）
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 应用token限制（如果有）
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        # 添加图像质量参数支持
        image_quality = kwargs.get('image_quality', 'auto')
        params = self.handle_image_quality(params, image_quality)
        
        return params


class GLMVisionAPI(BaseVisionAPINode):
    """
    GLM视觉模型API调用节点 - 框架版本
    支持智谱AI平台的GLM视觉模型调用
    """
    
    # 节点信息
    NODE_NAME = "GLMVisionAPI"
    DISPLAY_NAME = "GLM_视觉丨API"
    
    # GLM视觉模型列表
    GLM_VISION_MODELS = [
        # GLM-4.5V 系列（最新视觉模型）
        "GLM-4.5V",
        
        # GLM-4.1V Thinking 系列（支持思维链推理）
        "GLM-4.1V-Thinking-FlashX", 
        
        # GLM-4V 系列（经典视觉模型）
        "GLM-4V-Flash",  # 快速版本
        "GLM-4V",        # 标准版本  
        "GLM-4V-Plus",   # 增强版本
    ]
    
    # 硅基流动GLM视觉模型列表
    SILICONFLOW_GLM_VISION_MODELS = [
        "GLM-4.5V",
        "GLM-4.1V-9B-Thinking"
    ]
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "智谱AI": PlatformConfig(
            name="智谱AI",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            api_key_env="ZHIPUAI_API_KEY",
            config_key="glm_api_key",
            platform_key="zhipuai_vision",
            models=GLM_VISION_MODELS,
            model_mapping={
                "GLM-4.5V": "glm-4.5v",
                "GLM-4.1V-Thinking-FlashX": "glm-4.1v-thinking-flashx",
                "GLM-4V-Flash": "glm-4v-flash",
                "GLM-4V": "glm-4v",
                "GLM-4V-Plus": "glm-4v-plus"
            },
            supports_frequency_penalty=True
        ),
        "硅基流动": PlatformConfig(
            name="硅基流动",
            base_url="https://api.siliconflow.cn/v1",
            api_key_env="SILICONFLOW_API_KEY",
            config_key="siliconflow_api_key",
            platform_key="glm_vision_siliconflow",
            models=SILICONFLOW_GLM_VISION_MODELS,
            model_mapping={
                "GLM-4.5V": "zai-org/GLM-4.5V",
                "GLM-4.1V-9B-Thinking": "THUDM/GLM-4.1V-9B-Thinking"
            },
            max_tokens_limit=4096,
            supports_frequency_penalty=True
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "智谱AI": StandardGLMVisionAdapter,
        "硅基流动": StandardGLMVisionAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加GLM视觉特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义GLM视觉的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给GLM视觉模型的文本问题，GLM擅长图像理解、文档分析和视觉推理"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的GLM视觉模型
📋 智谱AI模型特点：
🔸 GLM-4.5V：最新视觉模型，全面提升的图像理解能力
🔸 GLM-4.1V-Thinking-FlashX：思维链推理版本，擅长复杂视觉分析
🔸 GLM-4V-Flash：快速响应版本，适合实时应用
🔸 GLM-4V：标准视觉版本，平衡性能和效果
🔸 GLM-4V-Plus：增强版本，高精度图像理解

📋 硅基流动模型特点：
🔸 GLM-4.5V：高性能视觉模型，性价比优秀
🔸 GLM-4.1V-9B-Thinking：9B参数思维链模型，高效推理
💡 GLM视觉模型在文档理解、图表分析、场景识别方面表现优异"""
        
        # 重建optional字典以确保参数顺序
        new_optional = {}
        
        # 保持原有参数顺序
        new_optional["temperature"] = base_types["optional"]["temperature"]
        new_optional["top_p"] = base_types["optional"]["top_p"]
        
        # 插入图像质量参数
        new_optional["image_quality"] = (["auto", "low", "high"], {
            "default": "auto",
            "tooltip": "图像处理质量：auto(自动选择), low(低质量，速度快), high(高质量，精度高)"
        })
        
        # 最后添加clear_history参数
        new_optional["clear_history"] = base_types["optional"]["clear_history"]
        
        # 替换原有的optional字典
        base_types["optional"] = new_optional
        
        # 调整GLM视觉的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.7
        base_types["optional"]["top_p"][1]["default"] = 0.9
        base_types["required"]["history"][1]["default"] = 8
        
        return base_types


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "GLMVisionAPI": GLMVisionAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GLMVisionAPI": "GLM_视觉丨API"
}
