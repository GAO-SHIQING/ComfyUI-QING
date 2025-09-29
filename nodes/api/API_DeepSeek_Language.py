# -*- coding: utf-8 -*-
"""
DeepSeek Language API节点 - 基于通用框架
调用DeepSeek语言模型API进行文本推理
支持多平台：火山引擎、阿里云百炼、硅基流动、腾讯云
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseLanguageAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class StandardDeepSeekAdapter(BasePlatformAdapter):
    """标准DeepSeek平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 应用token限制（如果有）
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        return params


class DeepSeekLanguageAPI(BaseLanguageAPINode):
    """
    DeepSeek语言模型API调用节点 - 框架版本
    支持多个服务平台的DeepSeek模型调用
    """
    
    # 节点信息
    NODE_NAME = "DeepSeekLanguageAPI"
    DISPLAY_NAME = "DeepSeek_语言丨API"
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "火山引擎": PlatformConfig(
            name="火山引擎",
            base_url="https://ark.cn-beijing.volces.com/api/v3",
            api_key_env="VOLCENGINE_API_KEY",
            config_key="volcengine_api_key",
            platform_key="volcengine",
            models=["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            model_mapping={
                "DeepSeek-V3.1": "deepseek-v3-1-250821",
                "DeepSeek-R1": "deepseek-r1-250528",
                "DeepSeek-V3": "deepseek-v3-250324"
            },
            supports_frequency_penalty=True
        ),
        "阿里云百炼": PlatformConfig(
            name="阿里云百炼",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="DASHSCOPE_API_KEY", 
            config_key="dashscope_api_key",
            platform_key="dashscope",
            models=["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            model_mapping={
                "DeepSeek-V3.1": "deepseek-v3.1",        
                "DeepSeek-R1": "deepseek-r1-0528",       
                "DeepSeek-V3": "deepseek-v3"             
            },
            supports_frequency_penalty=True
        ),
        "硅基流动": PlatformConfig(
            name="硅基流动",
            base_url="https://api.siliconflow.cn/v1",
            api_key_env="SILICONFLOW_API_KEY",
            config_key="siliconflow_api_key",
            platform_key="siliconflow",
            models=["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            model_mapping={
                "DeepSeek-V3.1": "deepseek-ai/DeepSeek-V3.1",
                "DeepSeek-R1": "deepseek-ai/DeepSeek-R1",
                "DeepSeek-V3": "deepseek-ai/DeepSeek-V3"
            },
            supports_frequency_penalty=True
        ),
        "腾讯云": PlatformConfig(
            name="腾讯云",
            base_url="https://api.lkeap.cloud.tencent.com/v1",
            api_key_env="TENCENT_LKEAP_API_KEY",
            config_key="tencent_lkeap_api_key",
            platform_key="tencent",
            models=["DeepSeek-V3.1", "DeepSeek-R1", "DeepSeek-V3"],
            model_mapping={
                "DeepSeek-V3.1": "deepseek-v3.1",
                "DeepSeek-R1": "deepseek-r1-0528",
                "DeepSeek-V3": "deepseek-v3-0324"
            },
            supports_frequency_penalty=True
        )
    }
    
    # 所有平台使用相同的适配器
    PLATFORM_ADAPTERS = {
        "火山引擎": StandardDeepSeekAdapter,
        "阿里云百炼": StandardDeepSeekAdapter,
        "硅基流动": StandardDeepSeekAdapter,
        "腾讯云": StandardDeepSeekAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加DeepSeek特定的提示信息"""
        base_types = super().get_input_types()
        
        # 自定义DeepSeek的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给DeepSeek模型的文本内容，DeepSeek擅长代码生成、数学推理和逻辑分析"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的DeepSeek模型
📋 模型特点：
🔸 DeepSeek-V3.1：最新版本，全面提升的推理和代码能力
🔸 DeepSeek-R1：推理专家版本，擅长复杂逻辑推理
🔸 DeepSeek-V3：稳定版本，平衡性能和效率
💡 DeepSeek模型在代码生成、数学问题求解、逻辑推理方面表现卓越"""
        
        # 调整DeepSeek的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.7
        base_types["optional"]["top_p"][1]["default"] = 0.9
        
        return base_types


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "DeepSeekLanguageAPI": DeepSeekLanguageAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DeepSeekLanguageAPI": "DeepSeek_语言丨API"
}
