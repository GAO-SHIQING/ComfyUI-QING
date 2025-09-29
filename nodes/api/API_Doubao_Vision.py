# -*- coding: utf-8 -*-
"""
Doubao Vision API节点 - 基于通用框架
调用Doubao视觉模型API进行图像理解和分析
支持火山引擎平台
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseVisionAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class StandardDoubaoVisionAdapter(BasePlatformAdapter):
    """标准Doubao视觉平台适配器"""
    
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


class DoubaoVisionAPI(BaseVisionAPINode):
    """
    Doubao视觉模型API调用节点 - 框架版本
    支持火山引擎平台的Doubao视觉模型调用
    """
    
    # 节点信息
    NODE_NAME = "DoubaoVisionAPI"
    DISPLAY_NAME = "Doubao_视觉丨API"
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "火山引擎": PlatformConfig(
            name="火山引擎",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key_env="VOLCENGINE_API_KEY",
            config_key="volcengine_api_key",
            platform_key="volcengine_vision",
            models=[
                "Doubao-Seed-1.6", 
                "Doubao-Seed-1.6-thinking", 
                "Doubao-Seed-1.6-flash", 
                "Doubao-Seed-1.6-vision", 
                "Doubao-1.5-vision-pro", 
                "Doubao-1.5-vision-lite", 
                "Doubao-1.5-thinking-vision-pro",
                "Doubao-1.5-UI-TARS",
                "Doubao-Seed-Translation"
            ],
            model_mapping={
                "Doubao-Seed-1.6": "doubao-seed-1-6-250615",
                "Doubao-Seed-1.6-thinking": "doubao-seed-1-6-thinking-250715",
                "Doubao-Seed-1.6-flash": "doubao-seed-1-6-flash-250828",
                "Doubao-Seed-1.6-vision": "doubao-seed-1-6-vision-250815",
                "Doubao-1.5-vision-pro": "doubao-1.5-vision-pro-250328",
                "Doubao-1.5-vision-lite": "doubao-1.5-vision-lite-250315",
                "Doubao-1.5-thinking-vision-pro": "doubao-1-5-thinking-vision-pro-250428",
                "Doubao-1.5-UI-TARS": "doubao-1-5-ui-tars-250428",
                "Doubao-Seed-Translation": "doubao-seed-translation-250915"
            },
            supports_frequency_penalty=True
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "火山引擎": StandardDoubaoVisionAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加Doubao视觉特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义Doubao视觉的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给Doubao视觉模型的文本问题，Doubao擅长图像理解、UI分析和视觉推理"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的Doubao视觉模型
📋 模型特点：
🔸 Doubao-Seed-1.6：最新种子版本，全面提升的视觉理解能力
🔸 Doubao-Seed-1.6-thinking：思维链推理版本，擅长复杂视觉分析
🔸 Doubao-Seed-1.6-flash：快速响应版本，适合实时应用
🔸 Doubao-1.5-vision-pro：专业视觉版本，高精度图像理解
🔸 Doubao-1.5-UI-TARS：UI专用版本，擅长界面元素识别
💡 Doubao视觉模型在UI分析、文档理解、场景识别方面表现卓越"""
        
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
        
        # 调整Doubao视觉的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.7
        base_types["optional"]["top_p"][1]["default"] = 0.9
        base_types["required"]["history"][1]["default"] = 10
        
        # 设置默认模型为 Doubao-1.5-vision-pro
        base_types["required"]["model"][1]["default"] = "Doubao-1.5-vision-pro"
        
        return base_types


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "DoubaoVisionAPI": DoubaoVisionAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DoubaoVisionAPI": "Doubao_视觉丨API"
}
