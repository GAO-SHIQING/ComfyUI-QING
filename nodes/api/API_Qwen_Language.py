# -*- coding: utf-8 -*-
"""
Qwen Language API节点 - 基于通用框架
调用Qwen语言模型API进行文本推理
支持平台：阿里云百炼、硅基流动
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseLanguageAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class AliyunQwenAdapter(BasePlatformAdapter):
    """阿里云百炼Qwen平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 对于qwq模型，使用更保守的参数
        model = kwargs.get('model', '')
        if "qwq" in model.lower():
            params["temperature"] = min(params.get("temperature", 0.7), 0.5)
        
        return params


class SiliconFlowQwenAdapter(BasePlatformAdapter):
    """硅基流动Qwen平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 应用token限制
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        return params


class QwenLanguageAPI(BaseLanguageAPINode):
    """
    Qwen语言模型API调用节点 - 框架版本
    支持阿里云百炼和硅基流动平台的Qwen模型调用
    """
    
    # 节点信息
    NODE_NAME = "QwenLanguageAPI"
    DISPLAY_NAME = "Qwen_语言丨API"
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "阿里云百炼": PlatformConfig(
            name="阿里云百炼",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="DASHSCOPE_API_KEY",
            config_key="dashscope_api_key",
            platform_key="qwen_dashscope",
            models=[
                "qwen3-max", "qwen3-235b-a22b-instruct-2507", "qwen3-30b-a3b-instruct-2507", 
                "qwen-plus", "qwen-max", "qwq-plus", "qwen-turbo"
            ],
            model_mapping={
                "qwen3-max": "qwen-max",
                "qwen3-235b-a22b-instruct-2507": "qwen2.5-72b-instruct",
                "qwen3-30b-a3b-instruct-2507": "qwen2.5-32b-instruct", 
                "qwen-plus": "qwen-plus",
                "qwen-max": "qwen-max",
                "qwq-plus": "qwq-32b-preview",
                "qwen-turbo": "qwen-turbo"
            },
            supports_frequency_penalty=True
        ),
        "硅基流动": PlatformConfig(
            name="硅基流动",
            base_url="https://api.siliconflow.cn/v1",
            api_key_env="SILICONFLOW_API_KEY",
            config_key="siliconflow_api_key",
            platform_key="qwen_siliconflow",
            models=[
                "qwen3-next-80b-a3b-instruct", "qwen3-235b-a22b-instruct-2507", 
                "qwen3-30b-a3b-instruct-2507", "qwen3-8b"
            ],
            model_mapping={
                "qwen3-next-80b-a3b-instruct": "Qwen/Qwen2.5-72B-Instruct",
                "qwen3-235b-a22b-instruct-2507": "Qwen/Qwen2.5-32B-Instruct", 
                "qwen3-30b-a3b-instruct-2507": "Qwen/Qwen2.5-14B-Instruct",
                "qwen3-8b": "Qwen/Qwen2.5-7B-Instruct"
            },
            max_tokens_limit=4096,
            supports_frequency_penalty=True
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "阿里云百炼": AliyunQwenAdapter,
        "硅基流动": SiliconFlowQwenAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加Qwen特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义Qwen的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给Qwen模型的文本内容，Qwen擅长逻辑推理、数学计算、代码生成和多语言处理"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的Qwen模型
📋 模型特点：
🔸 qwen3-max：最新旗舰版本，超强推理能力，适合复杂任务
🔸 qwen-plus：高性能版本，平衡效果与速度
🔸 qwen-turbo：快速响应版本，适合简单对话
🔸 qwq-plus：专业推理版本，擅长逻辑分析和数学问题
🔸 qwen3-235b：超大参数模型，顶级性能
💡 Qwen模型在中文理解、代码生成、数学推理方面表现优异"""
        
        base_types["required"]["max_tokens"][1]["tooltip"] = "模型生成文本时最多能使用的token数量。注意：硅基流动平台限制最大4096，阿里云百炼支持更高值"
        
        # 调整默认值
        base_types["optional"]["temperature"][1]["default"] = 0.3
        base_types["optional"]["top_p"][1]["default"] = 0.85
        
        return base_types


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "QwenLanguageAPI": QwenLanguageAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenLanguageAPI": "Qwen_语言丨API"
}
