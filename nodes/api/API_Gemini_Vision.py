# -*- coding: utf-8 -*-
"""
Gemini Vision API节点 - 基于通用框架
调用Gemini视觉模型API进行图像理解和分析
支持Google AI Studio平台
"""

from typing import Dict, Any
from .base_api_framework import (
    BaseVisionAPINode, 
    BasePlatformAdapter, 
    PlatformConfig
)


class GoogleAIStudioGeminiVisionAdapter(BasePlatformAdapter):
    """Google AI Studio Gemini视觉平台适配器"""
    
    def prepare_api_params(self, base_params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        params = base_params.copy()
        
        # Gemini不支持重复惩罚参数，但保持兼容性
        repetition_penalty = kwargs.get('repetition_penalty', 1.0)
        if repetition_penalty != 1.0:
            # Gemini使用不同的参数名，转换为temperature调整
            current_temp = params.get('temperature', 0.4)
            adjusted_temp = max(0.0, min(2.0, current_temp + (repetition_penalty - 1.0) * 0.3))
            params['temperature'] = adjusted_temp
        
        # 应用token限制
        params["max_tokens"] = self.apply_token_limit(params["max_tokens"])
        
        # Google AI Studio特定参数
        # 添加图像质量参数支持
        image_quality = kwargs.get('image_quality', 'auto')
        params = self.handle_image_quality(params, image_quality)
        
        # 根据文档，Gemini API通过OpenAI兼容层支持思考功能
        # 可以添加reasoning_effort参数（low, medium, high）
        reasoning_effort = kwargs.get('reasoning_effort', None)
        if reasoning_effort and reasoning_effort in ['low', 'medium', 'high']:
            params["reasoning_effort"] = reasoning_effort
        
        return params


class GeminiVisionAPI(BaseVisionAPINode):
    """
    Gemini视觉模型API调用节点 - 框架版本
    支持Google AI Studio平台的Gemini视觉模型调用
    """
    
    # 节点信息
    NODE_NAME = "GeminiVisionAPI"
    DISPLAY_NAME = "Gemini_视觉丨API"
    
    # 重写返回名称以适合视觉分析
    RETURN_NAMES = ("analysis_result", "conversation_info", "total_tokens")
    
    # 平台配置
    PLATFORM_CONFIGS = {
        "Google AI Studio": PlatformConfig(
            name="Google AI Studio",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key_env="GEMINI_API_KEY",
            config_key="gemini_api_key",
            platform_key="google_ai_studio_vision",
            models=[
                "gemini-2.5-pro",
                "gemini-2.5-flash-preview-09-2025",
                "gemini-2.5-flash-lite-preview-09-2025",
                "gemini-2.5-flash", 
                "gemini-2.5-flash-lite",
                "gemini-2.0-flash"
            ],
            model_mapping={
                "gemini-2.5-pro": "gemini-2.5-pro",
                "gemini-2.5-flash": "gemini-2.5-flash",
                "gemini-2.5-flash-lite": "gemini-2.5-flash-lite", 
                "gemini-2.0-flash": "gemini-2.0-flash",
                "gemini-2.5-flash-preview-09-2025": "gemini-2.5-flash-preview-09-2025",
                "gemini-2.5-flash-lite-preview-09-2025": "gemini-2.5-flash-lite-preview-09-2025"
            },
            max_tokens_limit=8192,
            supports_frequency_penalty=False,  # Gemini使用不同的参数控制
            supports_repetition_penalty=False
        )
    }
    
    # 平台适配器映射
    PLATFORM_ADAPTERS = {
        "Google AI Studio": GoogleAIStudioGeminiVisionAdapter
    }
    
    @classmethod
    def get_input_types(cls) -> Dict[str, Any]:
        """重写输入类型以添加Gemini视觉特定的提示信息和图像质量参数"""
        base_types = super().get_input_types()
        
        # 自定义Gemini视觉的提示信息
        base_types["required"]["text_input"][1]["tooltip"] = "输入要发送给Gemini视觉模型的文本问题，Gemini擅长图像理解、多模态推理、代码生成和复杂视觉分析"
        base_types["required"]["model"][1]["tooltip"] = """选择要使用的Gemini视觉模型
📋 Google AI Studio模型特点：
🔸 gemini-2.5-pro：最新专业版，最强性能和思考能力
🔸 gemini-2.5-flash-preview-09-2025：2025年9月预览版Flash模型，最新特性
🔸 gemini-2.5-flash-lite-preview-09-2025：2025年9月预览版轻量模型，快速响应
🔸 gemini-2.5-flash：最新Flash模型，速度和质量平衡
🔸 gemini-2.5-flash-lite：轻量版2.5模型，快速响应 (默认推荐)
🔸 gemini-2.0-flash：新一代Flash模型，性能提升

💡 Gemini在多模态理解、代码识别、图表分析、创意生成方面表现优异
💭 2.5系列支持深度思考功能，可设置推理努力级别
📖 参考文档：https://ai.google.dev/gemini-api/docs/openai"""
        
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
        
        # 添加Gemini特有的推理努力参数
        new_optional["reasoning_effort"] = (["none", "low", "medium", "high"], {
            "default": "none",
            "tooltip": "推理深度：none(关闭), low(轻度思考), medium(中度思考), high(深度思考) - Gemini 2.5系列特有功能"
        })
        
        # 最后添加clear_history参数
        new_optional["clear_history"] = base_types["optional"]["clear_history"]
        
        # 替换原有的optional字典
        base_types["optional"] = new_optional
        
        # 调整Gemini视觉的默认值
        base_types["optional"]["temperature"][1]["default"] = 0.4  # Gemini建议稍高的温度
        base_types["optional"]["top_p"][1]["default"] = 0.95  # Gemini支持更高的top_p值
        base_types["required"]["history"][1]["default"] = 6  # Gemini支持较长的对话历史
        base_types["required"]["max_tokens"][1]["default"] = 4096  # Gemini可以生成较长的回答
        base_types["required"]["model"][1]["default"] = "gemini-2.5-flash-lite"  # 设置默认模型（轻量级2.5）
        
        return base_types
    
    def generate_response(self, image, text_input: str, platform: str, model: str, max_tokens: int, history: int,
                         temperature: float = 0.4, top_p: float = 0.95, 
                         image_quality: str = "auto", reasoning_effort: str = "none", clear_history: bool = False):
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

获取Gemini API密钥：https://aistudio.google.com/app/apikey

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
            
            # 通过适配器准备最终参数（包含图像质量和推理努力）
            final_params = adapter.prepare_api_params(
                base_params, 
                image_quality=image_quality,
                reasoning_effort=reasoning_effort
            )
            
            # 调用API
            response = client.chat.completions.create(**final_params)
            
            # 处理响应
            reply, usage_info = self._handle_api_response(response, conversation_key)
            
            # 生成对话信息
            reasoning_info = f" | 推理: {reasoning_effort}" if reasoning_effort != "none" else ""
            conversation_info = f"平台: {platform} | 模型: {model} | 历史轮数: {len(messages)//2} | 图像质量: {image_quality}{reasoning_info} | 总Tokens: {usage_info['total_tokens']} (输入: {usage_info['prompt_tokens']}, 输出: {usage_info['completion_tokens']}, 限制: {max_tokens})"
            
            return (reply, conversation_info, usage_info['total_tokens'])
            
        except Exception as e:
            error_message = f"{self.NODE_NAME} API调用失败 ({platform}): {str(e)}"
            return (error_message, "错误状态", 0)


# ComfyUI节点注册
NODE_CLASS_MAPPINGS = {
    "GeminiVisionAPI": GeminiVisionAPI
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GeminiVisionAPI": "Gemini_视觉丨API"
}
