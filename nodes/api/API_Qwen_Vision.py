# -*- coding: utf-8 -*-
"""
Qwen Vision API节点 - 基于通用框架
调用Qwen视觉模型API进行图像理解和分析
支持阿里云百炼、硅基流动平台
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseVisionAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class AliyunQwenVisionAdapter(BasePlatformAdapter):
    """阿里云百炼Qwen视觉平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数（视觉模型通常不需要，但保持兼容性）
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 应用token限制
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        # 阿里云百炼特定参数
        # 添加图像质量参数支持
        image_quality = kwargs.get('image_quality', 'auto')
        params = self.handle_image_quality(params, image_quality)
        
        return params


class SiliconFlowQwenVisionAdapter(BasePlatformAdapter):
    """硅基流动Qwen视觉平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # 处理重复惩罚参数
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        params = self.handle_repetition_penalty(params, repetition_penalty)
        
        # 应用token限制
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        # 硅基流动特定参数处理
        # 添加图像质量参数支持
        image_quality = kwargs.get('image_quality', 'auto')
        params = self.handle_image_quality(params, image_quality)
        
        return params


class QwenVisionAPI(BaseVisionAPINode):
    """
    Qwen视觉模型API调用节点 - 框架版本
    支持阿里云百炼和硅基流动平台的Qwen视觉模型调用
    """
    
    # 节点信息
    NODE_NAME = "QwenVisionAPI"
    DISPLAY_NAME = "Qwen_视觉丨API"
    
    # 重写返回名称以适合视觉分析
    RETURN_NAMES = ("analysis_result", "conversation_info", "total_tokens")
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "阿里云百炼": PlatformConfig(
            name="阿里云百炼",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key_env="DASHSCOPE_API_KEY",
            config_key="dashscope_api_key",
            platform_key="dashscope_vision",
            models=[
                "qwen3-vl-plus", 
                "qwen3-vl-235b-a22b-instruct", 
                "qwen-vl-max-latest", 
                "qwen2.5-vl-72b-instruct"
            ],
            model_mapping={
                "qwen3-vl-plus": "qwen-vl-plus",
                "qwen3-vl-235b-a22b-instruct": "qwen2.5-vl-72b-instruct",
                "qwen-vl-max-latest": "qwen-vl-max-latest",
                "qwen2.5-vl-72b-instruct": "qwen2.5-vl-72b-instruct"
            },
            max_tokens_limit=8192,
            supports_frequency_penalty=True
        ),
        "硅基流动": PlatformConfig(
            name="硅基流动",
            base_url="https://api.siliconflow.cn/v1",
            api_key_env="SILICONFLOW_API_KEY",
            config_key="siliconflow_api_key",
            platform_key="siliconflow_vision",
            models=["qwen2.5-vl-72b-instruct"],
            model_mapping={
                "qwen2.5-vl-72b-instruct": "Qwen/Qwen2-VL-72B-Instruct"
            },
            max_tokens_limit=4096,
            supports_frequency_penalty=True
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "阿里云百炼": AliyunQwenVisionAdapter,
        "硅基流动": SiliconFlowQwenVisionAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加Qwen视觉特定的提示信息和图像质量参数"""
        base_types = super().get_input_types()
        
        # 自定义Qwen视觉的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给Qwen视觉模型的文本问题，Qwen-VL擅长图像理解、文档分析、OCR识别和视觉推理"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的Qwen视觉模型
📋 阿里云百炼模型特点：
🔸 qwen3-vl-plus：新一代视觉模型，图像理解能力强，推荐首选
🔸 qwen3-vl-235b-a22b-instruct：大参数视觉模型，精度更高
🔸 qwen-vl-max-latest：最新旗舰视觉模型，功能最全面
🔸 qwen2.5-vl-72b-instruct：经典大模型版本，稳定可靠

📋 硅基流动模型特点：
🔸 qwen2.5-vl-72b-instruct：开源版本，性价比高

💡 Qwen-VL系列在图像理解、文档OCR、图表分析、视觉推理方面表现优异"""
        
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
        
        # 调整Qwen视觉的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.3  # Qwen视觉模型建议较低温度
        base_types["optional"]["top_p"][1]["default"] = 0.8
        base_types["required"]["history"][1]["default"] = 5  # 视觉任务通常历史较短
        base_types["required"]["max_tokens"][1]["default"] = 2048  # 视觉描述通常较短
        
        return base_types
    
    def generate_response(self, image, text_input: str, platform: str, model: str, max_tokens: int, history: int,
                         temperature: float = 0.3, top_p: float = 0.8, 
                         image_quality: str = "auto", clear_history: bool = False):
        """
        生成视觉响应，添加图像质量参数支持
        """
        try:
            # 清除历史记录
            if clear_history:
                self.conversation_manager.clear_all()
            
            # 验证输入参数
            is_valid, error_msg = self._validate_inputs(platform, model)
            if not is_valid:
                return (error_msg, "参数错误", 0)
            
            # 获取平台配置和适配器
            platform_config = self.PLATFORM_CONFIGS[platform]
            adapter = self._get_platform_adapter(platform)
            
            # 获取API密钥
            api_key = self.api_key_manager.get_api_key(platform_config)
            if not api_key:
                error_msg = f"""错误：未提供{platform}的API密钥。请尝试以下方法之一：

1. 设置环境变量：{platform_config.api_key_env}
2. 在🎨QING设置中配置API密钥
3. 使用临时文件设置密钥

请配置后重试。"""
                return (error_msg, "API密钥缺失", 0)
            
            # 获取或创建客户端
            client = self.client_manager.get_or_create_client(platform_config, api_key)
            
            # 管理对话历史
            conversation_key = self.conversation_manager.get_conversation_key(
                platform_config.platform_key, model
            )
            
            # 准备视觉消息
            messages = self._prepare_vision_messages(image, text_input, conversation_key)
            
            # 限制历史长度
            self.conversation_manager.limit_history(conversation_key, history)
            
            # 准备基础API参数
            base_params = self._prepare_base_params(
                adapter.get_api_model_name(model),
                messages,
                adapter.apply_token_limit(max_tokens),
                temperature,
                top_p
            )
            
            # 通过适配器准备最终参数（包含图像质量）
            final_params = adapter.prepare_api_params(
                base_params, 
                image_quality=image_quality
            )
            
            # 调用API
            response = client.chat.completions.create(**final_params)
            
            # 处理响应
            reply, usage_info = self._handle_api_response(response, conversation_key)
            
            # 生成对话信息
            conversation_info = f"平台: {platform} | 模型: {model} | 历史轮数: {len(messages)//2} | 图像质量: {image_quality} | 总Tokens: {usage_info['total_tokens']} (输入: {usage_info['prompt_tokens']}, 输出: {usage_info['completion_tokens']}, 限制: {max_tokens})"
            
            return (reply, conversation_info, usage_info['total_tokens'])
            
        except Exception as e:
            error_message = f"{self.NODE_NAME} API调用失败 ({platform}): {str(e)}"
            return (error_message, "错误状态", 0)


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "QwenVisionAPI": QwenVisionAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "QwenVisionAPI": "Qwen_视觉丨API"
}
