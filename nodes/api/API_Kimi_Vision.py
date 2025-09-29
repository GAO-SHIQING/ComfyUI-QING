# -*- coding: utf-8 -*-
"""
Kimi Vision API节点 - 基于通用框架
调用Kimi视觉模型API进行图像理解和分析
支持月之暗面平台
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseVisionAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class StandardKimiVisionAdapter(BasePlatformAdapter):
    """标准Kimi视觉平台适配器"""
    
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


class KimiVisionAPI(BaseVisionAPINode):
    """
    Kimi视觉模型API调用节点 - 框架版本
    支持月之暗面平台的Kimi视觉模型调用
    """
    
    # 节点信息
    NODE_NAME = "KimiVisionAPI"
    DISPLAY_NAME = "Kimi_视觉丨API"
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "月之暗面": PlatformConfig(
            name="月之暗面",
            base_url="https://api.moonshot.cn/v1",
            api_key_env="MOONSHOT_API_KEY",
            config_key="moonshot_api_key",
            platform_key="moonshot_vision",
            models=["kimi-latest-8k", "kimi-latest-32k", "kimi-latest-128k"],
            model_mapping={
                "kimi-latest-8k": "kimi-latest",
                "kimi-latest-32k": "kimi-latest",
                "kimi-latest-128k": "kimi-latest"
            },
            supports_frequency_penalty=True
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "月之暗面": StandardKimiVisionAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加Kimi视觉特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义Kimi视觉的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给Kimi视觉模型的文本问题，Kimi擅长图像理解、场景分析和视觉问答"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的Kimi视觉模型
📋 模型特点：
🔸 kimi-latest-8k：8K上下文版本，适合简单图像分析
🔸 kimi-latest-32k：32K上下文版本，适合复杂图像理解
🔸 kimi-latest-128k：128K上下文版本，支持超长对话和详细分析
💡 Kimi视觉模型在图像理解、文字识别、场景分析方面表现优异"""
        
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
        
        # 调整Kimi视觉的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.8
        base_types["optional"]["top_p"][1]["default"] = 0.95
        base_types["required"]["history"][1]["default"] = 8
        
        return base_types


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "KimiVisionAPI": KimiVisionAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "KimiVisionAPI": "Kimi_视觉丨API"
}
